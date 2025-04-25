# Insurance Agent Workflows

📁 This folder contains the source codes, experimental outputs, and evaluation files associated with our study: **Leveraging Web-Search-Powered LLM Agents for Question Answering on Live Genetic Testing Insurance Policies**.

---

## 🧠 Purpose

This project investigates how web-search-capable LLM agents can support three key tasks in insurance policy workflows related to **genetic testing**, specifically for in-network labs like **GeneDx**:

1. **In-Network Insurance Provider Retrieval** & **Policy Document Retrieval**
2. **LLM Agent for Answering Relevant Questions**
3. **Pre-Authorization Form Completion**

All workflows aim to reduce administrative burden and improve access to coverage information in real time.

---

## 📂 Folder & File Descriptions

### `codes/`
- **Description**: Contains all scripts and notebooks for LLM-based provider and policy retrieval tasks.
- - `insurance_provider_retrieval.py`, `insurance_provider_retrieval.ipynb`: Scripts for retrieving GeneDx in-network providers using LLM agents.
- - `perplexity_insurance.ipynb`: Implementation using Perplexity AI for document search.
- - `policy_retrieval.py`, `LLM_policy_retrieval_modulized.ipynb`: Main driver script for running policy retrieval experiments across providers and prompts.

---

### `insurance_policy/`
- **Description**: Contains 587 **manually collected genetic testing policy documents** from 311 insurance providers.
- **Usage**: Serves as the ground truth for evaluating **LLM-based Policy Document Retrieval** performance.

---

### `results/`
- **Description**: Stores all experimental outputs including LLM-generated responses and evaluation summaries.

---

### `In-Network_providers.csv`
- **Description**: Cleaned and curated list of GeneDx in-network providers.
- **Usage**: Used as reference set for evaluating **In-Network Provider Retrieval** performance.


## 🧪 Experimental Tasks

1. **In-Network Provider Retrieval**  
   - Task: Identify insurance companies that are in-network with GeneDx.  
   - Input: Prompted queries via ChatGPT and Perplexity.  
   - Output: JSON list of providers → Compared with `In-Network_providers.csv`.

2. **Policy Document Retrieval**  
   - Task: Retrieve official genetic testing policy documents (PDFs or web pages).  
   - Output: Structured JSON with `pdf_links` and `webpage_links`.

3. **LLM Agent for Answering Relevant Questions**  
   - Task: Given a policy document and patient-specific information, answer key insurance-related questions.  
   - Examples: Will the test be approved? Is pre-authorization required? What steps are needed for claims?  
   - Output: Free-text answers grounded in retrieved policy content, manually evaluated for accuracy.

4. **Pre-Authorization Form Completion**  
   - Task: Generate a structured JSON submission based on retrieved policy and patient case.  
   - Output: Auto-filled form submitted via HTTP POST
---

## 📘 Related Manuscript

This project supports the manuscript titled:

**"Leveraging Web-Search-Powered LLM Agents for Question Answering on Live Genetic Testing Insurance Policies"**

Key contributions:
- Evaluation of real-time LLM-based retrieval
- Task-specific prompting & evaluation metrics
- JSON-based automation for clinical workflows

---

