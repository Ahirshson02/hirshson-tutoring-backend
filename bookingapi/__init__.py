from flask import Flask, render_template, request
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from bookingapi import messages
from .config import Config
from .controllers.booking_controller import create_booking_blueprint
from .repositories.supabase_repository import SupabaseBookingRepository
from .responses import failure, success
from .services.booking_service import BookingService
from .services.notification_service import NoOpNotificationService, GmailNotificationService

import os
from dotenv import load_dotenv

load_dotenv()


def create_app(config=Config) -> Flask:
    app = Flask(__name__)
    #mail = Mail(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=config.PROXY_HOPS)  # real client IP for rate limiting

    CORS(app, resources={r"/api/*": {"origins": config.ALLOWED_ORIGINS}}, methods=["GET", "POST", "OPTIONS"])

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[config.DEFAULT_LIMIT],
        storage_uri=config.RATE_LIMIT_STORAGE_URI,
    )
    limiter.init_app(app)

    # --- Wiring: swap these two lines to change storage or add notifications ---
    repo = SupabaseBookingRepository(config.SUPABASE_URL, config.SUPABASE_KEY)
   # notifier = NoOpNotificationService()  # <- PLUG IN email/SMS here (see notification_service.py)
    if os.getenv("GOOGLE_REFRESH_TOKEN") and os.getenv("GMAIL_SELF"):
        notifier = GmailNotificationService.from_env()
    else:
        notifier = NoOpNotificationService()   # your existing no-ops
    # ---------------------------------------------------------------------------

    service = BookingService(repo, notifier)
    app.register_blueprint(create_booking_blueprint(service, limiter))

    @app.get("/health")
    @limiter.exempt
    def health():
        return success()

    @app.route("/", methods=['GET','POST'])
    def home():
        return render_template('index.html')

    @app.route("/dummymail")
    def dummymail():
        sample_booking = {
        "bookingId": 123,
        "day": "Monday",
        "time": "4:00 PM",
        "guardianName": "Jane Smith",
        "studentName": "Alex Smith",
        "email": "jane.smith@example.com",
        "phone": "3055550123",
        "subject": "Algebra II",
        "notes": "Needs help preparing for an upcoming exam.",
        "wantsRecurring": True,
        "wantsMultiplePerWeek": False,
    }
        notifier.booking_created(sample_booking)

    @app.errorhandler(404)
    def _404(_):
        return failure(messages.NOT_FOUND, 404)

    @app.errorhandler(405)
    def _405(_):
        return failure(messages.METHOD_NOT_ALLOWED, 405)

    @app.errorhandler(429)
    def _429(_):
        return failure(messages.RATE_LIMITED, 429)

    @app.errorhandler(500)
    def _500(_):
        return failure(messages.SERVER_ERROR, 500)

    return app
