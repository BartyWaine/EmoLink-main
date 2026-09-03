# EmoLink - Detailed Project Log

This document serves as a comprehensive log of all architectural decisions, features, and code implemented across Phases 1 through 4 of the EmoLink project.

## System Architecture Overview
- **Frontend / Core Application:** PHP 8+ handling routing, templating, session management, and primary MySQL database interactions.
- **Backend AI Service:** Python 3.10+ FastAPI microservice running locally.
- **Database:** Shared MySQL (`emolink`) ensuring data integrity across both systems.
- **AI Integration:** Google Gemini (`gemini-2.5-flash`) via the `google-generativeai` SDK.

---

## Phase 1: Foundation (Auth & Families)
**Goal:** Establish the core database schema, user authentication, and the fundamental concept of isolated family groups ("GroupTrees").

1. **Database Schema (`sql/schema.sql`)**
   - Created normalized tables: `users`, `families`, `family_members`, `moods`, `journal_entries`, `ai_context`, `ai_topics`, `open_door_signals`, and `tree_progress`.
   - Used foreign keys with `ON DELETE CASCADE` to maintain referential integrity.
2. **Core Configuration & Auth (`app/config.php`, `app/db.php`, `app/auth.php`)**
   - Configured PDO with strictly parameterized queries to prevent SQL injection.
   - Implemented `is_logged_in()` and session-based authentication logic.
   - Built `login.php`, `register.php`, and `logout.php` using secure `password_hash()` and `password_verify()`.
3. **Family Management (`public/family.php`)**
   - Implemented logic to Create or Join a family using a generated 5-character alphanumeric Invite Code.
   - Wrapped creation logic in strict **PDO Transactions** to guarantee that a `families` row and a `family_members` row are created atomically.
4. **Dashboard Skeleton (`public/dashboard.php`)**
   - Built the initial UI utilizing vanilla CSS (`public/assets/style.css`) with a clean, modern aesthetic centered around a primary indigo hue (`#4f46e5`).

---

## Phase 2: Core Emotional Loop (Check-ins & Privacy)
**Goal:** Allow users to log moods/journals and view a real-time feed of their family's emotional state while respecting strict privacy bounds.

1. **Check-in System (`public/checkin.php`)**
   - Built an interface for users to select a mood (mapped to specific hex colors) and write a journal entry. Fixed the UI using the modern `:has()` CSS pseudo-class to ensure the radio button styling worked flawlessly.
2. **Open Door Signal (`public/open_door.php`)**
   - Created a simple POST endpoint to toggle a user's availability (`open`, `closed`, `maybe`) represented by a colored dot in the UI.
3. **Data Privacy & Security Guards**
   - Created the `require_family_member()` guard in PHP to absolutely ensure a user cannot access data for a `family_id` they do not belong to.
   - Upgraded `dashboard.php` SQL queries to implement **database-level privacy**. If a user sets their visibility to `private`, their mood and journal entries are excluded (`NULL`) from the feed of other members, but their account card and Open Door status remain visible.
4. **UI Polish**
   - Added logic to explicitly highlight the current logged-in user's card in the Family Pulse feed with a `(You)` tag and a tinted background.

---

## Phase 3: Per-Family AI Core
**Goal:** Integrate a standalone Python microservice that reads isolated family data and generates personalized conversation topics using Google Gemini.

1. **Microservice Initialization (`ai_service/`)**
   - Set up a Python virtual environment with `fastapi`, `uvicorn`, `pymysql`, and `pydantic`.
   - Created `.env` management to securely store the `GEMINI_API_KEY` and DB credentials.
2. **Data Isolation (`ai_service/db.py`)**
   - Implemented `get_family_data(family_id)` to fetch the last 10 moods, 7 journals, and rolling summary strictly for the requested family.
   - Implemented `save_ai_results()` wrapping the insertion of 3 new topics and the `ON DUPLICATE KEY UPDATE` of the `ai_context` summary in a **single transaction**.
3. **AI Context Builder (`ai_service/context_builder.py`)**
   - Wrote a dynamic prompt generator that feeds Gemini the family's recent emotional trends and explicitly requests warm, non-judgmental topics.
4. **Gemini Client & Strict Validation (`ai_service/gemini_client.py`)**
   - Upgraded to `gemini-2.5-flash` model utilizing `response_mime_type: "application/json"`.
   - Enforced a Pydantic schema (`Topic` and `GeminiResponse`) requiring exactly 3 topics and a rationale (`based_on` capped safely at 255 chars).
   - Implemented a defensive fallback block: If Gemini hallucinates or breaks JSON structure, the system degrades gracefully to standard fallback topics instead of crashing.
5. **FastAPI Endpoint (`ai_service/main.py`)**
   - Exposed `POST /generate-topics`.
   - Implemented an "Empty Guard": If a family has zero check-ins, the service returns `{"status": "empty"}` to prevent wasting AI quota.
6. **PHP Wiring (`public/topics.php`)**
   - Built the frontend UI that makes a synchronous, blocking cURL request to the Python backend on port 8001.
   - Added robust error handling in PHP to parse backend failures (e.g., missing API key, service offline) and display them cleanly to the user.
   - Connected this view to the dashboard via a "Get AI Topics" button.

---

## Phase 4: Gamification, AI Privacy Enhancements, & UX Polish
**Goal:** Gamify the application to encourage user engagement, enhance the privacy logic of the AI system, and apply final layout polish.

1. **Gamification Math & UI (`app/db.php`, `public/dashboard.php`)**
   - Implemented point triggers: +10 points for check-ins, +5 points for AI topics. 
   - Created `award_family_points()` with safe `INSERT IGNORE` UPSERT logic so new families automatically generate a Level 1 `tree_progress` row.
   - Built the Growth Tree component on the Dashboard. It calculates progress using modulo math (`$points % 50`) and dynamically updates the tree emoji based on level (🌱 🌿 🪴 🌳 🌲).
2. **Advanced AI Privacy Architecture (`ai_service/db.py`)**
   - **The Problem:** The AI backend was initially reading private check-ins and leaking names in its summary.
   - **The Solution:** We implemented an elegant "Anonymization" fix. The Python backend now retrieves all check-ins to build accurate emotional context, but explicitly overwrites the person's name with *"An Anonymous Family Member"* if their `visibility` is set to `private`. This physically guarantees the AI cannot leak names in its summary while still allowing it to generate empathetic, relevant topics.
3. **UX & Single Family Enforcement (`public/family.php`)**
   - Enforced a **Single Family Restriction**. Added logic to query if a user is already in a family, and if so, completely disables the "Create/Join" forms, ensuring users focus purely on their primary family connection. Cleaned up overlapping test data via manual DB scripts.
   - Polished the dashboard UI: Renamed the confusing "Toggle Open Door" button to *"I'm available to talk"* directly reflecting the Pitch Deck wording.
   - Added hard color coding to the visibility status text (Red for Private, Green for Shared).
4. **Asynchronous AI Enhancements (`public/topics.php`)**
   - Converted the "Generate Fresh Topics" button to use Vanilla JS `fetch()`. It now displays a non-blocking "Thinking..." loading spinner, drastically improving perceived performance.
   - Implemented graceful degradation: If the AJAX `fetch()` fails due to network issues, it seamlessly falls back to a synchronous HTML form POST to ensure the demo never breaks.
5. **Syntax Integrity & Project Wrap-up**
   - Conducted a full `php -l` and `python -m py_compile` linting pass across the entire codebase to mathematically guarantee zero syntax errors prior to submission.

---

## Phase 5: Pitch Deck Alignment & Mobile UI Polish
**Goal:** Visually upgrade the web application to match the high-fidelity UI mockups provided in the Pitch Deck, simulating a native mobile app experience without rebuilding the backend.

1. **Global Typography & Color Overhaul (`public/assets/style.css`)**
   - Replaced the generic indigo styling with the premium "Plum & Coral" aesthetic defined in the mockups.
   - Injected the Google Fonts API (`Fraunces` for headers, `Plus Jakarta Sans` for UI text) into all public-facing PHP files via an automated Python script.
   - Refined UI geometry by heavily increasing border-radiuses to 20px and applying soft, ambient drop shadows to emulate modern mobile app cards.
2. **Dynamic UI Feedback (`public/dashboard.php`)**
   - Implemented seamless Vanilla JS `fetch()` requests for the "I'm available to talk" button. 
   - When clicked, it updates its visual state (Grey ↔ Sage Green) and dynamically syncs with the user's color-coded dot in the "Family Pulse" feed, all without a single page reload or scroll jump.
3. **AI Summary Prompt Tuning (`ai_service/context_builder.py`)**
   - Noticed the AI was generating excessively brief summaries due to limited test data and the prompt literally asking for a "short paragraph".
   - Upgraded the prompt instruction to explicitly demand a detailed 2-3 sentence analysis capturing nuances and recurring themes, guaranteeing richer summaries even with sparse inputs.
4. **Safety & Crisis Escalation Path (`public/checkin.php`)**
   - Directly addressed the judge's feedback regarding minor safety and crisis management.
   - Implemented a dynamic UI listener that instantly reveals a "Crisis Resource" and trusted adult escalation path whenever a user logs a "Sad" or "Anxious" mood, ensuring a safe emotional environment.
