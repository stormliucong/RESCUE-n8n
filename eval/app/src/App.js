import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import TaskCreationPanel from './components/TaskCreationPanel';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Task Creation Interface</h1>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<TaskCreationPanel />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 