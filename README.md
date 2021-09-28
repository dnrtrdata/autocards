# Autocards

- Automatically create questions and answers from various input formats (PDF files, webpages, wikipedia, epub files, etc) for your favorite flashcards software (like [anki](https://apps.ankiweb.net/), [SuperMemo](https://supermemo.guru/wiki/SuperMemo) or others).
- Can handle virtually any language thanks to inbuilt translation (but usually at the cost of lower quality cards).
- To see a real world example, the complete output of [this article](https://www.biography.com/political-figure/philip-ii-of-macedon) can be found [in this folder](./output_example/). It's the direct output with no post processing whatsoever.
- Code is PEP compliant and with docstrings. Contributions and PR are extremely appreciated.
- Learn more by reading [the official write-up](https://paulbricman.com/thoughtware/autocards).

## How to:

- This has been tested on python 3.9 but will probably work on earlier versions as well.
- `git clone https://github.com/paulbricman/autocards`
- `cd autocards`
- `pip install -r ./requirements.txt`
- install punkt by running `python -m nltk.downloader punkt`
- open a python console: `ipython3`
- read the [usage guide below](#Usage)

## Usage:
All arguments are mentioned with their default value, you don't have to supply them every time.

* initialization:
    * `from autocards import Autocards`
    * `a = Autocards(in_lang="en", out_lang="en")`

       *translation modules sometimes need to be downloaded and can be rather large*

* consuming input text is done using one of the following ways:
    * `a.consume_var(my_text, per_paragraph=True)`
    * `a.consume_user_input(title="")`
    * `a.consume_textfile(filename, per_paragraph=True)`
    * `a.consume_pdf(pdf_path, per_paragraph=True)`
    * `a.consume_web(source, mode="url", element="p")`

       *mode can be "url" or "local"*

       *element is the html element, like p for paragraph*

* different ways to get the results back:
    * `out = a.string_output(prefix='', jeopardy=False)`

       *prefix is a text that will be appended before the qa*

       *jeopardy is when switching question and answer*

    * `a.print(prefix='', jeopardy=False)`
    * `a.pprint(prefix='', jeopardy=False)`

       *pretty printing*

    * `a.to_anki(deckname="autocards_export", tags="some_tag")`
    * `df = a.pandas_df(prefix='')`
    * `a.to_csv("output.csv", prefix="")`
    * `a.to_json("output.json", prefix="")`

    *Also note that a user provided his own scripts that you can get inspiration from, they are a bit outdated but can be found in the folder `examples_script`*
