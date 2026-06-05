"""Admin router: blacklist users and issue cancellation fines."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from campusrent.app.deps import get_db, require_role
from campusrent.app.models import User, UserStatus, UserRole, Order, OrderStatus
from campusrent.app.schemas import BlacklistRequest, FineRequest

router = APIRouter()


@router.post("/users/{user_id}/blacklist")
def blacklist_user(
    user_id: int,
    body: BlacklistRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """
    Blacklist a user by ID. Requires Admin role.

    - Find user by ID, return 404 if not found.
    - Cannot blacklist another admin (return 400).
    - Update user status to BLACKLISTED.
    - Return the updated user info.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot blacklist an admin user",
        )

    user.status = UserStatus.BLACKLISTED
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "status": user.status.value if hasattr(user.status, "value") else user.status,
        "name": user.name,
        "phone": user.phone,
        "reason": body.reason,
    }


@router.post("/orders/{order_id}/fine")
def issue_fine(
    order_id: int,
    body: FineRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """
    Issue a cancellation fine for an order. Requires Admin role.

    - Find order by ID, return 404 if not found.
    - Validate order status is CANCELLED_PENDING_FINE (return 400 if not).
    - Validate fine amount: must be between 0.01 and order.total_amount (return 400 if invalid).
    - Update order status to CANCELLED_FINED.
    - Return the updated order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != OrderStatus.CANCELLED_PENDING_FINE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not eligible for fine assessment",
        )

    if body.amount < 0.01 or body.amount > order.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fine amount must be between 0.01 and {order.total_amount}",
        )

    order.status = OrderStatus.CANCELLED_FINED
    db.commit()
    db.refresh(order)

    return {
        "id": order.id,
        "renter_id": order.renter_id,
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "total_amount": order.total_amount,
        "fine_amount": body.amount,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }
