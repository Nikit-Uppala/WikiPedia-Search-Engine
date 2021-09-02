from nltk.corpus import stopwords
import Stemmer
import re
import sys
import os
import json


if len(sys.argv) < 3:
    print("Too few arguments")
    quit()


stopWords = stopwords.words("english")


def printError():
    print("No inverted index exists in the given directory")
    quit()


def text_preprocessing(text):
    global query_tokens, query
    text = re.sub(r"&.+;", "", text) # Removing special symbols like &gt; &lt;
    text = re.sub(r"\#|\@|\,|\/|\\|\;", " ", text) # removing non alpha numeric
    text = text.split()
    query = text
    text = list(filter(lambda x: len(x) > 0 and x not in stopWords, text))
    stem = Stemmer.Stemmer("english")
    for i in range(len(text)):
        stemmed = stem.stemWord(text[i])
        if stemmed not in query_tokens.keys():
            query_tokens[text[i]] = stemmed
        text[i] = stemmed
    return text


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
            start_seek = tokens_offsets[tokens_in_index[token][0]][0]
            end_seek = tokens_offsets[tokens_in_index[token][0]][1]
            file.seek(start_seek)
            print(tokens_in_index[token][1])
            data = file.read(end_seek - start_seek)
            data = data.split("\n")
            for line in data:
                if len(line) == 0:
                    continue
                doc_id = int(line.split()[0])
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
        printError()


def execute_query():
    global query_tokens, query
    output = {}
    for token in query:
        if token not in query_tokens.keys():
            posting_lists = get_posting_lists(token)
        else:
            posting_lists = get_posting_lists(query_tokens[token])
        output[token] = posting_lists
    output = json.dumps(output, indent=" ")
    print(output)



def get_tokens(data):
    global tokens_in_index
    for line in data:
        line = line.split()
        tokens_in_index[line[0]] = [int(line[1]), int(line[2])]


def get_offsets(data):
    global tokens_offsets
    for line in data:
        line = line.split()
        tokens_offsets[int(line[0])] = [int(line[1]), int(line[2])]


inverted_index_path = sys.argv[1]
if not os.path.exists(inverted_index_path):
    print("Invalid path!")
    quit()
if inverted_index_path[-1] != "/" or inverted_index_path[-1] != "\\":
    inverted_index_path += "/"

tokens_file = f"{inverted_index_path}tokens.txt"
offsets_file = f"{inverted_index_path}offsets.txt"
inverted_index_file = f"{inverted_index_path}inverted_index.txt"
tokens_in_index = {}
tokens_offsets = {}

try:
    with open(tokens_file, "r") as file:
        data = file.readlines()
        get_tokens(data)
except:
    printError()

try:
    with open(offsets_file, "r") as file:
        data = file.readlines()
        get_offsets(data)
except:
    printError()

query = sys.argv[2].lower()
query_tokens = {}
query = re.sub(r"[tibrlc]:", " ", query)
query = text_preprocessing(query)
execute_query()
