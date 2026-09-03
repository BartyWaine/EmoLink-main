@echo off
echo ========================================
echo EmoLink - Full Setup Script
echo ========================================
echo This script will:
echo   1. Reset MySQL root password (if needed)
echo   2. Add new database tables
echo   3. Install Python dependencies
echo   4. Start the AI service
echo.
echo ========================================
echo.

REM Check if MySQL is accessible
echo [1/4] Checking MySQL connection...
"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root -e "SELECT 1" 2>nul
if errorlevel 1 (
    echo MySQL connection failed. Running password reset first...
    echo.
    echo Please run: reset_mysql.bat
    echo Then run this script again.
    pause
    exit /b 1
)
echo MySQL is accessible!
echo.

REM Add new tables
echo [2/4] Adding new database tables...
"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root emolink -e "
CREATE TABLE IF NOT EXISTS crisis_alerts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  family_id INT NOT NULL,
  user_id INT NOT NULL,
  alert_type ENUM('prolonged_sad', 'prolonged_anxious', 'mood_spike', 'concerning_pattern') NOT NULL,
  severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
  message TEXT,
  is_resolved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resolved_at TIMESTAMP NULL,
  FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sentiment_analysis (
  id INT AUTO_INCREMENT PRIMARY KEY,
  journal_entry_id INT NOT NULL,
  sentiment_score DECIMAL(3,2) DEFAULT 0.00,
  anxiety_score DECIMAL(3,2) DEFAULT 0.00,
  hope_score DECIMAL(3,2) DEFAULT 0.00,
  keywords TEXT,
  themes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topic_feedback (
  id INT AUTO_INCREMENT PRIMARY KEY,
  topic_id INT NOT NULL,
  user_id INT NOT NULL,
  feedback_type ENUM('discussed', 'skipped', 'helpful', 'not_helpful') NOT NULL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (topic_id) REFERENCES ai_topics(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS model_votes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  family_id INT NOT NULL,
  model_name VARCHAR(50) NOT NULL,
  topic_text TEXT NOT NULL,
  based_on VARCHAR(255),
  vote_score INT DEFAULT 0,
  is_selected BOOLEAN DEFAULT FALSE,
  generation_round INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mood_predictions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  family_id INT NOT NULL,
  user_id INT NOT NULL,
  predicted_mood VARCHAR(20),
  confidence DECIMAL(3,2) DEFAULT 0.00,
  prediction_basis VARCHAR(255),
  is_accurate BOOLEAN NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  validated_at TIMESTAMP NULL,
  FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS family_dynamics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  family_id INT UNIQUE NOT NULL,
  parent_engagement_score DECIMAL(3,2) DEFAULT 0.50,
  teen_engagement_score DECIMAL(3,2) DEFAULT 0.50,
  communication_gap DECIMAL(3,2) DEFAULT 0.00,
  dominant_role VARCHAR(20),
  suggested_focus_areas TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
);
" 2>nul

if errorlevel 1 (
    echo WARNING: Could not create tables. Database may need password reset.
    echo Skipping table creation - will retry after Python setup.
) else (
    echo Tables added successfully!
)
echo.

REM Install Python dependencies
echo [3/4] Installing Python dependencies...
py -m pip install fastapi uvicorn google-generativeai pydantic python-dotenv PyMySQL anthropic openai 2>nul
echo Python dependencies installed!
echo.

REM Start AI Service
echo [4/4] Starting AI Service...
echo.
echo ========================================
echo AI Service is starting on port 8001
echo.
echo API Documentation: http://127.0.0.1:8001/docs
echo Health Check: http://127.0.0.1:8001/health
echo.
echo Press Ctrl+C to stop the service.
echo ========================================
echo.
py -m uvicorn main:app --reload --port 8001 --host 127.0.0.1
