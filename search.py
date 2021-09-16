import time
from typing import final
start = time.time()
from nltk.corpus import stopwords
import Stemmer
import re
import sys
import os
import numpy as np
from encode_decode import decode, encode

if len(sys.argv) < 3:
    print("Too few arguments")
    quit()


stopWords = set(stopwords.words("english"))


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


def getDocsTF(data, fields=None):
    data = data.split("\n")
    docs_tf = {}
    for line in data:
        line = line.split()
        if len(line) > 1:
            tf = 0
            try:
                docID = decode(line[0])
            except:
                continue
            for i in range(1, len(line)):
                if fields is None:
                    tf += decode(line[i][1:])
                else:
                    if line[i][0] in fields:
                        tf += fields[line[i][0]] * decode(line[i][1:])
                    else:
                        tf += 0.35 * decode(line[i][1:])
            docs_tf[docID] = np.log(1+tf)
    return docs_tf


def update_score_and_results(file, freq, details, field=None):
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
        docs_tf = getDocsTF(data.rstrip(), field)
        for doc in docs_tf:
            if field is None:
                scores[doc] += freq * docs_tf[doc] * idf
            else:
                scores[doc] += docs_tf[doc] * idf
            if len(results) < top_results:
                results[doc] = scores[doc]
            else:
                min_score = -1
                for doc in results:
                    if min_score == -1 or results[min_score] > results[doc]:
                        min_score = doc
                if scores[doc] >= results[min_score]:
                    results[doc] = scores[doc]
                    results.pop(min_score)


def execute_query(query, field=False):
    index_file = open(inverted_index_file, "r")
    details = get_details(query)
    for token in sorted(query):
        if not field: 
            update_score_and_results(index_file, query[token], details[token])
        else:
            update_score_and_results(index_file, query[token], details[token], query[token])


def get_doc_ids(data):
    data = data.split("\n")
    ids = {}
    for line in data:
        line = line.split()
        if len(line) > 0:
            ids[line[0]] = line[1]
    return ids


def get_title_offsets(data):
    data = data.split("\n")
    offsets = {}
    for line in data:
        line = line.split()
        if len(line) > 0:
            offsets[line[0]] = [line[1], line[2]]
    return offsets


# def print_results():
#     global results, id_file, title_offsets_file, titles_file
#     doc_ids = {}
#     docs = list(sorted(results.keys()))
#     length = len(docs)
#     for i in range(len(docs)):
#         docs[i] = encode(docs[i])
#     with open(id_file, "r") as file:
#         total_size = os.path.getsize(id_file)
#         buffer = min(1000000, total_size)
#         start = 0
#         while total_size and start < length:
#             data = file.read(buffer)
#             if data[-1] != "\n":
#                 data = "".join([data, data.readline()])
#             total_size -= len(data)
#             data = data.rstrip()
#             buffer = min(buffer, total_size)
#             ids = get_doc_ids(data)
#             for i in range(start, length):
#                 if docs[i] in ids:
#                     doc_ids[docs[i]] = decode(ids[docs[i]])
#                     start = i+1
#     titles = {}
#     with open(titles_file, "r") as file:
#         lines = 0
#         buffer = 1000000
#         total_size = os.path.getsize(titles_file)
#         start = 0
#         while total_size > 0 and start < length:
#             data = file.read(buffer)
#             if data[-1] != "\n":
#                 data = "".join([data, file.readline()])
#             total_size -= len(data)
#             data = data.rstrip()
#             buffer = min(total_size, buffer)
#             data = list(filter(lambda x: len(x) > 0, data.split("\n")))
#             num_lines = len(data)
#             lines += num_lines
#             start_line = lines - num_lines + 1
#             for i in range(start, length):
#                 temp_doc = decode(docs[i])
#                 if temp_doc <=  lines:
#                     titles[docs[i]] = data[temp_doc - start_line]
#                     start = i+1


#     final_result = []
#     while len(results) != 0:
#         max_score = -1
#         for doc in results:
#             if max_score == -1 or results[doc] > results[max_score]:
#                 max_score = doc
#         max_doc = encode(max_score)
#         final_result.append((doc_ids[max_doc], titles[max_doc]))
#         results.pop(max_score)
#     # print(len(final_result))
#     for result in final_result:
#         print(result[0], result[1])


def print_results():
    global results, id_file, title_offsets_file, titles_file
    doc_ids = {}
    titles = {}
    title_offsets = {}
    docs = list(sorted(results.keys()))
    length = len(docs)
    for i in range(len(docs)):
        docs[i] = encode(docs[i])
    with open(title_offsets_file, "r") as file:
        total_size = os.path.getsize(title_offsets_file)
        buffer = min(1000000, total_size)
        start = 0
        while total_size > 0 and start < length:
            data = file.read(buffer)
            if data[-1] != "\n":
                data = "".join([data, file.readline()])
            total_size -= len(data)
            buffer = min(buffer, total_size)
            offsets = get_title_offsets(data.rstrip())
            for i in range(start, length):
                if docs[i] in offsets:
                    start = i+1
                    title_offsets[docs[i]] = [decode(offsets[docs[i]][0]), decode(offsets[docs[i]][1])]
    with open(titles_file, "r") as file:
        for doc in docs:
            file.seek(title_offsets[doc][0])
            bytes_to_read = title_offsets[doc][1] - title_offsets[doc][0]
            data = file.read(bytes_to_read).strip()
            data = data.split()
            if len(data) > 2:
                doc_ids[doc] = decode(data[0])
                titles[doc] = " ".join(data[1:])
    final_results = []
    while len(results) > 0:
        max_score = -1
        for doc in results:
            if max_score == -1 or results[doc] > results[max_score]:
                max_score = doc
        max_doc = encode(max_score)
        final_results.append([doc_ids[max_doc], titles[max_doc]])
        results.pop(max_score)
    if len(final_results) == 0:
        print("No documents found")
        return
    for result in final_results:
        print(result[0], result[1])

        


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

scores = np.zeros(numPages+1, dtype=np.float16)
results = {}
tokens_file = f"{inverted_index_path}tokens{flag}.txt"
offsets_file = f"{inverted_index_path}tokens_offsets{flag}.txt"
inverted_index_file = f"{inverted_index_path}inverted_index{flag}.txt"
titles_file = f"{inverted_index_path}titles.txt"
title_offsets_file = f"{inverted_index_path}titles_offsets.txt"
id_file = f"{inverted_index_path}ids.txt"
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
    print()
else:
    query = list(filter(lambda x: len(x) > 0, re.split(r"([tibrlc]):", query)))
    fields = {}
    for i in range(0, len(query), 2):
        fields[query[i]] = text_preprocessing(query[i+1])
    query = {}
    for field in fields:
        for word in fields[field]:
            if word not in query:
                query[word] = {}
            if field not in query[word]:
                query[word][field] = 0
            query[word][field] += 1
    execute_query(query, True)
    print_results()
    print()
print("time_taken =", time.time() - start)
