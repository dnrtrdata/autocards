#!/usr/bin/env python3

import PyPDF2
import sys
import argparse
sys.path.append("../../.")
from autocards import Autocards
from pathlib import Path
from pprint import pprint


parser = argparse.ArgumentParser()
parser.add_argument("--pdf", "-p",
                    metavar="PDF",
                    dest='pdf',
                    type=str,
                    required=True,
                    help="a path to the pdf you want to use")
args = parser.parse_args().__dict__



filepath = args['pdf']

if not Path(filepath).exists():
    print("File not found!")
    raise SystemExit()


file = PyPDF2.PdfFileReader(open(filepath, 'rb'))

full_text = []
for page in file.pages:
        full_text.append(page.extractText())

full_text = ' '.join(full_text)
full_text = full_text.replace("\n", " ")
print(full_text)


prefix = file.documentInfo['/Title']

auto = Autocards()
auto.clear()


sentence_list = full_text.split(".")
for i in sentence_list:  # readds the final point
    i = f"{i}.".strip()

output_file = Path(f"{file.parent}/output_file.txt")
output_file.touch()

print("Initialization complete.")

n = len(sentence_list)
for a in enumerate(sentence_list):
    i = a[0] ; s = a[1]
    print(s)
    print(f"Progress : {i}/{n} ({round(i/n*100,1)}%)")
    try :
        auto.consume_text(s)
        string = str('\"' + prefix + auto.qa_pairs[-1]['question'] + '\",\"' + auto.qa_pairs[-1]['answer'] + '\"' + "\n")
    except IndexError:
        print(f"Skipped sentence {s}")
        string = str(f"\"Skipped sentence : \", \"{s}\n\"")
    finally :
        with open(output_file.absolute(), "a") as of:
            of.write(string)

auto.print(prefix)

