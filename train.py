# Train the router, measure it honestly, and write predictions.csv.

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report

from kestrel_router import (RENAMED_TO_ORIGINAL, add_clean_text_column, build_model)

HOLDOUT_STARTS = "2026-04-01"           # newest three months are kept back for testing
C_VALUES_TO_TRY = (1, 3, 10, 30)


def load_training_data() -> pd.DataFrame:
    requests = pd.read_csv("data/train.csv")
    outcomes = pd.read_csv("data/resolution_log.csv")
    data = add_clean_text_column(requests.merge(outcomes, on="request_id"))
    data["right_team"] = data["final_team"].replace(RENAMED_TO_ORIGINAL)   # what we want to predict
    data["bot_team"] = data["team_label"].replace(RENAMED_TO_ORIGINAL)     # what the old bot did
    return data


def bootstrap_interval(is_correct: np.ndarray, repeats: int = 2000) -> list:
    rng = np.random.default_rng(0)
    scores = [is_correct[rng.integers(0, len(is_correct), len(is_correct))].mean() for _ in range(repeats)]
    return [float(np.percentile(scores, 2.5)), float(np.percentile(scores, 97.5))]


def main():
    data = load_training_data()

    #1. Honest test: learn from older months, test on the newest months
    older = data[data.created_at_ist < HOLDOUT_STARTS]
    newest = data[data.created_at_ist >= HOLDOUT_STARTS]

    accuracy_by_c = {}
    for c in C_VALUES_TO_TRY:
        model = build_model(c).fit(older, older.right_team)
        accuracy_by_c[c] = accuracy_score(newest.right_team, model.predict(newest))
    print("holdout accuracy for each C:", accuracy_by_c)

    best_c = max(accuracy_by_c, key=accuracy_by_c.get)
    model = build_model(best_c).fit(older, older.right_team)
    newest = newest.assign(prediction=model.predict(newest),
                           confidence=model.predict_proba(newest).max(axis=1))
    confident = newest.confidence >= 0.9
    unsure = newest.confidence < 0.5
    is_correct = (newest.right_team == newest.prediction).values

    # The "trap": a model trained to copy the bot's labels
    bot_copy = build_model(best_c).fit(older, older.bot_team)
    bot_copy_prediction = bot_copy.predict(newest)

    # 2. Save the numbers used in the memo
    metrics = {
        "C": best_c,
        "holdout_n": len(newest),
        "model_vs_final": accuracy_score(newest.right_team, newest.prediction),
        "bot_vs_final": accuracy_score(newest.right_team, newest.bot_team),
        "model_vs_bot_label": accuracy_score(newest.bot_team, newest.prediction),
        "bot_label_learnable": accuracy_score(newest.bot_team, bot_copy_prediction),
        "bot_clone_vs_final": accuracy_score(newest.right_team, bot_copy_prediction),
        "hi_conf_share": float(confident.mean()),
        "hi_conf_acc": accuracy_score(newest.right_team[confident], newest.prediction[confident]),
        "lo_conf_share": float(unsure.mean()),
        "lo_conf_acc": accuracy_score(newest.right_team[unsure], newest.prediction[unsure]),
        "ci95": bootstrap_interval(is_correct),
        "per_class": classification_report(newest.right_team, newest.prediction, output_dict=True),
        "train_transfers_per_req": float(data.transfers.mean()),
        "train_misrouted_share_bot": float((data.transfers > 0).mean()),
        "months": data.created_at_ist.str[:7].nunique(),
    }
    metrics["req_per_month"] = len(data) / metrics["months"]
    with open("evidence/metrics.json", "w") as f:
        json.dump(metrics, f, indent=1, default=float)
    pd.crosstab(newest.right_team, newest.prediction).to_csv("evidence/confusion_model.csv")
    pd.crosstab(newest.right_team, newest.bot_team).to_csv("evidence/confusion_bot.csv")
    print(json.dumps({k: v for k, v in metrics.items() if k != "per_class"}, indent=1))

    #3. Final model: learn from ALL labelled requests, then predict the test set
    final_model = build_model(best_c).fit(data, data.right_team)
    joblib.dump(final_model, "model/router.joblib")

    test_requests = pd.read_csv("data/test_unlabelled.csv")
    test_ready = add_clean_text_column(test_requests)
    teams = final_model.predict(test_ready)
    confidence = final_model.predict_proba(test_ready).max(axis=1)

    pd.DataFrame({"request_id": test_requests.request_id, "team": teams}).to_csv("predictions.csv", index=False)
    pd.DataFrame({"request_id": test_requests.request_id, "team": teams,
                  "confidence": confidence.round(3)}).to_csv("evidence/predictions_with_confidence.csv", index=False)
    print(pd.Series(teams).value_counts())
    print("share of low-confidence predictions:", (confidence < 0.5).mean())


if __name__ == "__main__":
    main()