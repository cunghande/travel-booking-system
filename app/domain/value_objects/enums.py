# ============================================================
# Travel Booking System — Domain Value Objects / Enums
# ============================================================

from __future__ import annotations

import enum


class RoleName(str, enum.Enum):
    """System roles for RBAC."""
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"


class TourStatus(str, enum.Enum):
    """Lifecycle status of a tour."""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class BookingStatus(str, enum.Enum):
    """Lifecycle status of a booking (for future use)."""
    DRAFT = "DRAFT"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, enum.Enum):
    """Payment transaction status (for future use)."""
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class AuditAction(str, enum.Enum):
    """Auditable actions."""
    USER_REGISTERED = "USER_REGISTERED"
    USER_LOGIN = "USER_LOGIN"
    USER_UPDATED = "USER_UPDATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REMOVED = "ROLE_REMOVED"
    TOUR_CREATED = "TOUR_CREATED"
    TOUR_UPDATED = "TOUR_UPDATED"
    TOUR_DELETED = "TOUR_DELETED"
    TOUR_PUBLISHED = "TOUR_PUBLISHED"
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    PAYMENT_CREATED = "PAYMENT_CREATED"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUND_APPROVED = "REFUND_APPROVED"
