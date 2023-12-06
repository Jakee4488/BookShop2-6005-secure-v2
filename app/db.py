import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('database.db')

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# Execute a DELETE command to remove a row
delete_command = "SELECT name FROM sqlite_master WHERE type='table'"
cursor.execute(delete_command)

# Commit the changes to the database
conn.commit()

# Close the cursor and connection
cursor.close()
conn.close()