Student ID: 16169703, 50572482, 45765950
Student Name: James Liu, Sijie Guo, Qizhi Tian


README - UCI Information Retrieval Assignment 3
==================================
Overview
==================================
This project is an implementation of a search engine for the UCI Information Retrieval course. The project consists of three main components:
1. Indexer: Builds an inverted index from the provided HTML documents.
2. Search Component: Allows users to perform searches using Boolean queries and ranks the results using tf-idf scoring.
3. Search Report: Provides a report of search results for specific queries.

==================================
How to Use the Software
==================================

1. Prerequisites:
- Python 3.x
- Required libraries: BeautifulSoup4, nltk

2. Project Structure:
- indexer.py: Contains the Indexer class responsible for building the inverted index.
- search.py: Contains the search functionality and helper functions.
- main.py: The main entry point to run the indexing and searching processes.
- data/: Directory to store the index files and other related data.
- DEV/: Directory containing the HTML files in JSON format.

3. Running the Code:
- Create DEV directory for your JSON files repository in the current directory.
- To build the index and perform searches, run the main.py file with command line:
	python3 main.py
