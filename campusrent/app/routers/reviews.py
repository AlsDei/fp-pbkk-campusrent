"""Reviews router: rating and review submission for completed orders."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from campusrent.app.deps import get_db, require_role
from campusrent.app.models import Review, Order, OrderStatus, Equipment, User, OrderItem
from campusrent.app.schemas import ReviewCreate, ReviewResponse

router = APIRouter()


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("penyewa")),
):
    """
    Submit a rating (1-5) and optional comment for a completed order.

    Validations:
    1. Order must exist and have status COMPLETED
    2. Order must belong to the current user
    3. Equipment must be part of the order's items
    4. No duplicate review for the same order_id + equipment_id
    """
    # 1. Order must exist and be completed
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order not found",
        )
    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be completed before rating",
        )

    # 2. Order must belong to the current user
    if order.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order does not belong to you",
        )

    # 3. Equipment must be in the order's items
    order_item = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id == payload.order_id,
            OrderItem.equipment_id == payload.equipment_id,
        )
        .first()
    )
    if not order_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment not found in this order",
        )

    # 4. No duplicate review for this order + equipment
    existing_review = (
        db.query(Review)
        .filter(
            Review.order_id == payload.order_id,
            Review.equipment_id == payload.equipment_id,
        )
        .first()
    )
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A review already exists for this order and equipment",
        )

    # Create the review
    review = Review(
        order_id=payload.order_id,
        equipment_id=payload.equipment_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.flush()

    # Recalculate equipment avg_rating
    equipment = db.query(Equipment).filter(Equipment.id == payload.equipment_id).first()
    reviews = db.query(Review).filter(Review.equipment_id == payload.equipment_id).all()
    avg = round(sum(r.rating for r in reviews) / len(reviews), 1)
    equipment.avg_rating = avg

    db.commit()
    db.refresh(review)

    return review
