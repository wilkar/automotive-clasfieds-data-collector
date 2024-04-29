import re
import warnings

import spacy
from bs4 import BeautifulSoup

nlp = spacy.load("pl_core_news_sm")


def clean_text(text: str) -> str:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        text = BeautifulSoup(text, "html.parser").get_text()
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    doc = nlp(text)
    lemmas = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    cleaned_text = " ".join(lemmas)
    return cleaned_text
