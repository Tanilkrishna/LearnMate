import React, { useContext, useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Sparkles, Send, Loader2, BookOpen, Calculator, Code, Leaf, Landmark, Atom, Palette, TestTube } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const topicIcons = {
  calculator: Calculator,
  code: Code,
  leaf: Leaf,
  'book-open': BookOpen,
  landmark: Landmark,
  atom: Atom,
  flask: Flask,
  palette: Palette
};

export default function AITutor() {
  const { user } = useContext(AuthContext);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatId, setChatId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchTopics();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchTopics = async () => {
    try {
      const response = await axios.get(`${API}/topics`);
      setTopics(response.data.topics);
    } catch (error) {
      console.error('Failed to fetch topics:', error);
    }
  };

  const handleTopicSelect = (topic) => {
    setSelectedTopic(topic);
    setMessages([{
      role: 'assistant',
      content: `Hi! I'm your AI Tutor for ${topic.name}. What would you like to learn today?`,
      timestamp: new Date().toISOString()
    }]);
    setChatId(null);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedTopic) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: inputMessage,
        topic: selectedTopic.name,
        chat_id: chatId
      });

      setChatId(response.data.chat_id);

      const aiMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2" data-testid="tutor-logo">
              <Sparkles className="h-8 w-8 text-blue-500" />
              <span className="text-2xl font-bold text-gradient">LearnMate</span>
            </Link>
            <div className="flex items-center space-x-6">
              <Link to="/" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="tutor-nav-home">Home</Link>
              <Link to="/features" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="tutor-nav-features">Features</Link>
              <Link to="/tutor" className="text-blue-500 font-semibold" data-testid="tutor-nav-tutor">AI Tutor</Link>
              <Link to="/dashboard" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="tutor-nav-dashboard">Dashboard</Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-20 pb-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto" data-testid="tutor-main">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-120px)]">
          {/* Sidebar */}
          <div className="lg:col-span-1" data-testid="tutor-sidebar">
            <Card className="h-full">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold mb-4" data-testid="sidebar-title">Select a Topic</h2>
                <div className="space-y-2">
                  {topics.map((topic, index) => {
                    const IconComponent = topicIcons[topic.icon] || BookOpen;
                    return (
                      <button
                        key={topic.id}
                        onClick={() => handleTopicSelect(topic)}
                        className={`w-full text-left p-3 rounded-lg transition-all flex items-center space-x-3 ${
                          selectedTopic?.id === topic.id
                            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
                            : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                        }`}
                        data-testid={`topic-button-${index}`}
                      >
                        <IconComponent className="h-5 w-5" />
                        <span>{topic.name}</span>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-3" data-testid="tutor-chat-area">
            <Card className="h-full flex flex-col">
              {selectedTopic ? (
                <>
                  {/* Chat Header */}
                  <div className="border-b p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-lg" data-testid="chat-header">
                    <h2 className="text-xl font-bold" data-testid="chat-topic-title">{selectedTopic.name}</h2>
                    <p className="text-sm opacity-90" data-testid="chat-topic-subtitle">Ask me anything about this topic!</p>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-4" data-testid="chat-messages">
                    {messages.map((message, index) => (
                      <div
                        key={index}
                        className={`chat-message flex ${
                          message.role === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                        data-testid={`chat-message-${index}`}
                      >
                        <div
                          className={`max-w-[80%] p-4 rounded-2xl ${
                            message.role === 'user'
                              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          <p className="whitespace-pre-wrap" data-testid={`message-content-${index}`}>{message.content}</p>
                        </div>
                      </div>
                    ))}
                    {loading && (
                      <div className="flex justify-start" data-testid="chat-loading">
                        <div className="bg-gray-100 p-4 rounded-2xl">
                          <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <div className="border-t p-4" data-testid="chat-input-area">
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Type your question..."
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                        data-testid="chat-input"
                      />
                      <Button
                        onClick={handleSendMessage}
                        disabled={loading || !inputMessage.trim()}
                        className="rounded-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                        data-testid="chat-send-button"
                      >
                        <Send className="h-5 w-5" />
                      </Button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center p-6" data-testid="chat-placeholder">
                  <div className="text-center">
                    <Sparkles className="h-16 w-16 text-blue-500 mx-auto mb-4" />
                    <h3 className="text-2xl font-bold text-gray-700 mb-2">Welcome to AI Tutor!</h3>
                    <p className="text-gray-500">Select a topic from the sidebar to begin learning</p>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}