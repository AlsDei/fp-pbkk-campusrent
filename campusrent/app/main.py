import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from campusrent.app.database import Base, engine
from campusrent.app.routers import admin, auth, equipment, orders, permits, reviews

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads/permits")

app = FastAPI(
    title="CampusRent API",
    description="REST API for CampusRent campus equipment rental marketplace",
)

# CORS middleware — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# Register routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(equipment.router, prefix="/equipment", tags=["equipment"])
app.include_router(orders.router, prefix="/vendor", tags=["vendor"])
app.include_router(permits.router, prefix="/permits", tags=["permits"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])


# Startup: create tables and upload directory
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
