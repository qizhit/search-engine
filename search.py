import re
from indexer import Indexer
from collections import defaultdict
import time

inv_index_location = {}
total_indexed_url = 0
total_unique_terms = 0
url_map = {}


stop_words = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't",
              'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
              "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't",
              'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have',
              "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him',
              'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't",
              'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor',
              'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out',
              'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some',
              'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
              "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to',
              'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were',
              "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's",
              'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
              "you've", 'your', 'yours', 'yourself', 'yourselves'}


def get_token_docs(query_tokens, storage_file, stemmer):
    token_records = []  # [[token1_record], [token2_record], ...]
    common_record = set()  # [doc_id, freq, importance, tf_idf]
    for token in query_tokens:
        token = stemmer.stem(token.lower())  # stemming the token
        storage_file.seek(int(inv_index_location[token]))  # get the seek position and find its records from storage
        line = storage_file.readline()
        records = line.strip("\n").split(',')[1:]  # ["doc_id:freq:importance:tf_idf", ...]
        # Sort each records by doc_id
        sorted_records = sorted(records, key=lambda item: item.split(':')[0])
        token_records.append(sorted_records)

    # Use the 3-way merge algorithm to find all record items in common_docs
    pointers = [0] * len(token_records)
    # If any pointer reaches the end of the list, end the while loop
    while all(pointer < len(token_records[i]) for i, pointer in enumerate(pointers)):
        # [record1_id, record2_id, record3_id, ...]
        current_ids = [token_records[i][pointers[i]].split(':')[0] for i in range(len(token_records))]
        min_id = min(current_ids)

        if all(current_id == min_id for current_id in current_ids):
            # All pointers point to elements with the same doc_id, append to common_record
            for i in range(len(token_records)):
                common_record.add(token_records[i][pointers[i]])
                pointers[i] += 1
        else:
            # Else, moves the pointer to the smallest doc_id forward
            for i in range(len(token_records)):
                if current_ids[i] == min_id:
                    pointers[i] += 1

    return list(common_record)


#EC: for 2gram and 3gram
def get_ngrams(tokens, n):
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngrams.append('_'.join(tokens[i:i + n]))
    return ngrams


def search():
    global url_map
    indexer_obj = Indexer()
    stemmer = indexer_obj.word_stemmer
    doc_freq3 = 500

    with open("storage.csv") as storage_file:
        while True:
            try:
                print("--------------------")
                print("Enter q/Q to exit or queries to search")
                query = input(">> ")
                start_time = time.perf_counter()
                if query in ["q", "Q"]:  # exit the search
                    return

                query_tokens = set(re.findall(r'\b[a-zA-Z0-9]+\b', query))  # Match alphanumeric characters
                stop_in_query = query_tokens.intersection(stop_words)
                stop_word_percent = (len(stop_in_query) / len(query_tokens)) * 100
                if stop_word_percent < 40:
                    # Get valid query tokens (not stop words)
                    query_tokens = query_tokens - stop_in_query

                token_records = get_token_docs(query_tokens, storage_file, stemmer)  # 2d arr that store each record for tokens
                doc_rank_lst = search_queries(token_records)
                print(f"{query}: {len(doc_rank_lst)} results\n")
                try:
                    if len(doc_rank_lst) > doc_freq3:
                        for doc in doc_rank_lst[200:500]:
                            print(url_map[doc[1]])
                    else:
                        for doc in doc_rank_lst[:300]:
                            print(url_map[doc[1]])
                except:
                    pass

                end_time = time.perf_counter()
                execution_time = end_time - start_time
                print(f"Search took {execution_time * 1000:.2f} ms.")

            except Exception as e:
                print(f"Unexpected Error2: {e}")


def search_queries(token_records):
    # compute top 5 url
    doc_rank = defaultdict(int)
    for doc in token_records:
        doc = doc.split(":")   # doc_id, freq, importance, tf-idf score
        tf_idf = float(doc[-1])
        doc_rank[doc[0]] += tf_idf  # tf-idf score for a specific term in each doc

    doc_rank_lst = []  # turn scores into list so they can be sorted
    for doc_id, tf_idf_score in doc_rank.items():
        doc_rank_lst.append((tf_idf_score, doc_id))
    doc_rank_lst.sort(reverse=True)

    return doc_rank_lst


def load_info():
    global total_indexed_url, total_unique_terms
    with open("index_of_index.txt") as f:
        for line in f:
            token, pos = line.strip("\n").split(":")
            inv_index_location[token] = pos

    with open("data.txt") as data_f:
        line_num = 0
        for line in data_f:
            if line_num > 2:
                line = line.split(",")
                url_map[line[0]] = line[1]
            else:
                if line_num == 0:
                    total_indexed_url = line
                elif line_num == 1:
                    total_unique_terms = line
            line_num += 1
