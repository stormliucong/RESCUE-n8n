# Agent Evaluation Plan

## Overview
This document outlines a comprehensive evaluation plan for the scheduling agent, consisting of two main parts:
1. Simple *Task-Based* Evaluation
2. Complex *Multi-Turn* Interaction Evaluation

## Part 1: Simple Task-Based Evaluation

### Evaluation Setup
The evaluation will use predefined tasks from evaluation prompts [1-16].py, covering:
- Patient Management (Tasks 1-2)
- Medical History (Tasks 3-4)
- Surgery Planning (Tasks 5-6)
- Insurance Management (Tasks 7-8)
- Guarantor Information (Tasks 9-10)
- Appointment Scheduling (Tasks 11-15)
- Waitlist Management (Task 16)

### Evaluation Metrics

- 1-5: require human or LLM to score
- 0-1: use defined assertion to score
- #: Work with execution log
- ##: Work with script to check FHIR server (`*.py`)

#### 1. Task Decomposition
- Ability to break down complex tasks into manageable steps (1-5#)
- Logical sequencing of operations (1-5#)
- Identification of dependencies between steps (1-5#)

#### 2. Tool Calling Accuracy 
- Correct identification of resourceType endpoints (0-1#)
- Appropriate selection of FHIR operations (GET, POST, PUT, etc.) (0-1#)
- Proper endpoint URL construction (0-1#)

#### 3. Tool Use Success 
- Correctness of JSON payload structure (0-1#)
- Proper handling of required vs optional fields (0-1#)

#### 4. Task Completion Success 
- End-to-end task completion rate (0-1##)
- Accuracy of final outcomes (0-1##)

#### 5. Critical Error Rate
- Make the critical error (1-5##)

#### 5. Cost-Effectiveness
- Token usage per task (#)
- Execution time measurements (#)
- Number of API calls required (#)

#### 6. Self-Correction Capability
- Error detection rate (0-1#)
- Alternative approach success rate (0-1#)

### Experimental Variations
1. Baseline System Prompts
   - 1a. Minimal instruction set
   - 1b. Detailed CoT (Chain of Thought) instructions

2. FHIR Resource Knowledge
   - Without specific FHIR resource guidance
   - With detailed FHIR resource relevant to the included tasks documented in the prompts.

3. Example Incorporation
   - Without task examples
   - With specific examples for each task type

4. Web search for FHIR resource page reading
   - Without example search capability
   - With dynamic example retrieval

## Part 2: Complex Multi-Turn Interaction Evaluation

### Evaluation Setup
1. Automated User Simulation
   - User profiles curated for a *user-agent*
   - Predefined interaction scenarios in prompts
   - Predined user behavior patterns in prompts


2. Manual User Testing
   - Real users

### Evaluation Metrics (Additional)

#### 1. Question Clarification Quality
- Relevance of clarifying questions (1-5#)
- Efficiency in gathering necessary information (1-5#)


#### 2. Edge Case Handling
- successful rate for complex cases (e.g. not defined in 1-16 tasks) (0-1##)

#### 3. Conversation Memory and Context
- Retention of user preferences (1-5#)
- Reference to previous interactions (1-5#)

#### 4. User Interaction Quality
- Response appropriateness (1-5#)
- Explanation clarity (1-5#)
- Professional tone maintenance (1-5#)


