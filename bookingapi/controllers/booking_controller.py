import logging

from flask import Blueprint, request

from .. import messages
from ..config import Config
from ..errors import BookingError
from ..responses import failure, success
from ..services.booking_service import BookingService

log = logging.getLogger(__name__)


def create_booking_blueprint(service: BookingService, limiter) -> Blueprint:
    bp = Blueprint("bookings", __name__, url_prefix="/api")

    @bp.get("/availabilities")
    @limiter.limit(Config.READ_LIMIT)
    def get_availabilities():
        try:
            return success({"availabilities": service.get_availabilities()})
        except Exception:
            log.exception("get_availabilities failed")
            return failure(messages.SERVER_ERROR, 500)

    @bp.post("/bookings")
    @limiter.limit(Config.BOOKING_LIMIT)
    def create_booking():
        payload = request.get_json(silent=True)
        try:
            return success({"booking": service.create_booking(payload)}, 201)
        except BookingError as e:
            return failure(e.message, e.status)
        except Exception:
            log.exception("create_booking failed")
            return failure(messages.SERVER_ERROR, 500)

    return bp
