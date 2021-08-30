import re
from typing import final
from nltk.corpus import stopwords
# from nltk.stem import SnowballStemmer
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import xml.sax
import sys

pages = 0
tokens = 0
words = set()
tokens_in_index = set()
stopWords = set(stopwords.words("english"))


def text_preprocessing(text):
    text = re.sub(r"`|~|!|@|#|\$|%|\^|&|\*|\(|\)|-|_|=|\+|\||\\|\[|\]|\{|\}|;|:|'|\"|,|<|>|\.|/|\?|\n|\t", " ", text)
    text = re.sub(r"&.+;", "", text)
    # text = text.split()
    text = word_tokenize(text)
    for word in text:
        words.add(word)
    text = list(filter(lambda x: x not in stopWords, text))
    # stemmer = SnowballStemmer(language="english")
    stemmer = PorterStemmer()
    text = [stemmer.stem(x) for x in text]
    for token in text:
        tokens_in_index.add(token)
    return text


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


def process_infobox(text):
    text = text.split("|")
    final_infobox = []
    for info in text:
        info = info.split("=")
        if len(info) > 1:
            final_infobox.append(info[-1])
    return " ".join(final_infobox)


def get_fields(title, text):
    fields = {}

    # getting title
    fields["t"] = text_preprocessing(title)

    # getting categories
    fields["c"] = text_preprocessing(" ".join(re.findall(r"\[\[category:(.*?)\]\]", text)))
    text = re.sub(r"\[\[category:(.*?)\]\]", "", text)

    # getting infobox
    fields["i"] = " ".join(re.findall(r"\{\{.*?infobox(.*?)\}\}", text, flags=re.DOTALL))
    fields["i"] = text_preprocessing(process_infobox(fields["i"]))
    text = re.sub(r"\{\{.*?infobox.*?\}\}", "", text, flags=re.DOTALL)

    # getting links
    text = split_on_links(text)
    fields["l"] = text_preprocessing("")
    if len(text) > 1:
        hyperlinks = re.findall(r"\[?(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})(.*)\]?", text[-1])
        for i in range(len(hyperlinks)):
            hyperlinks[i] = " ".join(hyperlinks[i])
        hyperlinks = " ".join(hyperlinks)
        fields["l"] = text_preprocessing(hyperlinks)
    text = text[0]
    
    # getting references
    text = split_on_references(text)
    if len(text) > 1:
        pass
    text = text[0]
    
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
        if self.current_tag == "title":
            self.title += content
        elif self.current_tag == "id":
            self.id += content
        elif self.current_tag == "text":
            self.text += content
    
    def endElement(self, name):
        global pages
        if name == "page":
            pages += 1
            # print("Page:", pages)
            data = get_fields(self.title.lower(), self.text.lower())



if len(sys.argv) == 1:
    quit()

contentHandler = Handler()
parser = xml.sax.make_parser()
parser.setContentHandler(contentHandler)
parser.parse(sys.argv[1])
print("\n\n\n")
print("Pages:", pages)
print("Total tokens:", len(words))
print("Total tokens in index:", len(tokens_in_index))
with open("lexicon_porter.txt", "w") as file:
    lexicon = "\n".join(sorted(tokens_in_index))
    file.write(lexicon)
