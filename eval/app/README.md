# Task Creation Interface

A React-based interface for creating and managing tasks with agent and tool configurations.

## Features

- Random UUID generation for task IDs
- Three-way agent selection (Required/Prohibited/Optional)
- Task difficulty selection
- Tool selection with placeholder configuration
- Setup environment configuration
- Task evaluation criteria
- Human agent action configuration
- Code/Text mode toggle for configuration sections

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Installation

1. Clone the repository
2. Navigate to the project directory:
   ```bash
   cd eval/app
   ```
3. Install dependencies:
   ```bash
   npm install
   ```

## Running the Application

To start the development server:

```bash
npm start
```

The application will be available at `http://localhost:3000`.

## Project Structure

```
src/
  ├── components/
  │   ├── sections/
  │   │   ├── TaskIdSection.js
  │   │   ├── AgentSelectionSection.js
  │   │   ├── DifficultySection.js
  │   │   ├── ToolSelectionSection.js
  │   │   ├── SetupSection.js
  │   │   ├── EvaluationSection.js
  │   │   └── HumanAgentSection.js
  │   └── TaskCreationPanel.js
  ├── data/
  │   ├── agent_list.json
  │   └── tool_list.json
  ├── App.js
  └── index.js
```

## Configuration Files

### agent_list.json
Contains the list of available agents with their capabilities and descriptions.

### tool_list.json
Contains the list of available tools with their placeholders and configuration options.

## Usage

1. The task ID is automatically generated and can be refreshed using the "Generate New ID" button
2. Select agents and their roles (Required/Prohibited/Optional)
3. Choose the task difficulty level
4. Select tools and configure their placeholders if required
5. Configure the setup environment using either code or text mode
6. Define evaluation criteria
7. Configure human agent actions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 