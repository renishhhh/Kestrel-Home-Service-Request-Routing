**To:** Ritu Deshpande  **From:** Kabir Nanda  **Re:** Replacing the routing bot

**The decision.** Yes, switch the bot off, but not on the 90% test you set. The labels in the export are what the bot *did*, not where requests *should* go. Comparing them with where requests were finally closed, the bot was right 77% of the time. A system built to match those labels at 90% would be copying the bot's mistakes. I built the replacement to match where requests actually ended up.

**The number.** On the newest quarter of past requests (held back from training), the new router sends 84% to the right team (likely range 82-86%), against 77% for the bot. It will not reach 90%, and nothing could from this data: about one message in nine says things like "please call me about my purifier", and the right team for those looks random. The router flags these for a quick question to the customer instead of guessing. When it is confident (77% of requests) it is right 97% of the time.

**Where the bot goes wrong (this is Meenal's point, confirmed).** Only 65% of the Billing queue is truly billing; the rest are people who mention they paid for a repair, installation, return or warranty. Consumables and Repairs are each right only about 60-64% of the time (purifier breakdowns and vague messages land there). That also changes headcount: Repairs is busiest either way (about 23% of work), but Installations (15%) and Returns (14%) are bigger than the bot's queues suggest, and Billing and Consumables are smaller (12% and 10%, versus 15% and 13.5% in the bot's queues).

**The rupees.** Each wrongly routed request costs about Rs 700 (1.4 transfers at Rs 305, plus Rs 260 for the extra customer call). At about 720 requests a month, the bot's misroutes cost roughly Rs 1.17 lakh a month; the new router's cost about Rs 0.81 lakh. That is about Rs 36,000 a month saved, plus Rs 26,700 a month from the licence you no longer pay (Rs 3.2 lakh a year): about Rs 63,000 a month in total. The router has no per-request fee. It runs on one small server; hosting should be a small fixed amount, but I have not got a quote, so Farhan should treat that as the one number still to confirm in writing. These savings assume the router's mistakes cost the same as the bot's.

**Next week.**
1. Run the router alongside the bot for two weeks, with agents seeing both suggestions. Do not switch off yet.
2. Check its accuracy on live requests. Switch the bot off if it holds at about 84%.
3. Ask Tanmay for a small hosting quote so Farhan has the run cost in writing.
4. Have Meenal's team handle the "ask the customer first" flags (about 1 in 9) with a standard one-line question.
5. Fix the Billing rule at the source: "I have paid" is not a billing request (policy section 3).
