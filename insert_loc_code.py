import re
import sqlite3

conn = sqlite3.connect('loc.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS location(loc text PRIMARY KEY, code text)')
conn.commit()

f = open('loc_code.txt')

for d in f.readlines():
    data = re.sub(r'\s{2}', '|', d.strip()).split('|')
    print data[1].strip(), data[0]
    c.execute('INSERT INTO location VALUES ("%s", "%s")'%(data[1].strip(), data[0]))

conn.commit()
f.close()