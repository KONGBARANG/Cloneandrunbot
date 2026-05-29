import sqlite3, os
path = 'delivery_bot.db'
print('exists', os.path.exists(path))
conn = sqlite3.connect(path)
c = conn.cursor()
c.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','index') ORDER BY name")
print(c.fetchall())
c.execute('PRAGMA table_info(users)')
print('users', c.fetchall())
c.execute('PRAGMA table_info(dispatches)')
print('dispatches', c.fetchall())
conn.close()
