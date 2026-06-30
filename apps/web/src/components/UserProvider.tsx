'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { fetchMe } from '@/lib/api';

interface UserContextValue {
  userId: string;
  userName: string;
  isAdmin: boolean;
}

const UserContext = createContext<UserContextValue>({
  userId: '',
  userName: '',
  isAdmin: false,
});

export function useUser() {
  return useContext(UserContext);
}

export default function UserProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserId] = useState('');
  const [userName, setUserName] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    fetchMe()
      .then((data) => {
        if (data?.id) setUserId(data.id);
        if (data?.name) setUserName(data.name);
        if (data?.is_admin !== undefined) setIsAdmin(data.is_admin);
      })
      .catch((e) => {
        console.error('Failed to fetch user:', e);
      });
  }, []);

  return (
    <UserContext.Provider value={{ userId, userName, isAdmin }}>{children}</UserContext.Provider>
  );
}
