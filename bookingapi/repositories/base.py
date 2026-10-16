from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ..models import Availability, User


class BookingRepository(ABC):
    """Storage contract. To change databases, implement this class and swap it in create_app()."""

    @abstractmethod
    def get_open_availabilities(self) -> list[Availability]:
        """All slots that are not booked, ordered by day then time."""

    @abstractmethod
    def claim_availability(self, availability_id: str, details: dict) -> Optional[Availability]:
        """Atomically mark an unbooked slot as booked and store `details` on it.

        Must return None if the slot does not exist or is already booked.
        details keys: subject, notes, wants_recurring, wants_multiple_per_week
        """

    @abstractmethod
    def release_availability(self, availability_id: str) -> None:
        """Undo a claim (used to roll back a failed booking)."""

    @abstractmethod
    def upsert_user(self, guardian_name: str, student_name: str, email: str, phone: Optional[str]) -> User:
        """Create the user, or update the existing one matched on (email, student_name)."""

    @abstractmethod
    def attach_user(self, availability_id: str, user_id: str) -> None:
        """Link a claimed slot to its user."""
        
    @abstractmethod
    def get_unnotified_bookings(self, older_than: datetime) -> list[dict]: ...

    @abstractmethod
    def mark_notified(self, slot_ids: list[str]) -> None: ...