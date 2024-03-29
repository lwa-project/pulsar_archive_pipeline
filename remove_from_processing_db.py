from __future__ import print_function
try:
    input = raw_input
except NameError:
    pass

import sqlite3
import os,socket

from common import DATABASE_PATH

print(DATABASE_PATH)
conn = sqlite3.connect(os.path.join(DATABASE_PATH, 'PulsarProcessing.db'))
c = conn.cursor()
mydir = os.getcwd()
hostname = socket.gethostname()
t1 = (hostname,mydir,"processing")
c.execute("SELECT object FROM processing WHERE node=? AND dir=? AND status=?",t1)
result = c.fetchall()
if len(result) != 0:
  outstring = "Currently processing "
  for row in result:
    outstring = outstring + str(row[0]) + ","
  outstring = outstring[:-1]
  print(outstring)
  for row in result:
    response = input("Would you like to remove: %s? " % str(row[0]))
    if response == "Y":
      print("Removing %s" % str(row[0]))
      t1 = (hostname,mydir,str(row[0]))
      c.execute("DELETE FROM processing WHERE node=? AND dir=? AND object=?",t1)
      conn.commit()
    else:
      print("Not removing")
