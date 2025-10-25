import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import Home from './pages/Home';
import AITutor from './pages/AITutor';
import Features from './pages/Features';
import Dashboard from './pages/Dashboard';
import { Toaster } from '@/components/ui/sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

axios.defaults.withCredentials = true;

export const AuthContext = React.createContext();

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processingAuth, setProcessingAuth] = useState(false);

  useEffect(() => {
    // Check for session_id in URL fragment first
    const hash = window.location.hash;
    if (hash && hash.includes('session_id=')) {
      setProcessingAuth(true);
      const sessionId = hash.split('session_id=')[1].split('&')[0];
      
      // Process the session
      axios.post(`${API}/auth/session`, { session_id: sessionId })
        .then(response => {
          setUser(response.data.user);
          // Clean URL
          window.history.replaceState(null, '', window.location.pathname);
        })
        .catch(err => {
          console.error('Session processing failed:', err);
        })
        .finally(() => {
          setProcessingAuth(false);
          setLoading(false);
        });
    } else {
      // Check existing session
      axios.get(`${API}/auth/me`)
        .then(response => {
          setUser(response.data);
        })
        .catch(() => {
          setUser(null);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, []);

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (loading || processingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/features" element={<Features />} />
          <Route 
            path="/tutor" 
            element={user ? <AITutor /> : <Navigate to="/" replace />} 
          />
          <Route 
            path="/dashboard" 
            element={user ? <Dashboard /> : <Navigate to="/" replace />} 
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthContext.Provider>
  );
}

export default App;