import React, { useState } from 'react';
import './SetupSection.css';

const SetupSection = ({ content, setContent }) => {
  const [isCodeMode, setIsCodeMode] = useState(false);

  return (
    <div className="setup-section">
      <div className="section-header">
        <h2>Setup Environment</h2>
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
          placeholder="Enter setup code here..."
          spellCheck="false"
        />
      ) : (
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="text-editor"
          placeholder="Enter setup instructions here..."
        />
      )}
    </div>
  );
};

export default SetupSection; 