'use client';

import { createContext, useContext, useEffect, useState } from 'react';

const BASE_URL = 'https://adonisagents-production.up.railway.app/api/v1';
const FALLBACK_USER_ID = 'df7c14fd-cde3-4025-be00-ca42f4d31741';

interface UserContextValue {
  userId: string;
  userName: string;
  isAdmin: boolean;
}

const UserContext = createContext<UserContextValue>({
  userId: FALLBACK_USER_ID,
  userName: '',
  isAdmin: false,
});

export function useUser() {
  return useContext(UserContext);
}

export default function UserProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserId] = useState(FALLBACK_USER_ID);
  const [userName, setUserName] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    fetch(`${BASE_URL}/me`, {
      headers: { 'X-User-Id': FALLBACK_USER_ID },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data?.id) setUserId(data.id);
        if (data?.name) setUserName(data.name);
        if (data?.is_admin !== undefined) setIsAdmin(data.is_admin);
      })
      .catch(() => {});
  }, []);

  return (
    <UserContext.Provider value={{ userId, userName, isAdmin }}>{children}</UserContext.Provider>
  );
}
