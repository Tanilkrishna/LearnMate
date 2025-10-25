import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { Button } from '@/components/ui/button';
import { Sparkles, Menu, X, LogOut } from 'lucide-react';

export default function Home() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const redirectUrl = encodeURIComponent(`${window.location.origin}/tutor`);
  const loginUrl = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;

  const handleGetStarted = () => {
    if (user) {
      navigate('/tutor');
    } else {
      window.location.href = loginUrl;
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2" data-testid="home-logo">
              <Sparkles className="h-8 w-8 text-blue-500" />
              <span className="text-2xl font-bold text-gradient">LearnMate</span>
            </Link>

            {/* Desktop Menu */}
            <div className="hidden md:flex items-center space-x-8">
              <Link to="/" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="nav-home">Home</Link>
              <Link to="/features" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="nav-features">Features</Link>
              {user && (
                <>
                  <Link to="/tutor" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="nav-tutor">AI Tutor</Link>
                  <Link to="/dashboard" className="text-gray-700 hover:text-blue-500 transition-colors" data-testid="nav-dashboard">Dashboard</Link>
                </>
              )}
              {user ? (
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600" data-testid="user-name">{user.name}</span>
                  <Button onClick={handleLogout} variant="outline" size="sm" data-testid="logout-button">
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </Button>
                </div>
              ) : (
                <Button onClick={handleGetStarted} data-testid="nav-login-button">
                  Get Started
                </Button>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-button"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 bg-white" data-testid="mobile-menu">
            <div className="px-4 py-4 space-y-3">
              <Link to="/" className="block text-gray-700 hover:text-blue-500" data-testid="mobile-nav-home">Home</Link>
              <Link to="/features" className="block text-gray-700 hover:text-blue-500" data-testid="mobile-nav-features">Features</Link>
              {user && (
                <>
                  <Link to="/tutor" className="block text-gray-700 hover:text-blue-500" data-testid="mobile-nav-tutor">AI Tutor</Link>
                  <Link to="/dashboard" className="block text-gray-700 hover:text-blue-500" data-testid="mobile-nav-dashboard">Dashboard</Link>
                </>
              )}
              {user ? (
                <Button onClick={handleLogout} variant="outline" className="w-full" data-testid="mobile-logout-button">
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </Button>
              ) : (
                <Button onClick={handleGetStarted} className="w-full" data-testid="mobile-login-button">
                  Get Started
                </Button>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8" data-testid="hero-section">
        <div className="max-w-7xl mx-auto">
          <div className="text-center relative">
            {/* Floating Decorations */}
            <div className="absolute top-0 left-1/4 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-float"></div>
            <div className="absolute top-0 right-1/4 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-float-delayed"></div>
            
            <div className="relative z-10">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6" data-testid="hero-title">
                Learn Smarter with Your
                <span className="block text-gradient">AI Tutor</span>
              </h1>
              <p className="text-base sm:text-lg lg:text-lg text-gray-600 max-w-2xl mx-auto mb-10" data-testid="hero-subtitle">
                Personalized lessons, quizzes, and progress tracking powered by AI
              </p>
              <Button 
                size="lg" 
                onClick={handleGetStarted}
                className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-full shadow-lg hover:shadow-xl transition-all"
                data-testid="hero-cta-button"
              >
                Start Learning
                <Sparkles className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* Feature Preview Cards */}
          <div className="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="feature-preview-section">
            {[
              { icon: '🧠', title: 'AI Tutor Chat', desc: 'Interactive learning conversations' },
              { icon: '🧩', title: 'Quiz Generator', desc: 'Test your knowledge instantly' },
              { icon: '📈', title: 'Progress Dashboard', desc: 'Track your improvement' },
              { icon: '⚡', title: 'Smart Summarizer', desc: 'Quick lesson summaries' }
            ].map((feature, index) => (
              <div 
                key={index} 
                className="glass-card rounded-2xl p-6 text-center hover:shadow-lg transition-shadow"
                data-testid={`feature-preview-${index}`}
              >
                <div className="text-4xl mb-3">{feature.icon}</div>
                <h3 className="font-semibold text-lg mb-2" data-testid={`feature-preview-title-${index}`}>{feature.title}</h3>
                <p className="text-sm text-gray-600" data-testid={`feature-preview-desc-${index}`}>{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white" data-testid="why-choose-section">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-12" data-testid="why-choose-title">Why Choose LearnMate?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div data-testid="benefit-0">
              <div className="text-5xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold mb-3" data-testid="benefit-title-0">Personalized Learning</h3>
              <p className="text-gray-600" data-testid="benefit-desc-0">AI adapts to your learning style and pace</p>
            </div>
            <div data-testid="benefit-1">
              <div className="text-5xl mb-4">🚀</div>
              <h3 className="text-xl font-semibold mb-3" data-testid="benefit-title-1">Fast Results</h3>
              <p className="text-gray-600" data-testid="benefit-desc-1">Learn efficiently with focused lessons</p>
            </div>
            <div data-testid="benefit-2">
              <div className="text-5xl mb-4">💡</div>
              <h3 className="text-xl font-semibold mb-3" data-testid="benefit-title-2">Always Available</h3>
              <p className="text-gray-600" data-testid="benefit-desc-2">24/7 AI tutor ready to help</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 px-4" data-testid="footer">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Sparkles className="h-6 w-6" />
            <span className="text-xl font-bold">LearnMate</span>
          </div>
          <p className="text-gray-400 text-sm" data-testid="footer-slogan">Smarter Learning Starts Here</p>
          <p className="text-gray-500 text-xs mt-4" data-testid="footer-copyright">© 2025 LearnMate. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}