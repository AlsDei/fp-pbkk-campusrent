"""
Permits router: upload permit letters and admin verification endpoints.
"""

import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from campusrent.app.deps import get_db, get_current_user, require_role
from campusrent.app.models import Permit, PermitStatus, User, UserRole
from campusrent.app.schemas import PermitResponse, PermitListResponse, PermitVerifyRequest

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads/permits")

# Allowed file types and max size
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and extension."""
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Allowed formats: PDF, JPG, PNG",
        )
    # Check extension
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Allowed formats: PDF, JPG, PNG",
            )


@router.post("/", response_model=PermitResponse, status_code=status.HTTP_201_CREATED)
async def upload_permit(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("penyewa")),
    db: Session = Depends(get_db),
):
    """
    Upload a permit letter (surat izin kegiatan).

    - Only Penyewa role can upload.
    - Allowed formats: PDF, JPG, PNG.
    - Max file size: 5 MB.
    - If user has a previous rejected permit, it is replaced.
    """
    # Validate file type
    _validate_file(file)

    # Read file content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum of 5 MB",
        )

    # Check if user has a previous rejected permit — if so, replace it
    existing_permit = (
        db.query(Permit)
        .filter(
            Permit.user_id == current_user.id,
            Permit.status == PermitStatus.REJECTED,
        )
        .first()
    )

    if existing_permit:
        # Delete old file from disk if it exists
        old_path = existing_permit.file_path
        if old_path and os.path.exists(old_path):
            os.remove(old_path)

        # Update the existing rejected permit record
        existing_permit.status = PermitStatus.PENDING
        existing_permit.rejection_reason = None
        existing_permit.reviewed_by = None
        existing_permit.created_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_permit)
        permit = existing_permit
    else:
        # Also check if user already has a pending permit — prevent duplicates
        existing_pending = (
            db.query(Permit)
            .filter(
                Permit.user_id == current_user.id,
                Permit.status == PermitStatus.PENDING,
            )
            .first()
        )
        if existing_pending:
            # Delete old file from disk if it exists
            old_path = existing_pending.file_path
            if old_path and os.path.exists(old_path):
                os.remove(old_path)

            permit = existing_pending
            permit.created_at = datetime.utcnow()
            db.commit()
            db.refresh(permit)
        else:
            # Create new permit record (file_path will be updated after we have the ID)
            permit = Permit(
                user_id=current_user.id,
                file_path="",  # placeholder, updated below
                status=PermitStatus.PENDING,
            )
            db.add(permit)
            db.commit()
            db.refresh(permit)

    # Build file path: ./uploads/permits/{user_id}_{permit_id}_{filename}
    filename = file.filename or "permit"
    safe_filename = filename.replace(" ", "_")
    file_path = os.path.join(
        UPLOAD_DIR, f"{current_user.id}_{permit.id}_{safe_filename}"
    )

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Update permit record with actual file path
    permit.file_path = file_path
    db.commit()
    db.refresh(permit)

    return permit


@router.get("/pending", response_model=PermitListResponse)
def list_pending_permits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    List pending permits for admin review (paginated).

    Only Admin role can access this endpoint.
    """
    query = db.query(Permit).filter(Permit.status == PermitStatus.PENDING)

    total = query.count()
    offset = (page - 1) * page_size
    permits = query.order_by(Permit.created_at.desc()).offset(offset).limit(page_size).all()

    # Build response with submitter info
    items = []
    for p in permits:
        submitter = db.query(User).filter(User.id == p.user_id).first()
        items.append({
            "id": p.id,
            "user_id": p.user_id,
            "file_path": p.file_path,
            "status": p.status.value if hasattr(p.status, "value") else p.status,
            "created_at": p.created_at,
            "submitter_name": submitter.name if submitter else None,
            "submitter_email": submitter.email if submitter else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{permit_id}/verify", response_model=PermitResponse)
def verify_permit(
    permit_id: int,
    body: PermitVerifyRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Admin approves or rejects a pending permit.

    - action: "approve" or "reject"
    - rejection_reason: required when action is "reject" (1-500 chars)
    - Records reviewer ID and timestamp.
    """
    permit = db.query(Permit).filter(Permit.id == permit_id).first()
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permit not found",
        )

    if permit.status != PermitStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permit is not in pending status",
        )

    if body.action == "approve":
        permit.status = PermitStatus.APPROVED
        permit.rejection_reason = None
    elif body.action == "reject":
        permit.status = PermitStatus.REJECTED
        permit.rejection_reason = body.rejection_reason

    # Record admin decision
    permit.reviewed_by = current_user.id

    db.commit()
    db.refresh(permit)

    return permit
