# EmoLink - Local Setup & Run Guide

This document explains how to set up and run the EmoLink web application locally. The project uses a split architecture: a PHP/MySQL frontend for user and family management, and a Python FastAPI backend for AI topic generation using Google Gemini.

## Prerequisites
- **XAMPP** (or Laragon/MAMP) with Apache and MySQL.
- **Python 3.10+** installed on your system.
- **Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/)).

---

## 1. Database Setup
1. Open XAMPP Control Panel and start **MySQL**.
2. Create a database named `emolink`.
3. Import the database schema from `sql/schema.sql`. (If you are running the project for the first time, this will create the required tables).

---

## 2. Environment Configuration

### PHP Frontend
The database credentials for the PHP app are located in `app/config.php`. If you are using standard XAMPP defaults, no changes are needed:
- DB_HOST: `127.0.0.1`
- DB_NAME: `emolink`
- DB_USER: `root`
- DB_PASS: *(empty)*

### Python AI Backend
The Python service needs your database credentials and Gemini API key to function.
1. Navigate to the `ai_service/` folder.
2. Rename `.env.example` to `.env` (or create a new `.env` file).
3. Fill in your credentials:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASS=
   DB_NAME=emolink
   AI_PORT=8001
   ```

---

## 3. Python Environment Setup
You only need to do this **once** to install the dependencies.
1. Open a terminal or PowerShell in the `ai_service` directory:
   ```powershell
   cd path\to\EmoLink\ai_service
   ```
2. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```
3. Activate the virtual environment:
   - **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
   - **Windows (Command Prompt):** `.\venv\Scripts\activate.bat`
   - **Mac/Linux:** `source venv/bin/activate`
4. Install the required Python packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```

---

## 4. How to Run the Project

Whenever you sit down to work on or use the project, you need to start **both** services:

### Step A: Start the Frontend (PHP/MySQL)
1. Open your **XAMPP Control Panel**.
2. Click **Start** next to **Apache**.
3. Click **Start** next to **MySQL**.

### Step B: Start the AI Brain (Python)
1. Open a terminal (PowerShell or Command Prompt).
2. Navigate to the `ai_service` folder and activate the virtual environment:
   ```powershell
   cd path\to\EmoLink\ai_service
   .\venv\Scripts\Activate.ps1
   ```
3. Start the Uvicorn server:
   ```powershell
   python -m uvicorn main:app --reload --port 8001
   ```
   *(Keep this terminal open as long as you want to use the AI features!)*

### Step C: Open the App
Open your web browser and navigate to:
- **App**: http://localhost:8080/emolink/public/login.php
- **AI Service**: http://localhost:8001/docs (API documentation)

> **Note:** If you placed your `EmoLink` folder somewhere else inside `htdocs`, adjust the URL accordingly. If Apache is on a different port, use that port.

---

## 🚀 Deployment

### PHP Frontend → Railway/Render (Recommended)

Railway and Render support PHP + MySQL natively:

1. Push to GitHub
2. Create new project on Railway/Render
3. Connect GitHub repository
4. Add environment variables:
   - `DB_HOST`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASS`
5. Set build command: (none needed for PHP)
6. Set start command: (none needed for PHP)
7. Deploy!

### AI Service → Vercel

See [ai_service/DEPLOY_VERCEL.md](ai_service/DEPLOY_VERCEL.md)

---

## 🔧 Troubleshooting

### "Database connection failed"
- Verify MySQL is running
- Check credentials in `app/config.php`
- Ensure `emolink` database exists

### "AI service offline"
- Verify Python service is running on port 8001
- Check `ai_service/.env` has valid GEMINI_API_KEY
- Check for CORS errors in browser console

### Apache won't start (port 80 blocked)
- Stop IIS: `net stop WAS /Y`
- Or change Apache port to 8080 in `httpd.conf`
- Update URL to use `:8080`
