import { createContext, useContext, ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getTodayRecord, getOpenRecord } from '../api/dailyOperations'
import type { DailyRecord } from '../types'

interface DailyRecordContextType {
  todayRecord: DailyRecord | null
  openRecord: DailyRecord | null  // Currently open day (any date)
  isLoading: boolean
  isDayOpen: boolean
  refetch: () => void
}

const DailyRecordContext = createContext<DailyRecordContextType | null>(null)

export function DailyRecordProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const { data: todayRecord, isLoading: todayLoading } = useQuery({
    queryKey: ['todayRecord'],
    queryFn: getTodayRecord,
    staleTime: 60000, // Consider fresh for 1 minute
  })

  const { data: openRecord, isLoading: openLoading } = useQuery({
    queryKey: ['openRecord'],
    queryFn: getOpenRecord,
    staleTime: 60000, // Consider fresh for 1 minute
  })

  const isLoading = todayLoading || openLoading
  const isDayOpen = openRecord?.status === 'open'

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: ['todayRecord'] })
    queryClient.invalidateQueries({ queryKey: ['openRecord'] })
  }

  return (
    <DailyRecordContext.Provider value={{
      todayRecord: todayRecord ?? null,
      openRecord: openRecord ?? null,
      isLoading,
      isDayOpen,
      refetch
    }}>
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
