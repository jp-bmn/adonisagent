'use client';

import { createContext, useContext, useEffect, useState } from 'react';

const BASE_URL = 'https://adonisagents-production.up.railway.app/api/v1';
const FALLBACK_USER_ID = 'df7c14fd-cde3-4025-be00-ca42f4d31741';

interface UserContextValue {
  userId: string;
}

const UserContext = createContext<UserContextValue>({ userId: FALLBACK_USER_ID });

export function useUser() {
  return useContext(UserContext);
}

export default function UserProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserId] = useState(FALLBACK_USER_ID);

  useEffect(() => {
    fetch(`${BASE_URL}/me`, {
      headers: { 'X-User-Id': FALLBACK_USER_ID },
    })
      .then((r) => r.json())
      .then((data) => { if (data?.id) setUserId(data.id); })
      .catch(() => {});
  }, []);

  return <UserContext.Provider value={{ userId }}>{children}</UserContext.Provider>;
}
