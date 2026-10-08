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
