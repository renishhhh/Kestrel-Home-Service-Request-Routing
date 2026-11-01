# Kestrel Home — Service-Request Routing

A lightweight, offline machine-learning system that routes customer service requests to one of seven support teams, with confidence scores and plain-English explanations.

## Features

- TF-IDF and Logistic Regression for request classification.
- Confidence-based routing, review, and manual triage.
- FastAPI REST API for predictions.
- Offline inference with no API key or per-request cost.

## Tech Stack

Python, scikit-learn, pandas, FastAPI, Joblib.

## Project Structure

```text
kestrel/
├── app/                # API server
├── data/               # Input datasets
├── evidence/           # Evaluation results
├── model/              # Trained model
├── kestrel_router.py   # Routing logic
├── train.py            # Model training
├── requirements.txt    # Dependencies
├── README.md
└── MEMO.md             # Modelling decisions
```

## Getting Started

**Requirement:** Python 3.12

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and start the API:

```bash
pip install -r requirements.txt
python app/server.py
```

Open http://127.0.0.1:8000/docs to explore the API.

## API Endpoints

- `GET /health` — Check service health.
- `POST /route` — Predict the appropriate support team.

The routing endpoint returns the predicted team, confidence, recommended action, runner-up, scores, and explanations.

## Model Decisions

- **Target:** `final_team`, representing the team that resolved the request.
- **Validation:** Time-based split — April 2025 to March 2026 for training and April to June 2026 for testing.
- **Ambiguous requests:** Flagged for review or manual triage.
- **Model choice:** TF-IDF + Logistic Regression for lightweight, offline inference.

## Limitations

- Approximately 11% of messages receive low-confidence predictions.
- Approximately 16% of requests may still be routed incorrectly.
- Vague messages may require manual review.

See [MEMO.md](MEMO.md) for detailed modelling decisions.
