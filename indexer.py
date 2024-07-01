import os
import json
import re
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import defaultdict
import csv
import math

important_weight = {}
class Indexer:
    def __init__(self) -> None:
        self.data_directory = r"./DEV"  # JSON files directory
        self.document_identifier = 0
        self.index_map = defaultdict(
            list
        )  # inverted index, key: word, value: document_identifier, freq, importance, tf_idf
        self.url_map = {}  # key: document_identifier, value: url
        self.processed_hashes = (
            set()
        )  # Store the hash of pages; detect and eliminate duplicate pages.
        self.word_stemmer = PorterStemmer()  # Create an instance of PorterStemmer
        self.inv_index_location = defaultdict(int)  # allow the usage of seek() when searching word

    def update_frequency(self, text, freq_map, important_text):
        tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text)  # Match alphanumeric characters
        imp_token = re.findall(r"\b[a-zA-Z0-9]+\b", important_text)
        stemmed_imp_token = []
        for word in imp_token:
            word = self.word_stemmer.stem(word.strip().lower())
            stemmed_imp_token.append(word)

        for word in tokens:
            word = self.word_stemmer.stem(word.lower())  # Get the stem of the word
            count, importance_score = freq_map.get(
                word, (0, 0)
            )  # Get freq and importance form frequency_map
            # Update frequency_map
            if word in stemmed_imp_token:
                if count == 0:
                    count += 1
                else:
                    count *= 2
            else:
                count += 1
            freq_map[word] = (
                count,
                importance_score + (1 if word in stemmed_imp_token else 0),
            )
        return tokens

    def save_to_csv(self):
        file_index = 0
        counter = 0
        csv_file = None
        try:
            for term, postings in self.index_map.items():
                if counter % 10000 == 0:  # Write a new file every 10000 entries
                    if csv_file:
                        csv_file.close()
                    csv_path = f"./storage_part{file_index}.csv"
                    csv_file = open(csv_path, mode="wb")  # Write as binary, lower size
                    file_index += 1  # Add file index for the next new file
                # write data as format: "word, doc_id:freq:importance, ..."
                data = [term.encode("utf-8")] + [
                    f"{post[0]}:{post[1]}:{post[2]}:{post[3]}".encode("utf-8")
                    for post in postings
                ]  # word, document_identifier:freq:importance:tf_idf

                self.inv_index_location[term] = csv_file.tell()
                csv_file.write(b",".join(data) + b"\n")
                counter += 1
        finally:
            if csv_file:
                csv_file.close()
        return file_index

    def save_inv_index_location(self):
        with open("index_of_index.txt", 'w', newline="") as file:
            writer = csv.writer(file)
            for token, pos in self.inv_index_location.items():
                writer.writerow([f"{token}:{pos}"])

    def calculate_file_size(self, path):
        try:
            byte_size = os.path.getsize(path)  # Get byte sizes in a file
            return byte_size / 1024  # Get kilobyte(KB) size
        except FileNotFoundError:
            print("file does not exist。")
            return 0

    def analyze_document(self, file_path):
        frequency_map = defaultdict(int)  # key: word, value: (freq, importance)
        try:
            with open(file_path, "r") as file:
                content_data = json.load(file)
                page_url = content_data["url"]
                self.url_map[self.document_identifier] = page_url
                self.document_identifier += 1
                html_content = BeautifulSoup(
                    content_data["content"], features="html.parser"
                )

                # Get important_tokens from specific tags
                text = html_content.get_text()
                important_tag = html_content.find_all(["b", "strong", "h1", "h2", "h3", "title"])               
                important_text = ' '.join(tag.get_text() for tag in important_tag)
                # Update frequency and important score of the words in text
                self.update_frequency(text, frequency_map, important_text)

            # Check page uniqueness; update the index map if the page is unique
            page_hash = hash(frozenset(frequency_map.items()))
            if page_hash not in self.processed_hashes:
                self.processed_hashes.add(
                    page_hash
                )  # Add the hash of the new page to the collection
                for word, (freq, importance) in frequency_map.items():
                    # compute tf scores for each word in a document
                    tf_score = 1 + math.log10(freq)

                    self.index_map[word].append(
                        (self.document_identifier, freq, importance, tf_score)
                    )
        except Exception as error:
            print(f"ERROR PROCESSING {file_path}: {str(error)}")

    def calc_tf_idf(self):
        for word, postings in self.index_map.items():
            new_postings = []
            for (doc_id, freq, importance, tf_score) in postings:
                idf_score = math.log10(len(self.url_map) / len(self.index_map[word]))
                tf_idf = tf_score * idf_score
                new_postings.append((doc_id, freq, importance, tf_idf))
            self.index_map[word] = new_postings

    def traversing_folder(self):
        for folder in os.listdir(self.data_directory):
            # Get the path of the sub directory in data_directory
            full_path = os.path.join(self.data_directory, folder)
            if os.path.isdir(full_path):
                for file in os.listdir(full_path):
                    # Get the path of the JSON file
                    file_path = os.path.join(full_path, file)
                    if os.path.splitext(file_path)[1] == ".json":
                        self.analyze_document(file_path)


def indexing():
    indexer_obj = Indexer()
    indexer_obj.traversing_folder()

    indexer_obj.calc_tf_idf()
    total_files_index = indexer_obj.save_to_csv()
    with open("storage.csv", "wb") as final_file:
        for i in range(total_files_index):
            part_path = f"./storage_part{i}.csv"
            with open(part_path, "rb") as part_file:
                for line in part_file:
                    word = line.decode().strip("\n").split(',')[0]
                    indexer_obj.inv_index_location[word] = final_file.tell()
                    final_file.write(line)
            os.remove(part_path)  # Delete sub files

    indexer_obj.save_inv_index_location()
    index_file_size = indexer_obj.calculate_file_size("storage.csv")

    print("DOCUMENT PROCESSING COMPLETED")
    print(f"DOCUMENTS INDEXED: {len(indexer_obj.url_map)}")
    print(f"UNIQUE TERMS COUNT: {len(indexer_obj.index_map)}")
    print(f"INDEX FILE SIZE: {index_file_size:.2f} KB")

    report_file_path = "index_report.txt"
    with open(report_file_path, "w") as report:
        report.write("DOCUMENT PROCESSING COMPLETED\n")
        report.write(f"DOCUMENTS INDEXED: {len(indexer_obj.url_map)}\n")
        report.write(f"UNIQUE TERMS COUNT: {len(indexer_obj.index_map)}\n")
        report.write(f"INDEX FILE SIZE: {index_file_size:.2f} KB\n")
        report_file_path = "index_report.txt"

    with open("data.txt", "w") as data_f:
        data_f.write(f"{len(indexer_obj.url_map)}\n")
        data_f.write(f"{len(indexer_obj.index_map)}\n")
        for doc_id, url in indexer_obj.url_map.items():
            data_f.write(f"{doc_id},{url}\n")
