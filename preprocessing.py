import re
from nltk.corpus import stopwords
import Stemmer


stopWords = set(stopwords.words("english"))


def text_preprocessing(text):
    text = re.sub(r"==.*==", "", text) # Removing section headings
    text = re.sub(r"&.+;", "", text) # Removing special symbols like &gt; &lt;
    text = re.sub(r"`|~|!|@|#|\$|%|\^|&|\*|\(|\)|-|_|=|\+|\||\\|\[|\]|\{|\}|;|:|'|\"|,|<|>|\.|/|\?|\n|\t", " ", text) # removing non alpha numeric
    text = text.split()
    text = list(filter(lambda x: x not in stopWords, text))
    stemmer = Stemmer.Stemmer("english")
    text = list(filter(lambda x: len(x) > 1, stemmer.stemWords(text)))
    return text
