import logging
import re
import uuid
from typing import Optional

from .. import messages
from ..config import SUBJECTS
from ..errors import BookingError
from ..models import Availability, User
from ..repositories.base import BookingRepository
from .notification_service import NotificationService

log = logging.getLogger(__name__)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+()\-.\s]{7,30}$")


def format_time(start_time: str) -> str:
    hour, minute = (int(p) for p in start_time.split(":")[:2])
    suffix = "AM" if hour < 12 else "PM"
    return f"{hour % 12 or 12}:{minute:02d} {suffix}"


class BookingService:
    def __init__(self, repo: BookingRepository, notifier: NotificationService):
        self._repo = repo
        self._notifier = notifier

    # ---- reads -------------------------------------------------------
    def get_availabilities(self) -> list[dict]:
        """Open weekly slots grouped by day: [{day, slots: [{id, day, time}]}]."""
        grouped: dict[int, list[dict]] = {}
        for slot in self._repo.get_open_availabilities():
            day = DAYS[slot.day_of_week]
            grouped.setdefault(slot.day_of_week, []).append(
                {"id": slot.id, "day": day, "time": format_time(slot.start_time)}
            )
        
        return [{"day": DAYS[d], "slots": slots} for d, slots in sorted(grouped.items())]

    # ---- writes ------------------------------------------------------
    def create_booking(self, payload) -> dict:
        data = self._validate(payload)
        
        claimed = self._repo.claim_availability(
            data["slot_id"],
            {
                "subject": data["subject"],
                "notes": data["notes"],
                "wants_recurring": data["wants_recurring"],
                "wants_multiple_per_week": data["wants_multiple_per_week"],
            },
        )
        if claimed is None:
            raise BookingError(messages.SLOT_TAKEN, 409)

        try:
            user = self._repo.upsert_user(data["guardian_name"], data["student_name"], data["email"], data["phone"])
            self._repo.attach_user(claimed.id, user.id)
        except Exception:
            log.exception("Booking failed after claiming slot %s; releasing it", claimed.id)
            self._repo.release_availability(claimed.id)
            raise

        booking = self._to_booking(claimed, user)
        try:
            self._notifier.booking_created(booking)
        except Exception:
            log.exception("Notification failed for booking %s", claimed.id)
        return booking

    # ---- helpers -----------------------------------------------------
    @staticmethod
    def _to_booking(slot: Availability, user: User) -> dict:
        return {
            "bookingId": slot.id,
            "day": DAYS[slot.day_of_week],
            "time": format_time(slot.start_time),
            "guardianName": user.guardian_name,
            "studentName": user.student_name,
            "email": user.email,
            "phone": user.phone,
            "subject": slot.subject,
            "notes": slot.notes,
            "wantsRecurring": slot.wants_recurring,
            "wantsMultiplePerWeek": slot.wants_multiple_per_week,
        }

    @staticmethod
    def _validate(payload) -> dict:
        if not isinstance(payload, dict):
            raise BookingError(messages.INVALID_REQUEST)

        def text(key: str, max_len: int) -> str:
            value = payload.get(key)
            value = value.strip() if isinstance(value, str) else ""
            if len(value) > max_len:
                raise BookingError(messages.FIELD_TOO_LONG)
            return value

        try:
            slot_id = str(uuid.UUID(str(payload.get("slotId"))))
        except ValueError:
            raise BookingError(messages.SLOT_INVALID)

        guardian = text("guardianName", 100)
        if not guardian:
            raise BookingError(messages.GUARDIAN_NAME_REQUIRED)
        student = text("studentName", 100)
        if not student:
            raise BookingError(messages.STUDENT_NAME_REQUIRED)
        email = text("email", 254).lower()
        if not EMAIL_RE.match(email):
            raise BookingError(messages.EMAIL_INVALID)
        phone: Optional[str] = text("phone", 30) or None
        if phone and not PHONE_RE.match(phone):
            raise BookingError(messages.PHONE_INVALID)
        subject = text("subject", 100)
        if subject not in SUBJECTS:
            raise BookingError(messages.SUBJECT_INVALID)
        notes: Optional[str] = text("notes", 1000) or None

        flags = {}
        for key in ("wantsRecurring", "wantsMultiplePerWeek"):
            value = payload.get(key, False)
            if not isinstance(value, bool):
                raise BookingError(messages.INVALID_REQUEST)
            flags[key] = value

        return {
            "slot_id": slot_id,
            "guardian_name": guardian,
            "student_name": student,
            "email": email,
            "phone": phone,
            "subject": subject,
            "notes": notes,
            "wants_recurring": flags["wantsRecurring"],
            "wants_multiple_per_week": flags["wantsMultiplePerWeek"],
        }
