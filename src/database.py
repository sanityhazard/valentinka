import sqlite3

class MessageDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.create_table()
        
    def open_conn(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        
    def close_conn(self):
        self.cursor.close()
        self.conn.close()

    def create_table(self):
        self.open_conn()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id BIGINT,
                recipient_message_id BIGINT,
                sender_id BIGINT,
                sender_message_id BIGINT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                username TEXT
            )
        ''')
        self.conn.commit()
        self.close_conn()

    def insert_user(self, user_id, username):
        self.open_conn()
        user_exists = self.cursor.execute('''
            SELECT * FROM users
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        if user_exists:
            return
        
        self.cursor.execute('''
            INSERT INTO users (user_id, username)
            VALUES (?, ?)
        ''', (user_id, username))
        self.conn.commit()
        self.close_conn()
        
    def get_username(self, user_id):
        self.open_conn()
        result = self.cursor.execute('''
            SELECT username FROM users
            WHERE user_id = ?
        ''', (user_id,)).fetchone()
        self.close_conn()
        return result[0] if result else None

    def insert_message(self, recipient_id, recipient_message_id, sender_id, sender_message_id):
        self.open_conn()
        self.cursor.execute('''
            INSERT INTO messages (recipient_id, recipient_message_id, sender_id, sender_message_id)
            VALUES (?, ?, ?, ?)
        ''', (recipient_id, recipient_message_id, sender_id, sender_message_id))
        self.conn.commit()
        self.close_conn()

    def get_message(self, recipient_id, recipient_message_id):
        self.open_conn()
        self.cursor.execute('''
            SELECT * FROM messages
            WHERE recipient_id = ? AND recipient_message_id = ?
        ''', (recipient_id, recipient_message_id))
        result = self.cursor.fetchone()
        self.close_conn()
        return result