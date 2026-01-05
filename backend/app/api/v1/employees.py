from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db
from app.core.i18n import t
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
)
from app.schemas.wage_analytics import HoursCalculationResponse
from app.services import employee_service, wage_analytics_service
from app.services.employee_service import (
    EmployeeNotFoundError,
    PositionNotFoundError,
    EmployeeHasHistoryError,
)

router = APIRouter()


def _to_response(employee: Employee) -> EmployeeResponse:
    """Convert Employee model to EmployeeResponse schema."""
    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        position_id=employee.position_id,
        position_name=employee.position.name if employee.position else "",
        hourly_rate=employee.effective_hourly_rate,
        is_active=employee.is_active,
        created_at=employee.created_at,
    )


@router.get("", response_model=EmployeeListResponse)
def list_employees(
    include_inactive: bool = Query(False, description="Uwzglednij nieaktywnych pracownikow"),
    db: Session = Depends(get_db),
):
    """Pobierz liste pracownikow."""
    employees = employee_service.get_employees(db, include_inactive)
    total = employee_service.count_employees(db, include_inactive)

    return EmployeeListResponse(
        items=[_to_response(e) for e in employees],
        total=total,
    )


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowego pracownika."""
    try:
        employee = employee_service.create_employee(db, data)
    except PositionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.position_not_found"),
        )
    return _to_response(employee)


# Static routes BEFORE path parameter routes
@router.get("/active", response_model=EmployeeListResponse)
def list_active_employees(db: Session = Depends(get_db)):
    """Pobierz liste tylko aktywnych pracownikow."""
    employees = employee_service.get_employees(db, include_inactive=False)
    total = employee_service.count_employees(db, include_inactive=False)

    return EmployeeListResponse(
        items=[_to_response(e) for e in employees],
        total=total,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz pracownika po ID."""
    employee = employee_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )
    return _to_response(employee)


@router.get("/{employee_id}/hours", response_model=HoursCalculationResponse)
def get_employee_hours(
    employee_id: int,
    start_date: date = Query(..., description="Data poczatkowa"),
    end_date: date = Query(..., description="Data koncowa"),
    db: Session = Depends(get_db),
):
    """
    Oblicz godziny i wynagrodzenie pracownika za okres.

    Zwraca liczbe przepracowanych godzin i wyliczone wynagrodzenie
    na podstawie stawki godzinowej pracownika.
    """
    try:
        result = wage_analytics_service.get_employee_hours_for_period(
            db=db,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj pracownika."""
    try:
        employee = employee_service.update_employee(db, employee_id, data)
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )
    except PositionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.position_not_found"),
        )
    return _to_response(employee)


@router.patch("/{employee_id}/deactivate", response_model=EmployeeResponse)
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """Dezaktywuj pracownika (soft delete)."""
    try:
        employee = employee_service.deactivate_employee(db, employee_id)
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )
    return _to_response(employee)


@router.patch("/{employee_id}/activate", response_model=EmployeeResponse)
def activate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """Aktywuj pracownika ponownie."""
    try:
        employee = employee_service.activate_employee(db, employee_id)
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )
    return _to_response(employee)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """Usun pracownika (tylko jesli nie ma historii zmian/wyplat)."""
    try:
        employee_service.delete_employee(db, employee_id)
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.employee_not_found"),
        )
    except EmployeeHasHistoryError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
