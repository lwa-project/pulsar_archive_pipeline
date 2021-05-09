import sqlite3
import getpass
import sys,os

from common import DATABASE_PATH

if getpass.getuser() not in ('kstovall', 'pulsar'):
  print("Must be run by 'kstovall' or 'pulsar'")
  sys.exit(1)
  
conn = sqlite3.connect(os.path.join(DATABASE_PATH, 'PulsarProcessing.db'))
c = conn.cursor()
c.execute("SELECT filename1,filename2,object FROM processing WHERE status='copied'")
rows = c.fetchall()
if len(rows) != 0:
        c.execute("SELECT filename1,filename2,object FROM processing WHERE status='scheduled'")
        rows2 = c.fetchall()

	if len(rows2) !=0:
        	for row in rows2:
                	t1 = (row[0],row[1])
                	c.execute("DELETE FROM processing WHERE status='scheduled' AND filename1=? AND filename2=?",t1)
                	conn.commit()
	else:
		pass

	for row in rows:
		pulsardir = os.path.dirname(row[0])
		print("Removing %s" % row[0])
		os.system("/usr/local/bin/rmrd -f %s" % row[0])
		print("Removing %s" % row[1])
		os.system("/usr/local/bin/rmrd -f %s" % row[1])
		t1 = (row[0],row[1])
		c.execute("UPDATE processing SET status='scheduled' WHERE filename1=? AND filename2=?",t1)
		conn.commit()
else:
	print ("Nothing available to schedule for deletion")	
conn.close()
