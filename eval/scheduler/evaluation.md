# Agent Evaluation Plan

## Overview
This document outlines a comprehensive evaluation plan for the scheduling agent, consisting of two main parts:
1. Simple *Task-Based* Evaluation
2. Complex *Multi-Turn* Interaction Evaluation

## Part 1: Simple Task-Based Evaluation

### Evaluation Setup
The evaluation will use predefined tasks from [task_*].py, covering:
- Patient Management 
- Medical History 
- Surgery Planning 
- Insurance Management 
- Guarantor Information 
- Appointment Scheduling 
- Waitlist Management
- other out-of-scope requests (Pending)
- other agent interaction (Pending)

Each task will be rated as easy (1), medium (2) & difficult (3) based on logics and lines of codes needed in human implementation.

### Evaluation Metrics

- 1-5: require human or LLM to score (this is task dependent, later we may summarize the criteria and train a "judge" agent to score it)
- 0-1: use defined assertion to score
- 0..*: dependend on the results

#### 1. Task Decomposition
- Ability to break down complex tasks into manageable steps (1-5)

#### 2. Tool Calling Accuracy 
- Correct identification of resourceType endpoints (0-1)
- Appropriate selection of FHIR operations (GET, POST, PUT, etc.) (0-1)
- Approriate order of tool selection (0-1)
- Proper refer other agents/workflows if it receives a request beyond its scope (0-1)

#### 3. Tool Use Success 
- Correctness of JSON payload structure (0-1). Derived from error codes.
- Break down the error codes captured (0..*)

#### 4. Task Completion Success 
- Task execution rate (0-1)
- End-to-end correct task completion rate (0-1)
- Critical error rate (0-1). critical errors are defined as those succesfully executed the task but incorrectly. Derived from the above two.

#### 5. Cost-Effectiveness
- Token usage per task (0..*)
- Execution time measurements (0..*)
- Number of API calls required (0..*)

### Experimental Variations
1. Baseline System Prompts
   - 1a. Minimal instruction set
   - 1b. Detailed CoT (Chain of Thought) instructions

2. FHIR Resource Knowledge (Pending)
   - Without specific FHIR resource guidance
   - With detailed FHIR resource relevant to the included tasks documented in the prompts.

3. Example Incorporation in System Prompts
   - Without task examples
   - With specific examples for each task type

4. Web search for FHIR resource page reading (Pending)
   - Without example search capability
   - With dynamic example retrieval

## Part 2: Complex Multi-Turn Interaction Evaluation (Pending)

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


