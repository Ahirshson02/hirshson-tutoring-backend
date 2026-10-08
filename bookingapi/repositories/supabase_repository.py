from datetime import datetime, timezone
from typing import Optional

from supabase import Client, create_client

from ..models import Availability, User
from .base import BookingRepository

AVAILABILITIES = "availabilities"
USERS = "users"


def _to_availability(row: dict) -> Availability:
    return Availability(
        id=row["id"],
        day_of_week=row["day_of_week"],
        start_time=row["start_time"],
        is_booked=row["is_booked"],
        user_id=row.get("user_id"),
        subject=row.get("subject"),
        notes=row.get("notes"),
        wants_recurring=row.get("wants_recurring", False),
        wants_multiple_per_week=row.get("wants_multiple_per_week", False),
    )


class SupabaseBookingRepository(BookingRepository):
    def __init__(self, url: str, service_key: str):
        self._db: Client = create_client(url, service_key)

    def get_open_availabilities(self) -> list[Availability]:
        res = (
            self._db.table(AVAILABILITIES)
            .select("*")
            .eq("is_booked", False)
            .order("day_of_week")
            .order("start_time")
            .execute()
        )
        return [_to_availability(r) for r in res.data]

    def claim_availability(self, availability_id: str, details: dict) -> Optional[Availability]:
        # Atomic in Postgres: locks the slot + neighbors, checks them, blocks neighbors, claims the slot.
        res = self._db.rpc(
            "claim_availability",
            {
                "p_id": availability_id,
                "p_subject": details["subject"],
                "p_notes": details.get("notes"),
                "p_wants_recurring": details["wants_recurring"],
                "p_wants_multiple": details["wants_multiple_per_week"],
            },
        ).execute()
        return _to_availability(res.data[0]) if res.data else None

    def release_availability(self, availability_id: str) -> None:
        self._db.rpc("release_availability", {"p_id": availability_id}).execute()

    def upsert_user(self, guardian_name: str, student_name: str, email: str, phone: Optional[str]) -> User:
        res = (
            self._db.table(USERS)
            .upsert(
                {"guardian_name": guardian_name, "student_name": student_name, "email": email, "phone": phone},
                on_conflict="email,student_name",
            )
            .execute()
        )
        row = res.data[0]
        return User(row["id"], row["guardian_name"], row["student_name"], row["email"], row.get("phone"))

    def attach_user(self, availability_id: str, user_id: str) -> None:
        self._db.table(AVAILABILITIES).update({"user_id": user_id}).eq("id", availability_id).execute()
