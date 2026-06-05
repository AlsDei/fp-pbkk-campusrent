"""Pydantic request/response schemas for CampusRent API."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ─── Registration Schemas ────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"penyewa", "pemilik_toko"}
        if v not in allowed:
            raise ValueError("Role must be 'penyewa' or 'pemilik_toko'")
        return v


class RegisterResponse(BaseModel):
    id: int
    email: str
    role: str

    model_config = {"from_attributes": True}


# ─── Login Schemas ───────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Equipment Schemas ───────────────────────────────────────────────────────


class EquipmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    price_per_day: float = Field(..., gt=0, le=99_999_999.99)
    condition: str

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        allowed = {"new", "good", "fair"}
        if v not in allowed:
            raise ValueError("Condition must be 'new', 'good', or 'fair'")
        return v


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price_per_day: Optional[float] = Field(None, gt=0, le=99_999_999.99)
    condition: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"new", "good", "fair"}
            if v not in allowed:
                raise ValueError("Condition must be 'new', 'good', or 'fair'")
        return v


class EquipmentResponse(BaseModel):
    id: int
    vendor_id: int
    name: str
    description: Optional[str] = None
    photo: Optional[str] = None
    price_per_day: float
    condition: str
    avg_rating: Optional[float] = None
    is_active: bool

    model_config = {"from_attributes": True}


class EquipmentListResponse(BaseModel):
    items: list[EquipmentResponse]
    total: int
    page: int
    page_size: int


# ─── Order Schemas ───────────────────────────────────────────────────────────


class OrderItemCreate(BaseModel):
    equipment_id: int
    quantity: int = Field(..., ge=1, le=10)
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    id: int
    equipment_id: int
    quantity: int
    start_date: date
    end_date: date
    subtotal: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    renter_id: int
    status: str
    total_amount: float
    created_at: datetime
    permit_id: Optional[int] = None
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int


class VendorOrderResponse(BaseModel):
    id: int
    renter_id: int
    status: str
    total_amount: float
    created_at: datetime
    permit_id: Optional[int] = None
    items: list[OrderItemResponse] = []
    renter_name: Optional[str] = None
    renter_email: Optional[str] = None
    renter_phone: Optional[str] = None

    model_config = {"from_attributes": True}


class VendorOrderListResponse(BaseModel):
    items: list[VendorOrderResponse]
    total: int
    page: int
    page_size: int


class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)


# ─── Permit Schemas ──────────────────────────────────────────────────────────


class PermitResponse(BaseModel):
    id: int
    user_id: int
    file_path: str
    status: str
    reviewed_by: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PermitListItem(BaseModel):
    id: int
    user_id: int
    file_path: str
    status: str
    created_at: Optional[datetime] = None
    submitter_name: Optional[str] = None
    submitter_email: Optional[str] = None


class PermitListResponse(BaseModel):
    items: list[PermitListItem]
    total: int
    page: int
    page_size: int


class PermitVerifyRequest(BaseModel):
    action: str
    rejection_reason: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"approve", "reject"}
        if v not in allowed:
            raise ValueError("Action must be 'approve' or 'reject'")
        return v

    @model_validator(mode="after")
    def validate_rejection_reason(self):
        if self.action == "reject":
            if not self.rejection_reason or len(self.rejection_reason.strip()) == 0:
                raise ValueError(
                    "rejection_reason is required when action is 'reject'"
                )
            if len(self.rejection_reason) > 500:
                raise ValueError(
                    "rejection_reason must be at most 500 characters"
                )
        return self


# ─── Review Schemas ──────────────────────────────────────────────────────────


class ReviewCreate(BaseModel):
    order_id: int
    equipment_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    order_id: int
    equipment_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Admin Schemas ───────────────────────────────────────────────────────────


class BlacklistRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class FineRequest(BaseModel):
    amount: float = Field(..., gt=0)
