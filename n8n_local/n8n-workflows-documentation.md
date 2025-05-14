# n8n Workflows Documentation

This document provides structured documentation for each n8n workflow in the system. Each section contains the title, tags, purpose, trigger, output, activation status, and webhook URL (if applicable).

---

## Diagnostic Agent
- **Tags**: type: core, status: dev
- **Purpose**: Analyze patient and family history data to assess hereditary risks and recommend appropriate genetic diagnostic or carrier tests. Relevant citations are provided as well.
- **Trigger**: Workflow input trigger (not a webhook)
- **Output**: Provides test recommendations and risk assessments internally.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Front Desk Agent
- **Tags**: type: core, status: dev
- **Purpose**: Handle patient or provider requests, determine intent, and coordinate specialist tools.
- **Trigger**: Webhook POST `/webhook/4905e8f1-db09-49f9-9308-9cb75dc52f21`
- **Output**: Summary responses sent via chat interface.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Admin Agent
- **Tags**: type: core, status: dev
- **Purpose**: Oversee administrative tasks for genetic consultations (scheduling, referrals, documentation).
- **Trigger**: Manual workflow trigger (no webhook)
- **Output**: Administrative task outcomes within the execution.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Front Desk Agent DEMO
- **Tags**: type: core, status: archived
- **Purpose**: Demonstration flow for front‑desk agent routing.
- **Trigger**: Multiple triggers including webhook `0a8650cd-4756-46d8-ab64-e51a21e06b83`
- **Output**: Routes and responds via chat, webhook, or messaging channels.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Triage Agent
- **Tags**: type: core, status: dev
- **Purpose**: Parse unstructured genetic requests, categorize care needs, and submit structured triage data.
- **Trigger**: Workflow input trigger (not a webhook)
- **Output**: POST JSON payload to backend API for counselor queueing.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Interactive Agent Test Workflow: Patient Agent
- **Tags**: type: test, status: dev
- **Purpose**: Simulate a patient agent in interactive consultation tests. Used to evaluate other agents.
- **Trigger**: Webhook POST `/webhook/4549813e-3274-43bf-b541-dcfda9854f00`
- **Output**: Replies forwarded to Front Desk Agent; confirmation JSON response.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Knowledge Base Update: PubMed
- **Tags**: type: secondary, status: dev
- **Purpose**: Retrieve PubMed articles from the journal 'Genetics in Medicine', and load embeddings into Pinecone.
- **Trigger**: Manual trigger
- **Output**: Article embeddings stored in Pinecone vector index.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Test Interpretation Agent
- **Tags**: type: core, status: dev
- **Purpose**: Interpret genetic test results alongside clinical context.
- **Trigger**: Workflow input trigger
- **Output**: Detailed interpretation generated within workflow.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Knowledge Base Update
- **Tags**: type: secondary, status: archived
- **Purpose**: Monitor Google Drive folder and update knowledge‑base embeddings (simulates retrieving internal protocols docs).
- **Trigger**: Google Drive file create/update.
- **Output**: Document embeddings & metadata pushed to Pinecone.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Knowledge Update DEMO
- **Tags**: type: secondary, status: archived
- **Purpose**: Demo flow for Google Drive → Pinecone ingestion.
- **Trigger**: Google Drive polling.
- **Output**: Embedded documents saved to Pinecone.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Schedule Agent
- **Tags**: type: core, status: archived
- **Purpose**: Manage appointment scheduling via FHIR APIs (create, reschedule, cancel).
- **Trigger**: Invoked by another workflow (no webhook)
- **Output**: FHIR resource operations executed through HTTP.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Verification Agent Design
- **Tags**: type: core, status: dev
- **Purpose**: Verify patient eligibility for care or external referral based on clinical rules.
- **Trigger**: Executed by another workflow (no webhook)
- **Output**: Structured eligibility assessment returned internally.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Patient Agent: Profile Generation via PubMed Case Reports
- **Tags**: type: eval, status: dev
- **Purpose**: Extract patient profiles & diagnoses from PubMed case reports and log results to Google Sheets.
- **Trigger**: Manual trigger
- **Output**: Structured profiles appended to Google Sheet.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Interactive Agent Evaluation: Front Desk Agent
- **Tags**: type: test, status: dev
- **Purpose**: Evaluate front‑desk agent routing and hand‑off logic.
- **Trigger**: Webhook POST `/webhook/413ab7a1-30ae-4276-a5d0-8d5ecda4f7a3`
- **Output**: Conversation JSON responses; forwards data to patient & education agents.
- **Status**: Active
- **Webhook**: https://congliu.app.n8n.cloud/webhook/413ab7a1-30ae-4276-a5d0-8d5ecda4f7a3

---

## Workflows Import
- **Tags**: type: test, status: temp
- **Purpose**: Import all of the project's workflows JSON via webhook. This is called by a github action to keep the workflows folder up-to-date.
- **Trigger**: Webhook `/webhook/26b664d3-4b93-4e13-b75b-0759c697c058`
- **Output**: Returns incoming items directly in HTTP response.
- **Status**: Active
- **Webhook**: https://congliu.app.n8n.cloud/webhook/26b664d3-4b93-4e13-b75b-0759c697c058

---

## Import Executions
- **Tags**: type: eval, status: temp
- **Purpose**: Fetch detailed execution logs by ID.
- **Trigger**: Webhook `/webhook/9e17d9af-78a5-46df-bb0f-76376c1eba3e`
- **Output**: Execution JSON returned to caller.
- **Status**: Active
- **Webhook**: https://congliu.app.n8n.cloud/webhook/9e17d9af-78a5-46df-bb0f-76376c1eba3e

---

## Agent Evaluation: Education Agent
- **Tags**: type: eval, status: dev
- **Purpose**: Evaluate Education Agent responses using questions from Google Sheet.
- **Trigger**: Manual trigger
- **Output**: Evaluation scores written back to Google Sheet.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Workflows Documentation Generator
- **Tags**: type: test, status: dev
- **Purpose**: Generate markdown documentation for n8n workflows via LLM.
- **Trigger**: Manual trigger
- **Output**: Documentation text produced within execution.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Schedule Agent Design
- **Tags**: type: core, status: dev
- **Purpose**: Automate appointment scheduling logic via FHIR.
- **Trigger**: Invoked internally (no webhook)
- **Output**: Scheduling operations performed via FHIR calls.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Education Agent
- **Tags**: type: core, status: dev
- **Purpose**: Provide personalized educational content on genetic conditions, tests, and management.
- **Trigger**: Webhook POST `/webhook/bdfcc15d-a70c-4fb4-9df6-5beaf18fa2d6`
- **Output**: Patient‑facing JSON reply with cited sources.
- **Status**: Inactive
- **Webhook**: https://congliu.app.n8n.cloud/webhook/bdfcc15d-a70c-4fb4-9df6-5beaf18fa2d6

---

## Knowledge Base Update: GeneReviews
- **Tags**: type: secondary, status: dev
- **Purpose**: Download, process, and index GeneReviews documents into vector store and metadata DB.
- **Trigger**: Manual trigger
- **Output**: Embeddings stored in Pinecone; metadata saved to Supabase.
- **Status**: Inactive
- **Webhook**: Not applicable

---

## Interactive Agent Evaluation: Customizable Patient Agent
- **Tags**: type: eval, status: dev
- **Purpose**: Simulate a patient by feeding the agent a patient profile. This is useful for evaluation scenarios.
- **Trigger**: Webhook POST `/webhook/4549813e-3274-43bf-b541-dcfda9854f00`
- **Output**: Patient replies JSON; forwards data as needed.
- **Status**: Inactive
- **Webhook**: https://congliu.app.n8n.cloud/webhook/4549813e-3274-43bf-b541-dcfda9854f00

---

## Interactive Agent Evaluation: Education Agent
- **Tags**: type: eval, status: dev
- **Purpose**: Provide personalized genetic education and diagnostic support through an interactive evaluation workflow, routing conversation data to patient or front‑desk agents as appropriate. 
- **Trigger**: Webhook POST `/webhook/bdfcc15d-a70c-4fb4-9df6-5beaf18fa2d6`
- **Output**: JSON responses with educational content, conversation state, and routing decisions; also forwards data via HTTP requests to patient and front‑desk agents.
- **Status**: Active
- **Webhook**: https://congliu.app.n8n.cloud/webhook/bdfcc15d-a70c-4fb4-9df6-5beaf18fa2d6
