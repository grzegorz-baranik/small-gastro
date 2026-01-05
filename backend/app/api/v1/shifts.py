from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.i18n import t
from app.models.shift_assignment import ShiftAssignment
from app.schemas.shift_assignment import (
    ShiftAssignmentCreate,
    ShiftAssignmentUpdate,
    ShiftAssignmentResponse,
    ShiftAssignmentListResponse,
)
from app.services import shift_service
from app.services.shift_service import (
    ShiftNotFoundError,
    DailyRecordNotFoundError,
    DayNotOpenError,
    EmployeeNotFoundError,
    EmployeeAlreadyAssignedError,
    InvalidTimeRangeError,
)

router = APIRouter()


def _to_response(shift: ShiftAssignment) -> ShiftAssignmentResponse:
    """Convert ShiftAssignment model to ShiftAssignmentResponse schema."""
    return ShiftAssignmentResponse(
        id=shift.id,
        employee_id=shift.employee_id,
        employee_name=shift.employee.name if shift.employee else "",
        start_time=shift.start_time,
        end_time=shift.end_time,
        hours_worked=shift.hours_worked,
        hourly_rate=shift.employee.effective_hourly_rate if shift.employee else 0,
    )


@router.get(
    "/daily-records/{daily_record_id}/shifts",
    response_model=ShiftAssignmentListResponse,
)
def list_shifts(
    daily_record_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz liste zmian dla danego dnia."""
    shifts = shift_service.get_shifts_by_daily_record(db, daily_record_id)

    return ShiftAssignmentListResponse(
        items=[_to_response(s) for s in shifts],
        total=len(shifts),
    )


@router.post(
    "/daily-records/{daily_record_id}/shifts",
    response_model=ShiftAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shift(
    daily_record_id: int,
    data: ShiftAssignmentCreate,
    db: Session = Depends(get_db),
):
    """Dodaj pracownika do zmiany."""
    try:
        shift = shift_service.create_shift(db, daily_record_id, data)
    except DailyRecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )
    except DayNotOpenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t("errors.employee_not_found"),
        )
    except EmployeeAlreadyAssignedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except InvalidTimeRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return _to_response(shift)


@router.put(
    "/daily-records/{daily_record_id}/shifts/{shift_id}",
    response_model=ShiftAssignmentResponse,
)
def update_shift(
    daily_record_id: int,
    shift_id: int,
    data: ShiftAssignmentUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj godziny zmiany."""
    try:
        shift = shift_service.update_shift(db, daily_record_id, shift_id, data)
    except DailyRecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )
    except DayNotOpenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ShiftNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.shift_not_found"),
        )
    except InvalidTimeRangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return _to_response(shift)


@router.delete(
    "/daily-records/{daily_record_id}/shifts/{shift_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_shift(
    daily_record_id: int,
    shift_id: int,
    db: Session = Depends(get_db),
):
    """Usun pracownika ze zmiany."""
    try:
        shift_service.delete_shift(db, daily_record_id, shift_id)
    except DailyRecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.daily_record_not_found"),
        )
    except DayNotOpenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ShiftNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.shift_not_found"),
        )
