import React, { useState } from 'react';
import './HumanAgentSection.css';

const HumanAgentSection = ({ content, setContent }) => {
  const [isCodeMode, setIsCodeMode] = useState(false);

  return (
    <div className="human-agent-section">
      <div className="section-header">
        <h2>Human Agent Actions</h2>
        <div className="mode-toggle">
          <label className="switch">
            <input
              type="checkbox"
              checked={isCodeMode}
              onChange={() => setIsCodeMode(!isCodeMode)}
            />
            <span className="slider round"></span>
          </label>
          <span>{isCodeMode ? 'Code Mode' : 'Text Mode'}</span>
        </div>
      </div>
      {isCodeMode ? (
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="code-editor"
          placeholder="Enter human agent code here..."
          spellCheck="false"
        />
      ) : (
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="text-editor"
          placeholder="Enter human agent actions here..."
        />
      )}
    </div>
  );
};

export default HumanAgentSection; 