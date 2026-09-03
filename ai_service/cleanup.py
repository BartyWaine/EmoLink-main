import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
conn = pymysql.connect(host=os.getenv('DB_HOST', '127.0.0.1'), user=os.getenv('DB_USER', 'root'), password=os.getenv('DB_PASS', ''), database=os.getenv('DB_NAME', 'emolink'))
cur = conn.cursor()
cur.execute("DELETE fm FROM family_members fm JOIN users u ON fm.user_id = u.id JOIN families f ON fm.family_id = f.id WHERE u.name = 'TestUser2' AND f.family_name = 'The Joyfuls'")
conn.commit()
print('Cleaned up TestUser2 from The Joyfuls!')
