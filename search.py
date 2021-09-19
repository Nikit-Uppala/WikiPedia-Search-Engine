import time
from typing import final
from nltk.corpus import stopwords
import Stemmer
import re
import sys
import os
import numpy as np
from encode_decode import decode, encode

start = time.time()
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
    tokens_file_obj = open(tokens_file, "r")
    for token in sorted(query):
        start_seek = decode(tokens_offsets[token[0]][0])
        end_seek = decode(tokens_offsets[token[0]][1])
        tokens_retrieved = binary_search(tokens_file_obj, start_seek, end_seek, token, True)
        if token in tokens_retrieved:
            details[token] = [decode(tokens_retrieved[token][0]), decode(tokens_retrieved[token][1]),
                    decode(tokens_retrieved[token][2])]
    tokens_file_obj.close()
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
                f = decode(line[i][1:])
                if fields is None:
                    tf += f
                else:
                    if line[i][0] in fields:
                        tf += fields[line[i][0]] * f
                    else:
                        tf += 0.35 * f
            docs_tf[docID] = np.log(1+tf)
    return docs_tf


def update_score_and_results(file, freq, details, field=None):
    global scores, results, numPages, top_results, min_score
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
                if min_score == -1 or results[min_score] > results[doc]:
                    min_score = doc
            else:
                if scores[doc] > results[min_score]:
                    results[doc] = scores[doc]
                    if doc != min_score:
                        results.pop(min_score)
                    min_score = doc
                    for doc in results:
                        if results[doc] < results[min_score]:
                            min_score = doc



def execute_query(query, field=False):
    index_file = open(inverted_index_file, "r")
    details = get_details(query)
    for token in sorted(query):
        if not field: 
            update_score_and_results(index_file, query[token], details[token])
        else:
            update_score_and_results(index_file, query[token], details[token], query[token])


def get_title_offsets(data):
    data = data.split("\n")
    offsets = {}
    for line in data:
        line = line.split()
        if len(line) > 2:
            offsets[line[0]] = [line[1], line[2]]
    return offsets


def get_secondary_offsets(data):
    data = data.split("\n")
    offsets = {}
    for line in data:
        line = line.split()
        if len(line) > 2:
            offsets[int(line[0])] = [line[1], line[2]]
    return offsets


def binary_search(file, start, end, string, token=False):
    mid = (start + end) // 2
    if not token:
        string = decode(string)
    while end - start > 1000:
        file.seek(mid)
        mid = mid + len(file.readline())
        data = file.readline()
        start_mid = mid + len(data)
        words = data.split()
        if len(words) > 0:
            if token:
                if string == words[0]:
                    return get_tokens_data(data)
                elif string > words[0]:
                    start = start_mid
                else:
                    end = mid
            else:
                num = decode(words[0])
                if string == num:
                    return get_title_offsets(data)
                elif string > num:
                    start = start_mid
                else:
                    end = mid
        else:
            print("Something's wrong")
        mid = (start + end) // 2
    file.seek(start)
    data = file.read(end-start)
    if token:
        return get_tokens_data(data)
    else:
        return get_title_offsets(data)


def print_results():
    global results, id_file, title_offsets_file, titles_file, start
    doc_ids = {}
    titles = {}
    title_offsets = {}
    docs = list(sorted(results.keys()))
    for i in range(len(docs)):
        docs[i] = encode(docs[i])
    with open(secondary_titles_file, "r") as file:
        data = file.read().strip()
        secondary_offsets = get_secondary_offsets(data)
    file = open(title_offsets_file, "r")
    for doc in docs:
        num = decode(doc)
        m = num//10000
        start_seek = decode(secondary_offsets[m][0])
        end_seek = decode(secondary_offsets[m][1])
        offsets = binary_search(file, start_seek, end_seek, doc)
        if doc in offsets:
            title_offsets[doc] = [decode(offsets[doc][0]), decode(offsets[doc][1])]
    file.close()
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
    with open(query_out_file, "a") as file:
        if len(final_results) == 0:
            file.write("No documents found\n")
            return
        for result in final_results:
            write_string = " ".join([str(result[0]), result[1]])
            write_string = write_string + "\n"
            file.write(write_string)
        file.write("time = " + str(time.time()-start) + "\n")
        file.write("\n")

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
secondary_titles_file = f"{inverted_index_path}secondary.txt"
id_file = f"{inverted_index_path}ids.txt"
tokens_offsets = {}
top_results = 10
min_score = -1
get_offsets()

# query = sys.argv[2].lower()
# field_query = len(query.split(":")) > 1
# if not field_query:
#     query = text_preprocessing(query)
#     execute_query(query)
#     print_results()
#     print()
# else:
#     query = list(filter(lambda x: len(x) > 0, re.split(r"([tibrlc]):", query)))
#     fields = {}
#     for i in range(0, len(query), 2):
#         fields[query[i]] = text_preprocessing(query[i+1])
#     query = {}
#     for field in fields:
#         for word in fields[field]:
#             if word not in query:
#                 query[word] = {}
#             if field not in query[word]:
#                 query[word][field] = 0
#             query[word][field] += 1
#     execute_query(query, True)
#     print_results()
#     print()
# print("time_taken =", time.time() - start)
query_file = sys.argv[2]
query_out_file = "queries_op.txt"
with open(query_file, "r") as file:
    for line in file:
        min_score = -1
        results = {}
        orginal_query = line.strip()
        query = orginal_query.lower()
        field_query = len(query.split(":")) > 1
        if not field_query:
            query = text_preprocessing(query)
            execute_query(query)
            print_results()
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
        start = time.time()
