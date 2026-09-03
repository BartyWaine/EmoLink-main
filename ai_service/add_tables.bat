@echo off
echo ========================================
echo EmoLink - Add New Database Tables
echo ========================================
echo.

echo Running MySQL commands to add new tables...
echo.

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

SHOW TABLES;
"

echo.
echo ========================================
echo Tables created successfully!
echo ========================================
pause
