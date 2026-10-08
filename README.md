# Tutoring booking API (Flask + Supabase)

## Setup
1. Create a Supabase project, then run `supabase/schema.sql` in the SQL Editor.
2. `cp .env.example .env` and fill in `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (service_role key) and `ALLOWED_ORIGINS`.
3. `pip install -r requirements.txt`
4. Run: `python wsgi.py` (dev) or `gunicorn wsgi:app` (production).

## Endpoints
- `GET /api/availabilities` -> `{"success": true, "availabilities": [{"day": "Monday", "slots": [{"id", "day", "time"}]}]}`
- `POST /api/bookings` body: `slotId, guardianName, studentName, email, phone?, subject, notes?, wantsRecurring, wantsMultiplePerWeek`
  -> `201 {"success": true, "booking": {...}}` or `{"success": false, "message": "..."}` (400 / 409 slot taken / 429 / 500)
- `GET /health`

## Where things live
- `messages.py` — every failure string
- `controllers/` HTTP only · `services/` rules and validation · `repositories/` storage
- Change database: implement `repositories/base.py`, swap it in `create_app()`
- Email/SMS: implement `services/notification_service.py`, swap it in `create_app()`

## Notes
- Re-open a booked slot manually with the SQL at the bottom of `schema.sql`; browse bookings in the `bookings_view` view.
- In-memory rate limiting is per process. Use one gunicorn worker, or set `RATE_LIMIT_STORAGE_URI` to Redis.
- `ALLOWED_ORIGINS` is the origin only (`https://username.github.io`), not the repo path.
