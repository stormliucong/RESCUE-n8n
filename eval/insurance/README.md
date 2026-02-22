# Insurance Agent Workflows

📁 This folder contains the source codes, experimental outputs, and evaluation files associated with our study: **Evaluating Large Language Model Agents for Genetic Testing Insurance Workflows An End-to-End Assessment of Retrieval and Reliability**.

---

## 🧠 Purpose

This project investigates how web-search-capable LLM agents can support three key tasks in insurance policy workflows related to **genetic testing**, specifically for in-network labs like **GeneDx**:

1. **In-Network Insurance Provider Retrieval** 
2. **Policy Document Retrieval**
3. **Patient-Policy Matching**
4. **LLM Agent for Answering Relevant Questions**

All workflows aim to reduce administrative burden and improve access to coverage information in real time.

---

## 📂 Folder Descriptions

### `codes/`
- **Description**: Contains all the scripts and notebooks for this research.
### `dataset/`
- **Description**: Contains all data sources except insurance policies utilized for this research.
### `results/`
- **Description**: Contains all the experiment results for this research.


## 🧪 Experimental Tasks

1. **In-Network Provider Retrieval**  
   - Task: Identify insurance companies that are in-network with GeneDx.  
   - Input: Prompted queries via ChatGPT and Perplexity.  
   - Output: JSON list of providers → Compared with `In-Network_providers_Update.csv`.

2. **Policy Document Retrieval**  
   - Task: Retrieve official genetic testing policy documents (PDFs or web pages).  
   - Output: Structured JSON with `pdf_links` and `webpage_links`.

3. **Patient-Policy Matching**  
   - Task: Given a patient-specific information, retrieve the best policy utlizing RAG.  
   - Output: Rank, policy name

4. **LLM Agent for Answering Relevant Questions**  
   - Task: Given a policy document and patient-specific information, answer key insurance-related questions.  
   - Examples: Will the test be approved? Is pre-authorization required? Is the age criteria meet?  
   - Output: Answer with a brief reasoning.
---

## 📘 Related Manuscript

This project supports the manuscript titled:

**"Evaluating Large Language Model Agents for Genetic Testing Insurance Workflows An End-to-End Assessment of Retrieval and Reliability"**

Key contributions:
- Evaluation of real-time LLM-based retrieval
- Task-specific prompting & evaluation metrics
- Assessing LLM agent performance on End-To-End genetic testing insurance workflow
- Quantify failure modes: retrieval sensitivity, abstention rate

---

