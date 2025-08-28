import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '@/services/api';

// Define the shape of the user object and auth state
interface User {
  id: number;
  username: string;
  email: string;

  full_name: string | null;
  role: 'student' | 'admin';
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (token: string, user: User) => void;
  logout: () => void;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create the provider component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    token: null,
    isLoading: true, // Start with loading state
  });

  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('accessToken');
      console.log('AuthContext init - token exists:', !!token);
      if (token) {
        console.log('AuthContext init - token length:', token.length);
        try {
          // No need to call /users/me, we can store user object from login
          const userString = localStorage.getItem('user');
          if(userString) {
            const user = JSON.parse(userString);
            console.log('AuthContext init - user loaded:', user.username, user.role);
            setAuthState({
              isAuthenticated: true,
              user,
              token,
              isLoading: false,
            });
          } else {
             // Fallback if user is not in local storage for some reason
             console.warn('AuthContext init - no user in localStorage, logging out');
             logout();
          }
        } catch (error) {
          console.error("Failed to initialize auth:", error);
          logout(); // If token is invalid, logout
        }
      } else {
        console.log('AuthContext init - no token found');
        setAuthState(prevState => ({ ...prevState, isLoading: false }));
      }
    };
    initializeAuth();
  }, []);

  const login = (token: string, user: User) => {
    console.log('AuthContext login - setting token, length:', token.length);
    localStorage.setItem('accessToken', token);
    localStorage.setItem('user', JSON.stringify(user));
    console.log('AuthContext login - token saved to localStorage');
    setAuthState({
      isAuthenticated: true,
      user,
      token,
      isLoading: false,
    });
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    setAuthState({
      isAuthenticated: false,
      user: null,
      token: null,
      isLoading: false,
    });
  };

  return (
    <AuthContext.Provider value={{ ...authState, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Create a custom hook for easy access to the context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 