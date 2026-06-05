from enum import Enum as PyEnum
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship

from campusrent.app.database import Base


# --- Enumerations ---

class UserRole(str, PyEnum):
    PENYEWA = "penyewa"
    PEMILIK_TOKO = "pemilik_toko"
    ADMIN = "admin"


class UserStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class EquipmentCondition(str, PyEnum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"


class OrderStatus(str, PyEnum):
    PENDING_PAYMENT = "pending_payment"
    PAID_ESCROW = "paid_escrow"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CANCELLED_PENDING_FINE = "cancelled_pending_fine"
    CANCELLED_FINED = "cancelled_fined"


class PermitStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# --- ORM Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    equipment = relationship("Equipment", back_populates="vendor")
    orders = relationship("Order", back_populates="renter", foreign_keys="Order.renter_id")
    permits = relationship("Permit", back_populates="user", foreign_keys="Permit.user_id")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    price_per_day = Column(Float, nullable=False)
    condition = Column(Enum(EquipmentCondition), nullable=False)
    avg_rating = Column(Float, nullable=True, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    vendor = relationship("User", back_populates="equipment")
    availability = relationship("Availability", back_populates="equipment")
    order_items = relationship("OrderItem", back_populates="equipment")
    reviews = relationship("Review", back_populates="equipment")


class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    date = Column(Date, nullable=False)
    is_blocked = Column(Boolean, nullable=False, default=False)

    # Relationships
    equipment = relationship("Equipment", back_populates="availability")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    renter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING_PAYMENT)
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    permit_id = Column(Integer, ForeignKey("permits.id"), nullable=True)

    # Relationships
    renter = relationship("User", back_populates="orders", foreign_keys=[renter_id])
    items = relationship("OrderItem", back_populates="order")
    permit = relationship("Permit", back_populates="orders")
    reviews = relationship("Review", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    equipment = relationship("Equipment", back_populates="order_items")


class Permit(Base):
    __tablename__ = "permits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(Enum(PermitStatus), nullable=False, default=PermitStatus.PENDING)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="permits", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    orders = relationship("Order", back_populates="permit")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="reviews")
    equipment = relationship("Equipment", back_populates="reviews")
