# Autocards
* Automatically create flashcards from user input, PDF files, wikipedia summary, webpages, and more!
* To get a real world example, you can take a look at the complete output on [this article](https://www.biography.com/political-figure/philip-ii-of-macedon) can be found [in this folder](./output_example/). Nothing has been manually altered, it's the direct output.
* Code is PEP compliant and all docstrings are written, hence contributions and PR are extremely appreciated
* Learn more by reading [the official write-up](https://psionica.org/docs/lab/autocards/).

## Install guide:
* `git clone https//github.com/Psionica/Autocards`
* `cd Autocards`
* `pip install -r ./requirements.txt`
* run a python console: `ipython3`
* install punkt by running `!python -m nltk.downloader punkt`

### Autocards usage
```
# loading
from autocards import Autocards
a = Autocards()

# eating the input text using one of the following ways:
a.consume_var(my_text, per_paragraph=True) 
a.consume_user_input(title="")
a.consume_wiki_summary(keyword, lang="en")
a.consume_textfile(filename, per_paragraph=True)
a.consume_pdf(pdf_path, per_paragraph=True)
a.consume_web(source, mode="url", element="p")
# =>  * element is the html element, like p for paragraph
#     * mode can be "url" or "local"

# three ways to get the results back:
out = a.string_output(prefix='', jeopardy=False)
#    =>  * prefix is a text that will be appended before the qa
#        * jeopardy is when switching question and answer
a.print(prefix='', jeopardy=False)
a.pprint(prefix='', jeopardy=False)  # pretty printing
df = a.pandas_output(prefix='')
a.to_csv("output.csv", prefix="", jeopardy=False)
a.to_json("output.json", prefix="", jeopardy=False)

# Also note that a user provided his own terrible scripts that you can get inspiration from, they are located in the folder `examples_script`
```
