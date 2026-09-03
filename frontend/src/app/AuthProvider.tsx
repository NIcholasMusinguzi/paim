import { createContext, type ReactNode, useContext } from "react";

import { type Me, useMe } from "../api/hooks/useMe";

type AuthState = { me: Me | null | undefined; isLoading: boolean };

const AuthContext = createContext<AuthState>({ me: undefined, isLoading: true });

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, isError } = useMe();
  const me = isError ? null : data;
  return <AuthContext.Provider value={{ me, isLoading }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
