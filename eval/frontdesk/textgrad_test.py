# optimise_frontdesk_textgrad_v01.py

import time, random, re, requests, json, textgrad as tg

# ─── 1) Configure TextGrad v0.1.x backward engine ─────────────────────────
tg.set_backward_engine("gpt-4o", override=True)

# ─── 2) Wrap your n8n webhook (agent + parser) as a BlackboxLLM ───────────
class N8NAgent(tg.BlackboxLLM):
    def __init__(self, name, webhook_url):
        super().__init__(name)
        self.webhook_url = webhook_url

    def __call__(self, var: tg.Variable) -> tg.Variable:
        """
        var.value            = the SYSTEM PROMPT
        var.role_description = the USER QUERY
        """
        payload = {
            "sessionId":      str(time.time_ns()),
            "message":        var.role_description,
            "from_agent":     "patient_agent",
            "system_prompt":  var.value,
            "fhir_server_url": ""
        }
        resp = requests.post(self.webhook_url, json=payload, timeout=30)
        resp.raise_for_status()
        # The workflow’s code node returns final JSON with to_agent, end_conversation, output, etc.
        return tg.Variable(
            resp.text,
            role_description="parsed JSON reply",
            requires_grad=False
        )

# ─── 3) Your starting system prompt (trainable) ─────────────────────────────
start_prompt = """You are a front desk agent for a telemedicine clinic. In every interaction you must check the Redis memory for context.

If the patient’s question is strictly administrative (e.g., about billing, clinic policies, etc.), provide the answer. End your response with the token "<PATIENT>".

If the patient’s question requires a medical diagnosis or specialized medical knowledge, forward the entire message verbatim to the education agent. End your output with the token "<EDUCATION>".

If the patient is specifically requesting to book, reschedule, or cancel an appointment, or asking about available time slots, clinic hours, or scheduling logistics, you must forward the entire message verbatim to the scheduling agent. End your output with the token "<SCHEDULING>".

By default, you must always end your reply with the token "<PATIENT>", unless it is a referral to an agent.

If at any point the conversation should conclude, output the single token: "<STOP>"."""
prompt_var = tg.Variable(start_prompt, role_description="", requires_grad=True)

# ─── 4) Create the Textual Gradient Descent optimizer ───────────────────────
optimizer = tg.TGD(parameters=[prompt_var])

# ─── 5) Hard-coded training & validation sets (check JSON fields only) ─────
train = [
    {"u":"Please update my insurance on file.",
     "gold":{"to_agent":"patient_agent",   "end_conversation":False}},
    {"u":"How does an MRI work?",
     "gold":{"to_agent":"education_agent","end_conversation":False}},
    {"u":"Can I book an appointment next Tuesday?",
     "gold":{"to_agent":"scheduling_agent","end_conversation":False}},
    {"u":"Thanks, that’s all for now.",
     "gold":{"to_agent":"patient_agent",   "end_conversation":True}},
    {"u":"Tell me a joke.",
     "gold":{"to_agent":"patient_agent",   "end_conversation":False}},
    {"u":"Do you accept my new billing code?",
     "gold":{"to_agent":"patient_agent",   "end_conversation":False}},
]

val = [
    {"u":"When are you open on Saturdays?",
     "gold":{"to_agent":"scheduling_agent","end_conversation":False}},
    {"u":"Explain side effects of ibuprofen.",
     "gold":{"to_agent":"education_agent","end_conversation":False}},
    {"u":"What’s your refund policy?",
     "gold":{"to_agent":"patient_agent",   "end_conversation":False}},
]

agent = N8NAgent("gpt-4o", "https://congliu.app.n8n.cloud/webhook/413ab7a1-30ae-4276-a5d0-8d5ecda4f7a3")

best_prompt, best_acc = prompt_var.value, 0.0

# ─── helper: judge JSON reply against gold fields ───────────────────────────
def judge_json(reply_text, gold):
    try:
        js = json.loads(reply_text)
    except:
        return 0.0
    score = 0
    score += (js.get("to_agent") == gold["to_agent"])
    score += (js.get("end_conversation") == gold["end_conversation"])
    return score / 2.0

# ─── 6) Optimization loop ─────────────────────────────────────────────────
for epoch in range(1, 4):
    print(f"\nEpoch {epoch}")
    optimizer.zero_grad()
    feedbacks = []

    # a) Training phase
    for ex in train:
        prompt_var.role_description = ex["u"]
        reply_var = agent(prompt_var)

        critic_inst = (
            f"Gold routing: {ex['gold']}\n"
            "Evaluate the JSON reply {pred} and return exactly:\n"
            "score: <0-1 float>\n"
            "feedback: \"<ONE sentence starting with 'Append: ', NO JSON, NO rewriting existing text unless it contardicts a previous point>\""
        )
        loss_var = tg.TextLoss(critic_inst)(reply_var)
        # capture that single-sentence feedback
        fb = str(loss_var).split("feedback:",1)[1].strip().strip('"')
        feedbacks.append(fb)
        loss_var.backward()

    # b) Apply textual gradient (rewrite prompt_var.value)
    try:
        optimizer.step()
    except IndexError:
        print("⚠️ Editor malformed → rollback")
        prompt_var.value = best_prompt

    # Prevent JSON from creeping into the prompt
    if re.search(r"\{.*\}", prompt_var.value):
        print("⚠️ Prompt looks like JSON → rollback")
        prompt_var.value = best_prompt

    # c) Validation pass
    pass_cnt = 0
    for ex in val:
        prompt_var.role_description = ex["u"]
        score = judge_json(agent(prompt_var).value, ex["gold"])
        if score == 1.0:
            pass_cnt += 1
    acc = pass_cnt / len(val)
    print("  Validation accuracy:", f"{acc:.0%}")

    # d) Accept or rollback
    if acc > best_acc:
        best_acc, best_prompt = acc, prompt_var.value
        print("  ✅ New best prompt")
    else:
        prompt_var.value = best_prompt
        print("  ↩ Reverted to previous best")

    # e) Show all feedbacks
    print("  Critic feedbacks:")
    for fb in feedbacks:
        print("   •", fb)

# ─── 7) Save optimized prompt ─────────────────────────────────────────────
with open("best_prompt.txt", "w") as f:
    f.write(best_prompt)

print(f"\nDone. Best validation accuracy: {best_acc:.0%}")
print("Optimized prompt:\n", best_prompt)
