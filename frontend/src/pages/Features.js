import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../App';
import { Button } from '@/components/ui/button';
import { Sparkles, Brain, PuzzlePiece, TrendingUp, Zap } from 'lucide-react';

export default function Features() {
  const { user } = useContext(AuthContext);
  const redirectUrl = encodeURIComponent(`${window.location.origin}/tutor`);
  const loginUrl = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;

  const features = [
    {
      icon: <Brain className="h-12 w-12 text-blue-500" />,
      title: 'Personalized Learning Paths',
      description: 'AI adapts to your skill level and learning style, creating a unique educational journey just for you.',
      color: 'from-blue-400 to-blue-600'
    },
    {
      icon: <PuzzlePiece className="h-12 w-12 text-purple-500" />,
      title: 'AI-Generated Quizzes',
      description: 'Test yourself instantly with custom quizzes generated from any topic. Get immediate feedback and explanations.',
      color: 'from-purple-400 to-purple-600'
    },
    {
      icon: <Zap className="h-12 w-12 text-yellow-500" />,
      title: 'Smart Summaries',
      description: 'Transform lengthy content into concise, digestible lessons. Learn more in less time.',
      color: 'from-yellow-400 to-orange-500'
    },
    {
      icon: <TrendingUp className="h-12 w-12 text-green-500" />,
      title: 'Progress Insights',
      description: 'Visual charts and analytics track your improvement over time. Stay motivated with XP points and streaks.',
      color: 'from-green-400 to-emerald-600'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2" data-testid="features-logo">
              <Sparkles className="h-8 w-8 text-blue-500" />
              <span className="text-2xl font-bold text-gradient">LearnMate</span>
            </Link>
            <div className="flex items-center space-x-6">
              <Link to="/" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="features-nav-home">Home</Link>
              <Link to="/features" className="text-blue-500 font-semibold" data-testid="features-nav-features">Features</Link>
              {user ? (
                <>
                  <Link to="/tutor" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="features-nav-tutor">AI Tutor</Link>
                  <Link to="/dashboard" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="features-nav-dashboard">Dashboard</Link>
                </>
              ) : (
                <Button onClick={() => window.location.href = loginUrl} data-testid="features-login-button">
                  Get Started
                </Button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8" data-testid="features-hero">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl font-bold mb-6" data-testid="features-title">
            Powerful Features for
            <span className="block text-gradient">Smarter Learning</span>
          </h1>
          <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto" data-testid="features-subtitle">
            Discover how LearnMate transforms the way you learn with cutting-edge AI technology
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="pb-20 px-4 sm:px-6 lg:px-8" data-testid="features-grid">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="feature-card glass-card rounded-3xl p-8 hover:scale-[1.02] transition-all duration-300"
                data-testid={`feature-card-${index}`}
              >
                <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${feature.color} mb-6`}>
                  {feature.icon}
                </div>
                <h3 className="text-2xl font-bold mb-4" data-testid={`feature-title-${index}`}>{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed" data-testid={`feature-desc-${index}`}>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-500 to-purple-600" data-testid="features-cta">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6" data-testid="cta-title">Ready to Transform Your Learning?</h2>
          <p className="text-lg mb-8 opacity-90" data-testid="cta-subtitle">Join thousands of learners already using LearnMate</p>
          <Button 
            size="lg"
            onClick={() => window.location.href = user ? '/tutor' : loginUrl}
            className="bg-white text-blue-600 hover:bg-gray-100 px-8 py-6 text-lg rounded-full shadow-lg"
            data-testid="cta-button"
          >
            {user ? 'Start Learning Now' : 'Get Started Free'}
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 px-4" data-testid="features-footer">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Sparkles className="h-6 w-6" />
            <span className="text-xl font-bold">LearnMate</span>
          </div>
          <p className="text-gray-400 text-sm">Smarter Learning Starts Here</p>
        </div>
      </footer>
    </div>
  );
}