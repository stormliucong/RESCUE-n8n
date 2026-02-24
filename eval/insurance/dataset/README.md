# Evaluating LLM Agents for Genetic Testing Insurance Workflows 

This folder contains structured evaluation datasets used in the LLM-based insurance workflow study.

⚠️ Insurance policy documents used for embedding and retrieval experiments are not included in this repository.

The files in this folder support two core evaluation components:

1. **Payer Identification**
   - Benchmarking LLM agent ability to retrieve in-network insurance providers.

2. **QA Evaluation**
   - Structured Q0–Q8 evaluation over synthetic patient cases.

---

## 📊 Core Evaluation Datasets

### 🔹 final_ground_truth.json
Final validated ground-truth annotations used for patient-policy matching and QA evaluation.

### 🔹 filtered_ground_truth.json
Initial downsampling version of the ground truth.

### 🔹 filtered_llm_samples.json
LLM-generated samples based on filtered_ground_truth.

---

## 🧬 Patient Case Datasets

### 🔹 Insurance_Genetic_Testing_QA.json
Structured evaluation schema defining the nine-question (Q0–Q8) framework used for policy-grounded insurance coverage assessment.

This file specifies:
- Question identifiers (Q0–Q8)
- Full question text
- Standardized answer options for each question

It serves as the evaluation template for structured QA experiments.

---

## 🏥 Payer Dataset

### 🔹 In-Network_Providers_Update.csv
Curated list of in-network insurance providers for GeneDx.

Used as a ground-truth for benchmarking name retrieval accuracy.

---

## 🧩 Category Harmonization and Stratified Evaluation

Due to heterogeneous terminology across insurance policies, 
clinical indication (Q3) and family history criteria (Q5) were 
normalized into standardized high-level categories.

To achieve this:

1. Insurance-specific criteria were mapped into unified categories.
2. Category mappings were aligned across:
   - Insurance provider
   - Genetic test type
   - Clinical indication group

### Intermediate Category Files

- `cat_ind_q3.csv`
- `cat_test_ins_q3.csv`
- `cat_ind_q5.csv`
- `cat_test_ins_q5.csv`

These files contain normalized category mappings prior to integration.

### Final Merged Files

- `q3_merged.csv`
- `q5_merged.csv`

These files were generated via outer joins between:
- Retrieval outputs
- Ground-truth annotations
- Standardized category mappings

The merged datasets serve as canonical master tables used for:

- QA sample generation
- Structured Q0–Q8 ground-truth construction

---

## ⚠️ Notes

- Policy documents are publicly available insurer documents.
- No protected health information (PHI) is included.