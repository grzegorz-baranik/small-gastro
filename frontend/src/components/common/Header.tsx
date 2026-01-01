import { useDailyRecord } from '../../context/DailyRecordContext'
import { formatDate } from '../../utils/formatters'
import { Clock, CheckCircle } from 'lucide-react'

export default function Header() {
  const { todayRecord, isDayOpen, isLoading } = useDailyRecord()

  const today = new Date().toISOString().split('T')[0]

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">Dzisiaj</p>
          <p className="text-lg font-semibold text-gray-900">{formatDate(today)}</p>
        </div>
        <div className="flex items-center gap-2">
          {isLoading ? (
            <div className="px-4 py-2 rounded-full bg-gray-100 text-gray-600 text-sm">
              Ladowanie...
            </div>
          ) : isDayOpen ? (
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-green-100 text-green-700 text-sm font-medium">
              <Clock className="w-4 h-4" />
              Dzien otwarty
            </div>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gray-100 text-gray-600 text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              {todayRecord ? 'Dzien zamkniety' : 'Dzien nie otwarty'}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
