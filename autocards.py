from pipelines import qg_pipeline

from tqdm import tqdm
from pathlib import Path
import pandas as pd
import time
import re
import os
from contextlib import suppress

import requests
import PyPDF2
import wikipedia
from wikipedia.exceptions import PageError
from bs4 import BeautifulSoup
from pprint import pprint
from epub_conversion.utils import open_book, convert_epub_to_lines

os.environ["TOKENIZERS_PARALLELISM"] = "true"


class Autocards:
    """
    Main class used to create flashcards from text. The variable
    'store_content' defines whether the original paragraph is stored in the
    output. This allows to store context alongside the question and answer pair
    but dramatically increase size. The variable notetype refers to the type
    of flashcard that must be created: either cloze, basic or both. The
    variable wtm allow to specify wether you want to remove the mention of
    Autocards in your cards.
    """

    def __init__(self,
                 store_content=True,
                 watermark=True,
                 cloze_type="anki"):
        print("Loading backend, this can take some time...")
        self.store_content = store_content
        self.cloze_type = cloze_type
        self.qg = qg_pipeline('question-generation',
                              model='valhalla/t5-base-qg-hl',
                              ans_model='valhalla/t5-small-qa-qg-hl')
        self.qa_dict = []

        if self.cloze_type not in ["anki", "SM"]:
            print("Invalid cloze type, must be either 'anki' or \
'SM'")
            raise SystemExit()

        self.qa_count = len(self.qa_dict)
        self.current_qa = self.qa_count

    def _call_qg(self, text, title):
        """
        Call question generation module, then turn the answer into a
        dictionnary containing metadata (clozed formating, creation time,
        title, source text)
        """
        try:
            self.qa_dict += self.qg(text)
        except IndexError:
            print(f"\nSkipping section because no cards \
could be made from that text: '{text}'\n")
            self.qa_dict.append({"question": "skipped",
                                 "answer": "skipped",
                                 "note_type": "basic"})

        self.current_qa = len(self.qa_dict)
        diff = self.current_qa - self.qa_count
        self.qa_count = len(self.qa_dict)

        cur_time = time.asctime()

        if self.store_content is True:
            stored_text = text
        else:
            stored_text = "Content not saved"

        # TODO: refactor loop
        for i in range(diff):
            i += 1
            if self.qa_dict[-i]["note_type"] == "cloze":
                cl_str = self.qa_dict[-i]["cloze"]
                cl_str = cl_str.replace("generate question: ", "")
                cl_str = cl_str.replace("<hl>", "{{c1::", 1)
                cl_str = cl_str.replace("<hl>", "}}", 1)
                cl_str = cl_str.replace(" }}", "}}")
                cl_str = cl_str.replace("{{c1:: ", "{{c1::")
                cl_str = cl_str.replace("</s>", "")
                self.qa_dict[-i]["cloze"] = cl_str

            if self.qa_dict[-i]["note_type"] == "basic":
                clozed_fmt = self.qa_dict[-i]['question'] + "<br>{{c1::"\
                    + self.qa_dict[-i]['answer'] + "}}"
                self.qa_dict[-i]["basic_in_clozed_format"] = clozed_fmt
            self.qa_dict[-i] = {**self.qa_dict[-i],
                                "creation_time_in_s": cur_time,
                                "source_title": title,
                                "source_text": stored_text}
        for i in range(diff):
            i += 1
            if self.cloze_type == "anki" and len(self.qa_dict) != i and\
               self.qa_dict[-i]["note_type"] == "cloze" and\
               self.qa_dict[-i+1]["note_type"] == "cloze":
                cl1 = re.sub(r"{{c\d+::|}}|\s", "",
                             self.qa_dict[-i]["cloze"])
                cl2 = re.sub(r"{{c\d+::|}}|\s", "",
                             self.qa_dict[-i+1]["cloze"])
                if cl1 == cl2:
                    cloze_n = int(re.search(r"{{c(\d+)::(.*?)}}",
                                        self.qa_dict[-i]["cloze"]).group(1))+1
                    match = re.search(r"{{c(\d+)::(.*?)}}",
                                      self.qa_dict[-i+1]["cloze"])
                    template = self.qa_dict[-i]["cloze"]
                    if "{{c" in template[0:match.start()]:
                        offset = len(str(cloze_n)) + 8
                    else:
                        offset = 0
                    big_cloze = template[0:match.start()+offset] +\
                        "{{c" + str(cloze_n) + "::" +\
                        template[match.start()+offset : match.end()+offset] +\
                        "}}" + template[match.end()+1+offset:]

                    big_cloze.strip()
                    breakpoint()
                    #self.qa_dict[-i]['cloze'] = big_cloze
                    self.qa_dict[-i+1]['cloze'] = big_cloze
                    self.qa_dict[-i]['cloze'] += " ___tomerge"
                    i -= 1   # to make sure all siblings are found

            if self.cloze_type == "SM":
                # TODO: implement SM cloze style
                print("SM cloze not yet implemented")
                raise SystemExit()


        if self.cloze_type == "anki":
            for qa in self.qa_dict:
                if qa["note_type"] == "cloze" and qa["cloze"].endswith(" ___tomerge"):
                    pass
                    #self.qa_dict.remove(qa)

        tqdm.write(f"Added {diff} qa pair (total = {self.current_qa})")

    def _sanitize_text(self, text):
        "correct common errors in text"
        # occurs sometimes in epubs apparently:
        text = text.replace("\xa0", " ")
        # wikipedia style citation:
        text = re.sub(r"\[\d*\]", "", text)
        # extra spaces:
        text = re.sub(r"\s\s*", " ", text)
        return text

    def consume_var(self, text, title="untitled variable",
                    per_paragraph=False):
        "Take text as input and create qa pairs"
        text = text.replace('\xad ', '')

        if per_paragraph:
            for paragraph in tqdm(text.split('\n\n'),
                                  desc="Processing by paragraph",
                                  unit="paragraph"):
                self._call_qg(paragraph, title)
        else:
            text = re.sub(r"\n\n*", ".", text)
            text = re.sub(r"\.\.*", ".", text)
            text = self._sanitize_text(text)
            self._call_qg(text, title)

    def consume_user_input(self, title="untitled user input"):
        "Take user input and create qa pairs"
        user_input = input("Enter your text below then press Enter (press\
 enter twice to validate input):\n>")

        print("\nFeeding your text to Autocards...")
        user_input = self._sanitize_text(user_input)
        self.consume_var(user_input, title, per_paragraph=False)
        print("Done feeding text.")

    def consume_pdf(self, pdf_path, per_paragraph=True):
        if not Path(pdf_path).exists():
            print(f"PDF file not found at {pdf_path}!")
            return None
        pdf = PyPDF2.PdfFileReader(open(pdf_path, 'rb'))
        try:
            title = pdf.documentInfo['/Title']
            print(f"PDF title : {title}")
        except KeyError:
            title = pdf_path.split("/")[-1]
            print(f"PDF title : {title}")

        full_text = []
        for page in pdf.pages:
            full_text.append(page.extractText())
        text = " ".join(full_text)
        text = self._sanitize_text(text)

        self.consume_var(text, title, per_paragraph)

    def consume_textfile(self, filepath, per_paragraph=False):
        "Take text file as input and create qa pairs"
        if not Path(filepath).exists():
            print(f"File not found at {filepath}")
        text = open(filepath).read()
        text = self._sanitize_text(text)
        filename = str(filepath).split("/")[-1]
        self.consume_var(text,
                         filename,
                         per_paragraph=per_paragraph)

    def consume_epub(self, filepath, title="untitled epub file"):
        "Take an epub file as input and create qa pairs"
        book = open_book(filepath)
        text = " ".join(convert_epub_to_lines(book))
        text = re.sub("<.*?>", "", text)
        text = re.sub("&nbsp;", " ", text)
        text = re.sub("&dash;", "-", text)
        text = re.sub("&.*?;", " ", text)
        # make paragraph limitation as expected in self.consume_var:
        text = text.replace("\r", "\n\n")
        text = re.sub("\n\n\n*", "\n\n", text)
        text = self._sanitize_text(text)
        self.consume_var(text, title, per_paragraph=True)

    def consume_web(self, source, mode="url", element="p"):
        "Take html file (local or via url) and create qa pairs"
        if mode not in ["local", "url"]:
            return "invalid arguments"
        if mode == "local":
            soup = BeautifulSoup(open(source), 'xml')
        elif mode == "url":
            res = requests.get(source, timeout=15)
            html = res.content
            soup = BeautifulSoup(html, 'xml')

        try:
            el = soup.article.body.find_all(element)
        except AttributeError:
            print("Using fallback method to extract page content")
            el = soup.find_all(element)

        title = ""
        with suppress(Exception):
            title = soup.find_all('h1')[0].text
        if title == "":
            with suppress(Exception):
                title = soup.find_all('h1').text
        if title == "":
            with suppress(Exception):
                title = soup.find_all('title').text
        if title == "":
            print("Couldn't find title of the page")
            title = source
        title.strip()

        valid_sections = []  # remove text sections that are too short:
        for section in el:
            section = ' '.join(section.get_text().split())
            if len(section) > 40:
                valid_sections += [section]
            else:
                print(f"Ignored string because too short: {section}")

        if not valid_sections:
            print("No valid sections found, change the 'element' argument\
 to look for other html sections than 'p'. Find the relevant 'element' using \
 the 'inspect' functionnality in your favorite browser.")
            return None

        for section in tqdm(valid_sections,
                            desc="Processing by section",
                            unit="section"):
            section = self._sanitize_text(section)
            self._call_qg(section, title)

    def clear_qa(self):
        "Delete currently stored qa pairs"
        self.qa_dict = []
        self.qa_count = 0
        self.current_qa = 0

    def string_output(self, prefix='', jeopardy=False):
        "Return qa pairs to the user"
        if prefix != "" and prefix[-1] != ' ':
            prefix += ' '
        if len(self.qa_dict) == 0:
            print("No qa generated yet!")
            return None

        res = []
        for qa_pair in self.qa_dict:
            if qa_pair['note_type'] == "basic":
                if jeopardy:
                    string = f"\"{prefix}{qa_pair['answer']}\",\" {qa_pair['question']}\""
                else:
                    string = f"\"{prefix}{qa_pair['question']}\",\" {qa_pair['answer']}\""
            elif qa_pair['note_type'] == "cloze":
                string = f"\"{prefix}{qa_pair['cloze']}\""
            res.append(string)
        return res

    def print(self, *args, **kwargs):
        "Print qa pairs to the user"
        print(self.string_output(*args, **kwargs))

    def pprint(self, *args, **kwargs):
        "Prettyprint qa pairs to the user"
        pprint(self.string_output(*args, **kwargs))

    def pandas_output(self, prefix=''):
        if len(self.qa_dict) == 0:
            print("No qa generated yet!")
            return None
        "Output a Pandas DataFrame containing qa pairs and metadata"
        df = pd.DataFrame(columns=list(self.qa_dict[0].keys()))
        for qa in self.qa_dict:
            df = df.append(qa, ignore_index=True)
        for i in df.index:
            for c in df.columns:
                if pd.isna(df.loc[i, c]):
                    # otherwise export functions break:
                    df.loc[i, c] = "Error"
        return df

    def to_csv(self, filename, prefix='', jeopardy=False):
        "Export qa pairs as csv file"
        if len(self.qa_dict) == 0:
            print("No qa generated yet!")
            return None
        if prefix != "" and prefix[-1] != ' ':
            prefix += ' '

        df = self.pandas_output(prefix)

        for i in df.index:
            for c in df.columns:
                df.loc[i, c] = str(df.loc[i, c]).replace(",", r"\,")

        df.to_csv(filename)
        print(f"Done writing qa pairs to {filename}")

    def to_json(self, filename, prefix='', jeopardy=False):
        "Export qa pairs as json file"
        if len(self.qa_dict) == 0:
            print("No qa generated yet!")
            return None
        if prefix != "" and prefix[-1] != ' ':
            prefix += ' '

        self.pandas_output(prefix).to_json(filename)
        print(f"Done writing qa pairs to {filename}")
