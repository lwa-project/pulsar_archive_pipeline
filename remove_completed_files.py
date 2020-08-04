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
for row in rows:
  pulsardir = os.path.dirname(row[0])
  print("Removing %s" % row[0])
  os.system("rmrd -f %s" % row[0])
  #ry:
  # os.remove(row[0])
  #xcept OSError:
  # pass
  print("Removing %s" % row[1])
  os.system("rmrd -f %s" % row[1])
  #ry:
  # os.remove(row[1])
  #xcept OSError:
  # pass
#  try:
#      os.rmdir(pulsardir)
#  except OSError:
#      pass
  t1 = (row[0],row[1])
  c.execute("DELETE FROM processing WHERE status='copied' AND filename1=? AND filename2=?",t1)
  conn.commit()
conn.close()
