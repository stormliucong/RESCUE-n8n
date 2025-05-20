import React, { useState, useEffect } from 'react';
import agentList from '../../data/agent_list.json';
import './AgentSelectionSection.css';

const AgentSelectionSection = ({ selectedAgents, setSelectedAgents }) => {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    setAgents(agentList.agents);
  }, []);

  const handleAgentSelection = (agentId, category) => {
    setSelectedAgents(prev => {
      const newSelection = { ...prev };
      
      // Remove from all categories first
      Object.keys(newSelection).forEach(key => {
        newSelection[key] = newSelection[key].filter(id => id !== agentId);
      });
      
      // Add to selected category if not "none"
      if (category !== 'none') {
        newSelection[category] = [...newSelection[category], agentId];
      }
      
      return newSelection;
    });
  };

  const getAgentCategory = (agentId) => {
    for (const [category, agents] of Object.entries(selectedAgents)) {
      if (agents.includes(agentId)) {
        return category;
      }
    }
    return 'none';
  };

  return (
    <div className="agent-selection-section">
      <h2>Agent Selection</h2>
      <div className="agent-list">
        {agents.map(agent => (
          <div key={agent.id} className="agent-item">
            <div className="agent-info">
              <h3>{agent.name}</h3>
              <p>{agent.description}</p>
            </div>
            <div className="agent-selection">
              <label>
                <input
                  type="radio"
                  name={`agent-${agent.id}`}
                  checked={getAgentCategory(agent.id) === 'required'}
                  onChange={() => handleAgentSelection(agent.id, 'required')}
                />
                Required
              </label>
              <label>
                <input
                  type="radio"
                  name={`agent-${agent.id}`}
                  checked={getAgentCategory(agent.id) === 'prohibited'}
                  onChange={() => handleAgentSelection(agent.id, 'prohibited')}
                />
                Prohibited
              </label>
              <label>
                <input
                  type="radio"
                  name={`agent-${agent.id}`}
                  checked={getAgentCategory(agent.id) === 'optional'}
                  onChange={() => handleAgentSelection(agent.id, 'optional')}
                />
                Optional
              </label>
              <label>
                <input
                  type="radio"
                  name={`agent-${agent.id}`}
                  checked={getAgentCategory(agent.id) === 'none'}
                  onChange={() => handleAgentSelection(agent.id, 'none')}
                />
                None
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentSelectionSection; 