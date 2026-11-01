"""code used by both training (train.py) and the live service (app/server.py).

Keeping it in one place guarantees that text is cleaned the SAME way when the model
learns and when it routes a new request.
"""
import re
import unicodedata

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

RENAMED_TO_ORIGINAL = {
    "Installs & Demo": "Installations",
    "Filters & Consumables": "Consumables",
}
ORIGINAL_TO_CURRENT = {original: new for new, original in RENAMED_TO_ORIGINAL.items()}

TEAMS = [
    "Billing", "Consumables", "Installations", "Product Advice",
    "Repairs", "Returns & Replacement", "Warranty Claims",
]

# Columns the model reads, besides the message text
CATEGORY_COLUMNS = ["channel", "product_family", "warranty_status"]


# text cleaning
def repair_broken_characters(text: str) -> str:
    """Fix text damaged in the Zoho migration (UTF-8 bytes shown as e.g. 'Ã©' or 'â€™')."""
    for _ in range(2):  # some messages were damaged twice
        try:
            text = text.encode("cp1252").decode("utf8")
        except Exception:
            break  # text is already fine
    return text


def remove_accents(text: str) -> str:
    """'namasté' -> 'namaste'."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def clean_text(raw_text: str) -> str:
    """Turn a raw customer message into plain lowercase words the model can learn from."""
    text = repair_broken_characters(str(raw_text))
    text = remove_accents(text).lower()
    text = re.sub(r"\b(sr|ko)\d+\b", " ", text)   # request/order numbers say nothing about the team
    text = re.sub(r"[^a-z0-9 ]+", " ", text)      # drop punctuation and symbols
    return re.sub(r"\s+", " ", text).strip()      # collapse repeated spaces


def add_clean_text_column(requests: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the requests with a new 'clean_text' column."""
    result = requests.copy()
    result["clean_text"] = result["request_text"].map(clean_text)
    return result

def build_model(regularisation_c: float = 10.0):
    """Text features (word + character patterns) and request details -> logistic regression.

    regularisation_c: higher = the model fits the training data more closely.
    """
    features = ColumnTransformer([
        ("words", TfidfVectorizer(ngram_range=(1, 3), min_df=2, sublinear_tf=True), "clean_text"),
        ("characters", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True), "clean_text"),
        ("details", OneHotEncoder(handle_unknown="ignore"), CATEGORY_COLUMNS),
    ])
    return make_pipeline(features, LogisticRegression(C=regularisation_c, max_iter=3000))