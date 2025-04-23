# Education/Diagnosis Agent Evaluation Framework

This document details an evaluation framework for testing the performance of AI agents built for genetic education and diagnostic support. It is structured around two primary evaluation benchmarks, each tailored to measure different functional aspects of the system.

---

## 1. Evaluation Benchmarks

We evaluate agent performance across two benchmarks:

### 1.1 Single Interaction Benchmark
This benchmark tests performance in isolated question-answer exchanges. Key categories:

- **Knowledge Tier Adherence**
  - Tests the model's ability to respect the hierarchy of knowledge sources using *dummy genetic material* injected into vector databases.
  - Goal: ensure it does **not overwrite dummy knowledge with pretrained content**.

- **Education Use Cases (Pretrained Knowledge)**
  - Since PubMed and GeneReviews material is not yet fully populated in the vector DB, we test the model’s ability to answer diverse questions using its pretrained knowledge.
  - Prompts cover: genetic conditions, rare diseases, and treatment protocols.

- **Diagnosis Use Cases (Pretrained Knowledge)**
  - Construct patient vignettes based on PubMed case studies, omitting final diagnosis.
  - Task: the model must infer a likely diagnosis from the symptoms (single-turn).

- **Agent Scope Control**
  - Tests whether the model avoids answering questions outside its scope (e.g., administrative or unrelated medical fields).

- **Agent Coordination**
  - Checks the model’s ability to forward queries outside its role to the appropriate agent (e.g., scheduling or front desk).

Future additions will expand coverage to specialized categories such as:
- Pharmacogenomics (drug-gene pairs)
- Prenatal procedures and counseling

---

### 1.2 Scenario-Based Interaction Benchmark
This benchmark involves multi-turn interactions between the Education Agent and:
- a *customized patient agent*, or
- a real human user via the UI.

Each simulated user is given a patient profile and acts either as the patient or a PCP. These profiles are built from PubMed case studies (symptoms retained, diagnosis hidden for evaluation/testing purposes).

At the end of the session, the full interaction history is judged by an LLM evaluator or manually. Evaluation criteria include:

- Ability to ask clarifying questions
- Tone & language adaptation (PCP vs patient)
- Final diagnosis accuracy
- Red-flag triage capability
- Memory recall (consistency across turns)
- Proper tool usage
- Appropriate agent hand-offs
- Specialized use cases (e.g., variant interpretation; to be validated with genetic counselors)
- **Error & Recovery Tracking**
  - Measures the agent's ability to handle tool failures or unexpected conditions gracefully, including retrying failed actions or issuing clarifying messages.

---

## 2. Technical Details

- Agents are hosted on **n8n cloud**, accessed via webhooks.
- Memory is managed using **Redis**, session-scoped.
- The model backend is **GPT-4o** or **GPT-4.1**.
- Vector store: Pinecone (currently contains dummy data; to be extended with GeneReviews and PubMed).
- Workflows for processing PubMed case studies are also hosted on n8n.

---

## 3. Evaluation Data Extraction

### For single-turn benchmarks:
We extract the following from the n8n execution logs:

| Variable        | Purpose                                               |
|-----------------|-------------------------------------------------------|
| `final_out`     | Agent’s final reply text                              |
| `tiers_used`    | Ordered list of tiers/tools invoked                   |
| `token_total`   | End-to-end token usage                                |
| `tool_outputs`  | Dict mapping each tool to its output                  |
| `input_query`   | Prompt that triggered the interaction                 |
| `total_exec_ms` | Overall response latency (ms)                         |
| `tool_exec_ms`  | Execution time for each tool node                     |
| `tool_order`    | Chronological order of tool calls                     |

### For multi-turn scenarios:
Evaluation spans multiple n8n executions. To aggregate them:
- Use `sessionId` to identify linked executions.
- Extract memory traces from Redis.
- Combine the logs into a single interaction history.

That composite record is then judged by a rubric-based LLM.

---

## 4. Evaluation Thresholds

This section is currently under development. Future updates will define pass/fail thresholds and scoring criteria for each benchmark layer.


