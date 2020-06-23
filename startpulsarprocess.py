#!/usr/bin/env python

from __future__ import print_function

import sqlite3
import os,socket,subprocess,sys
import glob

from common import *

#DATA_PATH = '/data/network/recent_data/kstovall/LS016'
#DATA_PATH = '/data/network/recent_data/swhite/DW003'

conn = sqlite3.connect(os.path.join(DATABASE_PATH, 'PulsarProcessing.db'))
c = conn.cursor()
mydir = os.getcwd()
hostname = socket.gethostname()
t1 = (hostname, mydir, "processing")
c.execute("SELECT object FROM processing WHERE node=? AND dir=? AND status=?",t1)
result = c.fetchall()
if len(result) != 0:
    outstring = "Currently processing %d sources (" % len(result)
    for row in result:
        outstring = outstring + str(row[0]) + ","
    outstring = outstring[:-1] + ")"
    print(outstring)
    sys.exit()
    
with open(os.path.join(DATABASE_PATH, 'PulsarProcessing.skip'), 'r') as skipf:
    skippulsars = skipf.read().splitlines()
    
if hostname not in ("lwaucf5", "lwaucf6"):
    skippulsars.append("J0034-0534")
    
skipfiles = []
for pending in glob.glob(os.path.join(RDQ_PATH, '*')):
    with open(pending) as skipf:
        for line in skipf:
            if line.startswith('rm'):
                skipfiles.append( line.strip().rstrip().split(None, 1)[1] )
                
df = subprocess.Popen(["df", mydir], stdout=subprocess.PIPE)
output = df.communicate()[0]
try:
    output = output.decode()
except AttributeError:
    # Python2 catch
    pass
device, size, used, available, percent, mountpoint = output.split("\n")[1].split()
available = int(available) * 1024
pulsardirs = glob.glob(os.path.join(DATA_PATH, "[BJ]*"))
for pulsardir in pulsardirs:
    pulsarname = os.path.basename(pulsardir)
    if pulsarname in skippulsars:
        print "Skipping %s" % pulsarname
        continue
        
    filenames = glob.glob(os.path.join(pulsardir, "05*"))
    for filename in filenames:
        basefilename = os.path.basename(filename)
        if "-" in basefilename:
            continue
        if "timetags" in basefilename:
            continue
        if filename in skipfiles:
            continue
        if len(basefilename.split("_")) == 2:
            mjd, identifier = basefilename.split("_")
            partnerfile = "%s_%s" % (mjd,str(int(identifier)+1).zfill(9))
            if os.path.isfile(os.path.join(pulsardir,partnerfile)):
                basefilesize = os.stat(filename).st_size
                partnerfilesize = os.stat(os.path.join(pulsardir,partnerfile)).st_size
                if basefilesize != 0 and partnerfilesize != 0:
                    sizediff = abs(1.0-float(basefilesize)/float(partnerfilesize))
                    if sizediff > 0.0024:
                        print("%s,%s has files of different size (%f), skipping" %    (pulsarname,basefilename,sizediff))
                        #cmd = "/usr/local/extensions/Pulsar/fastDRXCheck.py %s" % filename
                        #p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                        #out, err = p.communicate()
                        #print(len(out.split("\n")))
                        #print(out)
                        #cmd = "/usr/local/extensions/Pulsar/fastDRXCheck.py %s" % os.path.join(pulsardir,partnerfile)
                        #p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                        #out, err = p.communicate()
                        #print(len(out.split("\n")))
                        #print(out)
                        continue
                        
                if basefilesize == 0 or partnerfilesize == 0:
                    print("%s,%s has a file with zero size, will start single beam process" % (pulsarname,basefilename))
                    sizeneeded = basefilesize
                    if available < sizeneeded:
                        print("%s,%s needs more space than available, skipping" % (pulsarname,basefilename))
                        continue
                    t1 = (filename, os.path.join(pulsardir, partnerfile))
                    c.execute("SELECT * FROM processing")
                    result = c.fetchall()
                    c.execute("SELECT object,node,dir FROM processing WHERE filename1=? AND filename2=?",t1)
                    result = c.fetchall()
                    if len(result) != 0:
                        print("Current source (%s) is being processed on %s:%s" % (result[0][0],result[0][1],result[0][2]))
                        continue
                    else:
                        print(result)
                        
                    print("Starting new process: %s %s %s" % (pulsarname, basefilename, partnerfile))
                    t1 = (pulsarname, filename, os.path.join(pulsardir, partnerfile), hostname, mydir, 'processing')
                    c.execute("INSERT INTO processing (object,filename1,filename2,node,dir,status) VALUES (?,?,?,?,?,?)",t1)
                    conn.commit()
                    try:
                        os.mkdir(pulsarname)
                    except:
                        pass
                    os.chdir(pulsarname)
                    os.mkdir(str(int(mjd)))
                    os.chdir(str(int(mjd)))
                     
                    cmd = ""
                    if partnerfilesize == 0:
                        cmd = "%s %s 0 %s" % (os.path.join(SCRIPT_PATH, "makereducepulsar.py"), pulsarname, filename)
                    else:
                        cmd = "%s %s 0 %s" % (os.path.join(SCRIPT_PATH, "makereducepulsar.py"), pulsarname, os.path.join(pulsardir, partnerfile))
                    with open("Make.psr","w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()
                        
                    cmd = "touch singlebeam"
                    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    p.communicate()
                    
                    cmd = "make -j6 -l10 -f Make.psr"
                    with open("reducepulsar.out", "w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()
                        
                    sys.exit(0)
                    
                else:
                    sizeneeded =    basefilesize + partnerfilesize + partnerfilesize
                    if available < sizeneeded:
                        print("%s,%s needs more space than available, skipping" % (pulsarname, basefilename))
                        continue
                    t1 = (filename,os.path.join(pulsardir,partnerfile))
                    c.execute("SELECT * FROM processing")
                    result = c.fetchall()
                    c.execute("SELECT object,node,dir FROM processing WHERE filename1=? AND filename2=?",t1)
                    result = c.fetchall()
                    if len(result) != 0:
                        print("Current source (%s) is being processed on %s:%s" % (result[0][0], result[0][1], result[0][2]))
                        continue
                    print(result)
                    print("Starting new process: %s %s %s" % (pulsarname, basefilename, partnerfile))
                    t1 = (pulsarname,filename,os.path.join(pulsardir,partnerfile),hostname,mydir,'processing')
                    c.execute("INSERT INTO processing (object,filename1,filename2,node,dir,status) VALUES (?,?,?,?,?,?)",t1)
                    conn.commit()
                    os.mkdir(pulsarname)
                    os.chdir(pulsarname)
                    os.mkdir(str(int(mjd)))
                    os.chdir(str(int(mjd)))
                    
                    cmd = "%s %s 1 %s %s" % (os.path.join(SCRIPT_PATH, "makereducepulsar.py"), pulsarname, filename, os.path.join(pulsardir, partnerfile))
                    makefilename = "Make_%s.psr" % pulsarname
                    with open(makefilename, "w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()
                        
                    cmd = "make -j6 -l10 -f %s" % makefilename
                    with open("reducepulsar.out", "w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()
                        
                    sys.exit(0)
                    
print("Reached the end of file list, none met criteria")
conn.close()

