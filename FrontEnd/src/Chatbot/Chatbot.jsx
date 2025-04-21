import { useState, useRef, useEffect } from "react";
import "./chatbot.scss";
import { Bot, X, Loader2 } from "lucide-react";
import axios from "axios";

function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "🤖 Xin chào! Mình là T3VMovieBot – bạn cần mình hỗ trợ gì không?",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef(null); // ✅ ref cuối cùng để scroll tới

  const toggleChat = () => setIsOpen(!isOpen);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom(); // ✅ tự cuộn khi có tin nhắn hoặc loading thay đổi
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!question.trim()) return;
    const newMessages = [...messages, { from: "user", text: question }];
    setMessages(newMessages);
    setLoading(true);
    setQuestion("");

    try {
      const res = await axios.post("http://localhost:8000/chat", {
        question,
        history: [],
      });

      const botReply = res?.data?.response || "Không nhận được phản hồi.";
      setMessages((prev) => [...prev, { from: "bot", text: botReply }]);
    } catch (error) {
      console.error("Lỗi khi gọi API:", error);
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: "❌ Không thể kết nối đến chatbot API." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button className="chatbot-toggle" onClick={toggleChat}>
        {isOpen ? <X size={20} /> : <Bot size={24} />}
      </button>

      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">T3VMovieBot 🎬</div>
          <div className="chatbot-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`msg ${msg.from}`}>
                {msg.text}
              </div>
            ))}
            {loading && (
              <div className="msg bot">
                <Loader2 className="loading-spinner" size={16} /> Đang xử lý...
              </div>
            )}
            <div ref={messagesEndRef} /> {/* ✅ ref để auto scroll */}
          </div>
          <div className="chatbot-input">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Nhập câu hỏi..."
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading}>
              Gửi
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default Chatbot;
