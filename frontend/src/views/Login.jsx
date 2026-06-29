import React, { useState } from 'react';
import { Mail, Lock, User, Eye, EyeOff, Building2, Shield, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

export default function Login({ onLoginSuccess }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Fields
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (isSignUp) {
      if (!firstName || !lastName || !email || !companyName || !password) {
        setError('All fields are required.');
        setLoading(false);
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        setLoading(false);
        return;
      }

      const regRes = await api.register(email, password, `${firstName} ${lastName}`, companyName);
      if (!regRes.success) {
        setError(regRes.message || 'Registration failed.');
        setLoading(false);
        return;
      }
      
      // Auto login on signup success
      const user = await api.login(email, password);
      onLoginSuccess(user);
    } else {
      if (!email || !password) {
        setError('Please enter your email and password.');
        setLoading(false);
        return;
      }
      const user = await api.login(email, password);
      if (user) {
        onLoginSuccess(user);
      } else {
        setError('Invalid email or password.');
      }
    }
    setLoading(false);
  };



  return (
    <div className="auth-page">
      {/* Left Sidebar Branding Panel */}
      <div className="auth-sidebar">
        <div className="auth-sidebar-header">
          <div className="auth-logo-icon">IQ</div>
          <div className="auth-logo-text">
            <h2>DecisiolQ</h2>
            <p>Enterprise Decision Intelligence</p>
          </div>
        </div>

        <div className="auth-hero-section">
          <h1>Smarter Decisions.<br />Stronger Outcomes.</h1>
          <p>DecisiolQ helps enterprises make confident, data-driven decisions using AI, trusted knowledge, and human expertise.</p>
          
          <div className="auth-features-list">
            <div className="auth-feature-item">
              <div className="auth-feature-icon-wrapper">
                <Shield size={18} />
              </div>
              <div className="auth-feature-text">
                <h3>AI-Powered Decisioning</h3>
                <p>Leverage advanced AI agents to analyze, reason, and recommend the best course of action.</p>
              </div>
            </div>

            <div className="auth-feature-item">
              <div className="auth-feature-icon-wrapper">
                <Building2 size={18} />
              </div>
              <div className="auth-feature-text">
                <h3>Trusted Knowledge</h3>
                <p>Ground decisions in your organization's documents, policies, and data.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="auth-sidebar-footer">
          <Shield size={14} />
          <span>Your data is encrypted and secure. We never share your information.</span>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="auth-form-container">
        <div className="auth-card">
          <h2>{isSignUp ? 'Create your account' : 'Welcome back'}</h2>
          <p className="auth-card-subtitle">
            {isSignUp ? 'Join DecisiolQ and start making better decisions.' : 'Sign in to your DecisiolQ account'}
          </p>



          {error && <div style={{ color: 'var(--danger)', backgroundColor: 'var(--danger-bg)', padding: '12px', border: '1px solid var(--danger-border)', borderRadius: '6px', marginBottom: '20px', fontSize: '13px', fontWeight: '500' }}>{error}</div>}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            {isSignUp && (
              <div className="auth-input-row">
                <div className="auth-input-group">
                  <label>First Name</label>
                  <div className="auth-input-wrapper">
                    <User size={16} className="auth-input-icon" />
                    <input type="text" placeholder="Enter your first name" value={firstName} onChange={e => setFirstName(e.target.value)} required />
                  </div>
                </div>
                <div className="auth-input-group">
                  <label>Last Name</label>
                  <div className="auth-input-wrapper">
                    <User size={16} className="auth-input-icon" />
                    <input type="text" placeholder="Enter your last name" value={lastName} onChange={e => setLastName(e.target.value)} required />
                  </div>
                </div>
              </div>
            )}

            <div className="auth-input-group">
              <label>Work Email</label>
              <div className="auth-input-wrapper">
                <Mail size={16} className="auth-input-icon" />
                <input type="email" placeholder="Enter your work email" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
            </div>

            {isSignUp && (
              <div className="auth-input-group">
                <label>Company Name</label>
                <div className="auth-input-wrapper">
                  <Building2 size={16} className="auth-input-icon" />
                  <input type="text" placeholder="Enter your company name" value={companyName} onChange={e => setCompanyName(e.target.value)} required />
                </div>
              </div>
            )}

            <div className="auth-input-group">
              <label>Password</label>
              <div className="auth-input-wrapper">
                <Lock size={16} className="auth-input-icon" />
                <input type={showPassword ? 'text' : 'password'} placeholder={isSignUp ? 'Create a strong password' : 'Enter your password'} value={password} onChange={e => setPassword(e.target.value)} required />
                <button type="button" className="auth-input-toggle-password" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {isSignUp && (
              <div className="auth-input-group">
                <label>Confirm Password</label>
                <div className="auth-input-wrapper">
                  <Lock size={16} className="auth-input-icon" />
                  <input type={showConfirmPassword ? 'text' : 'password'} placeholder="Confirm your password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
                  <button type="button" className="auth-input-toggle-password" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            )}

            {/* Remember Me / T&C */}
            <div className="auth-form-options">
              {isSignUp ? (
                <label className="auth-checkbox-label">
                  <input type="checkbox" required />
                  <span>I agree to the <a href="#terms" className="auth-forgot-link">Terms of Service</a> and <a href="#privacy" className="auth-forgot-link">Privacy Policy</a></span>
                </label>
              ) : (
                <>
                  <label className="auth-checkbox-label">
                    <input type="checkbox" />
                    <span>Remember me</span>
                  </label>
                  <a href="#forgot" className="auth-forgot-link">Forgot password?</a>
                </>
              )}
            </div>

            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? 'Please wait...' : (isSignUp ? 'Create Account' : 'Sign in')}
            </button>
          </form>

          {/* Card Footer toggle */}
          <div className="auth-card-footer">
            {isSignUp ? (
              <span>Already have an account? <a href="#signin" onClick={(e) => { e.preventDefault(); setIsSignUp(false); setError(''); }}>Log in</a></span>
            ) : (
              <span>New to DecisiolQ? <a href="#signup" onClick={(e) => { e.preventDefault(); setIsSignUp(true); setError(''); }}>Create an account</a></span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
