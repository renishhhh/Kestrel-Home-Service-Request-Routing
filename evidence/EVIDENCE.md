# Evidence

Holdout: fit on Apr 2025-Mar 2026, scored on Apr-Jun 2026 (2,135 requests). Raw numbers: `metrics.json`, `rupees.json`, confusion tables in this folder.

| Compared | Accuracy vs where request was closed |
|---|---|
| Existing bot | 76.7% |
| Model trained on bot labels (copy of bot) | 75.8% (matches the bot's labels 94.8%) |
| **This model (trained on final team)** | **83.9%** (95% interval 82.4-85.4%) |

How often it does not work:
- Confidence >= 0.9: 77% of requests, 97.0% right.
- Confidence < 0.5: 11% of requests, 21.0% right. These are flagged `needs_triage`.
- Per team, precision and recall are all between 0.80 and 0.88.
- Vague messages ("complaint about X", "someone contact me about X"): final team is spread across all seven with no link to product, warranty, channel or time (p about 0.06-0.08), so no model can fix them from this data.

Bot's own problems (train, 10,822 requests): 25% needed at least one transfer; Billing queue is 65% truly billing, Consumables 60%, Repairs 64%; other queues 96-97%.
Reproduce: `python train.py && python evidence/evaluate.py`.
