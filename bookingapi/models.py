from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: str
    guardian_name: str
    student_name: str
    email: str
    phone: Optional[str] = None


@dataclass
class Availability:
    """A weekly recurring slot, e.g. day_of_week=0, start_time='17:00:00' = every Monday 5pm."""

    id: str
    day_of_week: int  # 0 = Monday ... 6 = Sunday
    start_time: str  # 'HH:MM:SS'
    is_booked: bool = False
    user_id: Optional[str] = None
    subject: Optional[str] = None
    notes: Optional[str] = None
    wants_recurring: bool = False
    wants_multiple_per_week: bool = False
