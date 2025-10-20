import os
import psycopg2
import json
import logging

DATABASE_URL = os.getenv("DATABASE_URL")
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"ডাটাবেস সংযোগ ব্যর্থ: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    
    with conn.cursor() as cur:
        # গ্রুপ সেটিংস টেবিল
        cur.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id BIGINT PRIMARY KEY,
                settings JSONB
            );
        """)
        # ব্যবহারকারীর ওয়ার্নিং টেবিল
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT,
                chat_id BIGINT,
                warnings INT DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            );
        """)
    conn.commit()
    conn.close()
    logger.info("ডাটাবেস সফলভাবে ইনিশিয়ালাইজ হয়েছে।")

def get_setting(chat_id, key):
    conn = get_db_connection()
    if not conn: return None
    
    with conn.cursor() as cur:
        cur.execute("SELECT settings FROM groups WHERE chat_id = %s", (chat_id,))
        result = cur.fetchone()
        if result and result[0] and key in result[0]:
            return result[0][key]
    conn.close()
    return None

def set_setting(chat_id, key, value):
    conn = get_db_connection()
    if not conn: return

    with conn.cursor() as cur:
        cur.execute("INSERT INTO groups (chat_id, settings) VALUES (%s, %s) ON CONFLICT (chat_id) DO UPDATE SET settings = groups.settings || %s;",
                    (chat_id, json.dumps({key: value}), json.dumps({key: value})))
    conn.commit()
    conn.close()

def add_warning(chat_id, user_id):
    conn = get_db_connection()
    if not conn: return 0

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (chat_id, user_id, warnings) VALUES (%s, %s, 1)
            ON CONFLICT (user_id, chat_id) DO UPDATE SET warnings = users.warnings + 1
            RETURNING warnings;
        """, (chat_id, user_id))
        warnings = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return warnings

def get_warnings(chat_id, user_id):
    conn = get_db_connection()
    if not conn: return 0
    
    with conn.cursor() as cur:
        cur.execute("SELECT warnings FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        result = cur.fetchone()
    conn.close()
    return result[0] if result else 0
