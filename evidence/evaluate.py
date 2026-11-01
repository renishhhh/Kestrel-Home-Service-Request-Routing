"""Turn the results into rupees. Run AFTER train.py """
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd

from kestrel_router import RENAMED_TO_ORIGINAL

# Costs from the operations policy (section 4)
COST_PER_TRANSFER = 305            # Rs, handling time for each transfer between teams
COST_EXTRA_CUSTOMER_CONTACT = 260  # Rs, a misrouted request causes one extra contact on average
LICENCE_PER_YEAR = 320000          # Rs, vendor routing bot

history = pd.read_csv("data/train.csv").merge(pd.read_csv("data/resolution_log.csv"), on="request_id")
history["right_team"] = history.final_team.replace(RENAMED_TO_ORIGINAL)
history["bot_team"] = history.team_label.replace(RENAMED_TO_ORIGINAL)
metrics = json.load(open("evidence/metrics.json"))

# What one wrongly routed request costs
bot_misroutes = history[history.bot_team != history.right_team]
transfers_per_misroute = float(bot_misroutes.transfers.mean())
cost_per_misroute = transfers_per_misroute * COST_PER_TRANSFER + COST_EXTRA_CUSTOMER_CONTACT

# Monthly cost with the bot vs with the new model
requests_per_month = metrics["req_per_month"]
bot_error_rate = 1 - metrics["bot_vs_final"]
model_error_rate = 1 - metrics["model_vs_final"]
monthly_saving = (bot_error_rate - model_error_rate) * requests_per_month * cost_per_misroute

results = {
    "transfers_per_misrouted": round(transfers_per_misroute, 2),
    "cost_per_misroute": round(cost_per_misroute),
    "bot_misroute_rate": round(bot_error_rate, 3),
    "model_misroute_rate": round(model_error_rate, 3),
    "monthly_volume": round(requests_per_month),
    "bot_monthly_misroute_cost": round(bot_error_rate * requests_per_month * cost_per_misroute),
    "model_monthly_misroute_cost": round(model_error_rate * requests_per_month * cost_per_misroute),
    "monthly_saving_from_fewer_misroutes": round(monthly_saving),
    "licence_monthly": round(LICENCE_PER_YEAR / 12),
    "total_monthly_benefit_before_hosting": round(monthly_saving + LICENCE_PER_YEAR / 12),
}

# How good is each of the bot's queues, and how work is really spread
results["bot_accuracy_by_queue"] = {
    queue: round(float((rows.bot_team == rows.right_team).mean()), 3)
    for queue, rows in history.groupby("bot_team")
}
results["bot_queue_share"] = history.bot_team.value_counts(normalize=True).round(3).to_dict()
results["actual_workload_share_final_team"] = history.right_team.value_counts(normalize=True).round(3).to_dict()
billing_queue = history[history.bot_team == "Billing"]
results["billing_queue_really_billing"] = round(float((billing_queue.right_team == "Billing").mean()), 3)
results["billing_queue_ends_up"] = billing_queue.right_team.value_counts(normalize=True).round(3).to_dict()

with open("evidence/rupees.json", "w") as f:
    json.dump(results, f, indent=1)
print(json.dumps(results, indent=1))