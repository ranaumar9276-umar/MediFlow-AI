import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { login as apiLogin, fetchMe } from "../api/endpoints";

interface AuthUser {
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("mediflow_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    fetchMe()
      .then((res) => {
        setUser({ email: res.data.email, full_name: res.data.full_name, role: res.data.role });
      })
      .catch(() => {
        localStorage.removeItem("mediflow_token");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await apiLogin(email, password);
    localStorage.setItem("mediflow_token", res.data.access_token);
    const authUser = { email: res.data.email, full_name: res.data.full_name, role: res.data.role };
    localStorage.setItem("mediflow_user", JSON.stringify(authUser));
    setUser(authUser);
  };

  const logout = () => {
    localStorage.removeItem("mediflow_token");
    localStorage.removeItem("mediflow_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
