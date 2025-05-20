import React from 'react';
import './DifficultySection.css';

const DifficultySection = ({ difficulty, setDifficulty }) => {
  return (
    <div className="difficulty-section">
      <h2>Task Difficulty</h2>
      <div className="difficulty-selector">
        <select
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
          className="difficulty-dropdown"
        >
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>
    </div>
  );
};

export default DifficultySection; 