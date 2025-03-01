# sql.py
import psycopg2
from contextlib import contextmanager


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(
        dbname="Telegram",
        user="postgres",
        password="Qwerty123",
        host="localhost",
        port="5432"
    )
    try:
        yield conn
    finally:
        conn.close()


def get_user_id(telegram_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else None


def add_user(telegram_id):
    # Сначала проверяем, существует ли пользователь
    user_id = get_user_id(telegram_id)
    if user_id is not None:
        return user_id  # Если пользователь уже есть, возвращаем его существующий id

    # Если пользователя нет, добавляем нового
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (telegram_id) VALUES (%s) RETURNING id",
                (telegram_id,)
            )
            conn.commit()
            result = cursor.fetchone()
            return result[0] if result else None


def add_word(user_id, en_word, ru_word):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_words (user_id, en_word, ru_word)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, en_word) DO NOTHING
                RETURNING word_id
                """,
                (user_id, en_word, ru_word)
            )
            conn.commit()
            return cursor.fetchone() is not None


def delete_word(user_id, en_word):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_words WHERE user_id = %s AND en_word = %s",
                (user_id, en_word)
            )
            conn.commit()
            return cursor.rowcount > 0


def get_user_words(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT en_word, ru_word FROM user_words WHERE user_id = %s",
                (user_id,)
            )
            return [{'en_word': row[0], 'ru_word': row[1]} for row in cursor.fetchall()]


def word_exists(user_id, en_word):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM user_words WHERE user_id = %s AND en_word = %s",
                (user_id, en_word)
            )
            return cursor.fetchone() is not None