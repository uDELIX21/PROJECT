/** Client-side session context (who am I + permissions). */
"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { api, isAuthError, MeResponse } from "./api";

interface SessionState {
  me: MeResponse | null;
  loading: boolean;
  refresh: () => Promise<void>;
}

const SessionContext = createContext<SessionState>({
  me: null,
  loading: true,
  refresh: async () => {},
});

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      setMe(await api<MeResponse>("/auth/me"));
    } catch (e) {
      if (isAuthError(e)) setMe(null);
      else throw e;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <SessionContext.Provider value={{ me, loading, refresh }}>{children}</SessionContext.Provider>
  );
}

export function useSession() {
  return useContext(SessionContext);
}

export function hasPerm(me: MeResponse | null, code: string): boolean {
  return !!me && me.permissions.includes(code);
}
