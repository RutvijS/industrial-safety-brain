import { useState } from "react";
import { sendMessage } from "../services/api";

function ChatBox() {
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async () => {
    const trimmed = message.trim();
    if (!trimmed) return;

    setError("");
    setLoading(true);

    // Add user message to conversation immediately
    setConversation((prev) => [...prev, { role: "user", text: trimmed }]);
    setMessage("");

    try {
      const aiResponse = await sendMessage(trimmed);
      setConversation((prev) => [...prev, { role: "ai", text: aiResponse }]);
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || "Failed to get a response. Is the backend running?";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chatbox">
      <div className="chatbox__messages" id="chat-messages">
        {conversation.length === 0 && (
          <div className="chatbox__welcome">
            <div className="chatbox__welcome-icon">🛡️</div>
            <h2>SafetyBrain AI</h2>
            <p>Your AI-powered industrial safety assistant. Ask me about workplace safety, hazard identification, OSHA regulations, and more.</p>
          </div>
        )}

        {conversation.map((msg, index) => (
          <div
            key={index}
            className={`chatbox__bubble chatbox__bubble--${msg.role}`}
          >
            <span className="chatbox__bubble-label">
              {msg.role === "user" ? "You" : "SafetyBrain AI"}
            </span>
            <p>{msg.text}</p>
          </div>
        ))}

        {loading && (
          <div className="chatbox__bubble chatbox__bubble--ai chatbox__bubble--loading">
            <span className="chatbox__bubble-label">SafetyBrain AI</span>
            <div className="chatbox__typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>

      {error && <div className="chatbox__error" id="chat-error">{error}</div>}

      <div className="chatbox__input-area">
        <input
          id="chat-input"
          type="text"
          className="chatbox__input"
          placeholder="Ask about industrial safety..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          autoComplete="off"
        />
        <button
          id="chat-send-btn"
          className="chatbox__send"
          onClick={handleSend}
          disabled={loading || !message.trim()}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default ChatBox;
