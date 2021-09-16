import xml.sax
import sys
from encode_decode import decode, encode


def write_to_title(pages, page_id, title):
    global current_offset, titles_file, titles_offsets_file
    title = title.encode("ascii", errors="ignore").decode()
    write_string = encode(int(page_id)) + " " + title + "\n"
    bytes_written = len(write_string)
    titles_file.write(write_string)
    new_offset = current_offset + bytes_written
    offset_string = encode(pages) + " " + encode(current_offset) + " " + encode(new_offset) + "\n"
    current_offset = new_offset
    titles_offsets_file.write(offset_string)

page_id = None
pages = 0
current_offset = 0
titles_file = open(f"{sys.argv[2]}titles.txt", "w")
titles_offsets_file = open(f"{sys.argv[2]}titles_offsets.txt", "w")
class Handler(xml.sax.ContentHandler):

    def startElement(self, name, attrs):
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
    

    def endElement(self, name):
        global pages, page_id
        if name == "id" and page_id is None:
            page_id = self.id.strip()
        if name == "page":
            pages += 1
            write_to_title(pages, page_id, self.title.strip())
            page_id = None
            # print(pages)


handler = Handler()
parser = xml.sax.make_parser()
parser.setContentHandler(handler)
parser.parse(sys.argv[1])
