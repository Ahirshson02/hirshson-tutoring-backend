from flask import Flask, render_template, request
#from flask_mail import Mail, Message
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

import logging, sys, os

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)

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
    if os.environ.get("GOOGLE_REFRESH_TOKEN") and os.environ.get("NOTIFY_EMAIL"):
        notifier = GmailNotificationService.from_env()
    else:
        notifier = NoOpNotificationService()   # your existing no-ops
    logging.info(f"notifier is type {notifier.__class__}")
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
