import db

conn = db.get_connection()
try:
    with conn.cursor() as cursor:
        # insert family 2 if missing
        cursor.execute("INSERT IGNORE INTO families (id, family_name, invite_code) VALUES (2, 'The Joyfuls', 'JOY123')")
        # insert user 2 if missing
        cursor.execute("INSERT IGNORE INTO users (id, name, email, password_hash) VALUES (2, 'HappyParent', 'happy@seed.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi')") # dummy hash
        cursor.execute("INSERT IGNORE INTO family_members (family_id, user_id, role, visibility) VALUES (2, 2, 'parent', 'shared')")
        
        # insert completely different moods (Happy and Okay)
        cursor.execute("INSERT INTO moods (family_id, user_id, mood, color) VALUES (2, 2, 'happy', '#facc15')")
        cursor.execute("INSERT INTO moods (family_id, user_id, mood, color) VALUES (2, 2, 'okay', '#a3e635')")
        
        # insert completely different journals
        cursor.execute("INSERT INTO journal_entries (family_id, user_id, entry_text) VALUES (2, 2, 'Had a wonderful day at the park today. Everyone was laughing.')")
        cursor.execute("INSERT INTO journal_entries (family_id, user_id, entry_text) VALUES (2, 2, 'Looking forward to the family movie night this weekend!')")
    conn.commit()
    print("Seed Family 2 complete.")
finally:
    conn.close()
