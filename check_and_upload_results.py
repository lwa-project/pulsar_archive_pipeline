#!/usr/bin/env python

import glob
import smtplib
import sys,os
import subprocess
import shutil
import sqlite3
import socket

from common import DATABASE_PATH

checkpsr = sys.argv[1]

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

if __name__ == "__main__":
    #Assuming we are checking a directory made from 2 beams (4 tunings) that were all combined
    if os.path.isfile('singlebeam'):
        print("Output is from a single file")
        arfiles = glob.glob("*.ar")
        if len(arfiles) != 2 and len(arfiles) != 4:
            print("Incorrect number of ar files, exiting")
            sys.exit(1)

        subfiles = glob.glob("*_subs_*.fits")
        if len(subfiles) != 2:
            print("Incorrect number of sub files, exiting")
            sys.exit(2)

        pfdfiles = glob.glob("*.pfd")
        if len(pfdfiles) != 8:
            print("Incorrect number of pfd files, exiting")
            sys.exit(3)
        print("Reached the end of all checks")
        fitsfiles = glob.glob("*.fits")
        fitsfiles = [x for x in fitsfiles if x not in subfiles]
        for fitsfile in fitsfiles:
            print "Removing %s" % fitsfile
            try:
                os.remove(fitsfile)
            except OSError:
                pass
    else:
        print("Output is from 2 files that have been combined")
        arfiles = glob.glob("*.ar")
        if len(arfiles) != 4 and len(arfiles) != 8:
            print("Incorrect number of ar files, exiting")
            sys.exit(1)

        subfiles = glob.glob("*_subs_*.fits")
        if len(subfiles) != 5:
            print("Incorrect number of sub files, exiting")
            sys.exit(2)

        pfdfiles = glob.glob("*.pfd")
        if len(pfdfiles) != 20:
            print("Incorrect number of pfd files, exiting")
            sys.exit(3)

        print("Reached the end of all checks")
        fitsfiles = glob.glob("*.fits")
        fitsfiles = [x for x in fitsfiles if x not in subfiles]
        for fitsfile in fitsfiles:
            print "Removing %s" % fitsfile
            try:
                os.remove(fitsfile)
            except OSError:
                pass

    #Check size of directory before copying to Pulsar Archive
    dirsize = get_size()
    print dirsize
    if dirsize > 110 * 1024 * 1024 * 1024:
        print "Directory size larger than expected, not copying"
        sys.exit(4)

    currentdir = os.getcwd()
    mjd = os.path.basename(currentdir)
    pulsardirname = os.path.dirname(currentdir)
    pulsarname = os.path.basename(pulsardirname)
    processdirname = os.path.dirname(pulsardirname)
    os.chdir(pulsardirname)
    cmd = "rsync -rP %s lda10g.alliance.unm.edu:/FileStore/PulsarArchive/%s/" % (mjd,pulsarname)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
      print "Rsync returned an error, marking DB entry as waiting and exiting"
      conn = sqlite3.connect(os.path.join(DATABASE_PATH, 'PulsarProcessing.db'))
      c = conn.cursor()
      hostname = socket.gethostname()
      t1 = (pulsarname,hostname,processdirname)
      c.execute("UPDATE processing set status='waiting' WHERE object=? AND node=? AND dir=?",t1)
      conn.commit()
      sys.exit(5)

    shutil.rmtree(mjd,ignore_errors=True)
    os.chdir(processdirname)
    os.rmdir(pulsardirname)
    conn = sqlite3.connect('/home/pulsar/bin/database/PulsarProcessing.db')
    c = conn.cursor()
    hostname = socket.gethostname()
    print pulsarname, hostname, processdirname
    t1 = (pulsarname,hostname,processdirname)
    print t1
    c.execute("UPDATE processing set status='copied' WHERE object=? AND node=? AND dir=?",t1)
    conn.commit()
    if (int(checkpsr) == 1):
      cmd = "python /home/pulsar/bin/startpulsarprocess.py"
      p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    out, err = p.communicate()
      sys.exit(0)
