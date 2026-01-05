import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, userEvent } from '../../../test/test-utils'
import PositionsSection from '../PositionsSection'
import * as positionsApi from '../../../api/positions'
import type { Position } from '../../../types'

// Mock the positions API
vi.mock('../../../api/positions', () => ({
  getPositions: vi.fn(),
  createPosition: vi.fn(),
  updatePosition: vi.fn(),
  deletePosition: vi.fn(),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Plus: () => <svg data-testid="plus-icon" />,
  Pencil: () => <svg data-testid="pencil-icon" />,
  Trash2: () => <svg data-testid="trash-icon" />,
  Briefcase: () => <svg data-testid="briefcase-icon" />,
  X: () => <svg data-testid="x-icon" />,
}))

describe('PositionsSection', () => {
  const mockPositions: Position[] = [
    {
      id: 1,
      name: 'Cook',
      hourly_rate: 25.0,
      employee_count: 2,
      created_at: '2026-01-01T10:00:00Z',
    },
    {
      id: 2,
      name: 'Cashier',
      hourly_rate: 22.0,
      employee_count: 1,
      created_at: '2026-01-02T10:00:00Z',
    },
    {
      id: 3,
      name: 'Helper',
      hourly_rate: 18.5,
      employee_count: 0,
      created_at: '2026-01-03T10:00:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(positionsApi.getPositions).mockResolvedValue({
      items: mockPositions,
      total: mockPositions.length,
    })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  // ============================================
  // RENDERING TESTS
  // ============================================

  describe('Rendering', () => {
    it('renders loading spinner while fetching positions', async () => {
      // Keep the promise pending to show loading state
      vi.mocked(positionsApi.getPositions).mockImplementation(
        () => new Promise(() => {})
      )

      render(<PositionsSection />)

      // Loading spinner should be visible (div with animate-spin class)
      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('renders positions list with hourly rates', async () => {
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      // Check position names are displayed
      expect(screen.getByText('Cook')).toBeInTheDocument()
      expect(screen.getByText('Cashier')).toBeInTheDocument()
      expect(screen.getByText('Helper')).toBeInTheDocument()

      // Check hourly rates are formatted correctly (currency format varies by locale)
      expect(screen.getByText(/25.*\/h/i)).toBeInTheDocument()
      expect(screen.getByText(/22.*\/h/i)).toBeInTheDocument()
      expect(screen.getByText(/18.*\/h/i)).toBeInTheDocument()
    })

    it('renders employee counts for each position', async () => {
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      // Employee counts should be displayed
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument()
    })

    it('renders empty state when no positions exist', async () => {
      vi.mocked(positionsApi.getPositions).mockResolvedValue({
        items: [],
        total: 0,
      })

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText(/No positions/i)).toBeInTheDocument()
      })
    })

    it('renders add position button', async () => {
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Position/i })).toBeInTheDocument()
      })
    })
  })

  // ============================================
  // CREATE POSITION TESTS (BDD: @positions @happy-path @smoke)
  // ============================================

  describe('Create Position', () => {
    it('opens add position modal when clicking add button', async () => {
      const user = userEvent.setup()
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Position/i }))

      // Modal should be open with title
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /Add Position/i })).toBeInTheDocument()
      })
    })

    it('creates a new position with name and hourly rate', async () => {
      const user = userEvent.setup()
      const newPosition: Position = {
        id: 4,
        name: 'Manager',
        hourly_rate: 35.0,
        employee_count: 0,
        created_at: '2026-01-04T10:00:00Z',
      }

      vi.mocked(positionsApi.createPosition).mockResolvedValue(newPosition)

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      // Open modal
      await user.click(screen.getByRole('button', { name: /Add Position/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Fill form
      const nameInput = screen.getByPlaceholderText(/Cook, Cashier/i)
      const rateInput = screen.getByPlaceholderText('25.00')

      await user.type(nameInput, 'Manager')
      await user.type(rateInput, '35.00')

      // Submit
      await user.click(screen.getByRole('button', { name: /Save/i }))

      // Verify API was called
      await waitFor(() => {
        expect(positionsApi.createPosition).toHaveBeenCalledWith({
          name: 'Manager',
          hourly_rate: 35.0,
        })
      })
    })

    it('shows error message when creating position with duplicate name', async () => {
      const user = userEvent.setup()

      vi.mocked(positionsApi.createPosition).mockRejectedValue({
        response: {
          data: {
            detail: 'Position with this name already exists',
          },
        },
      })

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Position/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      const nameInput = screen.getByPlaceholderText(/Cook, Cashier/i)
      const rateInput = screen.getByPlaceholderText('25.00')

      await user.type(nameInput, 'Cook')
      await user.type(rateInput, '30.00')

      await user.click(screen.getByRole('button', { name: /Save/i }))

      // Alert should be called with error message
      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Position with this name already exists')
      })
    })

    it('disables save button while loading', async () => {
      const user = userEvent.setup()

      // Create a promise that never resolves to keep loading state
      vi.mocked(positionsApi.createPosition).mockImplementation(
        () => new Promise(() => {})
      )

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Position/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      const nameInput = screen.getByPlaceholderText(/Cook, Cashier/i)
      const rateInput = screen.getByPlaceholderText('25.00')

      await user.type(nameInput, 'Manager')
      await user.type(rateInput, '35.00')

      // Submit form
      await user.click(screen.getByRole('button', { name: /Save/i }))

      // Button should show "Saving..." and be disabled
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Saving/i })).toBeDisabled()
      })
    })
  })

  // ============================================
  // EDIT POSITION TESTS (BDD: @positions @happy-path)
  // ============================================

  describe('Edit Position', () => {
    it('opens edit modal with pre-filled data when clicking edit button', async () => {
      const user = userEvent.setup()
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      // Find and click the edit button for Cook (first position)
      const editButtons = screen.getAllByTitle(/Edit/i)
      await user.click(editButtons[0])

      // Modal should open with Edit Position title
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /Edit Position/i })).toBeInTheDocument()
      })

      // Fields should be pre-filled
      expect(screen.getByDisplayValue('Cook')).toBeInTheDocument()
      expect(screen.getByDisplayValue('25')).toBeInTheDocument()
    })

    it('updates position hourly rate successfully', async () => {
      const user = userEvent.setup()
      const updatedPosition: Position = {
        ...mockPositions[0],
        hourly_rate: 27.0,
      }

      vi.mocked(positionsApi.updatePosition).mockResolvedValue(updatedPosition)

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByTitle(/Edit/i)
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Clear and update hourly rate
      const rateInput = screen.getByDisplayValue('25')
      await user.clear(rateInput)
      await user.type(rateInput, '27')

      await user.click(screen.getByRole('button', { name: /Save/i }))

      await waitFor(() => {
        expect(positionsApi.updatePosition).toHaveBeenCalledWith(1, {
          name: 'Cook',
          hourly_rate: 27.0,
        })
      })
    })
  })

  // ============================================
  // DELETE POSITION TESTS (BDD: @positions @validation)
  // ============================================

  describe('Delete Position', () => {
    it('prevents deletion of position with assigned employees', async () => {
      const user = userEvent.setup()
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      // Click delete button for Cook (has 2 employees)
      const deleteButtons = screen.getAllByTitle(/Delete/i)
      await user.click(deleteButtons[0])

      // Alert should show error message
      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(
          expect.stringMatching(/Cannot delete position with assigned employees/i)
        )
      })

      // Delete API should NOT be called
      expect(positionsApi.deletePosition).not.toHaveBeenCalled()
    })

    it('disables delete button for positions with employees', async () => {
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      // Delete buttons for positions with employees should be disabled
      const deleteButtons = screen.getAllByTitle(/Delete/i)

      // Cook has 2 employees - button should be disabled
      expect(deleteButtons[0]).toBeDisabled()
      // Cashier has 1 employee - button should be disabled
      expect(deleteButtons[1]).toBeDisabled()
      // Helper has 0 employees - button should be enabled
      expect(deleteButtons[2]).not.toBeDisabled()
    })

    it('deletes position without employees after confirmation', async () => {
      const user = userEvent.setup()
      vi.mocked(positionsApi.deletePosition).mockResolvedValue()
      vi.mocked(window.confirm).mockReturnValue(true)

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Helper')).toBeInTheDocument()
      })

      // Click delete button for Helper (has 0 employees - third position)
      const deleteButtons = screen.getAllByTitle(/Delete/i)
      await user.click(deleteButtons[2])

      // Confirm should be called
      expect(window.confirm).toHaveBeenCalled()

      // Delete API should be called
      await waitFor(() => {
        expect(positionsApi.deletePosition).toHaveBeenCalledWith(3)
      })
    })

    it('cancels deletion when user declines confirmation', async () => {
      const user = userEvent.setup()
      vi.mocked(window.confirm).mockReturnValue(false)

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Helper')).toBeInTheDocument()
      })

      const deleteButtons = screen.getAllByTitle(/Delete/i)
      await user.click(deleteButtons[2])

      expect(window.confirm).toHaveBeenCalled()
      expect(positionsApi.deletePosition).not.toHaveBeenCalled()
    })

    it('shows error when delete fails from API', async () => {
      const user = userEvent.setup()
      vi.mocked(window.confirm).mockReturnValue(true)
      vi.mocked(positionsApi.deletePosition).mockRejectedValue({
        response: {
          data: {
            detail: 'Cannot delete position with assigned employees',
          },
        },
      })

      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Helper')).toBeInTheDocument()
      })

      const deleteButtons = screen.getAllByTitle(/Delete/i)
      await user.click(deleteButtons[2])

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Cannot delete position with assigned employees')
      })
    })
  })

  // ============================================
  // MODAL BEHAVIOR TESTS
  // ============================================

  describe('Modal Behavior', () => {
    it('closes add modal when clicking close button', async () => {
      const user = userEvent.setup()
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Position/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Click close button (aria-label="Zamknij")
      const closeButton = screen.getByLabelText(/Zamknij/i)
      await user.click(closeButton)

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })

    it('clears form when modal is reopened', async () => {
      const user = userEvent.setup()
      render(<PositionsSection />)

      await waitFor(() => {
        expect(screen.getByText('Cook')).toBeInTheDocument()
      })

      // Open modal and fill form
      await user.click(screen.getByRole('button', { name: /Add Position/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      const nameInput = screen.getByPlaceholderText(/Cook, Cashier/i)
      await user.type(nameInput, 'Test Position')

      // Close modal
      const closeButton = screen.getByLabelText(/Zamknij/i)
      await user.click(closeButton)

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })

      // Reopen modal
      await user.click(screen.getByRole('button', { name: /Add Position/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Form should be empty
      const newNameInput = screen.getByPlaceholderText(/Cook, Cashier/i)
      expect(newNameInput).toHaveValue('')
    })
  })

  // ============================================
  // PARAMETERIZED TESTS (BDD: @positions @parameterized)
  // ============================================

  describe('Parameterized: Creating positions with different rates', () => {
    const testCases = [
      { name: 'Cook', rate: 25.0 },
      { name: 'Cashier', rate: 22.0 },
      { name: 'Helper', rate: 18.5 },
      { name: 'Manager', rate: 35.0 },
    ]

    testCases.forEach(({ name, rate }) => {
      it(`creates position "${name}" with rate "${rate}"`, async () => {
        const user = userEvent.setup()
        const newPosition: Position = {
          id: 10,
          name,
          hourly_rate: rate,
          employee_count: 0,
          created_at: '2026-01-04T10:00:00Z',
        }

        vi.mocked(positionsApi.createPosition).mockResolvedValue(newPosition)

        render(<PositionsSection />)

        await waitFor(() => {
          expect(screen.getByText('Cook')).toBeInTheDocument()
        })

        await user.click(screen.getByRole('button', { name: /Add Position/i }))

        await waitFor(() => {
          expect(screen.getByRole('dialog')).toBeInTheDocument()
        })

        const nameInput = screen.getByPlaceholderText(/Cook, Cashier/i)
        const rateInput = screen.getByPlaceholderText('25.00')

        await user.type(nameInput, name)
        await user.type(rateInput, rate.toString())

        await user.click(screen.getByRole('button', { name: /Save/i }))

        await waitFor(() => {
          expect(positionsApi.createPosition).toHaveBeenCalledWith({
            name,
            hourly_rate: rate,
          })
        })
      })
    })
  })
})
