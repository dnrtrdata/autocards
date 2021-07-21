# this code was part of the Autocards class but removed because it seemed too specific

import wikipedia
from wikipedia.exceptions import PageError


    def consume_wiki_summary(self, keyword, lang="en"):
        "Take a wikipedia keyword and creates qa pairs from its summary"
        if "http" in keyword:
            print("To consume a wikipedia summmary, you have to input \
the title of the article and not the url")
            return None
        wikipedia.set_lang(lang)
        try:
            wiki = wikipedia.page(keyword)
        except PageError as e:
            print(f"Page not found, error code:\n{e}")
            return None
        summary = wiki.summary
        title = wiki.title
        print(f"Article title: {title}")

        summary = self._sanitize_text(summary)
        self.consume_var(summary, title, True)

