# Technical Specification: Day Closing Wizard

## Metadata

| Field | Value |
|-------|-------|
| **Author** | AI Assistant |
| **Created** | 2026-01-04 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Functional Specification** | [Link](./README.md) |

---

## 1. Architecture Overview

### 1.1 Component Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend                                   │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    CloseDayWizard.tsx                           ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐││
│  │  │ WizardStep  │ │ WizardStep  │ │ WizardStep  │ │ WizardStep  │││
│  │  │   Opening   │ │   Events    │ │   Closing   │ │   Confirm   │││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│  │  WizardStepper   │  │ useWizardState   │  │ useClosingCalcs    │ │
│  │   (UI)           │  │   (Hook)         │  │   (Hook)           │ │
│  └──────────────────┘  └──────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼ (React Query - Existing API)
┌─────────────────────────────────────────────────────────────────────┐
│                         Backend API                                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  GET /api/v1/daily-records/{id}/summary   (existing)            ││
│  │  POST /api/v1/daily-records/{id}/close    (existing)            ││
│  │  GET /api/v1/ingredients                  (existing)            ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Components to Modify
- `frontend/src/components/daily/CloseDayModal.tsx` - Replace with new wizard
- `frontend/src/pages/DailyOperationsPage.tsx` - Update import to use new component

### 1.3 New Components
- `WizardStepper.tsx` - Reusable horizontal stepper component
- `CloseDayWizard.tsx` - Main wizard container with 4 steps
- `WizardStepOpening.tsx` - Step 1: Opening inventory display
- `WizardStepEvents.tsx` - Step 2: Day events summary
- `WizardStepClosing.tsx` - Step 3: Closing quantity entry with live calcs
- `WizardStepConfirm.tsx` - Step 4: Confirmation and summary
- `useClosingCalculations.ts` - Hook for real-time usage/discrepancy calculations

---

## 2. API Endpoints

**No new endpoints required.** The wizard will use existing endpoints:

### 2.1 Get Day Summary (Existing)

```http
GET /api/v1/daily-records/{id}/summary
```

**Response (200):**
```json
{
  "id": 1,
  "date": "2026-01-04",
  "status": "OPEN",
  "opening_time": "2026-01-04T08:00:00",
  "closing_time": null,
  "events": {
    "deliveries_count": 3,
    "deliveries_total_pln": 450.00,
    "transfers_count": 1,
    "spoilage_count": 2
  },
  "usage_items": [
    {
      "ingredient_id": 1,
      "ingredient_name": "Mięso kebab",
      "unit_type": "weight",
      "opening_quantity": 10.5,
      "deliveries_quantity": 5.0,
      "transfers_quantity": 0,
      "spoilage_quantity": 0.5,
      "expected_closing": 15.0,
      "expected_usage": 0
    }
  ],
  "calculated_sales": [],
  "total_income_pln": 0,
  "total_delivery_cost_pln": 450.00,
  "notes": null
}
```

### 2.2 Close Day (Existing)

```http
POST /api/v1/daily-records/{id}/close
```

**Request:**
```json
{
  "closing_inventory": [
    { "ingredient_id": 1, "quantity": 12.0 },
    { "ingredient_id": 2, "quantity": 60 }
  ],
  "notes": "Optional notes"
}
```

**Response (200):**
```json
{
  "id": 1,
  "date": "2026-01-04",
  "status": "CLOSED",
  "closed_at": "2026-01-04T17:30:00",
  "total_income_pln": 554.00,
  "total_delivery_cost_pln": 450.00
}
```

### 2.3 Get Day Events (New - Optional Enhancement)

If detailed event data is needed beyond what summary provides:

```http
GET /api/v1/daily-records/{id}/events
```

**Response (200):**
```json
{
  "deliveries": [
    {
      "id": 1,
      "ingredient_id": 1,
      "ingredient_name": "Mięso kebab",
      "quantity": 5.0,
      "price_pln": 250.00,
      "recorded_at": "2026-01-04T10:30:00"
    }
  ],
  "transfers": [
    {
      "id": 1,
      "ingredient_id": 4,
      "ingredient_name": "Sos czosnkowy",
      "quantity": 1.0,
      "direction": "storage_to_shop",
      "recorded_at": "2026-01-04T11:00:00"
    }
  ],
  "spoilage": [
    {
      "id": 1,
      "ingredient_id": 1,
      "ingredient_name": "Mięso kebab",
      "quantity": 0.5,
      "reason": "expired",
      "recorded_at": "2026-01-04T09:00:00"
    }
  ]
}
```

**Note:** This endpoint may already exist or can be added if the summary doesn't include enough detail for Step 2.

---

## 3. Database Schema

**No database changes required.** All necessary data is already available through existing models and relationships.

### 3.1 Existing Tables Used
- `daily_records` - Day open/close status
- `inventory_snapshots` - Opening/closing quantities
- `deliveries` - Delivery records
- `storage_transfers` - Transfer records
- `spoilage` - Spoilage records
- `calculated_sales` - Derived sales (populated on close)

---

## 4. Frontend Components

### 4.1 File Structure

```
frontend/src/
├── components/
│   ├── common/
│   │   └── WizardStepper.tsx          # NEW: Reusable stepper component
│   └── daily/
│       ├── CloseDayModal.tsx          # DEPRECATED: Keep for reference
│       ├── CloseDayWizard.tsx         # NEW: Main wizard container
│       ├── wizard/                     # NEW: Wizard step components
│       │   ├── WizardStepOpening.tsx
│       │   ├── WizardStepEvents.tsx
│       │   ├── WizardStepClosing.tsx
│       │   └── WizardStepConfirm.tsx
│       └── ...
├── hooks/
│   └── useClosingCalculations.ts      # NEW: Real-time calculation hook
└── types/
    └── wizard.ts                       # NEW: Wizard-specific types
```

### 4.2 TypeScript Interfaces

```typescript
// types/wizard.ts

export interface WizardStep {
  id: number;
  title: string;
  description?: string;
  status: 'pending' | 'current' | 'completed';
}

export interface ClosingInventoryEntry {
  ingredientId: number;
  value: string;  // String for controlled input
  numericValue: number | null;  // Parsed number
  isValid: boolean;
  error?: string;
}

export interface CalculatedRow {
  ingredientId: number;
  ingredientName: string;
  unitType: 'weight' | 'count';
  opening: number;
  deliveries: number;
  transfers: number;
  spoilage: number;
  expected: number;
  closing: number | null;
  usage: number | null;
  discrepancyPercent: number | null;
  discrepancyLevel: 'ok' | 'warning' | 'critical' | null;
}

export interface WizardState {
  currentStep: number;
  closingInventory: Record<number, ClosingInventoryEntry>;
  notes: string;
  calculations: CalculatedRow[];
  alerts: DiscrepancyAlert[];
  isValid: boolean;
}
```

### 4.3 WizardStepper Component

```typescript
// components/common/WizardStepper.tsx

interface WizardStepperProps {
  steps: WizardStep[];
  currentStep: number;
  onStepClick: (stepIndex: number) => void;
}

export default function WizardStepper({
  steps,
  currentStep,
  onStepClick
}: WizardStepperProps) {
  return (
    <nav className="flex items-center justify-center">
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          {/* Step circle */}
          <button
            onClick={() => step.status === 'completed' && onStepClick(index)}
            disabled={step.status === 'pending'}
            className={cn(
              'flex items-center justify-center w-10 h-10 rounded-full border-2',
              step.status === 'completed' && 'bg-primary-600 border-primary-600 text-white cursor-pointer',
              step.status === 'current' && 'border-primary-600 text-primary-600',
              step.status === 'pending' && 'border-gray-300 text-gray-400 cursor-not-allowed'
            )}
          >
            {step.status === 'completed' ? (
              <Check className="w-5 h-5" />
            ) : (
              step.id
            )}
          </button>

          {/* Step title below */}
          <span className="absolute mt-12 text-xs font-medium">
            {step.title}
          </span>

          {/* Connector line */}
          {index < steps.length - 1 && (
            <div className={cn(
              'w-16 h-0.5 mx-2',
              steps[index + 1].status !== 'pending'
                ? 'bg-primary-600'
                : 'bg-gray-300'
            )} />
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}
```

### 4.4 useClosingCalculations Hook

```typescript
// hooks/useClosingCalculations.ts

import { useMemo } from 'react';
import type { UsageItem, DiscrepancyAlert } from '../types';

interface UseClosingCalculationsProps {
  usageItems: UsageItem[];
  closingInventory: Record<number, string>;
}

interface CalculationResult {
  rows: CalculatedRow[];
  alerts: DiscrepancyAlert[];
  isValid: boolean;
}

export function useClosingCalculations({
  usageItems,
  closingInventory
}: UseClosingCalculationsProps): CalculationResult {

  return useMemo(() => {
    const rows: CalculatedRow[] = [];
    const alerts: DiscrepancyAlert[] = [];
    let isValid = true;

    for (const item of usageItems) {
      const closingValue = closingInventory[item.ingredient_id];
      const closing = closingValue ? parseFloat(closingValue) : null;

      let usage: number | null = null;
      let discrepancyPercent: number | null = null;
      let discrepancyLevel: 'ok' | 'warning' | 'critical' | null = null;

      if (closing !== null && !isNaN(closing)) {
        // Calculate usage
        usage = item.expected_closing - closing;

        // Calculate discrepancy (if there's expected usage to compare against)
        if (item.expected_usage && item.expected_usage > 0) {
          const diff = Math.abs(usage - item.expected_usage);
          discrepancyPercent = (diff / item.expected_usage) * 100;

          if (discrepancyPercent <= 5) {
            discrepancyLevel = 'ok';
          } else if (discrepancyPercent <= 10) {
            discrepancyLevel = 'warning';
            alerts.push({
              ingredient_id: item.ingredient_id,
              ingredient_name: item.ingredient_name,
              discrepancy_percent: discrepancyPercent,
              level: 'warning',
              message: `${item.ingredient_name}: ${discrepancyPercent.toFixed(1)}% różnicy`
            });
          } else {
            discrepancyLevel = 'critical';
            alerts.push({
              ingredient_id: item.ingredient_id,
              ingredient_name: item.ingredient_name,
              discrepancy_percent: discrepancyPercent,
              level: 'critical',
              message: `${item.ingredient_name}: ${discrepancyPercent.toFixed(1)}% różnicy`
            });
          }
        }
      } else if (closingValue === '' || closingValue === undefined) {
        isValid = false;
      }

      rows.push({
        ingredientId: item.ingredient_id,
        ingredientName: item.ingredient_name,
        unitType: item.unit_type as 'weight' | 'count',
        opening: item.opening_quantity,
        deliveries: item.deliveries_quantity,
        transfers: item.transfers_quantity,
        spoilage: item.spoilage_quantity,
        expected: item.expected_closing,
        closing,
        usage,
        discrepancyPercent,
        discrepancyLevel
      });
    }

    return { rows, alerts, isValid };
  }, [usageItems, closingInventory]);
}
```

### 4.5 CloseDayWizard Main Component

```typescript
// components/daily/CloseDayWizard.tsx

interface CloseDayWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  dailyRecord: DailyRecord;
}

const STEPS: WizardStep[] = [
  { id: 1, title: 'Otwarcie', status: 'current' },
  { id: 2, title: 'Zdarzenia', status: 'pending' },
  { id: 3, title: 'Zamknięcie', status: 'pending' },
  { id: 4, title: 'Potwierdź', status: 'pending' },
];

export default function CloseDayWizard({
  isOpen,
  onClose,
  onSuccess,
  dailyRecord
}: CloseDayWizardProps) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [closingInventory, setClosingInventory] = useState<Record<number, string>>({});
  const [notes, setNotes] = useState('');

  // Fetch data
  const { data: daySummary, isLoading } = useQuery({
    queryKey: ['daySummary', dailyRecord.id],
    queryFn: () => getDaySummary(dailyRecord.id),
    enabled: isOpen,
  });

  // Real-time calculations
  const { rows, alerts, isValid } = useClosingCalculations({
    usageItems: daySummary?.usage_items || [],
    closingInventory
  });

  // Close mutation
  const closeMutation = useMutation({
    mutationFn: (data: CloseRequest) => closeDay(dailyRecord.id, data),
    onSuccess: () => {
      onSuccess();
      onClose();
    }
  });

  // Step navigation
  const canProceed = useMemo(() => {
    if (currentStep === 2) return isValid;  // Step 3 requires valid inputs
    return true;
  }, [currentStep, isValid]);

  const handleNext = () => {
    if (canProceed && currentStep < 3) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleClose = () => {
    closeMutation.mutate({
      closing_inventory: rows.map(r => ({
        ingredient_id: r.ingredientId,
        quantity: r.closing!
      })),
      notes: notes || undefined
    });
  };

  // Update step statuses
  const stepsWithStatus = STEPS.map((step, index) => ({
    ...step,
    status: index < currentStep ? 'completed' :
            index === currentStep ? 'current' : 'pending'
  }));

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t('closeDayModal.title', { date: formatDate(dailyRecord.date) })}
      size="3xl"
    >
      {/* Stepper */}
      <div className="mb-6 pt-4">
        <WizardStepper
          steps={stepsWithStatus}
          currentStep={currentStep}
          onStepClick={setCurrentStep}
        />
      </div>

      {/* Step content */}
      <div className="min-h-[400px] max-h-[60vh] overflow-y-auto">
        {currentStep === 0 && (
          <WizardStepOpening daySummary={daySummary} />
        )}
        {currentStep === 1 && (
          <WizardStepEvents daySummary={daySummary} />
        )}
        {currentStep === 2 && (
          <WizardStepClosing
            rows={rows}
            closingInventory={closingInventory}
            onChange={setClosingInventory}
            alerts={alerts}
          />
        )}
        {currentStep === 3 && (
          <WizardStepConfirm
            daySummary={daySummary}
            rows={rows}
            alerts={alerts}
            notes={notes}
            onNotesChange={setNotes}
          />
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t mt-4">
        <button onClick={onClose} className="btn btn-secondary">
          {t('common.cancel')}
        </button>
        <div className="flex gap-2">
          {currentStep > 0 && (
            <button onClick={handleBack} className="btn btn-secondary">
              ← {t('wizard.back')}
            </button>
          )}
          {currentStep < 3 ? (
            <button
              onClick={handleNext}
              disabled={!canProceed}
              className="btn btn-primary"
            >
              {t('wizard.next')} →
            </button>
          ) : (
            <button
              onClick={handleClose}
              disabled={closeMutation.isPending}
              className="btn btn-danger"
            >
              {closeMutation.isPending ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>{t('dailyOperations.closeDay')} ⏹️</>
              )}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
```

### 4.6 WizardStepClosing - Real-time Calculations

```typescript
// components/daily/wizard/WizardStepClosing.tsx

interface WizardStepClosingProps {
  rows: CalculatedRow[];
  closingInventory: Record<number, string>;
  onChange: (inventory: Record<number, string>) => void;
  alerts: DiscrepancyAlert[];
}

export default function WizardStepClosing({
  rows,
  closingInventory,
  onChange,
  alerts
}: WizardStepClosingProps) {
  const { t } = useTranslation();

  const handleInputChange = (ingredientId: number, value: string) => {
    onChange({
      ...closingInventory,
      [ingredientId]: value
    });
  };

  const handleCopyExpected = () => {
    const newInventory: Record<number, string> = {};
    rows.forEach(row => {
      newInventory[row.ingredientId] = row.expected.toString();
    });
    onChange(newInventory);
  };

  const getStatusBadge = (row: CalculatedRow) => {
    if (!row.discrepancyLevel) return null;

    const colors = {
      ok: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-red-100 text-red-800'
    };

    const icons = {
      ok: <CheckCircle className="w-4 h-4" />,
      warning: <AlertTriangle className="w-4 h-4" />,
      critical: <AlertCircle className="w-4 h-4" />
    };

    return (
      <div className={`flex items-center gap-1 px-2 py-1 rounded ${colors[row.discrepancyLevel]}`}>
        {icons[row.discrepancyLevel]}
        <span className="text-xs font-medium">
          {row.discrepancyPercent?.toFixed(0)}%
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Formula explanation */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          <strong>Formuła:</strong> Otwarcie + Dostawy + Transfery - Straty - Zamknięcie = Zużycie
        </p>
        <button onClick={handleCopyExpected} className="btn btn-sm btn-secondary">
          {t('closeDayModal.copyExpected')}
        </button>
      </div>

      {/* Table with live calculations */}
      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left">Składnik</th>
              <th className="px-3 py-2 text-right">Otw.</th>
              <th className="px-3 py-2 text-right text-green-600">+Dost.</th>
              <th className="px-3 py-2 text-right text-blue-600">+Trans.</th>
              <th className="px-3 py-2 text-right text-red-600">-Straty</th>
              <th className="px-3 py-2 text-right font-bold">=Oczek.</th>
              <th className="px-3 py-2 text-right">Zamkn.</th>
              <th className="px-3 py-2 text-right">Zużycie</th>
              <th className="px-3 py-2 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map(row => (
              <tr key={row.ingredientId}>
                <td className="px-3 py-2">
                  <div className="font-medium">{row.ingredientName}</div>
                  <div className="text-xs text-gray-500">
                    {row.unitType === 'weight' ? 'kg' : 'szt'}
                  </div>
                </td>
                <td className="px-3 py-2 text-right text-gray-600">
                  {formatQuantity(row.opening, row.unitType)}
                </td>
                <td className="px-3 py-2 text-right text-green-600">
                  {row.deliveries > 0 ? `+${formatQuantity(row.deliveries, row.unitType)}` : '-'}
                </td>
                <td className="px-3 py-2 text-right text-blue-600">
                  {row.transfers > 0 ? `+${formatQuantity(row.transfers, row.unitType)}` : '-'}
                </td>
                <td className="px-3 py-2 text-right text-red-600">
                  {row.spoilage > 0 ? `-${formatQuantity(row.spoilage, row.unitType)}` : '-'}
                </td>
                <td className="px-3 py-2 text-right font-bold">
                  {formatQuantity(row.expected, row.unitType)}
                </td>
                <td className="px-3 py-2">
                  <input
                    type="number"
                    min="0"
                    step={row.unitType === 'weight' ? '0.01' : '1'}
                    value={closingInventory[row.ingredientId] || ''}
                    onChange={e => handleInputChange(row.ingredientId, e.target.value)}
                    className="input w-20 text-right text-sm"
                    placeholder="0"
                  />
                </td>
                <td className="px-3 py-2 text-right font-medium">
                  {row.usage !== null ? formatQuantity(row.usage, row.unitType) : '-'}
                </td>
                <td className="px-3 py-2">
                  <div className="flex justify-center">
                    {getStatusBadge(row)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Rozbieżności</h4>
          {alerts.map(alert => (
            <div
              key={alert.ingredient_id}
              className={cn(
                'flex items-center gap-2 p-3 rounded-lg',
                alert.level === 'warning' && 'bg-yellow-50 text-yellow-800',
                alert.level === 'critical' && 'bg-red-50 text-red-800'
              )}
            >
              {alert.level === 'warning' ? (
                <AlertTriangle className="w-4 h-4" />
              ) : (
                <AlertCircle className="w-4 h-4" />
              )}
              <span className="text-sm font-medium">{alert.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 5. i18n Translations

### 5.1 Polish Translations (pl.json)

```json
{
  "wizard": {
    "back": "Wstecz",
    "next": "Dalej",
    "step1Title": "Otwarcie",
    "step2Title": "Zdarzenia",
    "step3Title": "Zamknięcie",
    "step4Title": "Potwierdź",
    "openingInventory": "Stan otwarcia",
    "dayEvents": "Zdarzenia dnia",
    "closingInventory": "Wprowadź ilości zamknięcia",
    "confirmation": "Potwierdzenie zamknięcia dnia",
    "formula": "Formuła: Otwarcie + Dostawy + Transfery - Straty - Zamknięcie = Zużycie",
    "noEventsToday": "Brak zdarzeń w ciągu dnia",
    "discrepancies": "Rozbieżności",
    "warnings": "Ostrzeżenia",
    "calculatedSales": "Wyliczona sprzedaż",
    "financialSummary": "Podsumowanie finansowe",
    "revenue": "Przychód",
    "deliveryCosts": "Koszty dostaw",
    "grossProfit": "Zysk brutto",
    "openedAt": "Dzień otwarty",
    "infoOpeningValues": "Te wartości zostały wprowadzone przy otwieraniu dnia.",
    "continueToEvents": "Przejdź dalej, aby zobaczyć zdarzenia w ciągu dnia.",
    "impactSummary": "Podsumowanie wpływu na stan"
  }
}
```

### 5.2 English Translations (en.json)

```json
{
  "wizard": {
    "back": "Back",
    "next": "Next",
    "step1Title": "Opening",
    "step2Title": "Events",
    "step3Title": "Closing",
    "step4Title": "Confirm",
    "openingInventory": "Opening Inventory",
    "dayEvents": "Day Events",
    "closingInventory": "Enter Closing Quantities",
    "confirmation": "Confirm Day Close",
    "formula": "Formula: Opening + Deliveries + Transfers - Spoilage - Closing = Usage",
    "noEventsToday": "No events during the day",
    "discrepancies": "Discrepancies",
    "warnings": "Warnings",
    "calculatedSales": "Calculated Sales",
    "financialSummary": "Financial Summary",
    "revenue": "Revenue",
    "deliveryCosts": "Delivery Costs",
    "grossProfit": "Gross Profit",
    "openedAt": "Day opened",
    "infoOpeningValues": "These values were entered when opening the day.",
    "continueToEvents": "Continue to see events during the day.",
    "impactSummary": "Impact Summary"
  }
}
```

---

## 6. Security

### 6.1 Data Validation
- All numeric inputs are validated client-side before submission
- Backend validates closing inventory quantities (non-negative, correct type)
- Only the owner of the daily record can close it (existing authorization)

### 6.2 Potential Threats
| Threat | Mitigation |
|--------|------------|
| Invalid numeric input | Client-side and server-side validation |
| Submitting for wrong day | Backend validates record belongs to user |
| XSS in notes field | React's default escaping + backend sanitization |

---

## 7. Performance

### 7.1 Real-time Calculations
- Calculations run in `useMemo` to avoid unnecessary recalculations
- Only recalculate when `closingInventory` or `usageItems` change
- Target: <50ms calculation time for 20 ingredients

### 7.2 Data Fetching
- Use React Query for caching day summary data
- Single API call on modal open (existing pattern)
- No additional API calls for calculations (all client-side)

### 7.3 Bundle Size
- Wizard components are lazy-loaded with modal
- Estimated additional bundle size: ~5KB gzipped

---

## 8. Testing

### 8.1 Unit Tests
- [ ] `useClosingCalculations` - calculation accuracy
- [ ] `useClosingCalculations` - edge cases (zero values, negatives)
- [ ] `WizardStepper` - step status rendering
- [ ] `WizardStepper` - navigation callbacks

### 8.2 Integration Tests
- [ ] Full wizard flow from open to close
- [ ] Step validation prevents invalid navigation
- [ ] Real-time calculations update correctly
- [ ] Form submission sends correct data

### 8.3 E2E Tests
- [ ] Complete day closing flow with real data
- [ ] Verify discrepancy alerts appear
- [ ] Verify calculated sales display

---

## 9. Deployment Plan

### 9.1 Migration Steps
1. Add new wizard components alongside existing `CloseDayModal`
2. Add feature flag to switch between old/new modal
3. Test thoroughly in staging
4. Enable for all users
5. Remove old `CloseDayModal` after confirmation period

### 9.2 Rollback
If issues occur, revert feature flag to use old `CloseDayModal`.

---

## 10. Future Enhancements

- [ ] Historical comparison (yesterday's closing vs today's opening)
- [ ] Save draft functionality for partial entry
- [ ] Print/export day summary as PDF
- [ ] Mobile-optimized layout

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-04 | AI Assistant | Initial version |
