import re
import xml.sax
import sys
from nltk.corpus import stopwords
import Stemmer
import os


if len(sys.argv) < 3:
    print("Too few arguments")
    quit()
pages = 0
tokens = 0
words = set()
tokens_in_index = {}
tokens_offsets = {}
inverted_index = {}
stopWords = set(stopwords.words("english"))
index_path = sys.argv[2]
if index_path[-1] != "/" or index_path[-1] != "\\":
    index_path += "/"
if not os.path.exists(index_path):
    os.makedirs(index_path)


def write_tokens():
    with open(f"{index_path}tokens.txt", "w") as file:
        entries = []
        for entry in sorted(tokens_in_index):
            new_entry = " ".join([str(entry), str(tokens_in_index[entry][0]), str(tokens_in_index[entry][1])])
            entries.append(new_entry)
        entries = "\n".join(entries)
        file.write(entries)


def write_offsets():
    with open(f"{index_path}offsets.txt", "w") as file:
        entries = []
        for i in range(len(tokens_offsets)):
            new_entry = " ".join([str(i), str(tokens_offsets[i][0]), str(tokens_offsets[i][1])])
            entries.append(new_entry)
        entries = "\n".join(entries)
        file.write(entries)


def write_to_file():
    global tokens, tokens_in_index, inverted_index, tokens_offsets, index_path
    current_offset = 0
    prev_token = -1
    out_file = open(f"{index_path}inverted_index.txt", "w")
    for token in sorted(inverted_index):
        if prev_token != token:
            if prev_token in tokens_offsets.keys():
                tokens_offsets[prev_token][1] = current_offset
            tokens_offsets[token][0] = current_offset
        entries = []
        for doc in inverted_index[token]:
            new_entry = str(doc[0])
            if "t" in doc[1].keys():
                new_entry = " ".join([new_entry, f"t:{doc[1]['t']}"])
            if "i" in doc[1].keys():
                new_entry = " ".join([new_entry, f"i:{doc[1]['i']}"])
            if "c" in doc[1].keys():
                new_entry = " ".join([new_entry, f"c:{doc[1]['c']}"])
            if "b" in doc[1].keys():
                new_entry = " ".join([new_entry, f"b:{doc[1]['b']}"])
            if "r" in doc[1].keys():
                new_entry = " ".join([new_entry, f"r:{doc[1]['r']}"])
            if "l" in doc[1].keys():
                new_entry = " ".join([new_entry, f"l:{doc[1]['l']}"])
            entries.append(new_entry)
        entries = "\n".join(entries)
        entries += "\n"
        out_file.write(entries)
        current_offset += len(entries)
        prev_token = token


def insert_word(word):
    global tokens, tokens_in_index, tokens_offsets
    tokens_in_index[word] = [tokens, 0]
    tokens_offsets[tokens] = [-1, -1]
    tokens += 1


def insert_into_inverted_index(data, page_number):
    global inverted_index, tokens_in_index
    entries = {}
    for key in data:
        for word in data[key]:
            if word not in entries.keys():
                entries[word] = {}
            if word not in tokens_in_index.keys():
                insert_word(word)
            if key not in entries[word]:
                entries[word][key] = 0
            entries[word][key] += 1
    for word in entries:
        tokens_in_index[word][1] += 1
        if tokens_in_index[word][0] not in inverted_index.keys():
            inverted_index[tokens_in_index[word][0]] = []
        new_entry = (page_number, entries[word])
        inverted_index[tokens_in_index[word][0]].append(new_entry)


def split_on_links(text):
    text = text.split("==external links==")
    if len(text) > 1:
        return text
    if len(text) == 1:
        text = text[0].split("== external links==")
    if len(text) == 1:
        text = text[0].split("==external links ==")
    if len(text) == 1:
        text = text[0].split("== external links ==")
    return text


def split_on_references(text):
    text = text.split("==references==")
    if len(text) == 1:
        text = text[0].split("== references==")
    if len(text) == 1:
        text = text[0].split("==references ==")
    if len(text) == 1:
        text = text[0].split("== references ==")
    return text


def get_infobox(lines):
    infobox_open = False
    infobox_data = ""
    last_line_infobox = 0
    for i in range(len(lines)):
        line = lines[i].strip()
        if infobox_open and line == "}}":
            infobox_open = False
            last_line_infobox = i+1
        elif infobox_open:
            # infobox_data = " ".join([infobox_data, line])
            line = line.split("=")
            if len(line) > 1:
                line = " ".join(line[1:])
                infobox_data = " ".join([infobox_data, line])
        elif not infobox_open and len(re.findall(r"\{\{infobox", line)) > 0:
            infobox_open = True
            line = re.sub(r"\{\{infobox", "", line)
            infobox_data = " ".join([infobox_data, line])
    return infobox_data, last_line_infobox


def text_preprocessing(text):
    text = re.sub(r"<!--.*-->", "", text) # Removing comments
    text = re.sub(r"==.*==", "", text) # Removing section headings
    text = re.sub(r"&.+;", "", text) # Removing special symbols like &gt; &lt;
    text = re.sub(r"`|~|!|@|#|\$|%|\^|&|\*|\(|\)|-|_|=|\+|\||\\|\[|\]|\{|\}|;|:|'|\"|,|<|>|\.|/|\?|\n|\t", " ", text) # removing non alpha numeric
    text = text.split()
    text = list(filter(lambda x: x not in stopWords, text))
    stemmer = Stemmer.Stemmer("english")
    text = stemmer.stemWords(text)
    return text


def get_fields(title, text):
    fields = {}

    # getting title
    fields["t"] = text_preprocessing(title)

    # getting links
    text = split_on_links(text)
    fields["l"] = []
    if len(text) > 1:
        # getting categories
        fields["c"] = text_preprocessing(" ".join(re.findall(r"\[\[category:(.*?)\]\]", text[-1])))
        text[-1] = re.sub(r"\[\[category:(.*?)\]\]", "", text[-1])

        hyperlinks = re.findall(r"\[(.*)\]", text[-1])
        hyperlinks = " ".join(hyperlinks)
        fields["l"] = text_preprocessing(hyperlinks)
    text = text[0]

    # getting references
    text = split_on_references(text)
    fields["r"] = []
    if len(text) > 1:
        # getting categories if not collected
        if "c" not in fields.keys():
            fields["c"] = text_preprocessing(" ".join(re.findall(r"\[\[category:(.*?)\]\]", text[-1])))
            text[-1] = re.sub(r"\[\[category:(.*?)\]\]", "", text[-1])
        references1 = filter(lambda x: x not in["reflist", "refbegin", "refend", "cite"], re.findall(r"\{(.*)\}", text[-1]))
        references2 = filter(lambda x: x not in["reflist", "refbegin", "refend", "cite"], re.findall(r"\[(.*)\]", text[-1]))
        references = " ".join(references1)
        references = " ".join(references2)
        fields["r"] = text_preprocessing(references)

    text = text[0]

    # getting categories if not collected
    if "c" not in fields.keys():
        fields["c"] = text_preprocessing(" ".join(re.findall(r"\[\[category:(.*?)\]\]", text)))
        text = re.sub(r"\[\[category:(.*?)\]\]", "", text)

    # remaining text contains body and infobox
    # getting infobox
    text = text.split("\n")
    fields["i"], line_number = get_infobox(text)
    fields["i"] = text_preprocessing(fields["i"])
    text = " ".join(text[line_number:])
    
    # body left in text
    fields["b"] = text_preprocessing(text)
    return fields


class Handler(xml.sax.ContentHandler):

    def startElement(self, name, attribs):
        self.current_tag = name
        if name == "text":
            self.text = ""
        elif name == "title":
            self.title = ""
        elif name == "id":
            self.id = ""
    
    def characters(self, content):
        if len(content) == 0:
            return
        if self.current_tag == "title":
            self.title = "".join([self.title, content])
        elif self.current_tag == "id":
            self.id = "".join([self.id, content])
        elif self.current_tag == "text":
            self.text = "".join([self.text, content])
    
    def endElement(self, name):
        global pages, inverted_index
        if name == "page":
            pages += 1
            data = get_fields(self.title.lower(), self.text.lower())
            insert_into_inverted_index(data, pages)
            # if pages % 20000 == 0:
                # write_to_file()
                # inverted_index = {}


contentHandler = Handler()
parser = xml.sax.make_parser()
parser.setContentHandler(contentHandler)
parser.parse(sys.argv[1])
write_to_file()
write_tokens()
write_offsets()
