# HomeChef (HackYeah 2026)

Home cooks in India list tomorrow's dishes by SMS or voice. Customers pre-order on a mobile-first site. Hackathon MVP: optimise for a working demo, not production.

## Rules for you
- Be terse. After a task, print only the changed files and how to check them. No explanations unless asked.
- Run the app with `docker compose up -d --build` and check with curl. Never run a server in the foreground.
- templates/ belongs to Akshaya after phase 1: create placeholders once, then don't edit them. prompts/ and the text inside app/replies.py belong to Huyen: create stubs once, then only touch the code that loads them.
- No tests beyond scripts/smoke.py. No extra features, no extra dependencies.
- Small, readable files. The team must be able to explain every line to a jury.

## Stack
Python 3.12, FastAPI, Jinja2, SQLAlchemy 2 (sync), PostgreSQL 16, Docker Compose (app + db). Tailwind via CDN. Sessions: Starlette SessionMiddleware.
Speech-to-text: faster-whisper, model from env WHISPER_MODEL (default small), language hi, model cache on a Docker volume. Dockerfile installs ffmpeg.
Text-to-speech: gTTS (lang hi), mp3 files in static/audio/.
LLM: provider from env LLM_PROVIDER (gemini|rules, default gemini). Gemini uses google-genai SDK with GEMINI_API_KEY and GEMINI_MODEL (default gemini-2.5-flash-lite), JSON output. Rules is an offline regex parser. If Gemini errors or takes over 5 s, fall back to rules.
Twilio: twilio package, active only if TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER are set.
Config from .env; commit .env.example.

## Layout
app/: main.py, db.py, models.py, pages.py (customer routes), orders.py (business logic), cook.py (SMS, voice, phone screen), llm.py, speech.py, replies.py
templates/, static/, prompts/parse_listing.txt, scripts/seed.sql, scripts/smoke.py

## Data model
users(id, name, email unique, password_hash)
cooks(id, name, phone unique, area, address, channel sms|voice, default_pickup, batch_limit=5, completed_orders=0)
listings(id, cook_id, dish, region, portions, price_inr, date, pickup_start, pickup_end, status open|closed)
orders(id, user_id, listing_id, qty, amount_inr, pickup_slot, status pending|paid|closed|handed_over)
payouts(id, cook_id, listing_id, kind advance|settlement, amount_inr, created_at)
messages(id, cook_id, direction in|out, channel sms|voice, text, audio_path, created_at)

## Business rules
- Browsing is open. Customers sign up / log in with name + email + password (pbkdf2_hmac via hashlib). No email verification. Demo account: rohit@example.com / demo1234.
- Cooks are registered by a self-help group coordinator via GET+POST /register-cook (name, phone, area, address, channel, default_pickup). Registration creates the cook with batch_limit=5 and stores the WELCOME reply as her first outbound message. Unknown numbers hitting the SMS pipeline get a fixed NOT_REGISTERED reply and are not auto-created.
- Order qty can't exceed remaining portions. Payment is mocked: POST /pay marks the order paid.
- The cook's address appears only on that customer's own paid order page.
- A new listing's portions must be <= cook.batch_limit, otherwise the reply states the limit.
- close_orders(date): that date's listings become closed, the cook gets a 40% advance of the paid total, and a notification with order count and advance.
- handover(order_id): the cook gets the remaining 60%, completed_orders += 1, and every 5 completed orders batch_limit += 5.
- Notifying a cook = save an outbound message. Voice cooks also get a gTTS mp3. SMS cooks also get a real SMS if Twilio is configured.

## Cook message pipeline
SMS body or Whisper transcript -> llm.parse_listing(text) using prompts/parse_listing.txt -> JSON {dish, portions, price_inr, date, pickup_window, missing: []}.
If missing is not empty, reply with the matching question from replies.py. Otherwise create the listing and reply with a confirmation. Unknown phone number -> fixed NOT_REGISTERED reply, no auto-create.
replies.py: dict KEY -> {"sms": Hinglish in Latin script, max 160 chars, "voice": Hindi in Devanagari}.

## Routes
Customer (HTML): GET / (?area=), GET /dish/{id}, GET+POST /signup, GET+POST /login, GET /logout, GET+POST /checkout/{listing_id}, POST /pay/{order_id}, GET /order/{id}, GET /my-orders
Cook: GET+POST /register-cook (coordinator form), POST /sms/incoming (Twilio webhook, TwiML reply), GET /phone (simulated phone: choose cook, message thread, text box, record button), POST /phone/sms (form: cook_phone, text) -> JSON {reply_text}, POST /phone/voice (multipart: cook_phone, audio webm) -> JSON {transcript, reply_text, reply_audio_url}
Demo: GET /admin (orders list + buttons), POST /admin/close-orders?date=, POST /admin/handover/{order_id}
