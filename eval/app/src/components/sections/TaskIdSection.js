import React from 'react';
import './TaskIdSection.css';

const TaskIdSection = ({ taskId, onNewId }) => {
  return (
    <div className="task-id-section">
      <h2>Task ID</h2>
      <div className="task-id-content">
        <input
          type="text"
          value={taskId}
          readOnly
          className="task-id-input"
        />
        <button onClick={onNewId} className="new-id-button">
          Generate New ID
        </button>
      </div>
    </div>
  );
};

export default TaskIdSection; 