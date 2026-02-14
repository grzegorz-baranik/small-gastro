"""
API endpoints for shift templates and schedule management.

Endpoints:
- /shift-templates - CRUD for recurring shift templates
- /shift-schedules/week - Get weekly schedule view
- /shift-schedules/{date}/{employee_id} - Manage schedule overrides
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.api.deps import get_db
from app.core.i18n import t
from app.schemas.shift_template import (
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    ShiftTemplateResponse,
    ShiftTemplateListResponse,
)
from app.schemas.shift_schedule import (
    ScheduleOverrideCreate,
    ScheduleOverrideResponse,
    WeeklyScheduleResponse,
)
from app.services.shift_template_service import (
    ShiftTemplateService,
    EmployeeNotFoundError,
)

router = APIRouter()


# =============================================================================
# Shift Templates Endpoints
# =============================================================================

@router.get("/shift-templates", response_model=ShiftTemplateListResponse)
def list_shift_templates(
    employee_id: Optional[int] = Query(None, description="Filtruj wedlug pracownika"),
    db: Session = Depends(get_db),
):
    """Pobierz liste szablonow zmian."""
    service = ShiftTemplateService(db)
    templates = service.get_all(employee_id=employee_id)
    total = service.count(employee_id=employee_id)

    return ShiftTemplateListResponse(
        items=templates,
        total=total,
    )


@router.post("/shift-templates", response_model=ShiftTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_shift_template(
    data: ShiftTemplateCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowy szablon zmiany."""
    service = ShiftTemplateService(db)
    try:
        template = service.create(data)
        db.commit()
        return template
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Szablon dla tego pracownika i dnia tygodnia juz istnieje",
        )


@router.get("/shift-templates/{template_id}", response_model=ShiftTemplateResponse)
def get_shift_template(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz szablon zmiany po ID."""
    service = ShiftTemplateService(db)
    template = service.get(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Szablon nie zostal znaleziony",
        )
    return template


@router.put("/shift-templates/{template_id}", response_model=ShiftTemplateResponse)
def update_shift_template(
    template_id: int,
    data: ShiftTemplateUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj szablon zmiany."""
    service = ShiftTemplateService(db)
    template = service.update(template_id, data)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Szablon nie zostal znaleziony",
        )
    db.commit()
    return template


@router.delete("/shift-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift_template(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Usun szablon zmiany."""
    service = ShiftTemplateService(db)
    deleted = service.delete(template_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Szablon nie zostal znaleziony",
        )
    db.commit()


# =============================================================================
# Weekly Schedule Endpoints
# =============================================================================

@router.get("/shift-schedules/week", response_model=WeeklyScheduleResponse)
def get_weekly_schedule(
    start_date: date = Query(..., description="Data poczatkowa tygodnia"),
    db: Session = Depends(get_db),
):
    """
    Pobierz harmonogram tygodniowy.

    Zwraca 7 dni harmonogramu, lacznie z szablonami i nadpisaniami.
    """
    service = ShiftTemplateService(db)
    return service.get_weekly_schedule(start_date)


# =============================================================================
# Schedule Override Endpoints
# =============================================================================

@router.put(
    "/shift-schedules/{override_date}/{employee_id}",
    response_model=ScheduleOverrideResponse
)
def create_or_update_schedule_override(
    override_date: date,
    employee_id: int,
    data: ScheduleOverrideCreate,
    db: Session = Depends(get_db),
):
    """
    Utworz lub zaktualizuj nadpisanie harmonogramu dla daty i pracownika.

    Uzyj is_day_off=true, aby oznaczyc dzien wolny.
    """
    service = ShiftTemplateService(db)
    try:
        override = service.create_or_update_override(employee_id, override_date, data)
        db.commit()
        return override
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )


@router.delete(
    "/shift-schedules/{override_date}/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_schedule_override(
    override_date: date,
    employee_id: int,
    db: Session = Depends(get_db),
):
    """Usun nadpisanie harmonogramu - pracownik wróci do szablonu."""
    service = ShiftTemplateService(db)
    deleted = service.delete_override(employee_id, override_date)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nadpisanie nie zostalo znalezione",
        )
    db.commit()
