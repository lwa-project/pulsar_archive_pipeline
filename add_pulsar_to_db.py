import sqlite3
import getpass
import sys,os
import argparse

from common import DATABASE_PATH

parser=argparse.ArgumentParser(
        description='''Add a pulsar to the processing database when process is started manually''')
parser.add_argument('psrname', nargs="?", type=str, help='name of the pulsar')
parser.add_argument('filename1', nargs="?",  type=str, help='name of raw file1 with path')
parser.add_argument('filename2', nargs="?", type=str, help='name of second raw file (same as filename1 if only 1 beam)')
parser.add_argument('node', nargs="?", type=str,help='node where processing' )
parser.add_argument('directory', nargs="?", type=str, help='path to the directory where pulsar name folder exists' )
args, unknown = parser.parse_known_args()

if getpass.getuser() not in ('kstovall', 'pulsar'):
  print("Must be run by 'kstovall' or 'pulsar'")
  sys.exit(1)
  
psrname=sys.argv[1]
filename1=sys.argv[2]
filename2=sys.argv[3]
node=sys.argv[4]
directory=sys.argv[5]
status="processing"
t1=(psrname,filename1,filename2,node,directory,status)

conn = sqlite3.connect(os.path.join(DATABASE_PATH, 'PulsarProcessing.db'))
c = conn.cursor()
c.execute("INSERT INTO processing (object,filename1,filename2,node,dir,status) VALUES (?,?,?,?,?,?)",t1)
conn.commit()
conn.close()
