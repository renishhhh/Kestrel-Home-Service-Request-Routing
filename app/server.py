"""The routing service: one endpoint (POST /route) and one screen (/).

Run from the project folder:   python app/server.py
Needs no API key and has no per-request cost: the model runs locally.
"""
import os
import sys

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from kestrel_router import ORIGINAL_TO_CURRENT, add_clean_text_column

model = joblib.load(os.path.join(PROJECT_FOLDER, "model", "router.joblib"))
app = Flask(__name__, static_folder=os.path.join(PROJECT_FOLDER, "app", "static"))

REQUIRED_FIELDS = ["channel", "product_family", "warranty_status", "request_text"]

# How sure the model must be before we trust it (measured: >=0.9 is right ~97% of the time,
# <0.5 is right only ~21% of the time)
CONFIDENT = 0.90
UNSURE = 0.50

# Everyday words that are not useful as an explanation for a Kestrel employee
FILLER_WORDS = {"the", "my", "on", "for", "and", "please", "pls", "sir", "hi", "paid", "kindly",
                "thanks", "asap", "help", "with", "has", "not", "via", "extra", "this", "payment"}


def words_that_drove_the_decision(request_row: pd.DataFrame, team: str, limit: int = 4) -> list:
    """The message phrases that pushed the model towards `team` (for the 'reasons' shown to staff)."""
    features, classifier = model.steps[0][1], model.steps[1][1]
    feature_values = features.transform(request_row)
    team_index = list(classifier.classes_).index(team)
    push_towards_team = feature_values.multiply(classifier.coef_[team_index]).tocoo()
    feature_names = features.get_feature_names_out()

    strongest_first = sorted(zip(push_towards_team.col, push_towards_team.data), key=lambda item: -item[1])
    phrases = []
    for column, strength in strongest_first:
        name = feature_names[column]
        if not name.startswith("words__"):
            continue
        phrase = name[len("words__"):]
        is_useful = strength > 0.05 and len(phrase) > 3 and not set(phrase.split()) & FILLER_WORDS
        if is_useful:
            phrases.append(phrase)
        if len(phrases) == limit:
            break
    return phrases


def decide_action(team: str, runner_up: str, confidence: float):
    """Turn the model's confidence into advice for the service desk."""
    if confidence >= CONFIDENT:
        return "route", f"Clear request: the wording points strongly to {team}."
    if confidence >= UNSURE:
        return "route_and_review", f"Probably {team}, but {runner_up} is plausible. Check the first reply."
    return "needs_triage", ("The message does not say enough to route reliably "
                            "(e.g. 'please call me about my purifier'). Ask the customer one question before assigning.")


@app.get("/")
def screen():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/route")
def route():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Send a JSON object."), 400
    missing = [field for field in REQUIRED_FIELDS if not str(body.get(field, "")).strip()]
    if missing:
        return jsonify(error="Missing fields: " + ", ".join(missing)), 400

    request_row = add_clean_text_column(pd.DataFrame([{field: str(body[field]) for field in REQUIRED_FIELDS}]))
    probabilities = model.predict_proba(request_row)[0]
    best_first = np.argsort(-probabilities)
    team = model.classes_[best_first[0]]
    runner_up = model.classes_[best_first[1]]
    confidence = float(probabilities[best_first[0]])

    action, summary = decide_action(team, runner_up, confidence)
    reasons = [summary]
    phrases = words_that_drove_the_decision(request_row, team)
    if phrases:
        reasons.append("Words that drove this: " + ", ".join(f'"{p}"' for p in phrases) + ".")
    if "paid" in request_row.clean_text.iloc[0] and team != "Billing":
        reasons.append("Customer mentions paying, but the problem is not the payment itself, "
                       "so it is not Billing (policy s3).")

    return jsonify(
        team=team,
        current_team_name=ORIGINAL_TO_CURRENT.get(team, team),
        confidence=round(confidence, 3),
        action=action,
        runner_up=runner_up,
        scores={name: round(float(p), 3) for name, p in zip(model.classes_, probabilities)},
        reasons=reasons,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))