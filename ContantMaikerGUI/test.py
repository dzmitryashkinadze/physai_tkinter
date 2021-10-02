import sqlite3


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def select_all_problems(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM PROBLEMS LIMIT 1 OFFSET 0;")
    rows = cur.fetchall()
    for row in rows:
        print(row)


if __name__ == '__main__':
    database = 'PhysAI.db'
    # create a database connection
    conn = create_connection(database)
    with conn:
        print("Query problems:")
        select_all_problems(conn)
