"""Equipment router: public catalog endpoints and vendor management."""

import os
import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from campusrent.app.deps import get_current_user, get_db, require_role
from campusrent.app.models import (
    Availability,
    Equipment,
    EquipmentCondition,
    Order,
    OrderItem,
    OrderStatus,
    User,
    UserRole,
)
from campusrent.app.schemas import EquipmentListResponse, EquipmentResponse, EquipmentUpdate

UPLOAD_DIR_EQUIPMENT = "./uploads/equipment"

# Allowed photo content types
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png"}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter()


# ─── Public Catalog Endpoints ────────────────────────────────────────────────


@router.get("", response_model=EquipmentListResponse)
def list_equipment(
    search: Optional[str] = Query(None, description="Keyword search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Browse the equipment catalog with optional keyword search.
    Returns only active equipment, paginated.
    """
    query = db.query(Equipment).filter(Equipment.is_active == True)

    # Case-insensitive keyword search in name and description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Equipment.name.ilike(search_term),
                Equipment.description.ilike(search_term),
            )
        )

    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return EquipmentListResponse(
        items=[EquipmentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{equipment_id}")
def get_equipment_detail(
    equipment_id: int,
    db: Session = Depends(get_db),
):
    """
    Get full equipment detail including vendor info, average rating,
    and availability for the next 90 days.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Get vendor info
    vendor = db.query(User).filter(User.id == equipment.vendor_id).first()

    # Compute availability for next 90 days
    today = date.today()
    end_date = today + timedelta(days=90)

    # Get blocked dates from availability table
    blocked_dates = (
        db.query(Availability.date)
        .filter(
            Availability.equipment_id == equipment_id,
            Availability.is_blocked == True,
            Availability.date >= today,
            Availability.date <= end_date,
        )
        .all()
    )
    blocked_set = {row.date for row in blocked_dates}

    # Get dates with confirmed bookings (orders in active statuses)
    active_statuses = [
        OrderStatus.PENDING_PAYMENT,
        OrderStatus.PAID_ESCROW,
    ]

    booked_items = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.equipment_id == equipment_id,
            Order.status.in_(active_statuses),
            OrderItem.start_date <= end_date,
            OrderItem.end_date >= today,
        )
        .all()
    )

    # Build set of booked dates
    booked_set = set()
    for item in booked_items:
        current = max(item.start_date, today)
        item_end = min(item.end_date, end_date)
        while current <= item_end:
            booked_set.add(current)
            current += timedelta(days=1)

    # Build availability list for all 90 days
    availability = []
    current = today
    while current <= end_date:
        availability.append({
            "date": current.isoformat(),
            "available": current not in blocked_set and current not in booked_set,
        })
        current += timedelta(days=1)

    return {
        "id": equipment.id,
        "vendor_id": equipment.vendor_id,
        "name": equipment.name,
        "description": equipment.description,
        "photo": equipment.photo,
        "price_per_day": equipment.price_per_day,
        "condition": equipment.condition.value if hasattr(equipment.condition, "value") else equipment.condition,
        "avg_rating": equipment.avg_rating,
        "is_active": equipment.is_active,
        "vendor": {
            "id": vendor.id,
            "name": vendor.name,
            "email": vendor.email,
        } if vendor else None,
        "availability": availability,
    }


# ─── Pydantic models for availability management ─────────────────────────────


class AvailabilityDateAction(BaseModel):
    date: date
    is_blocked: bool


class AvailabilityRequest(BaseModel):
    dates: list[AvailabilityDateAction] = Field(..., min_length=1)


# ─── Vendor Equipment Management Endpoints ───────────────────────────────────


@router.post("/equipment", status_code=status.HTTP_201_CREATED)
async def create_equipment(
    name: str = Form(...),
    description: str = Form(...),
    price_per_day: float = Form(...),
    condition: str = Form(...),
    photo: UploadFile = File(...),
    current_user: User = Depends(require_role("pemilik_toko")),
    db: Session = Depends(get_db),
):
    """
    Create a new equipment listing with photo upload.
    Requires vendor (pemilik_toko) role.
    """
    # Validate name length
    if not name or len(name.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required",
        )
    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must be at most 100 characters",
        )

    # Validate description length
    if not description or len(description.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description is required",
        )
    if len(description) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be at most 1000 characters",
        )

    # Validate price_per_day
    if price_per_day <= 0 or price_per_day > 99_999_999.99:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price per day must be between 0.01 and 99,999,999.99",
        )

    # Validate condition
    allowed_conditions = {"new", "good", "fair"}
    if condition not in allowed_conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Condition must be 'new', 'good', or 'fair'",
        )

    # Validate photo type
    if photo.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo must be JPEG or PNG format",
        )

    # Validate photo size (read content)
    photo_content = await photo.read()
    if len(photo_content) > MAX_PHOTO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo must be at most 5 MB",
        )

    # Create equipment record first to get its ID
    equipment = Equipment(
        vendor_id=current_user.id,
        name=name.strip(),
        description=description.strip(),
        price_per_day=price_per_day,
        condition=EquipmentCondition(condition),
        is_active=True,
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    # Save photo to local filesystem
    os.makedirs(UPLOAD_DIR_EQUIPMENT, exist_ok=True)
    filename = photo.filename or "photo.jpg"
    # Sanitize filename
    safe_filename = f"{equipment.id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR_EQUIPMENT, safe_filename)

    with open(file_path, "wb") as f:
        f.write(photo_content)

    # Update equipment with photo path
    equipment.photo = file_path
    db.commit()
    db.refresh(equipment)

    return {
        "id": equipment.id,
        "vendor_id": equipment.vendor_id,
        "name": equipment.name,
        "description": equipment.description,
        "photo": equipment.photo,
        "price_per_day": equipment.price_per_day,
        "condition": equipment.condition.value if hasattr(equipment.condition, "value") else equipment.condition,
        "avg_rating": equipment.avg_rating,
        "is_active": equipment.is_active,
    }


@router.put("/equipment/{equipment_id}")
def update_equipment(
    equipment_id: int,
    update_data: EquipmentUpdate,
    current_user: User = Depends(require_role("pemilik_toko")),
    db: Session = Depends(get_db),
):
    """
    Update an equipment listing. Only the owner vendor can update.
    Requires vendor (pemilik_toko) role.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Verify ownership
    if equipment.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this equipment",
        )

    # Update fields that are provided
    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        if field == "condition" and value is not None:
            setattr(equipment, field, EquipmentCondition(value))
        else:
            setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)

    return {
        "id": equipment.id,
        "vendor_id": equipment.vendor_id,
        "name": equipment.name,
        "description": equipment.description,
        "photo": equipment.photo,
        "price_per_day": equipment.price_per_day,
        "condition": equipment.condition.value if hasattr(equipment.condition, "value") else equipment.condition,
        "avg_rating": equipment.avg_rating,
        "is_active": equipment.is_active,
    }


@router.delete("/equipment/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(require_role("pemilik_toko")),
    db: Session = Depends(get_db),
):
    """
    Delete an equipment listing. Only the owner vendor can delete.
    Cannot delete if there are active orders.
    Requires vendor (pemilik_toko) role.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Verify ownership
    if equipment.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this equipment",
        )

    # Check for active orders
    active_statuses = [OrderStatus.PENDING_PAYMENT, OrderStatus.PAID_ESCROW]
    active_order_count = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.equipment_id == equipment_id,
            Order.status.in_(active_statuses),
        )
        .count()
    )

    if active_order_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete equipment with active orders",
        )

    # Delete related availability records
    db.query(Availability).filter(Availability.equipment_id == equipment_id).delete()

    # Delete related order_items (only non-active orders should remain at this point)
    db.query(OrderItem).filter(OrderItem.equipment_id == equipment_id).delete()

    # Delete related reviews
    from campusrent.app.models import Review
    db.query(Review).filter(Review.equipment_id == equipment_id).delete()

    # Delete the equipment
    db.delete(equipment)
    db.commit()

    return {"detail": "Equipment deleted successfully"}


@router.post("/equipment/{equipment_id}/availability")
def manage_availability(
    equipment_id: int,
    request: AvailabilityRequest,
    current_user: User = Depends(require_role("pemilik_toko")),
    db: Session = Depends(get_db),
):
    """
    Manage availability (block/unblock dates) for an equipment item.
    Rejects blocking dates that have active orders.
    Requires vendor (pemilik_toko) role + ownership.
    """
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Verify ownership
    if equipment.vendor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this equipment",
        )

    # Check if any dates being blocked have active orders
    dates_to_block = [d.date for d in request.dates if d.is_blocked]

    if dates_to_block:
        active_statuses = [OrderStatus.PENDING_PAYMENT, OrderStatus.PAID_ESCROW]

        # Find order items that overlap with dates being blocked
        conflicting_items = (
            db.query(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(
                OrderItem.equipment_id == equipment_id,
                Order.status.in_(active_statuses),
            )
            .all()
        )

        # Build set of dates with active orders
        booked_dates = set()
        for item in conflicting_items:
            current = item.start_date
            while current <= item.end_date:
                booked_dates.add(current)
                current += timedelta(days=1)

        # Check for conflicts
        conflicting_dates = [d for d in dates_to_block if d in booked_dates]
        if conflicting_dates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot block dates with active orders: {[d.isoformat() for d in conflicting_dates]}",
            )

    # Process each date action
    for date_action in request.dates:
        existing = (
            db.query(Availability)
            .filter(
                Availability.equipment_id == equipment_id,
                Availability.date == date_action.date,
            )
            .first()
        )

        if existing:
            existing.is_blocked = date_action.is_blocked
        else:
            new_avail = Availability(
                equipment_id=equipment_id,
                date=date_action.date,
                is_blocked=date_action.is_blocked,
            )
            db.add(new_avail)

    db.commit()

    # Return updated availability calendar
    today = date.today()
    end_date_range = today + timedelta(days=90)

    availability_records = (
        db.query(Availability)
        .filter(
            Availability.equipment_id == equipment_id,
            Availability.date >= today,
            Availability.date <= end_date_range,
        )
        .all()
    )

    availability_calendar = [
        {
            "date": record.date.isoformat(),
            "is_blocked": record.is_blocked,
        }
        for record in availability_records
    ]

    return {
        "equipment_id": equipment_id,
        "availability": availability_calendar,
    }
