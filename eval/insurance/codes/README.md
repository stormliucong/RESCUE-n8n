# Code Structure

This directory contains modular implementations of the experimental components used in the LLM-based insurance workflow study for genetic testing.

Each task is executed via a dedicated entry script.  
All other Python files within each module serve as internal utilities (data loading, parsing, scoring, aggregation, etc.).

---

## 🔹 Entry Scripts (One per Task)

| Task | Entry Script | Description | Outputs |
|------|-------------|-------------|---------|
| Payer name retrieval | `name_retrieval/experiment.py` | LLM-based payer identification experiments | `results/name_retrieval/` |
| Policy document retrieval | `policy_retrieval/experiment.py` | Policy link retrieval + MD5 verification | `results/policy_retrieval/` |
| Patient–policy matching (ST + header) | `patient_policy_match/header_execute.py` | SentenceTransformer embedding + summarized policy input | `results/patient_policy_match/` |
| Patient–policy matching (ST + whole policy) | `patient_policy_match/whole_policy_execute.py` | SentenceTransformer embedding + full policy text | `results/patient_policy_match/` |
| Patient–policy matching (OpenAI embedding) | `patient_policy_match/policy_openai.py` | OpenAI text-embedding-3-small + header/whole-policy input | `results/patient_policy_match/` |
| Insurance QA Evaluation (OpenAI backbone) | `rag_qna/openai_embedding.py` | Executes structured insurance QA (Q0–Q8) under document-conditioning settings (Baseline (no document), all_correct, all_incorrect) using Text-embedding-3-small embedding based patient-policy matching (match/unmatch) results. This configuration is used in the manuscript. | `results/LLM_QnA/RAG/final/final_qna_results/open_ai` |
| Insurance QA Evaluation (ST backbone) | `rag_qna/ST_embedding_qna.py` |Executes structured insurance QA (Q0–Q8) under document-conditioning settings (Baseline (no document), all_correct, all_incorrect) using SentenceTransformer embedding based patient-policy matching (match/unmatch) results.  | `results/LLM_QnA/RAG/final/final_qna_results/ST` |

### QA Document Conditioning Strategy

The QA module does not perform retrieval itself.  
Instead, it consumes previously generated patient–policy matching results and evaluates downstream QA performance under controlled document-conditioning scenarios:

- **Baseline**: No policy document provided (patient narrative only).
- **Matched / Unmatched**: Documents selected according to matching outcomes from patient-policy matching.
- **All Correct**: Every patient is paired with its ground-truth policy document.
- **All Incorrect**: Every patient is paired with a high-similarity but incorrect policy document (excluding the ground truth).

---

## 🔹 Run Examples

From the repository root:
```bash
cd eval/insurance
```

### 1️⃣ In-network provider retrieval
```bash
codes/name_retrieval/experiment.py
```

### 2️⃣ Policy document retrieval
```bash
codes/policy_retrieval/experiment.py
```

### 3️⃣ Patient–policy matching
SentenceTransformer (header input):
```bash
codes/patient_policy_match/header_execute.py
```

SentenceTransformer (whole-policy input):
```bash
codes/patient_policy_match/whole_policy_execute.py
```

OpenAI embedding (text-embedding-3-small):
```bash
codes/patient_policy_match/policy_openai.py
```

### 4️⃣ LLM QA (used in manuscript)
```bash
codes/rag_qna/openai_embedding.py
```

---

## 🔹 Module Overview

### 1️⃣ name_retrieval/

Implements payer identification experiments.

Responsibilities include:
- Provider name extraction
- GPT-4o Judge
- Log parsing and preprocessing
- Experimental execution scripts

This module evaluates whether LLM agents can correctly identify in-network insurance providers.

---

### 2️⃣ policy_retrieval/

Implements policy document retrieval pipelines.

Core components:
- Policy document acquisition (PDF download and loading)
- Prompt-based retrieval experiments
- Experimental execution control
- Retrieval result aggregation and merging
- MD5-based document comparison and verification
- Retrieval performance assessment

This module evaluates retrieval correctness and document alignment.

---

### 3️⃣ patient_policy_matching/

Implements the policy–patient alignment and retrieval evaluation (RAG).

This module performs:
- Candidate policy retrieval
- Embedding-based ranking
- LLM-based reranking
- Whole-policy/Summarized (Header) input execution
- Retrieval result aggregation
- MD5-based document verification
- Match-rate computation and analysis


It quantifies retrieval correctness under different configurations
(e.g., Top-K, Top-C, LLM reranked rank, cosine similarity rank, whole-policy execution).

---

### 4️⃣ rag_qna/

Implements the full structured Q0–Q8 evaluation pipeline.

This module includes:
- Baseline QA execution (patient narrative only)
- Documented QA (patient narrative + policy documents)
- Batch execution and result management
- JSON-to-CSV merging utilities
- Final accuracy and adjusted accuracy calculation

This module evaluates downstream decision quality under different document-conditioning settings.

---

### 5️⃣ analysis_figures/

Contains statistical analysis (QA only), patient-policy match analysis and figure generation scripts used in manuscript preparation.

---

## 🔹 Utility Scripts

- `qna_sample_generation.py`  
  Generates synthetic QA patient samples and ground-truth annotations.

- `batch_check.py`  
  Performs batch checks across experimental outputs and download the results.

---
