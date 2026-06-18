import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface ProfileContextType {
  profile: string;
  setProfile: (name: string) => Promise<void>;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

export function useProfile() {
  const context = useContext(ProfileContext);
  if (!context) throw new Error('useProfile must be used within ProfileProvider');
  return context;
}

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfileState] = useState<string>('');

  useEffect(() => {
    fetch('/api/profile')
      .then((r) => r.json())
      .then((data) => setProfileState(data.profile ?? ''))
      .catch(() => {});
  }, []);

  const setProfile = async (name: string) => {
    const body = new URLSearchParams({ profile_name: name });
    const res = await fetch('/api/profile', { method: 'POST', body });
    if (res.ok) {
      const data = await res.json();
      setProfileState(data.profile ?? name);
    }
  };

  return (
    <ProfileContext.Provider value={{ profile, setProfile }}>
      {children}
    </ProfileContext.Provider>
  );
}
