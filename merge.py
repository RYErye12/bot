import sqlite3

# Paths to the database and schema files
db1_path = "database3.db"
db2_path = "merged_database.db"
merged_db_path = "merged_database2.db"

# Copy the schema and data from both databases into the merged database
def merge_databases(db1_path, db2_path, merged_db_path):
    # Connect to the first and second databases and the new merged database
    conn1 = sqlite3.connect(db1_path)
    conn2 = sqlite3.connect(db2_path)
    merged_conn = sqlite3.connect(merged_db_path)

    try:
        # Get schema and data from both databases
        with conn1, conn2, merged_conn:
            cursor1 = conn1.cursor()
            cursor2 = conn2.cursor()
            merged_cursor = merged_conn.cursor()

            # Get tables from both databases
            cursor1.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables1 = [row[0] for row in cursor1.fetchall()]

            cursor2.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables2 = [row[0] for row in cursor2.fetchall()]

            # Merge data from the first database
            for table in tables1:
                cursor1.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
                create_table_query = cursor1.fetchone()[0]
                try:
                    merged_cursor.execute(create_table_query)
                except sqlite3.OperationalError as e:
                    print(f"Skipping table creation for {table}: {e}")

                cursor1.execute(f"SELECT * FROM {table};")
                rows = cursor1.fetchall()
                for row in rows:
                    placeholders = ', '.join('?' for _ in row)
                    merged_cursor.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)

            # Merge data from the second database
            for table in tables2:
                cursor2.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
                create_table_query = cursor2.fetchone()[0]
                try:
                    merged_cursor.execute(create_table_query)
                except sqlite3.OperationalError as e:
                    print(f"Skipping table creation for {table}: {e}")

                cursor2.execute(f"SELECT * FROM {table};")
                rows = cursor2.fetchall()
                for row in rows:
                    placeholders = ', '.join('?' for _ in row)
                    merged_cursor.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)

            # Commit all changes
            merged_conn.commit()

    finally:
        # Close connections
        conn1.close()
        conn2.close()
        merged_conn.close()



def merge_databases_handle_conflicts(db1_path, db2_path, merged_db_path):
    # Connect to the first and second databases and the new merged database
    conn1 = sqlite3.connect(db1_path)
    conn2 = sqlite3.connect(db2_path)
    merged_conn = sqlite3.connect(merged_db_path)

    try:
        # Get schema and data from both databases
        with conn1, conn2, merged_conn:
            cursor1 = conn1.cursor()
            cursor2 = conn2.cursor()
            merged_cursor = merged_conn.cursor()

            # Get tables from both databases
            cursor1.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables1 = [row[0] for row in cursor1.fetchall()]

            cursor2.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables2 = [row[0] for row in cursor2.fetchall()]

            # Merge data from the first database
            for table in tables1:
                cursor1.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
                create_table_query = cursor1.fetchone()[0]
                try:
                    merged_cursor.execute(create_table_query)
                except sqlite3.OperationalError as e:
                    print(f"Skipping table creation for {table}: {e}")

                cursor1.execute(f"SELECT * FROM {table};")
                rows = cursor1.fetchall()
                for row in rows:
                    placeholders = ', '.join('?' for _ in row)
                    try:
                        merged_cursor.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
                    except sqlite3.IntegrityError:
                        # Skip rows causing unique constraint violations
                        print(f"Skipping duplicate row in {table}: {row}")

            # Merge data from the second database
            for table in tables2:
                cursor2.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
                create_table_query = cursor2.fetchone()[0]
                try:
                    merged_cursor.execute(create_table_query)
                except sqlite3.OperationalError as e:
                    print(f"Skipping table creation for {table}: {e}")

                cursor2.execute(f"SELECT * FROM {table};")
                rows = cursor2.fetchall()
                for row in rows:
                    placeholders = ', '.join('?' for _ in row)
                    try:
                        merged_cursor.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
                    except sqlite3.IntegrityError:
                        # Skip rows causing unique constraint violations
                        print(f"Skipping duplicate row in {table}: {row}")

            # Commit all changes
            merged_conn.commit()

    finally:
        # Close connections
        conn1.close()
        conn2.close()
        merged_conn.close()

# Merge the databases, handling conflicts
merge_databases_handle_conflicts(db1_path, db2_path, merged_db_path)

# Return the path to the merged database
merged_db_path
