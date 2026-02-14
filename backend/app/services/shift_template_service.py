"""
Service for managing shift templates and schedule overrides.

Shift templates define recurring weekly shift patterns.
Schedule overrides modify templates for specific dates.
"""
from datetime import date, time, timedelta
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.shift_template import ShiftTemplate
from app.models.shift_schedule_override import ShiftScheduleOverride
from app.models.employee import Employee
from app.schemas.shift_template import (
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    ShiftTemplateResponse,
    DAY_NAMES,
    EmployeeMinimal,
)
from app.schemas.shift_schedule import (
    ScheduleOverrideCreate,
    ScheduleOverrideResponse,
    DayShift,
    DaySchedule,
    WeeklyScheduleResponse,
)


class EmployeeNotFoundError(Exception):
    """Raised when an employee is not found."""
    pass


class ShiftTemplateNotFoundError(Exception):
    """Raised when a shift template is not found."""
    pass


class ShiftTemplateService:
    """
    Service class for shift template and schedule override operations.

    Provides methods for:
    - Creating, updating, deleting shift templates
    - Managing schedule overrides for specific dates
    - Getting shifts for a specific date (combines templates + overrides)
    - Generating weekly schedule views
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Shift Template Operations
    # =========================================================================

    def create(self, data: ShiftTemplateCreate) -> ShiftTemplateResponse:
        """
        Create a new shift template.

        Raises IntegrityError if template already exists for employee + day.
        """
        # Verify employee exists
        employee = self.db.query(Employee).filter(Employee.id == data.employee_id).first()
        if not employee:
            raise EmployeeNotFoundError(f"Employee with ID {data.employee_id} not found")

        template = ShiftTemplate(
            employee_id=data.employee_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        template.employee = employee  # Set relationship for immediate access
        self.db.add(template)
        self.db.flush()  # Flush to get ID and trigger constraint checks

        return self._to_response(template, employee.name)

    def get(self, template_id: int) -> Optional[ShiftTemplateResponse]:
        """Get a shift template by ID."""
        template = (
            self.db.query(ShiftTemplate)
            .options(joinedload(ShiftTemplate.employee))
            .filter(ShiftTemplate.id == template_id)
            .first()
        )
        if not template:
            return None
        return self._to_response(template, template.employee.name)

    def get_all(self, employee_id: Optional[int] = None) -> list[ShiftTemplateResponse]:
        """
        Get all shift templates, optionally filtered by employee.

        Returns templates ordered by employee_id, day_of_week.
        """
        query = (
            self.db.query(ShiftTemplate)
            .options(joinedload(ShiftTemplate.employee))
        )

        if employee_id is not None:
            query = query.filter(ShiftTemplate.employee_id == employee_id)

        templates = query.order_by(
            ShiftTemplate.employee_id,
            ShiftTemplate.day_of_week
        ).all()

        return [self._to_response(t, t.employee.name) for t in templates]

    def get_by_employee(self, employee_id: int) -> list[ShiftTemplateResponse]:
        """
        Get all templates for a specific employee, ordered by day_of_week.
        """
        templates = (
            self.db.query(ShiftTemplate)
            .options(joinedload(ShiftTemplate.employee))
            .filter(ShiftTemplate.employee_id == employee_id)
            .order_by(ShiftTemplate.day_of_week)
            .all()
        )
        return [self._to_response(t, t.employee.name) for t in templates]

    def update(self, template_id: int, data: ShiftTemplateUpdate) -> Optional[ShiftTemplateResponse]:
        """Update a shift template."""
        template = (
            self.db.query(ShiftTemplate)
            .options(joinedload(ShiftTemplate.employee))
            .filter(ShiftTemplate.id == template_id)
            .first()
        )
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        self.db.flush()
        return self._to_response(template, template.employee.name)

    def delete(self, template_id: int) -> bool:
        """
        Delete a shift template.

        Returns True if deleted, False if not found.
        """
        template = self.db.query(ShiftTemplate).filter(ShiftTemplate.id == template_id).first()
        if not template:
            return False

        self.db.delete(template)
        self.db.flush()
        return True

    def count(self, employee_id: Optional[int] = None) -> int:
        """Count shift templates, optionally filtered by employee."""
        query = self.db.query(func.count(ShiftTemplate.id))
        if employee_id is not None:
            query = query.filter(ShiftTemplate.employee_id == employee_id)
        return query.scalar() or 0

    # =========================================================================
    # Schedule Override Operations
    # =========================================================================

    def create_or_update_override(
        self,
        employee_id: int,
        override_date: date,
        data: ScheduleOverrideCreate
    ) -> ScheduleOverrideResponse:
        """
        Create or update a schedule override for a specific date.

        If an override already exists for employee + date, it will be updated.
        """
        # Verify employee exists
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise EmployeeNotFoundError(f"Employee with ID {employee_id} not found")

        # Check for existing override
        override = (
            self.db.query(ShiftScheduleOverride)
            .filter(
                ShiftScheduleOverride.employee_id == employee_id,
                ShiftScheduleOverride.date == override_date
            )
            .first()
        )

        if override:
            # Update existing
            override.start_time = data.start_time
            override.end_time = data.end_time
            override.is_day_off = data.is_day_off
        else:
            # Create new
            override = ShiftScheduleOverride(
                employee_id=employee_id,
                date=override_date,
                start_time=data.start_time,
                end_time=data.end_time,
                is_day_off=data.is_day_off,
            )
            self.db.add(override)

        self.db.flush()

        return ScheduleOverrideResponse(
            id=override.id,
            employee_id=override.employee_id,
            employee_name=employee.name,
            date=override.date,
            start_time=override.start_time,
            end_time=override.end_time,
            is_day_off=override.is_day_off,
        )

    def delete_override(self, employee_id: int, override_date: date) -> bool:
        """
        Delete a schedule override.

        Returns True if deleted, False if not found.
        """
        override = (
            self.db.query(ShiftScheduleOverride)
            .filter(
                ShiftScheduleOverride.employee_id == employee_id,
                ShiftScheduleOverride.date == override_date
            )
            .first()
        )
        if not override:
            return False

        self.db.delete(override)
        self.db.flush()
        return True

    # =========================================================================
    # Schedule Query Operations
    # =========================================================================

    def get_shifts_for_date(self, target_date: date) -> list[dict]:
        """
        Get all scheduled shifts for a specific date.

        Combines shift templates with overrides:
        - If an override exists for an employee + date, use it instead of template
        - If override is a day off, exclude that employee from results
        - Overrides without templates (extra shifts) are also included

        Returns a list of dicts with shift info including 'source' field.
        """
        day_of_week = target_date.weekday()  # 0=Monday

        # Get all overrides for this date
        overrides = (
            self.db.query(ShiftScheduleOverride)
            .options(joinedload(ShiftScheduleOverride.employee))
            .filter(ShiftScheduleOverride.date == target_date)
            .all()
        )
        override_by_employee = {o.employee_id: o for o in overrides}

        # Get all templates for this day of week
        templates = (
            self.db.query(ShiftTemplate)
            .options(joinedload(ShiftTemplate.employee))
            .filter(ShiftTemplate.day_of_week == day_of_week)
            .all()
        )

        shifts = []

        # Process templates, applying overrides where they exist
        for template in templates:
            if template.employee_id in override_by_employee:
                # Override exists - use it instead of template
                override = override_by_employee[template.employee_id]
                if override.is_day_off:
                    # Employee has day off - skip
                    continue

                shift_data = {
                    "employee_id": template.employee_id,
                    "employee_name": template.employee.name,
                    "start_time": override.start_time,
                    "end_time": override.end_time,
                    "source": "override",
                    "is_override": True,
                }

                # Check if employee is inactive
                if not template.employee.is_active:
                    shift_data["employee_inactive"] = True
                    shift_data["warning"] = "Pracownik jest nieaktywny"

                shifts.append(shift_data)
            else:
                # No override - use template
                shift_data = {
                    "employee_id": template.employee_id,
                    "employee_name": template.employee.name,
                    "start_time": template.start_time,
                    "end_time": template.end_time,
                    "source": "template",
                    "is_override": False,
                }

                # Check if employee is inactive
                if not template.employee.is_active:
                    shift_data["employee_inactive"] = True
                    shift_data["warning"] = "Pracownik jest nieaktywny"

                shifts.append(shift_data)

        # Add overrides for employees without templates (extra shifts)
        template_employee_ids = {t.employee_id for t in templates}
        for override in overrides:
            if override.employee_id not in template_employee_ids:
                if override.is_day_off:
                    # Day off override for an employee without template - no shift
                    continue

                shift_data = {
                    "employee_id": override.employee_id,
                    "employee_name": override.employee.name,
                    "start_time": override.start_time,
                    "end_time": override.end_time,
                    "source": "override",
                    "is_override": True,
                }

                # Check if employee is inactive
                if not override.employee.is_active:
                    shift_data["employee_inactive"] = True
                    shift_data["warning"] = "Pracownik jest nieaktywny"

                shifts.append(shift_data)

        return shifts

    def get_weekly_schedule(self, start_date: date) -> WeeklyScheduleResponse:
        """
        Get the weekly schedule starting from the given date.

        Returns 7 days of schedule data.
        """
        schedules = []

        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()

            shifts_data = self.get_shifts_for_date(current_date)
            shifts = [
                DayShift(
                    employee_id=s["employee_id"],
                    employee_name=s["employee_name"],
                    start_time=s["start_time"],
                    end_time=s["end_time"],
                    source=s["source"],
                    is_override=s["is_override"],
                    employee_inactive=s.get("employee_inactive"),
                    warning=s.get("warning"),
                )
                for s in shifts_data
            ]

            schedules.append(DaySchedule(
                date=current_date,
                day_of_week=day_of_week,
                day_name=DAY_NAMES[day_of_week],
                shifts=shifts,
            ))

        end_date = start_date + timedelta(days=6)

        return WeeklyScheduleResponse(
            week_start=start_date,
            week_end=end_date,
            schedules=schedules,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _to_response(self, template: ShiftTemplate, employee_name: str) -> ShiftTemplateResponse:
        """Convert ShiftTemplate model to response schema."""
        employee_minimal = None
        if template.employee:
            employee_minimal = EmployeeMinimal(
                id=template.employee.id,
                name=template.employee.name
            )

        return ShiftTemplateResponse(
            id=template.id,
            employee_id=template.employee_id,
            employee_name=employee_name,
            day_of_week=template.day_of_week,
            day_name=DAY_NAMES[template.day_of_week],
            start_time=template.start_time,
            end_time=template.end_time,
            created_at=template.created_at,
            employee=employee_minimal,
        )
