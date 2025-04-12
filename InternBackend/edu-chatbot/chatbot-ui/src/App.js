import React, { useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");

  const handleSubmit = async () => {
    try {
      const result = await axios.post("http://127.0.0.1:5000/chat", { message });
      setResponse(result.data.response);
    } catch (error) {
      setResponse("Error occurred. Please try again.");
    }
  };

  return (
    <div className="App">
      <h1>Chatbot</h1>
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask me anything!"
      />
      <button onClick={handleSubmit}>Send</button>
      <div>
        <p>Response: {response}</p>
      </div>
    </div>
  );
}

export default App;
