#!/usr/bin/env python3


#################################################################
# Notes :
# * you can pause and resume this process usinc ctrl+c (it will
#   open the pdb debugger, you can resume by tiping c then enter
#   in pdb
#################################################################
from pathlib import Path
import requests
import re
import sys
import pandas as pd
import time
import argparse
import signal
from bs4 import BeautifulSoup
from pprint import pprint as pprint
from tqdm import tqdm

sys.path.append("../../.")  # otherwise it can't find Autocards
from autocards import Autocards


def debug_signal_handler(signal, frame):
    """
    according to stackoverflow, this allows to make the script interruptible
    and resume it at will (ctrl+C / c)
    https://stackoverflow.com/questions/10239760/interrupt-pause-running-python-program-in-pdb/39478157#39478157
    """
    import pdb
    pdb.set_trace()
signal.signal(signal.SIGINT, debug_signal_handler)

parser = argparse.ArgumentParser()
parser.add_argument("--url", "-u",
                    metavar="URL",
                    dest='url',
                    type=str,
                    required=True,
                    help="a link to a page")
parser.add_argument("--element", "-e",
                    metavar="element",
                    dest='element',
                    type=str,
                    required=False,
                    default="p",
                    help="tag of html element of the page you're looking for\
                            for example 'p' for paragraph, default is 'p'")


def sanitize_text(text: str) -> str:
    "used to cleanup text and removing annotations"
    text = str(text)
    text = re.sub(r"\[\d*\]", "", text)
    return text.strip()


def get_parsed_from_url(url: str):
    "gets the content of the page from its url"
    res = requests.get(url, timeout=30)
    html_page = res.content
    return BeautifulSoup(html_page, "html.parser")


def get_title(parsed):
    "returns the title from the url"
    return sanitize_text(parsed.find_all('h1')[0].text)


def get_element_and_title(one_url: str) -> list[str]:
    """
    extracts the paragraph and the title from a url
    careful, it returns [[p1, p2, p3, ...], title]
    """
    soup = get_parsed_from_url(one_url)
    results = soup.find_all(element)
    output = []
    for i in results:
        i = sanitize_text(i.text)
        output.append(i)
    try:
        output.remove("")
        output.remove("\n")
    except ValueError:
        pass
    return [output, get_title(soup)]


def check_output_file() -> str:
    """
    checks if there is already an output file, if so then change the name
    of the future file. This avoid erasing it by mistake
    """
    if not Path("./output.csv").exists():
        return "output.csv"
    i = 0
    while i <= 1000:
        i += 1
        if not Path(f"./output_{i}.csv").exists():
            return f"output_{i}.csv"
        if i == 999:
            print("Cannot create output file because name already exists!")
            raise SystemExit()


if __name__ == "__main__":
    # fetch arguments
    args = parser.parse_args().__dict__
    url = args['url']
    element = args['element']

    # gets data from outline url
    soup = get_parsed_from_url(url)
    outline_title = get_title(soup)

    # misc
    auto = Autocards()
    auto.clear()
    df = pd.DataFrame(columns=["creation_time", "clozed_text", "question",
                               "answer", "title", "url", "paragraph"])
    output_name = check_output_file()

    # now let's process the url
    (text_content, title) = get_element_and_title(url)

    print("Processing each paragraph :")
    for p in tqdm(text_content):  # loops over each paragraph
        try:
            auto.consume_text(p)
        except IndexError:
            answer = "This issue often appears when the paragraph is not suited for card creation."
            question = "Skipped paragraph"
            
        p = p.replace(",", r"\,")
        p = p.replace("\n", "<br>")
        p.strip()
        title.strip()
        for qa_i in range(len(auto.qa_pairs)):
            q = auto.qa_pairs[qa_i]['question']
            a = auto.qa_pairs[qa_i]['answer']
            q.strip() ; a.strip()
            clozed_text = q + "<br>{{c1::" + a + "}}"
            dic ={"creation_time": time.asctime(),
                   "clozed_text": clozed_text,
                   "question": q,
                   "answer": a,
                   "title": title,
                   "url": url,
                   #"sentence": s,
                   "paragraph": p}
            df = df.append(dic, ignore_index=True)
            #pprint(dic)  # used to debug, careful it hides tqdm
            df.to_csv(output_name)
        df.drop_duplicates(['question', 'answer'], keep = "first", inplace=True, ignore_index=True)
        auto.clear()
