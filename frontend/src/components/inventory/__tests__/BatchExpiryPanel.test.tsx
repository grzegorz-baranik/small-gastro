/**
 * BatchExpiryPanel Component Tests (GREEN Phase)
 *
 * Tests for the Batch Expiry Panel component that displays batch tracking
 * information with FIFO order and expiry alerts.
 *
 * Test Coverage:
 * - Renders expiry alerts summary when batches are expiring
 * - Displays no alerts message when no expiring batches
 * - Shows ingredient batch rows that can be expanded
 * - Displays batch details with FIFO order, expiry date, and quantity
 * - Highlights expired, critical, and warning batches
 * - Shows loading state while fetching data
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, userEvent } from '../../../test/test-utils'
import BatchExpiryPanel from '../BatchExpiryPanel'
import * as batchesApi from '../../../api/batches'
import type { ExpiryAlertsResponse, IngredientBatch } from '../../../types'

// Mock the batches API
vi.mock('../../../api/batches', () => ({
  getExpiryAlerts: vi.fn(),
  getBatchesForIngredient: vi.fn(),
}))

describe('BatchExpiryPanel', () => {
  // Mock data - expiry alerts
  const mockAlertsWithExpiring: ExpiryAlertsResponse = {
    alerts: [
      {
        batch_id: 1,
        batch_number: 'B-20260105-001',
        ingredient_id: 1,
        ingredient_name: 'Kebab meat',
        expiry_date: '2026-01-08',
        days_until_expiry: 2,
        remaining_quantity: 5.5,
        unit_label: 'kg',
        location: 'storage',
        alert_level: 'critical',
      },
      {
        batch_id: 2,
        batch_number: 'B-20260103-001',
        ingredient_id: 2,
        ingredient_name: 'Pita bread',
        expiry_date: '2026-01-10',
        days_until_expiry: 4,
        remaining_quantity: 20,
        unit_label: 'szt',
        location: 'storage',
        alert_level: 'warning',
      },
    ],
    expired_count: 0,
    critical_count: 1,
    warning_count: 1,
  }

  const mockAlertsEmpty: ExpiryAlertsResponse = {
    alerts: [],
    expired_count: 0,
    critical_count: 0,
    warning_count: 0,
  }

  const mockAlertsWithExpired: ExpiryAlertsResponse = {
    alerts: [
      {
        batch_id: 3,
        batch_number: 'B-20260101-001',
        ingredient_id: 1,
        ingredient_name: 'Kebab meat',
        expiry_date: '2026-01-04',
        days_until_expiry: -2,
        remaining_quantity: 2.0,
        unit_label: 'kg',
        location: 'storage',
        alert_level: 'expired',
      },
    ],
    expired_count: 1,
    critical_count: 0,
    warning_count: 0,
  }

  // Mock data - ingredient batches
  const mockBatchesForIngredient: IngredientBatch[] = [
    {
      id: 1,
      batch_number: 'B-20260103-001',
      ingredient_id: 1,
      ingredient_name: 'Kebab meat',
      unit_label: 'kg',
      delivery_item_id: 1,
      expiry_date: '2026-01-08',
      initial_quantity: 10.0,
      remaining_quantity: 5.5,
      location: 'storage',
      is_active: true,
      days_until_expiry: 2,
      is_expiring_soon: true,
      age_days: 3,
      notes: null,
      created_at: '2026-01-03T10:00:00Z',
    },
    {
      id: 2,
      batch_number: 'B-20260105-001',
      ingredient_id: 1,
      ingredient_name: 'Kebab meat',
      unit_label: 'kg',
      delivery_item_id: 2,
      expiry_date: '2026-01-15',
      initial_quantity: 8.0,
      remaining_quantity: 8.0,
      location: 'storage',
      is_active: true,
      days_until_expiry: 9,
      is_expiring_soon: false,
      age_days: 1,
      notes: 'Fresh batch',
      created_at: '2026-01-05T08:00:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ============================================
  // RENDERING TESTS
  // ============================================

  describe('Rendering', () => {
    it('shows loading spinner while fetching alerts', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<BatchExpiryPanel />)

      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('displays expiry alerts summary when batches are expiring', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        // Find the header specifically (h4 element)
        expect(screen.getByRole('heading', { level: 4 })).toBeInTheDocument()
      })

      // Should show critical and warning counts in the summary section
      const summarySection = screen.getByRole('heading', { level: 4 }).parentElement
      expect(summarySection).toHaveTextContent(/1/)
      expect(summarySection).toHaveTextContent(/<3/)
      expect(summarySection).toHaveTextContent(/<7/)
    })

    it('shows expired alert prominently when batches are expired', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpired)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText(/1.*Expired/i)).toBeInTheDocument()
      })
    })

    it('shows no batches message when alerts list is empty', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsEmpty)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText(/No.*batch/i)).toBeInTheDocument()
      })
    })
  })

  // ============================================
  // INGREDIENT ROW EXPANSION TESTS
  // ============================================

  describe('Ingredient Row Expansion', () => {
    it('displays ingredient names from alerts', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
        expect(screen.getByText('Pita bread')).toBeInTheDocument()
      })
    })

    it('expands ingredient row when clicked', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      // Click to expand
      const kebabRow = screen.getByRole('button', { name: /kebab meat/i })
      await user.click(kebabRow)

      // Should fetch batches for this ingredient
      await waitFor(() => {
        expect(batchesApi.getBatchesForIngredient).toHaveBeenCalledWith(1)
      })
    })

    it('shows batch details after expanding', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      // Expand the ingredient
      await user.click(screen.getByRole('button', { name: /kebab meat/i }))

      // Wait for batches to load and display
      await waitFor(() => {
        expect(screen.getByTestId('batch-row-1')).toBeInTheDocument()
        expect(screen.getByTestId('batch-row-2')).toBeInTheDocument()
      })
    })
  })

  // ============================================
  // BATCH DISPLAY TESTS
  // ============================================

  describe('Batch Display', () => {
    it('shows batch number for each batch', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /kebab meat/i }))

      await waitFor(() => {
        expect(screen.getByText('B-20260103-001')).toBeInTheDocument()
        expect(screen.getByText('B-20260105-001')).toBeInTheDocument()
      })
    })

    it('shows FIFO order badges (1, 2, 3...)', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /kebab meat/i }))

      await waitFor(() => {
        const fifoBadges = screen.getAllByTestId('fifo-badge')
        expect(fifoBadges).toHaveLength(2)
        expect(fifoBadges[0]).toHaveTextContent('1')
        expect(fifoBadges[1]).toHaveTextContent('2')
      })
    })

    it('displays remaining quantity for each batch', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /kebab meat/i }))

      await waitFor(() => {
        // Check for quantity display
        const quantityElements = screen.getAllByTestId('batch-quantity')
        expect(quantityElements.length).toBeGreaterThan(0)
      })
    })

    it('displays expiry date for batches with expiry', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /kebab meat/i }))

      await waitFor(() => {
        const expiryElements = screen.getAllByTestId('expiry-date')
        expect(expiryElements.length).toBeGreaterThan(0)
      })
    })

    it('shows batch age in days', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /kebab meat/i }))

      await waitFor(() => {
        const ageElements = screen.getAllByTestId('batch-age')
        expect(ageElements.length).toBeGreaterThan(0)
        expect(ageElements[0]).toHaveTextContent(/\d+d/)
      })
    })
  })

  // ============================================
  // EXPIRY STATUS HIGHLIGHTING TESTS
  // ============================================

  describe('Expiry Status Highlighting', () => {
    it('shows "Expired" badge for expired batches', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpired)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        // Should find multiple "Expired" texts - one in summary, one in badge
        const expiredElements = screen.getAllByText(/Expired/i)
        expect(expiredElements.length).toBeGreaterThanOrEqual(1)
      })
    })

    it('shows "Expiring soon" badge for critical/warning batches', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        // At least one "Expiring soon" badge should be visible
        const expiringSoonBadges = screen.getAllByText(/expiring.*soon/i)
        expect(expiringSoonBadges.length).toBeGreaterThan(0)
      })
    })
  })

  // ============================================
  // ACCESSIBILITY TESTS
  // ============================================

  describe('Accessibility', () => {
    it('has proper aria-expanded attribute on expandable rows', async () => {
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      const expandButton = screen.getByRole('button', { name: /kebab meat/i })
      expect(expandButton).toHaveAttribute('aria-expanded', 'false')
    })

    it('updates aria-expanded when row is expanded', async () => {
      const user = userEvent.setup()
      vi.mocked(batchesApi.getExpiryAlerts).mockResolvedValue(mockAlertsWithExpiring)
      vi.mocked(batchesApi.getBatchesForIngredient).mockResolvedValue(mockBatchesForIngredient)

      render(<BatchExpiryPanel />)

      await waitFor(() => {
        expect(screen.getByText('Kebab meat')).toBeInTheDocument()
      })

      const expandButton = screen.getByRole('button', { name: /kebab meat/i })
      await user.click(expandButton)

      expect(expandButton).toHaveAttribute('aria-expanded', 'true')
    })
  })
})
