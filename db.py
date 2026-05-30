# db.py
# ---------------------------------------------------------------
# MySQL database layer for Escape Room Game
#
# SETUP:
#   1. Install MySQL Connector:
#        pip install mysql-connector-python
#
#   2. Make sure MySQL server is RUNNING
#
#   3. Update HOST / USER / PASSWORD below
#
#   4. Run:
#        python db.py
#
# ---------------------------------------------------------------

import hashlib
import mysql.connector
from mysql.connector import Error

# ---------------------------------------------------------------
# MYSQL CONFIG
# ---------------------------------------------------------------

HOST = "localhost"
USER = "root"
PASSWORD = "root123"   # change if needed
DATABASE = "escape_room"


# ---------------------------------------------------------------
# CONNECTION FUNCTIONS
# ---------------------------------------------------------------

def _connect(with_database=True):
    """
    Creates and returns a MySQL connection.
    """

    try:
        if with_database:
            return mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DATABASE
            )
        else:
            return mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD
            )

    except Error as e:
        print("\n[DATABASE CONNECTION ERROR]")
        print(e)
        raise


# ---------------------------------------------------------------
# DATABASE INITIALISATION
# ---------------------------------------------------------------

def init_db():
    """
    Creates database + tables if they don't exist.
    Safe to run multiple times.
    """

    try:
        # -------------------------------------------------------
        # CREATE DATABASE
        # -------------------------------------------------------

        conn = _connect(with_database=False)
        cur = conn.cursor()

        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")

        conn.commit()
        cur.close()
        conn.close()

        # -------------------------------------------------------
        # CONNECT TO DATABASE
        # -------------------------------------------------------

        conn = _connect()
        cur = conn.cursor()

        # -------------------------------------------------------
        # CREATE PROFILES TABLE
        # -------------------------------------------------------

        cur.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,

                username VARCHAR(32) NOT NULL UNIQUE,

                password_hash VARCHAR(255) NOT NULL,

                is_admin TINYINT(1) NOT NULL DEFAULT 0,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # -------------------------------------------------------
        # CREATE GAME STATE TABLE
        # -------------------------------------------------------
        # IMPORTANT:
        # keys_held uses VARCHAR instead of TEXT
        # because MySQL TEXT columns cannot have default values
        # -------------------------------------------------------

        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_state (

                profile_id INT NOT NULL UNIQUE,

                current_room VARCHAR(64) DEFAULT 'room_1',

                progress_pct INT DEFAULT 0,

                keys_held VARCHAR(255) DEFAULT '',

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,

                FOREIGN KEY (profile_id)
                REFERENCES profiles(id)
                ON DELETE CASCADE
            )
        """)

        # -------------------------------------------------------
        # CREATE DEFAULT ADMIN ACCOUNT
        # -------------------------------------------------------

        admin_password = "lorem ipsum"

        admin_hash = hashlib.sha256(
            admin_password.encode()
        ).hexdigest()

        cur.execute("""
            INSERT IGNORE INTO profiles
            (username, password_hash, is_admin)

            VALUES (%s, %s, 1)
        """, ("ADMIN", admin_hash))

        conn.commit()

        cur.close()
        conn.close()

        print("\nDatabase initialised successfully.")

    except Error as e:
        print("\n[DATABASE INITIALISATION ERROR]")
        print(e)


# ---------------------------------------------------------------
# PROFILE FUNCTIONS
# ---------------------------------------------------------------

def get_all_profiles():
    """
    Returns:
        [(id, username, is_admin), ...]
    """

    try:
        conn = _connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                username,
                is_admin

            FROM profiles

            ORDER BY
                is_admin DESC,
                created_at ASC
        """)

        rows = cur.fetchall()

        cur.close()
        conn.close()

        return rows

    except Error as e:
        print("\n[GET PROFILES ERROR]")
        print(e)
        return []


def create_profile(username, password):
    """
    Creates a new user profile.

    Returns:
        (True, profile_id)
        OR
        (False, error_message)
    """

    try:
        pw_hash = hashlib.sha256(
            password.encode()
        ).hexdigest()

        conn = _connect()
        cur = conn.cursor()

        # -------------------------------------------------------
        # INSERT PROFILE
        # -------------------------------------------------------

        cur.execute("""
            INSERT INTO profiles
            (username, password_hash, is_admin)

            VALUES (%s, %s, 0)
        """, (username, pw_hash))

        profile_id = cur.lastrowid

        # -------------------------------------------------------
        # CREATE GAME STATE
        # -------------------------------------------------------

        cur.execute("""
            INSERT INTO game_state
            (profile_id)

            VALUES (%s)
        """, (profile_id,))

        conn.commit()

        cur.close()
        conn.close()

        return True, profile_id

    except Error as e:

        if "Duplicate entry" in str(e):
            return False, "Username already taken."

        return False, str(e)


def verify_login(username, password):
    """
    Verifies login credentials.

    Returns:
        (True, profile_id, is_admin)
        OR
        (False, None, None)
    """

    try:
        pw_hash = hashlib.sha256(
            password.encode()
        ).hexdigest()

        conn = _connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                is_admin

            FROM profiles

            WHERE
                username = %s
                AND password_hash = %s
        """, (username, pw_hash))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if row:
            return True, row[0], row[1]

        return False, None, None

    except Error as e:
        print("\n[LOGIN ERROR]")
        print(e)

        return False, None, None


# ---------------------------------------------------------------
# GAME STATE FUNCTIONS
# ---------------------------------------------------------------

def get_game_state(profile_id):
    """
    Returns game state dictionary.

    Example:
    {
        'current_room': 'room_2',
        'progress_pct': 40,
        'keys_held': 'red_key,blue_key'
    }
    """

    try:
        conn = _connect()

        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT
                current_room,
                progress_pct,
                keys_held

            FROM game_state

            WHERE profile_id = %s
        """, (profile_id,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        return row

    except Error as e:
        print("\n[GET GAME STATE ERROR]")
        print(e)

        return None


def save_game_state(
    profile_id,
    current_room,
    progress_pct,
    keys_held
):
    """
    Saves or updates game state.
    """

    try:
        conn = _connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO game_state
            (
                profile_id,
                current_room,
                progress_pct,
                keys_held
            )

            VALUES (%s, %s, %s, %s)

            ON DUPLICATE KEY UPDATE

                current_room = VALUES(current_room),

                progress_pct = VALUES(progress_pct),

                keys_held = VALUES(keys_held)
        """, (
            profile_id,
            current_room,
            progress_pct,
            keys_held
        ))

        conn.commit()

        cur.close()
        conn.close()

        return True

    except Error as e:
        print("\n[SAVE GAME STATE ERROR]")
        print(e)

        return False


# ---------------------------------------------------------------
# TEST / INITIALISE
# ---------------------------------------------------------------

if __name__ == "__main__":

    init_db()

    profiles = get_all_profiles()

    print("\nProfiles in database:")
    print(profiles)