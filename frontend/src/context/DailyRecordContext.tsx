import { createContext, useContext, ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getTodayRecord } from '../api/dailyOperations'
import type { DailyRecord } from '../types'

interface DailyRecordContextType {
  todayRecord: DailyRecord | null
  isLoading: boolean
  isDayOpen: boolean
  refetch: () => void
}

const DailyRecordContext = createContext<DailyRecordContextType | null>(null)

export function DailyRecordProvider({ children }: { children: ReactNode }) {
  const { data: todayRecord, isLoading, refetch } = useQuery({
    queryKey: ['todayRecord'],
    queryFn: getTodayRecord,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const isDayOpen = todayRecord?.status === 'open'

  return (
    <DailyRecordContext.Provider value={{ todayRecord: todayRecord ?? null, isLoading, isDayOpen, refetch }}>
      {children}
    </DailyRecordContext.Provider>
  )
}

export function useDailyRecord() {
  const context = useContext(DailyRecordContext)
  if (!context) {
    throw new Error('useDailyRecord must be used within a DailyRecordProvider')
  }
  return context
}
