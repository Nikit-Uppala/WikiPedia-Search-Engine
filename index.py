import re
import xml.sax
import sys
from preprocessing import text_preprocessing

pages = 0
tokens = 0
words = set()
tokens_in_index = {}
inverted_index = []
flag = 0


def insert_word(word):
    global tokens, tokens_in_index
    tokens_in_index[word] = [tokens, 0, -1, -1]
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
        new_entry = {tokens_in_index[word][0]: entries[word]}
        new_entry[tokens_in_index[word][0]]["p"] = page_number
        inverted_index.append(new_entry)


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
            line = line.split("=")
            if len(line) > 1:
                for j in range(len(line)-1, 0, -1):
                    infobox_data = " ".join([infobox_data, line[j]])
        elif not infobox_open and len(re.findall(r"\{\{infobox", line)) > 0:
            infobox_open = True
            line = re.sub(r"\{\{infobox", "", line)
            infobox_data = " ".join([infobox_data, line])
    return infobox_data, last_line_infobox


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
    
    # fields["i"] = " ".join(re.findall(r"\{\{.*?infobox(.*?)\}\}", text, flags=re.DOTALL))
    # fields["i"] = text_preprocessing(process_infobox(fields["i"]))
    # text = re.sub(r"\{\{.*?infobox.*?\}\}", "", text, flags=re.DOTALL)
    
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
            if pages % 20000 == 0:
                inverted_index = []



if len(sys.argv) == 1:
    quit()

contentHandler = Handler()
parser = xml.sax.make_parser()
parser.setContentHandler(contentHandler)
parser.parse(sys.argv[1])
