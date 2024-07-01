from indexer import indexing
from search import search, load_info
import os

if __name__ == "__main__":
    try:
        # check if the inverted index already exist
        if not os.path.exists("index_of_index.txt") or os.path.getsize("index_of_index.txt") == 0:
            indexing()
        load_info()
        search()
    except Exception as e:
        print(f"Unexpected Error1: {e}")
