import React, { useContext, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Sparkles, Trophy, Target, Zap, BookOpen, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const { user } = useContext(AuthContext);
  const [progress, setProgress] = useState(null);
  const [quizResults, setQuizResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [progressRes, quizRes] = await Promise.all([
        axios.get(`${API}/progress`),
        axios.get(`${API}/quiz/results`)
      ]);
      setProgress(progressRes.data);
      setQuizResults(quizRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getMotivationalQuote = () => {
    const quotes = [
      'Great job! Keep up the amazing work!',
      'You\'re making excellent progress!',
      'Every lesson brings you closer to mastery!',
      'Your dedication is inspiring!',
      'Knowledge is power, and you\'re growing stronger!'
    ];
    return quotes[Math.floor(Math.random() * quotes.length)];
  };

  const getXPLevel = (xp) => {
    return Math.floor(xp / 100) + 1;
  };

  const getXPProgress = (xp) => {
    return (xp % 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2" data-testid="dashboard-logo">
              <Sparkles className="h-8 w-8 text-blue-500" />
              <span className="text-2xl font-bold text-gradient">LearnMate</span>
            </Link>
            <div className="flex items-center space-x-6">
              <Link to="/" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="dashboard-nav-home">Home</Link>
              <Link to="/features" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="dashboard-nav-features">Features</Link>
              <Link to="/tutor" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="dashboard-nav-tutor">AI Tutor</Link>
              <Link to="/dashboard" className="text-blue-500 font-semibold" data-testid="dashboard-nav-dashboard">Dashboard</Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto" data-testid="dashboard-main">
        {/* Header */}
        <div className="mb-8" data-testid="dashboard-header">
          <h1 className="text-4xl font-bold mb-2" data-testid="dashboard-title">
            Welcome back, <span className="text-gradient">{user?.name?.split(' ')[0]}</span>!
          </h1>
          <p className="text-gray-600" data-testid="dashboard-subtitle">{getMotivationalQuote()}</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8" data-testid="stats-cards">
          <Card className="glass-card hover:shadow-lg transition-shadow" data-testid="stat-card-xp">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-600" data-testid="stat-xp-label">Total XP</p>
                  <p className="text-3xl font-bold text-gradient" data-testid="stat-xp-value">{progress?.xp_points || 0}</p>
                </div>
                <div className="p-3 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full">
                  <Trophy className="h-8 w-8 text-white" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Level {getXPLevel(progress?.xp_points || 0)}</span>
                  <span className="text-gray-600">{getXPProgress(progress?.xp_points || 0)}/100 XP</span>
                </div>
                <Progress value={getXPProgress(progress?.xp_points || 0)} className="h-2" data-testid="xp-progress-bar" />
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card hover:shadow-lg transition-shadow" data-testid="stat-card-topics">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600" data-testid="stat-topics-label">Topics Learned</p>
                  <p className="text-3xl font-bold text-gradient" data-testid="stat-topics-value">{progress?.topics_learned?.length || 0}</p>
                </div>
                <div className="p-3 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full">
                  <BookOpen className="h-8 w-8 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card hover:shadow-lg transition-shadow" data-testid="stat-card-streak">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600" data-testid="stat-streak-label">Learning Streak</p>
                  <p className="text-3xl font-bold text-gradient" data-testid="stat-streak-value">{progress?.learning_streak || 0} days</p>
                </div>
                <div className="p-3 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full">
                  <Zap className="h-8 w-8 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Topics Learned */}
          <Card data-testid="topics-learned-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2" data-testid="topics-learned-title">
                <Target className="h-5 w-5 text-blue-500" />
                <span>Topics You've Mastered</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {progress?.topics_learned?.length > 0 ? (
                <div className="space-y-2" data-testid="topics-list">
                  {progress.topics_learned.map((topic, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg"
                      data-testid={`topic-item-${index}`}
                    >
                      <div className="p-2 bg-white rounded-full">
                        <BookOpen className="h-4 w-4 text-blue-500" />
                      </div>
                      <span className="font-medium" data-testid={`topic-name-${index}`}>{topic}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8" data-testid="topics-empty">
                  <p className="text-gray-500">Start learning to see your progress here!</p>
                  <Link to="/tutor">
                    <Button className="mt-4" data-testid="start-learning-button">Start Learning</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Quiz Results */}
          <Card data-testid="quiz-results-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2" data-testid="quiz-results-title">
                <TrendingUp className="h-5 w-5 text-green-500" />
                <span>Recent Quiz Results</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {quizResults.length > 0 ? (
                <div className="space-y-3" data-testid="quiz-list">
                  {quizResults.slice(0, 5).map((result, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg"
                      data-testid={`quiz-result-${index}`}
                    >
                      <div>
                        <p className="font-medium" data-testid={`quiz-topic-${index}`}>{result.topic}</p>
                        <p className="text-sm text-gray-600" data-testid={`quiz-date-${index}`}>
                          {new Date(result.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold text-gradient" data-testid={`quiz-score-${index}`}>
                          {result.score}/{result.total}
                        </p>
                        <p className="text-sm text-gray-600" data-testid={`quiz-percentage-${index}`}>
                          {Math.round((result.score / result.total) * 100)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8" data-testid="quiz-empty">
                  <p className="text-gray-500">No quiz results yet. Start testing your knowledge!</p>
                  <Link to="/tutor">
                    <Button className="mt-4" data-testid="take-quiz-button">Take a Quiz</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Continue Learning CTA */}
        <Card className="mt-8 bg-gradient-to-r from-blue-500 to-purple-600 text-white" data-testid="continue-learning-card">
          <CardContent className="p-8 text-center">
            <Sparkles className="h-12 w-12 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-2" data-testid="continue-learning-title">Keep the momentum going!</h3>
            <p className="text-lg opacity-90 mb-6" data-testid="continue-learning-subtitle">Your next learning adventure awaits</p>
            <Link to="/tutor">
              <Button 
                size="lg"
                className="bg-white text-blue-600 hover:bg-gray-100"
                data-testid="continue-learning-button"
              >
                Continue Learning
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}