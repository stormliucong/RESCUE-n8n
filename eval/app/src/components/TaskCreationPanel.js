import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import TaskIdSection from './sections/TaskIdSection';
import AgentSelectionSection from './sections/AgentSelectionSection';
import DifficultySection from './sections/DifficultySection';
import ToolSelectionSection from './sections/ToolSelectionSection';
import SetupSection from './sections/SetupSection';
import EvaluationSection from './sections/EvaluationSection';
import HumanAgentSection from './sections/HumanAgentSection';
import './TaskCreationPanel.css';

const TaskCreationPanel = () => {
  const [taskId, setTaskId] = useState(uuidv4());
  const [selectedAgents, setSelectedAgents] = useState({
    required: [],
    prohibited: [],
    optional: []
  });
  const [difficulty, setDifficulty] = useState('medium');
  const [selectedTools, setSelectedTools] = useState({
    required: [],
    prohibited: [],
    optional: []
  });
  const [setupContent, setSetupContent] = useState('');
  const [evaluationContent, setEvaluationContent] = useState('');
  const [humanAgentContent, setHumanAgentContent] = useState('');

  const handleNewTaskId = () => {
    setTaskId(uuidv4());
  };

  return (
    <div className="task-creation-panel">
      <TaskIdSection taskId={taskId} onNewId={handleNewTaskId} />
      <AgentSelectionSection
        selectedAgents={selectedAgents}
        setSelectedAgents={setSelectedAgents}
      />
      <DifficultySection
        difficulty={difficulty}
        setDifficulty={setDifficulty}
      />
      <ToolSelectionSection
        selectedTools={selectedTools}
        setSelectedTools={setSelectedTools}
      />
      <SetupSection
        content={setupContent}
        setContent={setSetupContent}
      />
      <EvaluationSection
        content={evaluationContent}
        setContent={setEvaluationContent}
      />
      <HumanAgentSection
        content={humanAgentContent}
        setContent={setHumanAgentContent}
      />
    </div>
  );
};

export default TaskCreationPanel; 