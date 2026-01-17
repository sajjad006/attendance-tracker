import { createContext, useContext, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { semesterApi } from '../api/academic';
import { useAuth } from './AuthContext';

const SemesterContext = createContext(null);

export function SemesterProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [currentSemester, setCurrentSemester] = useState(null);

  const { data: semesters = [], isLoading, refetch } = useQuery({
    queryKey: ['semesters'],
    queryFn: semesterApi.getAll,
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (semesters.length > 0 && !currentSemester) {
      const current = semesters.find(s => s.is_current) || semesters[0];
      setCurrentSemester(current);
    }
  }, [semesters, currentSemester]);

  const selectSemester = (semester) => {
    setCurrentSemester(semester);
  };

  const value = {
    semesters,
    currentSemester,
    selectSemester,
    isLoading,
    refetch,
  };

  return (
    <SemesterContext.Provider value={value}>
      {children}
    </SemesterContext.Provider>
  );
}

export function useSemester() {
  const context = useContext(SemesterContext);
  if (!context) {
    throw new Error('useSemester must be used within a SemesterProvider');
  }
  return context;
}
