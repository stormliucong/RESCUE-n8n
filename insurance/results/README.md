
## 📦 providers_generation_eval_results

This folder contains results of **in-network insurance provider generation experiments** using various prompts.

- **[Prompt]_experiment[#].csv**  
  Results for each prompt and trial number. Each CSV file contains retrieval performance for that specific prompt and trial.

- **summary_stats.csv**  
  Aggregated statistics summarizing overall experiment outcomes across all prompt trials.

## 📦 policy_retrieval

This folder contains results of **insurance policy retrieval experiments**, where LLMs were used to find official genetic testing coverage policies.

### llm_searched/

- Structure: `[Prompt]_[Trial#]` → Insurance companies  
- Contains the **raw insurance coverage policy documents retrieved by LLM**. 
Each file includes insurance provider names, retrieved file names, MD5 hash values, source links, and matching status for verifying document consistency and uniqueness per prompt and trial.

### md5/

- Structure: `[Prompt]_[Trial#]_md5.csv`  
- Contains **MD5 hash values** for each document retrieved per prompt and trial number. 

### retrieval/

- Structure: `[Prompt]_[Trial#].csv`  
- Stores the **retrieved insurance policy result summaries for each prompt and trial number**. Each file includes retrieved PDF links, webpage links, counts of retrieved and saved documents, total counts per provider, and overall aggregated statistics.

### md5_stats_by_trial.csv

- Provides **summary statistics** for MD5 hashing across all policy retrieval experiments. 

### prompt_combined_stat.csv

- Aggregated **summary statistics for the overall policy retrieval experiments**.  


