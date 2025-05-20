import React, { useState, useEffect } from 'react';
import toolList from '../../data/tool_list.json';
import './ToolSelectionSection.css';

const ToolSelectionSection = ({ selectedTools, setSelectedTools }) => {
  const [tools, setTools] = useState([]);
  const [toolPlaceholders, setToolPlaceholders] = useState({});

  useEffect(() => {
    setTools(toolList.tools);
  }, []);

  const handleToolSelection = (toolId, category) => {
    setSelectedTools(prev => {
      const newSelection = { ...prev };
      
      // Remove from all categories first
      Object.keys(newSelection).forEach(key => {
        newSelection[key] = newSelection[key].filter(id => id !== toolId);
      });
      
      // Add to selected category if not "none"
      if (category !== 'none') {
        newSelection[category] = [...newSelection[category], toolId];
      }
      
      return newSelection;
    });
  };

  const handlePlaceholderChange = (toolId, placeholderName, value) => {
    setToolPlaceholders(prev => ({
      ...prev,
      [toolId]: {
        ...prev[toolId],
        [placeholderName]: value
      }
    }));
  };

  const getToolCategory = (toolId) => {
    for (const [category, tools] of Object.entries(selectedTools)) {
      if (tools.includes(toolId)) {
        return category;
      }
    }
    return 'none';
  };

  return (
    <div className="tool-selection-section">
      <h2>Tool Selection</h2>
      <div className="tool-list">
        {tools.map(tool => (
          <div key={tool.id} className="tool-item">
            <div className="tool-info">
              <h3>{tool.name}</h3>
              <p>{tool.description}</p>
            </div>
            <div className="tool-selection">
              <label>
                <input
                  type="radio"
                  name={`tool-${tool.id}`}
                  checked={getToolCategory(tool.id) === 'required'}
                  onChange={() => handleToolSelection(tool.id, 'required')}
                />
                Required
              </label>
              <label>
                <input
                  type="radio"
                  name={`tool-${tool.id}`}
                  checked={getToolCategory(tool.id) === 'prohibited'}
                  onChange={() => handleToolSelection(tool.id, 'prohibited')}
                />
                Prohibited
              </label>
              <label>
                <input
                  type="radio"
                  name={`tool-${tool.id}`}
                  checked={getToolCategory(tool.id) === 'optional'}
                  onChange={() => handleToolSelection(tool.id, 'optional')}
                />
                Optional
              </label>
              <label>
                <input
                  type="radio"
                  name={`tool-${tool.id}`}
                  checked={getToolCategory(tool.id) === 'none'}
                  onChange={() => handleToolSelection(tool.id, 'none')}
                />
                None
              </label>
            </div>
            {getToolCategory(tool.id) === 'required' && (
              <div className="tool-placeholders">
                <h4>Placeholder Configuration</h4>
                {tool.placeholders.map(placeholder => (
                  <div key={placeholder.name} className="placeholder-item">
                    <label>{placeholder.description}</label>
                    {placeholder.type === 'enum' ? (
                      <select
                        value={toolPlaceholders[tool.id]?.[placeholder.name] || ''}
                        onChange={(e) => handlePlaceholderChange(tool.id, placeholder.name, e.target.value)}
                      >
                        <option value="">Select {placeholder.name}</option>
                        {placeholder.options.map(option => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={toolPlaceholders[tool.id]?.[placeholder.name] || ''}
                        onChange={(e) => handlePlaceholderChange(tool.id, placeholder.name, e.target.value)}
                        placeholder={`Enter ${placeholder.name}`}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ToolSelectionSection; 