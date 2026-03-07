import React, { useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const handleSend = async () => {
    if (!message.trim()) return;

    try {
      const res = await fetch('http://localhost:8080/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
      });

      const data = await res.json();
      setResponse(data.response || 'No response');
      setMessage('');
    } catch (error) {
      setResponse('Error connecting to backend: ' + error.message);
    }
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
