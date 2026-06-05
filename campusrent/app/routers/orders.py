"""Orders router: order placement, payment, cancellation, and vendor delivery."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from campusrent.app.deps import get_db, get_current_user, require_role
from campusrent.app.models import (
    Order, OrderItem, OrderStatus, Equipment, Availability,
    Permit, PermitStatus, User,
)
from campusrent.app.schemas import (
    OrderCreate, OrderResponse, OrderItemResponse, PaymentRequest,
    VendorOrderResponse, VendorOrderListResponse,
)

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("penyewa")),
):
    """
    Place a new order. Requires penyewa role and an approved permit.

    Validates:
    - User has an approved permit
    - All equipment items exist and are active
    - Dates are not in the past
    - Items are available for requested date ranges (no blocked dates, no overlapping bookings)

    Calculates subtotals and creates the order with status pending_payment.
    """

    # 1. Verify user has an approved permit
    permit = (
        db.query(Permit)
        .filter(
            Permit.user_id == current_user.id,
            Permit.status == PermitStatus.APPROVED,
        )
        .first()
    )
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must have an approved permit to place an order",
        )

    today = date.today()
    total_amount = 0.0
    order_items_data = []

    # 2. Validate each item
    for item in order_data.items:
        # 2a. Verify equipment exists and is active
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == item.equipment_id, Equipment.is_active == True)
            .first()
        )
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Equipment with id {item.equipment_id} not found or inactive",
            )

        # 2b. Verify start_date is not in the past
        if item.start_date < today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"start_date for equipment {item.equipment_id} cannot be in the past",
            )

        # 2c. Check Availability table for blocked dates in [start_date, end_date]
        blocked_dates = (
            db.query(Availability)
            .filter(
                Availability.equipment_id == item.equipment_id,
                Availability.is_blocked == True,
                Availability.date >= item.start_date,
                Availability.date <= item.end_date,
            )
            .first()
        )
        if blocked_dates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Equipment {item.equipment_id} has blocked dates in the requested range",
            )

        # 2d. Check OrderItem table for overlapping bookings with active orders
        active_statuses = [OrderStatus.PENDING_PAYMENT, OrderStatus.PAID_ESCROW]
        overlapping_booking = (
            db.query(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(
                OrderItem.equipment_id == item.equipment_id,
                Order.status.in_(active_statuses),
                OrderItem.start_date <= item.end_date,
                OrderItem.end_date >= item.start_date,
            )
            .first()
        )
        if overlapping_booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Equipment {item.equipment_id} is already booked for the requested dates",
            )

        # 3. Calculate subtotal: price_per_day × (end_date - start_date + 1) × quantity
        num_days = (item.end_date - item.start_date).days + 1
        subtotal = equipment.price_per_day * num_days * item.quantity
        total_amount += subtotal

        order_items_data.append({
            "equipment_id": item.equipment_id,
            "quantity": item.quantity,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "subtotal": subtotal,
        })

    # 4. Create the order
    new_order = Order(
        renter_id=current_user.id,
        status=OrderStatus.PENDING_PAYMENT,
        total_amount=total_amount,
        permit_id=permit.id,
    )
    db.add(new_order)
    db.flush()  # Get the order ID

    # 5. Create order items
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=new_order.id,
            **item_data,
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)

    return new_order


@router.post("/{order_id}/pay", response_model=OrderResponse)
def pay_order(
    order_id: int,
    payment: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("penyewa")),
):
    """
    Pay for an order. Simulates payment by checking the amount matches the total
    and flipping status from pending_payment to paid_escrow.

    Validates:
    - Order exists (404 if not)
    - Order belongs to the current user (403 if not)
    - Order is in pending_payment status (400 if not)
    - Payment amount exactly matches order total_amount (400 if not)
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to pay for this order",
        )

    if order.status != OrderStatus.PENDING_PAYMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not eligible for payment",
        )

    if payment.amount != order.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount must equal order total of {order.total_amount}",
        )

    order.status = OrderStatus.PAID_ESCROW
    db.commit()
    db.refresh(order)

    return order


@router.get("/", response_model=list[OrderResponse])
def get_order_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("penyewa")),
):
    """
    Get the current penyewa's order history, paginated and sorted by date descending.

    Before returning, auto-cancels any pending_payment orders that are older than 24 hours.
    """
    # Fetch all orders for the current user
    orders = db.query(Order).filter(Order.renter_id == current_user.id).all()

    # Auto-cancel expired pending_payment orders (older than 24 hours)
    now = datetime.now(timezone.utc)
    for order in orders:
        if order.status == OrderStatus.PENDING_PAYMENT:
            created = order.created_at
            # Handle timezone-naive datetimes (e.g., from SQLite)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created < now - timedelta(hours=24):
                order.status = OrderStatus.CANCELLED
    db.commit()

    # Re-query with pagination and sorting
    query = (
        db.query(Order)
        .filter(Order.renter_id == current_user.id)
        .order_by(Order.created_at.desc())
    )

    offset = (page - 1) * page_size
    orders_page = query.offset(offset).limit(page_size).all()

    return orders_page


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("penyewa")),
):
    """
    Cancel an order. Only the penyewa who owns the order can cancel it.

    Cancellation logic:
    - Only orders with status pending_payment or paid_escrow can be cancelled.
    - Find the earliest start_date among order items.
    - If days_until_start < 1 (less than 24 hours): status = CANCELLED_PENDING_FINE
    - Else: status = CANCELLED
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to cancel this order",
        )

    cancellable_statuses = [OrderStatus.PENDING_PAYMENT, OrderStatus.PAID_ESCROW]
    if order.status not in cancellable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be cancelled in its current status",
        )

    # Find earliest start_date among order items
    earliest_start = (
        db.query(func.min(OrderItem.start_date))
        .filter(OrderItem.order_id == order.id)
        .scalar()
    )

    today = date.today()
    days_until_start = (earliest_start - today).days

    if days_until_start < 1:
        order.status = OrderStatus.CANCELLED_PENDING_FINE
    else:
        order.status = OrderStatus.CANCELLED

    db.commit()
    db.refresh(order)

    return order


@router.get("/orders", response_model=VendorOrderListResponse)
def get_vendor_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pemilik_toko")),
):
    """
    Get incoming orders for the vendor's equipment. Paginated, sorted by date descending.

    Accessible at /vendor/orders via the vendor prefix.
    Conditionally includes renter contact info only for paid_escrow or completed orders.
    """
    # Find order IDs that have items belonging to vendor's equipment
    order_ids_query = (
        db.query(OrderItem.order_id)
        .filter(OrderItem.equipment_id.in_(db.query(Equipment.id).filter(Equipment.vendor_id == current_user.id)))
        .distinct()
    )

    # Count total
    total = order_ids_query.count()

    # Get paginated order IDs sorted by date descending
    offset = (page - 1) * page_size
    order_ids = (
        db.query(Order.id)
        .filter(Order.id.in_(order_ids_query))
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    order_id_list = [oid[0] for oid in order_ids]

    # Fetch full order objects with relationships
    orders = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.renter))
        .filter(Order.id.in_(order_id_list))
        .order_by(Order.created_at.desc())
        .all()
    )

    # Build response with conditional renter contact info
    result_items = []
    for order in orders:
        # Conditionally include renter contact info
        if order.status in [OrderStatus.PAID_ESCROW, OrderStatus.COMPLETED]:
            renter_name = order.renter.name
            renter_email = order.renter.email
            renter_phone = order.renter.phone
        else:
            renter_name = None
            renter_email = None
            renter_phone = None

        vendor_order = VendorOrderResponse(
            id=order.id,
            renter_id=order.renter_id,
            status=order.status.value if hasattr(order.status, 'value') else order.status,
            total_amount=order.total_amount,
            created_at=order.created_at,
            permit_id=order.permit_id,
            items=[
                OrderItemResponse(
                    id=item.id,
                    equipment_id=item.equipment_id,
                    quantity=item.quantity,
                    start_date=item.start_date,
                    end_date=item.end_date,
                    subtotal=item.subtotal,
                )
                for item in order.items
            ],
            renter_name=renter_name,
            renter_email=renter_email,
            renter_phone=renter_phone,
        )
        result_items.append(vendor_order)

    return VendorOrderListResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/orders/{order_id}/deliver", response_model=OrderResponse)
def deliver_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pemilik_toko")),
):
    """
    Vendor confirms delivery for an order. Updates status to 'completed'.
    This acts as the escrow release (status update only, no money movement).

    Validates:
    - Order exists
    - Order has items belonging to vendor's equipment
    - Order is in paid_escrow status
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Verify that order has items belonging to vendor's equipment
    vendor_item = (
        db.query(OrderItem)
        .join(Equipment, OrderItem.equipment_id == Equipment.id)
        .filter(
            OrderItem.order_id == order.id,
            Equipment.vendor_id == current_user.id,
        )
        .first()
    )
    if not vendor_item:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to deliver this order",
        )

    if order.status != OrderStatus.PAID_ESCROW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be in paid_escrow status to confirm delivery",
        )

    order.status = OrderStatus.COMPLETED
    db.commit()
    db.refresh(order)

    return order
