import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginPayload, RegisterPayload } from '../types/auth';
import {
  getToken,
  getStoredUser,
  loginApi,
  registerApi,
  getMeApi,
  deleteAccountApi,
  removeAuth,
} from '../api/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  deleteAccount: () => Promise<void>;
  refreshUser: () => Promise<void>;
  loginDemo: (email: string, fullName: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(getStoredUser());
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const currentToken = getToken();
      if (!currentToken) {
        setUser(null);
        setLoading(false);
        return;
      }
      const me = await getMeApi();
      setUser(me);
    } catch (err) {
      console.warn('Auth token expired or invalid:', err);
      removeAuth();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (payload: LoginPayload) => {
    const res = await loginApi(payload);
    setUser(res.user);
  };

  const register = async (payload: RegisterPayload) => {
    const res = await registerApi(payload);
    setUser(res.user);
  };

  const logout = () => {
    removeAuth();
    setUser(null);
  };

  const deleteAccount = async () => {
    await deleteAccountApi();
    setUser(null);
  };

  const loginDemo = async (email: string, fullName: string) => {
    const demoPassword = 'DemoPassword123!';
    try {
      // Try login first
      await login({ email, password: demoPassword });
    } catch {
      // If not registered yet, auto-register then login
      await register({ email, password: demoPassword, full_name: fullName });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
        deleteAccount,
        refreshUser,
        loginDemo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
