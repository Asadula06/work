import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("repairs.db")
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    status TEXT DEFAULT 'Новая',
                    client_id INTEGER,
                    master_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(client_id) REFERENCES users(id),
                    FOREIGN KEY(master_id) REFERENCES users(id)
                )
            """)

    def authenticate_user(self, username, password, role):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, role FROM users WHERE username = ? AND password = ? AND role = ?
        """, (username, password, role))
        return cursor.fetchone()

    def register_user(self, username, password, role):
        try:
            with self.conn:
                self.conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            return True
        except sqlite3.IntegrityError:
            return False

    def get_requests(self, role, user_id):
        cursor = self.conn.cursor()
        if role == "Клиент":
            cursor.execute("SELECT id, description, status, '' FROM requests WHERE client_id = ?", (user_id,))
        else:
            cursor.execute("SELECT id, description, status, client_id FROM requests WHERE master_id IS NULL OR master_id = ?", (user_id,))
        return cursor.fetchall()

    def create_request(self, client_id, description):
        with self.conn:
            self.conn.execute("INSERT INTO requests (description, client_id) VALUES (?, ?)", (description, client_id))

    def assign_request(self, master_id, request_id):
        with self.conn:
            self.conn.execute("UPDATE requests SET master_id = ?, status = 'В процессе' WHERE id = ?", (master_id, request_id))

    def complete_request(self, request_id):
        with self.conn:
            self.conn.execute("UPDATE requests SET status = 'Выполнено' WHERE id = ?", (request_id,))
