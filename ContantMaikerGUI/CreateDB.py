import sqlite3

db_conn = sqlite3.connect('PhysAI.db')

c = db_conn.cursor()

c.execute('''CREATE TABLE BUNDLES (
             ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
             BUNDLE TEXT NOT NULL );''')

c.execute('''CREATE TABLE CONTENT (
             ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
             BUNDLE TEXT NOT NULL,
             PROBLEM_ID INTEGER );''')

c.execute('''CREATE TABLE PROBLEMS (
             ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
             TEXT TEXT NOT NULL,
             IMAGE_PATH TEXT DEFAULT NULL,
             SOLUTION_VARIABLE TEXT NOT NULL,
             SOLUTION_VALUE TEXT NOT NULL,
             GRAPH_PATH TEXT NOT NULL );''')

db_conn.commit()

db_conn.close()
