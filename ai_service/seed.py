import db

conn = db.get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("INSERT IGNORE INTO families (id, family_name, invite_code) VALUES (1, 'SeedFamily', 'SEED12')")
        cursor.execute("INSERT IGNORE INTO users (id, name, email, password_hash) VALUES (1, 'SeedUser', 'seed@seed.com', 'hash')")
        cursor.execute("INSERT IGNORE INTO family_members (family_id, user_id, role, visibility) VALUES (1, 1, 'parent', 'shared')")
        cursor.execute("INSERT INTO moods (family_id, user_id, mood, color) VALUES (1, 1, 'anxious', '#c084fc')")
        cursor.execute("INSERT INTO moods (family_id, user_id, mood, color) VALUES (1, 1, 'sad', '#60a5fa')")
        cursor.execute("INSERT INTO journal_entries (family_id, user_id, entry_text) VALUES (1, 1, 'Feeling very stressed about work lately.')")
        cursor.execute("INSERT INTO journal_entries (family_id, user_id, entry_text) VALUES (1, 1, 'Not getting enough sleep.')")
    conn.commit()
    print("Seed complete.")
finally:
    conn.close()
