from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.i18n import t
from app.models.position import Position
from app.schemas.position import (
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionListResponse,
)
from app.services import position_service
from app.services.position_service import (
    PositionExistsError,
    PositionNotFoundError,
    PositionHasEmployeesError,
)

router = APIRouter()


def _to_response(position: Position, employee_count: int = 0) -> PositionResponse:
    """Convert Position model to PositionResponse schema."""
    return PositionResponse(
        id=position.id,
        name=position.name,
        hourly_rate=position.hourly_rate,
        employee_count=employee_count,
        created_at=position.created_at,
    )


@router.get("", response_model=PositionListResponse)
def list_positions(db: Session = Depends(get_db)):
    """Pobierz liste wszystkich stanowisk."""
    positions = position_service.get_positions(db)

    # Get employee counts for each position
    items = []
    for position in positions:
        count = position_service.get_employee_count_for_position(db, position.id)
        items.append(_to_response(position, count))

    return PositionListResponse(items=items, total=len(items))


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    data: PositionCreate,
    db: Session = Depends(get_db),
):
    """Utworz nowe stanowisko."""
    try:
        position = position_service.create_position(db, data)
    except PositionExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return _to_response(position, 0)


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: int,
    db: Session = Depends(get_db),
):
    """Pobierz stanowisko po ID."""
    position, count = position_service.get_position_with_employee_count(db, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.position_not_found"),
        )
    return _to_response(position, count)


@router.put("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: int,
    data: PositionUpdate,
    db: Session = Depends(get_db),
):
    """Zaktualizuj stanowisko."""
    try:
        position = position_service.update_position(db, position_id, data)
    except PositionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.position_not_found"),
        )
    except PositionExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    count = position_service.get_employee_count_for_position(db, position_id)
    return _to_response(position, count)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
):
    """Usun stanowisko."""
    try:
        position_service.delete_position(db, position_id)
    except PositionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("errors.position_not_found"),
        )
    except PositionHasEmployeesError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
