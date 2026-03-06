import React, { useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const handleSend = async () => {
    // TODO: Connect to backend API
    setResponse('Backend not connected yet');
  };

  return (
    <div className="app">
      <header>
        <h1>Open-Cowork</h1>
      </header>
      <main>
        <div className="chat-container">
          <div className="messages">
            {response && <div className="message">{response}</div>}
          </div>
          <div className="input-area">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type a message..."
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
