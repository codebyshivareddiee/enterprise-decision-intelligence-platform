import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, clearTokens, getAccessToken } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    const token = getAccessToken();
    if (token) {
      try {
        const currentUser = await api.getMe();
        if (currentUser) {
          setUser(currentUser);
        } else {
          clearTokens();
          setUser(null);
        }
      } catch (err) {
        console.error("Auth check failed", err);
        clearTokens();
        setUser(null);
      }
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    const loggedInUser = await api.login(email, password);
    if (loggedInUser) {
      setUser(loggedInUser);
      return true;
    }
    return false;
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.warn("Logout request failed, proceeding to clear tokens locally");
    } finally {
      clearTokens();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, checkAuth, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
