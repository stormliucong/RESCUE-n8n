# Agent Performance Evaluation

This directory contains the evaluation framework for assessing the performance of individual agents in the multi-agent chatbot system. Each agent is evaluated separately to ensure comprehensive testing and performance measurement.

## Evaluation Structure

The evaluation is split into two main parts for each agent:

1. **Action-Based Evaluation**
   - Focuses on individual actions and their correctness
   - Tests specific capabilities in isolation
   - Measures accuracy, response time, and error handling
   - Includes unit tests for each action type

2. **End-to-End Evaluation**
   - Simulates real-world scenarios in a controlled environment
   - Tests the agent's ability to handle complete conversations
   - Measures overall performance and user satisfaction
   - Includes integration tests and user simulation

## Agents Under Evaluation

### 1. Schedule Agent
Location: `eval/schedule/`
- **Action-Based Tests**
  - Appointment scheduling
  - Availability checking
  - Rescheduling
  - Cancellation handling
  - Time slot management

- **End-to-End Tests**
  - Complete scheduling workflows
  - Conflict resolution
  - User interaction patterns
  - Error recovery scenarios

### 2. Education Agent
Location: `eval/education/`
- **Action-Based Tests**
  - Course information retrieval
  - Program details explanation
  - Prerequisite checking
  - Registration guidance
  - FAQ handling

- **End-to-End Tests**
  - Student journey simulation
  - Course selection assistance
  - Program planning
  - Registration process
  - Information clarification

### 3. Insurance Agent
Location: `eval/insurance/`
- **Action-Based Tests**
  - Coverage explanation
  - Claim processing
  - Policy details retrieval
  - Premium calculation
  - Document verification

- **End-to-End Tests**
  - Insurance application process
  - Claim filing workflow
  - Policy management
  - Coverage adjustment
  - Customer support scenarios

## Evaluation Metrics

Each evaluation includes the following metrics:

1. **Accuracy**
   - Correct action execution
   - Appropriate response generation
   - Error rate

2. **Performance**
   - Response time
   - Resource utilization
   - Scalability

3. **User Experience**
   - Conversation flow
   - Clarity of responses
   - Helpfulness
   - User satisfaction

4. **Reliability**
   - Error handling
   - Recovery from failures
   - Consistency in responses

## Running Evaluations

Detailed instructions for running evaluations can be found in each agent's respective directory:

- [Schedule Agent Evaluation](schedule/README.md)
- [Education Agent Evaluation](education/README.md)
- [Insurance Agent Evaluation](insurance/README.md)

## Contributing

To add new evaluation scenarios or modify existing ones:

1. Create a new test case in the appropriate agent directory
2. Follow the existing test structure and format
3. Update the relevant README with new test information
4. Submit a pull request for review

## Requirements

- Node.js >= 14.x
- Redis server
- Test data sets (provided in each agent's directory)
- Evaluation environment configuration (see individual agent READMEs)

## License

This evaluation framework is part of the main project and follows the same licensing terms. 