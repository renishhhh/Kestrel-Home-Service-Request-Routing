# Kestrel Home - service-request router

Routes a service request to one of the seven teams, with a confidence and plain-English reasons.
Runs fully offline. **No API key, no per-request cost.**

## Run (clean machine, Python 3.12)
```
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app/server.py                                   # then open http://127.0.0.1:8000
```
The trained model is committed (`model/router.joblib`), so nothing needs training to start.
To retrain and regenerate predictions and evidence:
```
python train.py && python evidence/evaluate.py
```
Endpoint: `POST /route` with `{"channel","product_family","warranty_status","request_text"}`
returns `team`, `current_team_name`, `confidence`, `action` (`route` / `route_and_review` / `needs_triage`), `runner_up`, `scores`, `reasons`.
Bad input returns HTTP 400 with a readable message. `GET /health` for liveness.

## The key decision
`team_label` is **what the bot did**, not what was right. `resolution_log.final_team` is where the request was closed.
They agree only 77% of the time. A model trained on `team_label` copies the bot (it can match it 95%)
and its mistakes (76% right vs outcomes). So this model is trained on **final_team**.
The "90% match to labels" bar therefore is not the right target; see memo.

## Decisions I had to make
- **Target = final_team**, folded to the seven names in teams.csv. "Installs & Demo" and "Filters & Consumables" are
  the same teams after 15 Jan 2026 (policy s5), so they are merged for training. `predictions.csv` uses the seven names
  in `teams.csv`'s `team` column; the API also returns `current_team_name` (e.g. Installs & Demo). If your scorer wants the new names, map Installations->Installs & Demo, Consumables->Filters & Consumables.
- **Validation = time-based** (train Apr 2025-Mar 2026, test Apr-Jun 2026), because the real test is the newest requests.
- **Text cleaning**: Zoho mojibake repaired, accents stripped, SR/KO reference numbers removed (no routing signal).
  The test set is all CRM, so the mojibake does not affect it.
- **resolved_at is not used** (Zoho times are UTC, not converted; the model does not need it, and it is unknown at routing time anyway).
- **Data is "15 months", not 18** (Apr 2025 - Jun 2026). Used as given.
- **No LLM in the product.** Cost grows with volume for an API; this does not. Tested: TF-IDF + logistic regression
  is as accurate as the ambiguity allows (see evidence).
- **Vague messages** ("please call me about my purifier") are flagged `needs_triage` rather than pretend-routed.
  Their true team looks random in the data (no pattern by product, warranty, channel, time).
- Data stays in this repo/engagement team only (policy s10). Do not publish the CSVs.

## Files
`predictions.csv` (2,178 rows) | `train.py` | `kestrel_router.py` | `app/` | `evidence/` | `MEMO.md` 

## Known limits
~11% of messages come out low-confidence (21% right on those). About 16% of all requests will still reach the wrong team.
Only the bot's team is known at creation, not the customer's real need; some of that is not knowable from the text.
