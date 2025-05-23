import sqlite3
import csv
from datetime import datetime

DB_FILE = "musicTest.db"

def setup():
    db = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY AUTOINCREMENT, songName TEXT, frame TEXT, note1 TEXT, note2 TEXT, note3 TEXT, note4 TEXT, note5 TEXT, note6 TEXT, note7 TEXT, note8 TEXT, influence1 TEXT, influence2 TEXT, influence3 TEXT, influence4 TEXT, influence5 TEXT, influence6 TEXT, influence7 TEXT, influence8 TEXT);")
    db.commit()
    db.close()

def addSongEntry(songName, frame, note1, note2, note3, note4, note5, note6, note7, note8, influence1, influence2, influence3,influence4, influence5, influene6, influence7, influence8):
    db = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = db.cursor()
    c.execute("INSERT INTO songs (songName, frame, note1, note2, note3, note4, note5, note6, note7, note8, influence1, influence2, influence3,influence4, influence5, influence6, influence7, influence8) VALUES (?,?,?,?,?,?,?,?,?,?,?, ?, ?, ?, ?, ?, ?, ?)", (songName, frame, note1, note2, note3, note4, note5, note6, note7, note8, influence1, influence2, influence3,influence4, influence5, influene6, influence7, influence8))
    db.commit()
    db.close()

#Updates a value in a table with a new value
def setTableData(table, updateValueType, newValue, valueType, value):
    db = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = db.cursor()
    c.execute(f"UPDATE {table} SET {updateValueType} = '{newValue}' WHERE {valueType} = ?", (value,))
    db.commit()
    db.close()


# Getting information from tables ------------------------------------------
#Selecting specific argument-based data
def getTableData(table, valueType, value):
    db = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = db.cursor()
    # make sure that this all exists
    c.execute("SELECT * FROM " + table + " WHERE " + valueType + " = ?", (value,))
    result = c.fetchone()
    db.close()
    # check in case there is an error in fetching data
    if result:
        return result
    else:
        return -1

#Selecting specific argument-based data -- same as getTableData except gets all rows instead of only one
def getAllTableData(table, valueType, value):
    db = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = db.cursor()
    # make sure that this all exists
    c.execute("SELECT * FROM " + table + " WHERE " + valueType + " = ?", (value,))
    result = c.fetchall()
    db.close()
    # check in case there is an error in fetching data
    if result:
        return result
    else:
        return -1

#Resetting any table
def resetTable(tableName):
    db = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = db.cursor()
    c.execute("DELETE FROM " + tableName)
    db.commit()
    db.close()
