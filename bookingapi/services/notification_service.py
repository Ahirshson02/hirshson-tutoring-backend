"""
NOTIFICATIONS: PLUG-IN POINT
----------------------------
BookingService calls `notifier.booking_created(booking)` after every successful
booking. Today that does nothing but log. To add email and/or SMS:

  1. Subclass NotificationService below (e.g. EmailNotificationService,
     SmsNotificationService, or one class that does both).
  2. Swap it in where `notifier = ...` is created in bookingapi/__init__.py.

`booking` is the same dict returned to the client (day, time, guardianName,
studentName, email, phone, subject, notes, ...). Exceptions raised here are
caught and logged by BookingService, so a failed email never fails a booking.
"""
import base64
import logging
import os
from email.message import EmailMessage

from googleapiclient.discovery import build

from .google_auth import get_google_credentials
import logging
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class NotificationService(ABC):
    @abstractmethod
    def booking_created(self, booking: dict) -> None:
        """Send whatever notifications a new booking should trigger."""


class NoOpNotificationService(NotificationService):
    def booking_created(self, booking: dict) -> None:
        log.info("New booking (no notifier configured): %s %s", booking["day"], booking["time"])


def _clean(value) -> str:
    """Single-line, safe-for-headers version of user input."""
    return " ".join(str(value or "").split())


class GmailNotificationService(NotificationService):
    def __init__(self, sender: str, recipient: str):
        self.sender = sender
        self.recipient = recipient
        self._gmail = build(
            "gmail", "v1",
            credentials=get_google_credentials(),
            cache_discovery=False,
        )

    @classmethod
    def from_env(cls):
        return cls(os.environ["GMAIL_SELF"], os.environ["GMAIL_SELF"])

    def booking_created(self, booking: dict) -> None:
        log.info("GmailNotificationSerivce.booking_created")
        try:
            msg = EmailMessage()
            msg["To"] = self.recipient
            msg["From"] = self.sender
            msg["Reply-To"] = _clean(booking.get("email"))
            msg["Subject"] = (
                f"New booking: {_clean(booking.get('day'))} {_clean(booking.get('time'))}"
                f" - {_clean(booking.get('studentName'))} ({_clean(booking.get('subject'))})"
            )
        except Exception:
            log.exception("Exception when forming EmailMessage")

        try:
            yes_no = lambda v: "Yes" if v else "No"
            msg.set_content(
                "New tutoring session booked\n\n"
                f"Slot: {booking.get('day')} at {booking.get('time')} (weekly)\n"
                f"Subject: {booking.get('subject')}\n\n"
                f"Guardian: {booking.get('guardianName')}\n"
                f"Student: {booking.get('studentName')}\n"
                f"Email: {booking.get('email')}\n"
                f"Phone: {booking.get('phone') or '(not provided)'}\n\n"
                f"Interested in recurring: {yes_no(booking.get('wantsRecurring'))}\n"
                f"Interested in multiple per week: {yes_no(booking.get('wantsMultiplePerWeek'))}\n\n"
                f"Notes:\n{booking.get('notes') or '(none)'}\n\n"
                f"Booking ID: {booking.get('bookingId')}\n"
            )

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            self._gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
            log.info("Booking email sent for %s", booking.get("bookingId"))
        except Exception:
            log.exception("Exception when forming/sending self email")