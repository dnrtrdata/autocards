#!/usr/bin/env python3


import sys
sys.path.append("../../.")
from autocards import Autocards
from pathlib import Path


prefix = "On Napoléon : "
file = Path("./napoleon.txt")

if not file.exists():
    print("File not found!")
    raise SystemExit()
else:
    full_text = file.read_text()

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
