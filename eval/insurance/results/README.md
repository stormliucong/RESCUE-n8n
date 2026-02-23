# 📊 Insurance Workflow Experiment Results

This folder contains experimental outputs for the evaluating LLM agents for genetic testing insurance workflow.
Raw experiment outputs are organized by iteration for retrieval tasks (name & policy), while 
aggregated evaluation results are stored separately for analysis and reporting.

---

# 🧩 1️⃣ name_retrieval

Contains results for **insurance payer (in-network provider) retrieval experiments**.

## 📂 Structure

name_retrieval/
├── final/
│   ├── iteration_1/
│   ├── iteration_2/
│   └── iteration_3/
└── evaluation_results/

## 🔹 final/iteration_{#}/

Raw outputs for each experimental iteration.

Each iteration stores:
- Model-specific outputs
  - Prompt-specific results (e.g., baseline, explicit_source)
- Retrieved provider names

These represent the direct outputs of LLM-based payer name generation experiments.

## 🔹 evaluation_results/

Processed evaluation outputs for **payer name retrieval** experiments.
This directory contains analysis-ready tables that summarize performance by
(model × prompt × iteration) and include GPT-4o matching criteria.


### Main files

- **name_result_fin.csv**  
  Master evaluation table (row = model × prompt × iteration).
  Includes:
  - retrieved count (`ret`) and total gold count (`total`)
  - match counts 
  - Precision / Recall / F1 for each matching criterion
  This file is the primary source for cross-model / cross-prompt comparisons,
  statistical analysis, and figure generation.

- **{model}_eval_by_{judge}.csv** (e.g., `gpt_4o_eval_by_gpt_4o.csv`, `gpt_5_mini_eval_by_gpt_...csv`)  
  Per-model summary tables grouped by prompt type and iteration.
  Typically includes per-iteration rows and an `Average` row for the prompt.

- **llm_evaluation_log_*.csv**  
  Logs generated during LLM-based matching/evaluation.
  Useful for debugging discrepancies (e.g., common/missing/extra provider lists).
---

# 📄 2️⃣ policy_retrieval

Contains outputs of **insurance policy document retrieval experiments**.

These experiments evaluate whether LLMs can correctly retrieve official
genetic testing coverage policy documents.

## 📂 Structure

policy_retrieval/
└── final/
    ├── iteration_1/
    ├── iteration_2/
    ├── iteration_3/
    ├── all_assessments.csv
    ├── all_links.csv
    ├── payer_results.csv
    └── policy_experiment_result.csv

---

## 🔹 final/iteration_{#}/

Raw policy retrieval outputs for each independent experiment run.
Each iteration follows a hierarchical structure of model_prompt_payer.


### Directory hierarchy

- **Model level**  
`gpt-4o`, `gpt-5-mini`

- **Prompt level**  
`baseline`, `keyword`, `verified`

- **Insurance provider level**  
`Aetna`, `Blue_Cross_and_Blue_Shield_Federal_Employee_Program`, `Cigna`, `United_Healthcare`

---

### Files within each provider folder

Each provider folder typically contains:

- `*_raw_response.txt`  
  Full raw LLM output for the retrieval query.

- `*_result.json`  
  Structured extraction of the LLM response, including identified links and metadata.

- `downloaded/`  
  Downloaded policy files (PDF or HTML) retrieved during the experiment.

- `downloaded_pdfs.csv`  
  List of downloaded documents with metadata (file name, source URL, status).

- `links_summary.csv`  
  Summary of all retrieved candidate links before filtering or verification.

- `md5_comparison_results.csv` (if applicable)  
  MD5 hash comparison results used to verify document uniqueness and match with ground truth.

---

## 🔹 Aggregated Result Files

The following CSV files summarize results across all iterations:

### all_assessments.csv
Contains detailed assessment records for every experiment run,
including prompt, model, insurance provider, and retrieval outcome.

### all_links.csv
Comprehensive list of all retrieved links across experiments.

### policy_experiment_result.csv
Overall retrieval experiment summary statistics,
used for reporting and manuscript figures.

---

# 🔬 Reproducibility Note

- `final/iteration_*` directories contain raw experiment outputs.
- Aggregated CSV files provide processed results for analysis.
- Evaluation summaries are derived from raw outputs using scripts in `codes/`.

This structure ensures full reproducibility of reported results.