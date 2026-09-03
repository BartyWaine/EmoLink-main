# EmoLink Deployment to Railway

## Step 1: Push to GitHub

```bash
cd D:\EmoLink-main

# Initialize git
git init
git add .
git commit -m "EmoLink for Railway deployment"

# Create repo at https://github.com/new
git remote add origin https://github.com/bartywaine/emolink-main.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select `emolink-main` repository
5. Railway will detect Dockerfile and deploy

## Step 3: Add MySQL Database

1. In your Railway project → Click **"New"**
2. Select **"Database"** → **"MySQL"**
3. Wait for provision (~1 minute)
4. Click on the MySQL service → **"Variables"** tab
5. Copy these values:
   - `MYSQLHOST`
   - `MYSQLPORT`
   - `MYSQLUSER`
   - `MYSQLPASSWORD`
   - `MYSQL_DATABASE`

## Step 4: Configure Environment Variables

1. Go back to your PHP service (emolink-main)
2. Click **"Variables"** tab
3. Add these variables (use values from Step 3):

```
DB_HOST = your-mysql-host
DB_PORT = 3306
DB_NAME = railway
DB_USER = root
DB_PASS = your-mysql-password
AI_SERVICE_URL = https://emolink-ai.vercel.app
```

**To find DB_HOST:**
- In MySQL service → Variables → Look for `MYSQL_HOST` or check Connection string

## Step 5: Import Database Schema

1. In MySQL service → Click **"Connection"** tab
2. Click **"TablePlus"** or use connection string
3. Run this SQL or import `database/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS families (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('parent', 'teen') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS family_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('parent', 'teen') NOT NULL,
    visibility ENUM('visible', 'private') DEFAULT 'visible',
    FOREIGN KEY (family_id) REFERENCES families(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS moods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    family_id INT NOT NULL,
    mood VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (family_id) REFERENCES families(id)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    family_id INT NOT NULL,
    entry_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (family_id) REFERENCES families(id)
);

CREATE TABLE IF NOT EXISTS ai_topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    topic_text TEXT NOT NULL,
    based_on VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id)
);

CREATE TABLE IF NOT EXISTS ai_context (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id)
);

CREATE TABLE IF NOT EXISTS crisis_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    user_id INT,
    alert_type VARCHAR(50),
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    description TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id)
);

CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    journal_entry_id INT NOT NULL,
    sentiment_score DECIMAL(3,2),
    anxiety_score DECIMAL(3,2),
    label VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id)
);

CREATE TABLE IF NOT EXISTS topic_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    user_id INT NOT NULL,
    feedback_type VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES ai_topics(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS tree_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL UNIQUE,
    points INT DEFAULT 0,
    level INT DEFAULT 1,
    FOREIGN KEY (family_id) REFERENCES families(id)
);

CREATE TABLE IF NOT EXISTS family_dynamics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    communication_gap DECIMAL(3,2),
    dominant_role VARCHAR(50),
    participation_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id)
);
```

## Step 6: Deploy!

After adding environment variables, Railway will auto-redeploy.

Click **"Deployments"** tab to watch progress.

## Step 7: Access Your App

Once deployed, Railway provides a URL:
`https://emolink-main.up.railway.app`

## Test Accounts

Register new accounts at the login page, or use phpMyAdmin to insert:

```sql
INSERT INTO families (family_name) VALUES ('Smith Family');

INSERT INTO users (email, password_hash, name, role) VALUES 
('parent@test.com', '$2y...', 'Parent User', 'parent'),
('teen@test.com', '$2y...', 'Teen User', 'teen');

INSERT INTO family_members (family_id, user_id, role) VALUES 
(1, 1, 'parent'),
(1, 2, 'teen');
```

## Troubleshooting

### "Connection refused" to MySQL
- Make sure MySQL is in the same Railway project
- Check DB_HOST uses internal Railway hostname

### 500 Error
- Check Railway logs: Deployment → View Logs
- Verify all PHP files have correct `require_once` paths

### Assets not loading
- Make sure `assets/style.css` exists
- Check file paths in HTML
