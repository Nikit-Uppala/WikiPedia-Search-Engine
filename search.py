from nltk.corpus import stopwords
import Stemmer
import re
import sys
import os
import numpy as np
from numpy.core.defchararray import index
from encode_decode import decode


if len(sys.argv) < 3:
    print("Too few arguments")
    quit()


stopWords = stopwords.words("english")


def printError():
    print("No inverted index exists in the given directory")
    quit()


def text_preprocessing(text):
    text = text.strip().encode("ascii", errors="ignore").decode()
    text = re.sub(r"&.+;", "", text) # Removing special symbols like &gt; &lt;
    text = re.sub(r"`|~|!|@|#|\$|%|\^|&|\*|\(|\)|-|_|=|\+|\||\\|\[|\]|\{|\}|;|:|'|\"|,|<|>|\.|/|\?|\n|\t", " ", text) # removing non alpha numeric
    text = text.split()
    text = list(filter(lambda x: len(x) > 0 and x not in stopWords, text))
    stemmer = Stemmer.Stemmer("english")
    text = stemmer.stemWords(text)
    query_terms = {}
    for word in text:
        if word not in query_terms.keys():
            query_terms[word] = 0
        query_terms[word] += 1
    return query_terms


def empty_posting_list():
    return {
        "title": [],
        "infobox": [],
        "body": [],
        "references": [],
        "links": [],
        "category": []
    }


def get_posting_lists(token):
    global tokens_in_index, tokens_offsets, inverted_index_file
    lists = empty_posting_list()
    if token not in tokens_in_index.keys():
        return lists
    try:
        with open(inverted_index_file, "r") as file:
            start_seek = decode(tokens_offsets[tokens_in_index[token][0]][0])
            end_seek = decode(tokens_offsets[tokens_in_index[token][0]][1])
            file.seek(start_seek)
            data = file.read(end_seek - start_seek)
            data = data.split("\n")
            for line in data:
                if len(line) == 0:
                    continue
                doc_id = decode(line.split()[0])
                if "t" in line:
                    lists["title"].append(doc_id)
                if "i" in line:
                    lists["infobox"].append(doc_id)
                if "b" in line:
                    lists["body"].append(doc_id)
                if "r" in line:
                    lists["references"].append(doc_id)
                if "l" in line:
                    lists["links"].append(doc_id)
                if "c" in line:
                    lists["category"].append(doc_id)
        return lists
    except:
        print("From inverted index")
        printError()


def get_tokens_data(data):
    data = data.split("\n")
    tokens = {}
    for line in data:
        line = line.split()
        if len(line) > 0:
            tokens[line[0]] = [line[1], line[2], line[3]]
    return tokens


def get_details(query):
    global tokens_file, tokens_offsets
    details = {}
    with open(tokens_file, "r") as file:
        tokens_in_query = list(sorted(query))
        len_tokens = len(tokens_in_query)
        start = 0
        for token in tokens_in_query:
            details[token] = [0, 0, 0]
        letters = set([x[0] for x in tokens_in_query])
        for letter in sorted(letters):
            file.seek(decode(tokens_offsets[letter][0]))
            bytes_to_read = decode(tokens_offsets[letter][1]) - decode(tokens_offsets[letter][0])
            buffer = min(100000, bytes_to_read)
            while bytes_to_read > 0:
                data = file.read(buffer)
                if data[-1] != "\n":
                    data = "".join([data, file.readline()])
                bytes_to_read -= len(data)
                buffer = min(buffer, bytes_to_read)
                tokens_retrieved = get_tokens_data(data.rstrip())
                for i in range(start, len_tokens):
                    token = tokens_in_query[i]
                    if token in tokens_retrieved:
                        details[token] = [decode(tokens_retrieved[token][0]), decode(tokens_retrieved[token][1]), 
                        decode(tokens_retrieved[token][2])]
                        start = i+1
                if start == len_tokens:
                    break
                if tokens_in_query[start][0] != letter:
                    continue
    return details


def getDocsTF(data):
    data = data.split("\n")
    docs_tf = {}
    for line in data:
        line = line.split()
        if len(line) > 0:
            tf = 0
            docID = decode(line[0])
            for i in range(1, len(line)):
                tf += decode(line[i][1:])
            docs_tf[docID] = np.log(1+tf)
    return docs_tf


def update_score_and_results(file, freq, details):
    global scores, results, numPages, top_results
    bytes_to_read = details[2] - details[1]
    idf = np.log(numPages/details[0])
    buffer = min(100000, bytes_to_read)
    file.seek(details[1])
    while bytes_to_read > 0:
        data = file.read(buffer)
        if data[-1] != "\n":
            data = " ".join([data, file.readline()])
        bytes_to_read -= len(data)
        docs_tf = getDocsTF(data.rstrip())
        for doc in docs_tf:
            scores[doc-1] += freq * docs_tf[doc] * idf
            if len(results) < top_results:
                results[doc] = scores[doc-1]
            else:
                min_score = -1
                for doc in results:
                    if min_score == -1:
                        min_score = doc
                    if results[doc] < results[min_score]:
                        min_score = doc
                results[doc] = scores[doc-1]
                results.pop(min_score)


def execute_query(query, field=False):
    index_file = open(inverted_index_file, "r")
    if not field:
        details = get_details(query)
        for token in sorted(query):
            update_score_and_results(index_file, query[token], details[token])


def print_results():
    global results
    for doc in results:
        print(doc)


def get_tokens(data):
    global tokens_in_index
    for line in data:
        line = line.split()
        tokens_in_index[line[0]] = [line[1], line[2]]


def get_offsets():
    global tokens_offsets, offsets_file
    with open(offsets_file, "r") as file:
        data = file.read().split("\n")
        for line in data:
            line = line.strip().split()
            if len(line) > 0:
                tokens_offsets[line[0]] = [line[1], line[2]]


inverted_index_path = sys.argv[1]
if not os.path.exists(inverted_index_path):
    print("Invalid path!")
    quit()
if inverted_index_path[-1] != "/" and inverted_index_path[-1] != "\\":
    inverted_index_path += "/"

with open(f"{inverted_index_path}imp_data.txt", "r") as file:
    data = file.read().split()
    flag = int(data[0])
    numPages = int(data[1])

scores = np.zeros(numPages, dtype=np.float16)
results = {}
tokens_file = f"{inverted_index_path}tokens{flag}.txt"
offsets_file = f"{inverted_index_path}tokens_offsets{flag}.txt"
inverted_index_file = f"{inverted_index_path}inverted_index{flag}.txt"
tokens_in_index = {}
tokens_offsets = {}
top_results = 10
get_offsets()

query = sys.argv[2].lower()
field_query = len(query.split(":")) > 1
if not field_query:
    query = text_preprocessing(query)
    execute_query(query)
    print_results()
