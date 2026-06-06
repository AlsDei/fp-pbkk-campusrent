"""Seed the database with sample data for development/testing."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from campusrent.app.database import engine, Base, SessionLocal
from campusrent.app.models import (
    User, UserRole, UserStatus, Equipment, EquipmentCondition,
    Order, OrderItem, OrderStatus, Permit, PermitStatus, Review,
)
from campusrent.app.auth import hash_password
from datetime import datetime, date, timedelta
import random

def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Check if data already exists
    if db.query(User).first():
        print("Database already has data. Skipping seed.")
        db.close()
        return

    print("Seeding database...")

    # ─── Users ────────────────────────────────────────────────────────────────

    password_hash = hash_password("password123")

    admin = User(
        email="admin@campusrent.com",
        password_hash=password_hash,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        name="Admin CampusRent",
        phone="081234567890",
    )

    vendor1 = User(
        email="vendor1@campusrent.com",
        password_hash=password_hash,
        role=UserRole.PEMILIK_TOKO,
        status=UserStatus.ACTIVE,
        name="Toko Elektronik Jaya",
        phone="081234567891",
    )

    vendor2 = User(
        email="vendor2@campusrent.com",
        password_hash=password_hash,
        role=UserRole.PEMILIK_TOKO,
        status=UserStatus.ACTIVE,
        name="Rental Alat Teknik",
        phone="081234567892",
    )

    renter1 = User(
        email="renter1@campusrent.com",
        password_hash=password_hash,
        role=UserRole.PENYEWA,
        status=UserStatus.ACTIVE,
        name="Budi Santoso",
        phone="081234567893",
    )

    renter2 = User(
        email="renter2@campusrent.com",
        password_hash=password_hash,
        role=UserRole.PENYEWA,
        status=UserStatus.ACTIVE,
        name="Sari Dewi",
        phone="081234567894",
    )

    db.add_all([admin, vendor1, vendor2, renter1, renter2])
    db.commit()
    db.refresh(admin)
    db.refresh(vendor1)
    db.refresh(vendor2)
    db.refresh(renter1)
    db.refresh(renter2)

    print(f"  Created users: admin, vendor1, vendor2, renter1, renter2")

    # ─── Equipment ────────────────────────────────────────────────────────────

    equipment_data = [
        ("Projector Epson EB-X51", "Projector LCD 3800 lumens, cocok untuk presentasi dan acara kampus.", 75000, EquipmentCondition.GOOD, vendor1.id),
        ("Speaker JBL PartyBox 310", "Speaker portable bluetooth 240W, bass kuat untuk acara outdoor.", 150000, EquipmentCondition.NEW, vendor1.id),
        ("Kamera Canon EOS M50", "Mirrorless camera 24.1MP, lengkap dengan lensa kit 15-45mm.", 200000, EquipmentCondition.GOOD, vendor1.id),
        ("Laptop ASUS ROG Strix", "Gaming laptop i7, RTX 3060, 16GB RAM. Cocok untuk rendering/editing.", 250000, EquipmentCondition.GOOD, vendor1.id),
        ("Drone DJI Mini 3", "Drone ringan dengan kamera 4K, flight time 38 menit.", 300000, EquipmentCondition.NEW, vendor2.id),
        ("Tripod Takara ECO-196A", "Tripod aluminium tinggi 1.5m, cocok untuk kamera dan HP.", 25000, EquipmentCondition.FAIR, vendor2.id),
        ("Mic Wireless Boya BY-WM4", "Wireless lavalier microphone, jarak 50m, cocok untuk vlog/podcast.", 50000, EquipmentCondition.GOOD, vendor2.id),
        ("Ring Light 18 inch", "LED ring light dengan stand, 3 mode warna, remote control.", 45000, EquipmentCondition.NEW, vendor2.id),
        ("Tenda Camping 4 Orang", "Tenda dome waterproof untuk 4 orang, mudah dipasang.", 80000, EquipmentCondition.GOOD, vendor2.id),
        ("Sound System Portable", "Sound system 500W dengan 2 mic wireless, cocok untuk seminar.", 200000, EquipmentCondition.FAIR, vendor1.id),
        ("GoPro Hero 11", "Action camera 5.3K, waterproof 10m, HyperSmooth 5.0.", 175000, EquipmentCondition.NEW, vendor1.id),
        ("Whiteboard Portable 120x90", "Whiteboard magnetic dengan stand roda, include spidol & penghapus.", 35000, EquipmentCondition.FAIR, vendor2.id),
    ]

    equipment_list = []
    for name, desc, price, condition, vendor_id in equipment_data:
        eq = Equipment(
            vendor_id=vendor_id,
            name=name,
            description=desc,
            price_per_day=price,
            condition=condition,
            avg_rating=round(random.uniform(3.5, 5.0), 1),
            is_active=True,
        )
        equipment_list.append(eq)

    db.add_all(equipment_list)
    db.commit()
    for eq in equipment_list:
        db.refresh(eq)

    print(f"  Created {len(equipment_list)} equipment items")

    # ─── Permits ──────────────────────────────────────────────────────────────

    permit1 = Permit(
        user_id=renter1.id,
        file_path="./uploads/permits/sample_permit_1.pdf",
        status=PermitStatus.APPROVED,
        reviewed_by=admin.id,
    )

    permit2 = Permit(
        user_id=renter2.id,
        file_path="./uploads/permits/sample_permit_2.pdf",
        status=PermitStatus.APPROVED,
        reviewed_by=admin.id,
    )

    db.add_all([permit1, permit2])
    db.commit()
    db.refresh(permit1)
    db.refresh(permit2)

    print(f"  Created 2 approved permits")

    # ─── Orders ───────────────────────────────────────────────────────────────

    today = date.today()

    # Completed order for renter1
    order1 = Order(
        renter_id=renter1.id,
        status=OrderStatus.COMPLETED,
        total_amount=450000,
        permit_id=permit1.id,
        created_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(order1)
    db.commit()
    db.refresh(order1)

    order1_item1 = OrderItem(
        order_id=order1.id,
        equipment_id=equipment_list[0].id,  # Projector
        quantity=1,
        start_date=today - timedelta(days=8),
        end_date=today - timedelta(days=5),
        subtotal=225000,
    )
    order1_item2 = OrderItem(
        order_id=order1.id,
        equipment_id=equipment_list[1].id,  # Speaker
        quantity=1,
        start_date=today - timedelta(days=8),
        end_date=today - timedelta(days=7),
        subtotal=225000,
    )
    db.add_all([order1_item1, order1_item2])

    # Pending payment order for renter2
    order2 = Order(
        renter_id=renter2.id,
        status=OrderStatus.PENDING_PAYMENT,
        total_amount=600000,
        permit_id=permit2.id,
        created_at=datetime.utcnow() - timedelta(hours=2),
    )
    db.add(order2)
    db.commit()
    db.refresh(order2)

    order2_item = OrderItem(
        order_id=order2.id,
        equipment_id=equipment_list[4].id,  # Drone
        quantity=1,
        start_date=today + timedelta(days=3),
        end_date=today + timedelta(days=4),
        subtotal=600000,
    )
    db.add(order2_item)

    # Paid escrow order for renter1
    order3 = Order(
        renter_id=renter1.id,
        status=OrderStatus.PAID_ESCROW,
        total_amount=200000,
        permit_id=permit1.id,
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(order3)
    db.commit()
    db.refresh(order3)

    order3_item = OrderItem(
        order_id=order3.id,
        equipment_id=equipment_list[2].id,  # Camera
        quantity=1,
        start_date=today + timedelta(days=1),
        end_date=today + timedelta(days=1),
        subtotal=200000,
    )
    db.add(order3_item)

    db.commit()
    print(f"  Created 3 orders with items")

    # ─── Reviews ──────────────────────────────────────────────────────────────

    review1 = Review(
        order_id=order1.id,
        equipment_id=equipment_list[0].id,
        rating=5,
        comment="Projector sangat terang dan mudah digunakan. Recommended!",
    )
    review2 = Review(
        order_id=order1.id,
        equipment_id=equipment_list[1].id,
        rating=4,
        comment="Speaker bass-nya mantap, cuma agak berat dibawa.",
    )

    db.add_all([review1, review2])
    db.commit()

    print(f"  Created 2 reviews")

    # ─── Summary ──────────────────────────────────────────────────────────────

    print("\n✅ Seed complete!\n")
    print("=" * 50)
    print("ACCOUNTS (all passwords: password123)")
    print("=" * 50)
    print(f"  Admin:   admin@campusrent.com")
    print(f"  Vendor:  vendor1@campusrent.com")
    print(f"  Vendor:  vendor2@campusrent.com")
    print(f"  Renter:  renter1@campusrent.com")
    print(f"  Renter:  renter2@campusrent.com")
    print("=" * 50)

    db.close()


if __name__ == "__main__":
    seed()
