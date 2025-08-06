import sqlite3

# Initialize DB with wish_count support
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            wallet TEXT,
            wish_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Add new user or update wallet without resetting wish count
def add_user(telegram_id, wallet):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Add user if not exists
    c.execute('''
        INSERT OR IGNORE INTO users (telegram_id, wallet, wish_count)
        VALUES (?, ?, 0)
    ''', (telegram_id, wallet))
    # Always update wallet
    c.execute('''
        UPDATE users SET wallet = ? WHERE telegram_id = ?
    ''', (wallet, telegram_id))
    conn.commit()
    conn.close()

# Get a user's wallet
def get_wallet(telegram_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT wallet FROM users WHERE telegram_id=?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Increment the user's wish count
def increment_wish_count(telegram_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET wish_count = wish_count + 1 WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()

# Get a user's current wish count
def get_wish_count(telegram_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT wish_count FROM users WHERE telegram_id=?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# Return top users by wish count
def get_leaderboard(limit=10):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        SELECT telegram_id, wallet, wish_count
        FROM users
        ORDER BY wish_count DESC
        LIMIT ?
    ''', (limit,))
    results = c.fetchall()
    conn.close()
    return results

# Get all users (for token tracking, etc.)
def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT telegram_id, wallet FROM users')
    results = c.fetchall()
    conn.close()
    return results
