import sqlite3

conn = sqlite3.connect('data/sap_data_4.db')
cursor = conn.cursor()

# Get table names
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', cursor.fetchall())

# Get column info
cursor.execute('PRAGMA table_info(sap_reports)')
print('\nColumns:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

# Get row count
cursor.execute('SELECT COUNT(*) FROM sap_reports')
print(f'\nTotal rows: {cursor.fetchone()[0]}')

conn.close()
