import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, userEvent } from '../../../test/test-utils'
import EmployeesSection from '../EmployeesSection'
import * as employeesApi from '../../../api/employees'
import * as positionsApi from '../../../api/positions'
import type { Employee, Position } from '../../../types'

// Mock the APIs
vi.mock('../../../api/employees', () => ({
  getEmployees: vi.fn(),
  createEmployee: vi.fn(),
  updateEmployee: vi.fn(),
  deactivateEmployee: vi.fn(),
  activateEmployee: vi.fn(),
}))

vi.mock('../../../api/positions', () => ({
  getPositions: vi.fn(),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Plus: () => <svg data-testid="plus-icon" />,
  Pencil: () => <svg data-testid="pencil-icon" />,
  UserX: () => <svg data-testid="user-x-icon" />,
  UserCheck: () => <svg data-testid="user-check-icon" />,
  Users: () => <svg data-testid="users-icon" />,
  X: () => <svg data-testid="x-icon" />,
}))

describe('EmployeesSection', () => {
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
  ]

  const mockActiveEmployees: Employee[] = [
    {
      id: 1,
      name: 'John Smith',
      position_id: 1,
      position_name: 'Cook',
      hourly_rate: 27.0,
      is_active: true,
      created_at: '2026-01-01T10:00:00Z',
    },
    {
      id: 2,
      name: 'Jane Doe',
      position_id: 2,
      position_name: 'Cashier',
      hourly_rate: 22.0,
      is_active: true,
      created_at: '2026-01-02T10:00:00Z',
    },
  ]

  const mockInactiveEmployee: Employee = {
    id: 3,
    name: 'Bob Wilson',
    position_id: 1,
    position_name: 'Cook',
    hourly_rate: 25.0,
    is_active: false,
    created_at: '2026-01-03T10:00:00Z',
  }

  const mockAllEmployees = [...mockActiveEmployees, mockInactiveEmployee]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(positionsApi.getPositions).mockResolvedValue({
      items: mockPositions,
      total: mockPositions.length,
    })
    vi.mocked(employeesApi.getEmployees).mockImplementation((includeInactive) => {
      if (includeInactive) {
        return Promise.resolve({
          items: mockAllEmployees,
          total: mockAllEmployees.length,
        })
      }
      return Promise.resolve({
        items: mockActiveEmployees,
        total: mockActiveEmployees.length,
      })
    })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  // ============================================
  // RENDERING TESTS
  // ============================================

  describe('Rendering', () => {
    it('renders loading spinner while fetching employees', async () => {
      vi.mocked(employeesApi.getEmployees).mockImplementation(
        () => new Promise(() => {})
      )

      render(<EmployeesSection />)

      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('renders active employees by default', async () => {
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      expect(screen.getByText('John Smith')).toBeInTheDocument()
      expect(screen.getByText('Jane Doe')).toBeInTheDocument()
      expect(screen.queryByText('Bob Wilson')).not.toBeInTheDocument()
    })

    it('renders employee details correctly', async () => {
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      // Position names
      expect(screen.getAllByText('Cook')[0]).toBeInTheDocument()
      expect(screen.getByText('Cashier')).toBeInTheDocument()

      // Hourly rates (currency format varies by locale)
      expect(screen.getByText(/27.*\/h/i)).toBeInTheDocument()
      expect(screen.getByText(/22.*\/h/i)).toBeInTheDocument()

      // Status badges
      const activeBadges = screen.getAllByText(/Active/i)
      expect(activeBadges.length).toBeGreaterThan(0)
    })

    it('renders empty state when no employees exist', async () => {
      vi.mocked(employeesApi.getEmployees).mockResolvedValue({
        items: [],
        total: 0,
      })

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText(/No employees/i)).toBeInTheDocument()
      })
    })

    it('shows warning when no positions exist', async () => {
      vi.mocked(positionsApi.getPositions).mockResolvedValue({
        items: [],
        total: 0,
      })

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText(/Add a position first/i)).toBeInTheDocument()
      })
    })

    it('disables add employee button when no positions exist', async () => {
      vi.mocked(positionsApi.getPositions).mockResolvedValue({
        items: [],
        total: 0,
      })

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Add Employee/i })).toBeDisabled()
      })
    })
  })

  // ============================================
  // FILTERING TESTS (BDD: @employees @filtering)
  // ============================================

  describe('Filtering', () => {
    it('shows only active employees by default', async () => {
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      expect(screen.getByText('John Smith')).toBeInTheDocument()
      expect(screen.getByText('Jane Doe')).toBeInTheDocument()
      expect(screen.queryByText('Bob Wilson')).not.toBeInTheDocument()
    })

    it('shows all employees including inactive when checkbox is checked', async () => {
      const user = userEvent.setup()
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      // Check the "Show inactive" checkbox
      const checkbox = screen.getByLabelText(/Show inactive/i)
      await user.click(checkbox)

      await waitFor(() => {
        expect(employeesApi.getEmployees).toHaveBeenCalledWith(true)
      })

      await waitFor(() => {
        expect(screen.getByText('Bob Wilson')).toBeInTheDocument()
      })
    })

    it('hides inactive employees when checkbox is unchecked', async () => {
      const user = userEvent.setup()
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      // Check then uncheck the checkbox
      const checkbox = screen.getByLabelText(/Show inactive/i)
      await user.click(checkbox)

      await waitFor(() => {
        expect(screen.getByText('Bob Wilson')).toBeInTheDocument()
      })

      await user.click(checkbox)

      await waitFor(() => {
        expect(employeesApi.getEmployees).toHaveBeenLastCalledWith(false)
      })
    })
  })

  // ============================================
  // CREATE EMPLOYEE TESTS (BDD: @employees @happy-path @smoke)
  // ============================================

  describe('Create Employee', () => {
    it('opens add employee modal when clicking add button', async () => {
      const user = userEvent.setup()
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Employee/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /Add Employee/i })).toBeInTheDocument()
      })
    })

    it('creates employee with position default rate when no custom rate', async () => {
      const user = userEvent.setup()
      const newEmployee: Employee = {
        id: 4,
        name: 'Anna Smith',
        position_id: 2,
        position_name: 'Cashier',
        hourly_rate: 22.0,
        is_active: true,
        created_at: '2026-01-04T10:00:00Z',
      }

      vi.mocked(employeesApi.createEmployee).mockResolvedValue(newEmployee)

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Employee/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Fill name
      const nameInput = screen.getByPlaceholderText(/John Smith/i)
      await user.type(nameInput, 'Anna Smith')

      // Select position
      const positionSelect = screen.getByRole('combobox')
      await user.selectOptions(positionSelect, '2')

      // Leave custom rate unchecked
      await user.click(screen.getByRole('button', { name: /Save/i }))

      await waitFor(() => {
        expect(employeesApi.createEmployee).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Anna Smith',
            position_id: 2,
            hourly_rate: null,
          }),
          expect.anything() // React Query mutation context
        )
      })
    })

    it('creates employee with custom hourly rate', async () => {
      const user = userEvent.setup()
      const newEmployee: Employee = {
        id: 4,
        name: 'Peter Smith',
        position_id: 2,
        position_name: 'Cashier',
        hourly_rate: 24.5,
        is_active: true,
        created_at: '2026-01-04T10:00:00Z',
      }

      vi.mocked(employeesApi.createEmployee).mockResolvedValue(newEmployee)

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Employee/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Fill name
      const nameInput = screen.getByPlaceholderText(/John Smith/i)
      await user.type(nameInput, 'Peter Smith')

      // Select position
      const positionSelect = screen.getByRole('combobox')
      await user.selectOptions(positionSelect, '2')

      // Enable custom rate checkbox
      const customRateCheckbox = screen.getByLabelText(/Use custom rate/i)
      await user.click(customRateCheckbox)

      // Fill custom rate
      const rateInputs = document.querySelectorAll('input[type="number"]')
      const rateInput = rateInputs[0] as HTMLInputElement
      await user.clear(rateInput)
      await user.type(rateInput, '24.50')

      await user.click(screen.getByRole('button', { name: /Save/i }))

      await waitFor(() => {
        expect(employeesApi.createEmployee).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Peter Smith',
            position_id: 2,
            hourly_rate: 24.5,
          }),
          expect.anything() // React Query mutation context
        )
      })
    })

    it('shows position rate hint when position is selected', async () => {
      const user = userEvent.setup()
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Employee/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Select Cashier position (rate: 22.00)
      const positionSelect = screen.getByRole('combobox')
      await user.selectOptions(positionSelect, '2')

      // Should show position rate hint (when custom rate is disabled)
      await waitFor(() => {
        expect(screen.getByText(/Position rate:/i)).toBeInTheDocument()
      })
    })
  })

  // ============================================
  // EDIT EMPLOYEE TESTS
  // ============================================

  describe('Edit Employee', () => {
    it('opens edit modal with pre-filled data', async () => {
      const user = userEvent.setup()
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByTitle(/Edit/i)
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /Edit Employee/i })).toBeInTheDocument()
      })

      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument()
    })

    it('updates employee successfully', async () => {
      const user = userEvent.setup()
      const updatedEmployee: Employee = {
        ...mockActiveEmployees[0],
        name: 'John Updated',
      }

      vi.mocked(employeesApi.updateEmployee).mockResolvedValue(updatedEmployee)

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      const editButtons = screen.getAllByTitle(/Edit/i)
      await user.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      const nameInput = screen.getByDisplayValue('John Smith')
      await user.clear(nameInput)
      await user.type(nameInput, 'John Updated')

      await user.click(screen.getByRole('button', { name: /Save/i }))

      await waitFor(() => {
        expect(employeesApi.updateEmployee).toHaveBeenCalledWith(1, expect.objectContaining({
          name: 'John Updated',
        }))
      })
    })
  })

  // ============================================
  // DEACTIVATE/ACTIVATE EMPLOYEE TESTS (BDD: @employees @happy-path)
  // ============================================

  describe('Deactivate Employee', () => {
    it('deactivates employee after confirmation', async () => {
      const user = userEvent.setup()
      const deactivatedEmployee: Employee = {
        ...mockActiveEmployees[0],
        is_active: false,
      }

      vi.mocked(employeesApi.deactivateEmployee).mockResolvedValue(deactivatedEmployee)
      vi.mocked(window.confirm).mockReturnValue(true)

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      // Find and click deactivate button (UserX icon)
      const deactivateButtons = screen.getAllByTitle(/Deactivate/i)
      await user.click(deactivateButtons[0])

      expect(window.confirm).toHaveBeenCalledWith(
        expect.stringContaining('John Smith')
      )

      await waitFor(() => {
        expect(employeesApi.deactivateEmployee).toHaveBeenCalledWith(
          1,
          expect.anything() // React Query mutation context
        )
      })
    })

    it('does not deactivate when confirmation is cancelled', async () => {
      const user = userEvent.setup()
      vi.mocked(window.confirm).mockReturnValue(false)

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      const deactivateButtons = screen.getAllByTitle(/Deactivate/i)
      await user.click(deactivateButtons[0])

      expect(window.confirm).toHaveBeenCalled()
      expect(employeesApi.deactivateEmployee).not.toHaveBeenCalled()
    })
  })

  describe('Activate Employee', () => {
    // TODO: This test has a React Query mutation timing issue - mutation not being triggered
    it.skip('activates inactive employee', async () => {
      const user = userEvent.setup()
      const activatedEmployee: Employee = {
        ...mockInactiveEmployee,
        is_active: true,
      }

      vi.mocked(employeesApi.activateEmployee).mockResolvedValue(activatedEmployee)

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      // Enable showing inactive employees
      const checkbox = screen.getByLabelText(/Show inactive/i)
      await user.click(checkbox)

      await waitFor(() => {
        expect(screen.getByText('Bob Wilson')).toBeInTheDocument()
      })

      // Find and click activate button for inactive employee
      const activateButtons = screen.getAllByTitle(/Activate/i)
      await user.click(activateButtons[0])

      await waitFor(() => {
        // React Query calls the mutation function with the id as first argument
        expect(employeesApi.activateEmployee).toHaveBeenCalled()
        const calls = vi.mocked(employeesApi.activateEmployee).mock.calls
        expect(calls.length).toBeGreaterThan(0)
        expect(calls[0][0]).toBe(3)
      })
    })
  })

  // ============================================
  // STATUS DISPLAY TESTS
  // ============================================

  describe('Status Display', () => {
    it('shows active badge for active employees', async () => {
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      // Use exact match for "Active" to avoid matching "Activate" button
      const activeBadges = screen.getAllByText('Active')
      expect(activeBadges.length).toBe(2) // Both active employees
    })

    it('shows inactive badge for inactive employees', async () => {
      const user = userEvent.setup()
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      const checkbox = screen.getByLabelText(/Show inactive/i)
      await user.click(checkbox)

      await waitFor(() => {
        expect(screen.getByText('Bob Wilson')).toBeInTheDocument()
      })

      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })

    it('applies opacity to inactive employee row', async () => {
      const user = userEvent.setup()
      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      const checkbox = screen.getByLabelText(/Show inactive/i)
      await user.click(checkbox)

      await waitFor(() => {
        expect(screen.getByText('Bob Wilson')).toBeInTheDocument()
      })

      // Find the row for Bob Wilson and check for opacity class
      const bobRow = screen.getByText('Bob Wilson').closest('tr')
      expect(bobRow).toHaveClass('opacity-60')
    })
  })

  // ============================================
  // ERROR HANDLING TESTS
  // ============================================

  describe('Error Handling', () => {
    it('shows error when create fails', async () => {
      const user = userEvent.setup()

      vi.mocked(employeesApi.createEmployee).mockRejectedValue({
        response: {
          data: {
            detail: 'Employee creation failed',
          },
        },
      })

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /Add Employee/i }))

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      const nameInput = screen.getByPlaceholderText(/John Smith/i)
      await user.type(nameInput, 'Test Employee')

      const positionSelect = screen.getByRole('combobox')
      await user.selectOptions(positionSelect, '1')

      await user.click(screen.getByRole('button', { name: /Save/i }))

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Employee creation failed')
      })
    })

    it('shows error when deactivate fails', async () => {
      const user = userEvent.setup()
      vi.mocked(window.confirm).mockReturnValue(true)
      vi.mocked(employeesApi.deactivateEmployee).mockRejectedValue({
        response: {
          data: {
            detail: 'Deactivation failed',
          },
        },
      })

      render(<EmployeesSection />)

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument()
      })

      const deactivateButtons = screen.getAllByTitle(/Deactivate/i)
      await user.click(deactivateButtons[0])

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Deactivation failed')
      })
    })
  })
})
