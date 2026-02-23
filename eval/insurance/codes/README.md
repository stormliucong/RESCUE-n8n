# Code Structure

This directory contains modular implementations of the experimental components used in the LLM-based insurance workflow study for genetic testing.

The codebase is organized by experimental module rather than by file type, enabling controlled comparison across retrieval, matching, and QA settings.

---

## 🔹 Module Overview

### 1️⃣ name_retrieval/

Implements payer identification experiments.

Responsibilities include:
- Provider name extraction
- GPT-4o Matching
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

Contains statistical analysis (QA only) and figure generation scripts used in manuscript preparation.

---

## 🔹 Utility Scripts

- `qna_sample_generation.py`  
  Generates synthetic QA patient samples and ground-truth annotations.

- `batch_check.py`  
  Performs batch checks across experimental outputs and download the results.

---
