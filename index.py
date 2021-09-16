import re
import xml.sax
import sys
from nltk.corpus import stopwords
import Stemmer
import os
from encode_decode import encode, decode
from bz2file import BZ2File


if len(sys.argv) < 3:
    print("Too few arguments")
    quit()
pages = 0
numFiles = 0
words = set()
tokens_in_index = {}
inverted_index = {}
num_tokens = 0
stopWords = set(stopwords.words("english"))
current_title_offset = 0
index_path = sys.argv[2]
if index_path[-1] != "/" and index_path[-1] != "\\":
    index_path += "/"
if not os.path.exists(index_path):
    os.makedirs(index_path)
first_letters = [chr(x) for x in range(ord('0'), 1+ord('9'))]
first_letters.extend([chr(x) for x  in range(ord('a'), 1+ord('z'))])


def open_files(flag, mode):
    files = []
    files.append(open(f"{index_path}tokens_offsets{flag}.txt", mode))
    files.append(open(f"{index_path}tokens{flag}.txt", mode))
    files.append(open(f"{index_path}inverted_index{flag}.txt", mode))
    return files


def close_files(files):
    for file in files:
        file.close()


temp = open_files(0, "w")
close_files(temp)
temp = open_files(1, "w")
close_files(temp)
titles_file = open(f"{index_path}titles.txt", "w")
titles_offset_file = open(f"{index_path}titles_offsets.txt", "w")
ids_file = open(f"{index_path}ids.txt", "w")

def printError():
    print("Can't write to this directory")
    quit()


def write_title(page, docID, title):
    global current_title_offset, titles_offset_file, titles_file
    title = title.encode("ascii", errors="ignore").decode()
    write_string = " ".join([encode(int(docID)), title])
    write_string = write_string + "\n"
    bytes_written = titles_file.write(write_string)
    new_offset = current_title_offset + bytes_written
    offset_string = " ".join([encode(page), encode(current_title_offset), encode(new_offset)])
    offset_string = offset_string + "\n"
    titles_offset_file.write(offset_string)
    current_title_offset = new_offset


def get_token_offsets(file):
    data = file.readlines()
    offsets = {}
    for letter in first_letters:
        offsets[letter] = [0, 0]
    for line in data:
        line = line.strip().split()
        if len(line) > 0:
            offsets[line[0]] = [decode(line[1]), decode(line[2])]
    return offsets


def get_tokens(data):
    data = data.strip().split("\n")
    tokens_in_file = {}
    for line in data:
        line = line.strip().split()
        if len(line) > 0:
            tokens_in_file[line[0]] = [decode(line[1]), decode(line[2]), decode(line[3])]
    return tokens_in_file


def write_index_from_file(inp_file, out_file, offsets):
    inp_file.seek(offsets[1])
    offset_increase = 0
    bytes_to_read = offsets[2] - offsets[1]
    buffer = min(100000, bytes_to_read)
    while bytes_to_read > 0:
        data = inp_file.read(buffer)
        bytes_to_read -= buffer
        buffer = min(buffer, bytes_to_read)
        offset_increase += len(data)
        out_file.write(data)
    return offset_increase


def write_index_from_memory(file, token):
    global tokens_in_index, inverted_index
    offset_increase = 0
    entries = []
    for entry in inverted_index[token]:
        docId = encode(entry[0])
        new_entry = docId
        if "t" in entry[1]:
            new_entry = " ".join([new_entry, f"t{encode(100 * entry[1]['t'])}"])
        if "i" in entry[1]:
            new_entry = " ".join([new_entry, f"i{encode(20 * entry[1]['i'])}"])
        if "b" in entry[1]:
            new_entry = " ".join([new_entry, f"b{encode(entry[1]['b'])}"])
        if "r" in entry[1]:
            new_entry = " ".join([new_entry, f"r{encode(entry[1]['r'])}"])
        if "l" in entry[1]:
            new_entry = " ".join([new_entry, f"l{encode(entry[1]['l'])}"])
        if "c" in entry[1]:
            new_entry = " ".join([new_entry, f"c{encode(entry[1]['c'])}"])
        entries.append(new_entry)
    entries = "\n".join(entries)
    entries = entries + "\n"
    file.write(entries)
    offset_increase += len(entries)
    return offset_increase


def write_token_info(file, token, details):
    data = " ".join([token, encode(details[0]), encode(details[1]), encode(details[2])])
    data = data + "\n"
    offset_increase = len(data)
    file.write(data)
    return offset_increase


def write_token_offset(file, letter, details):
    data = " ".join([letter, encode(details[0]), encode(details[1])])
    data = data + "\n"
    file.write(data)
        

def write_to_file():
    global tokens_in_index, inverted_index, index_path, numFiles, num_tokens
    num_tokens = 0
    inp_file = (numFiles+1)%2
    out_file = numFiles%2
    inp_files = open_files(inp_file, "r")
    out_files = open_files(out_file, "w")
    token_offsets = get_token_offsets(inp_files[0])
    current_offset = 0
    current_token_offset = 0
    tokens_2 = list(sorted(tokens_in_index.keys()))
    p2 = 0
    len2 = len(tokens_2)
    for letter in first_letters:
        tokens_in_file = {}
        bytes_to_read = token_offsets[letter][1] - token_offsets[letter][0]
        buffer = min(100000, bytes_to_read)
        inp_files[1].seek(token_offsets[letter][0])
        token_offsets[letter][0] = current_token_offset
        frequency = 0
        while bytes_to_read > 0:
            data = inp_files[1].read(buffer)
            if len(data) <= 0 or data[-1] != "\n":
                data = "".join([data, inp_files[1].readline()])
            bytes_to_read = bytes_to_read - len(data)
            data = data.rstrip()
            buffer = min(buffer, bytes_to_read)
            tokens_in_file = get_tokens(data)
            tokens_1 = list(sorted(tokens_in_file.keys()))
            p1 = 0
            len1 = len(tokens_1)
            while p1 < len1 and p2 < len2:
                if tokens_1[p1] <= tokens_2[p2]:
                    tokens_in_file[tokens_1[p1]][1] = current_offset
                    current_offset += write_index_from_file(inp_files[2], out_files[2], tokens_in_file[tokens_1[p1]])
                    if tokens_1[p1] not in tokens_in_index.keys():
                        tokens_in_file[tokens_1[p1]][2] = current_offset
                        current_token_offset += write_token_info(out_files[1], tokens_1[p1], tokens_in_file[tokens_1[p1]])
                    else:
                        tokens_in_index[tokens_1[p1]][1] = tokens_in_file[tokens_1[p1]][1]
                        tokens_in_index[tokens_1[p1]][0] += tokens_in_file[tokens_1[p1]][0]
                    p1 += 1
                    frequency += 1
                else:
                    if tokens_2[p2] not in tokens_in_file.keys():
                        frequency += 1
                        tokens_in_index[tokens_2[p2]][1] = current_offset
                    current_offset += write_index_from_memory(out_files[2], tokens_2[p2])
                    tokens_in_index[tokens_2[p2]][2] = current_offset
                    current_token_offset += write_token_info(out_files[1], tokens_2[p2], tokens_in_index[tokens_2[p2]])
                    p2 += 1
            while p1 < len1:
                tokens_in_file[tokens_1[p1]][1] = current_offset
                current_offset += write_index_from_file(inp_files[2], out_files[2], tokens_in_file[tokens_1[p1]])
                if tokens_1[p1] not in tokens_in_index.keys():
                    tokens_in_file[tokens_1[p1]][2] = current_offset
                    current_token_offset += write_token_info(out_files[1], tokens_1[p1], tokens_in_file[tokens_1[p1]])
                else:
                    tokens_in_index[tokens_1[p1]][1] = tokens_in_file[tokens_1[p1]][1]
                    tokens_in_index[tokens_1[p1]][0] += tokens_in_file[tokens_1[p1]][0]
                p1 += 1
                frequency += 1
            while p2 < len2 and tokens_2[p2] <= tokens_1[-1]:
                if tokens_2[p2] not in tokens_in_file.keys():
                    tokens_in_index[tokens_2[p2]][1] = current_offset
                    frequency += 1
                current_offset += write_index_from_memory(out_files[2], tokens_2[p2])
                tokens_in_index[tokens_2[p2]][2] = current_offset
                current_token_offset += write_token_info(out_files[1], tokens_2[p2], tokens_in_index[tokens_2[p2]])
                p2 += 1    
        while p2 < len2 and tokens_2[p2][0] == letter:
            if tokens_2[p2] not in tokens_in_file.keys():
                tokens_in_index[tokens_2[p2]][1] = current_offset
                frequency += 1
            current_offset += write_index_from_memory(out_files[2], tokens_2[p2])
            tokens_in_index[tokens_2[p2]][2] = current_offset
            current_token_offset += write_token_info(out_files[1], tokens_2[p2], tokens_in_index[tokens_2[p2]])
            p2 += 1
        token_offsets[letter][1] = current_token_offset
        num_tokens += frequency
        write_token_offset(out_files[0], letter, token_offsets[letter])
    close_files(inp_files)
    open_files(inp_file, "w")
    close_files(inp_files)
    close_files(out_files)
        



def insert_word(word):
    global tokens_in_index
    tokens_in_index[word] = [0, -1, -1]


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
        tokens_in_index[word][0] += 1
        if word not in inverted_index.keys():
            inverted_index[word] = []
        new_entry = (page_number, entries[word])
        inverted_index[word].append(new_entry)


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
            infobox_data = " ".join([infobox_data, line])
        elif not infobox_open and len(re.findall(r"\{\{infobox", line)) > 0:
            infobox_open = True
            line = re.sub(r"\{\{infobox", "", line)
            infobox_data = " ".join([infobox_data, line])
    return infobox_data, last_line_infobox


def text_preprocessing(text):
    text = text.strip().encode("ascii", errors="ignore").decode()
    text = re.sub(r"<!--.*-->", "", text) # Removing comments
    # text = re.sub(r"==.*==", "", text) # Removing section headings
    text = re.sub(r"&.+;", "", text) # Removing special symbols like &gt; &lt;
    text = re.sub(r"`|~|!|@|#|\$|%|\^|&|\*|\(|\)|-|_|=|\+|\||\\|\[|\]|\{|\}|;|:|'|\"|,|<|>|\.|/|\?|\n|\t", " ", text) # removing non alpha numeric
    text = text.split()
    text = list(filter(lambda x: len(x) > 0 and x not in stopWords, text))
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

page_id = None
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
        global pages, inverted_index, tokens_in_index, numFiles, titles_file, titles_offset_file, page_id
        if name == "id" and page_id == None:
            page_id = self.id
        if name == "page":
            pages += 1
            self.title = self.title.strip()
            data = get_fields(self.title.lower(), self.text.lower())
            insert_into_inverted_index(data, pages)
            write_title(pages, page_id, self.title)
            page_id = None
            print(pages)
            page_id = None
            if pages % 30000 == 0:
                write_to_file()
                inverted_index = {}
                tokens_in_index = {}
                numFiles += 1


contentHandler = Handler()
parser = xml.sax.make_parser()
parser.setContentHandler(contentHandler)
xml_dump = BZ2File(sys.argv[1])
parser.parse(sys.argv[1])
if len(inverted_index) > 0:
    write_to_file()
    numFiles += 1
print(num_tokens)
with open(f"{index_path}imp_data.txt", "w") as file:
    file.write(str((numFiles+1)%2) + " " + str(pages))
titles_offset_file.close()
titles_file.close()
ids_file.close()
xml_dump.close()
