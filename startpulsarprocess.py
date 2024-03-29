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
    
if hostname not in ("lwaucf1", "lwaucf2","lwaucf3"):
    skippulsars.append("J0034-0534")
    skippulsars.append("J0459-0210")

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
pulsardirs.sort(key=os.path.getmtime) #sort pulsardirs by the update time, to process old files first
for pulsardir in pulsardirs:
    pulsarname = os.path.basename(pulsardir)
    if pulsarname in skippulsars:
        print("Skipping %s" % pulsarname)
        continue
    filenames = glob.glob(os.path.join(pulsardir, "06*"))
    if len(filenames)==0:
        continue
    filenames.sort() ## so partnerfile is always +1
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
            ## since any file could be identified as basefile(like for B0525+21 higher indext was), check for +/- 1 for partnerfile
            #partnerfile1 = "%s_%s" % (mjd,str(int(identifier)+1).zfill(9))
            #partnerfile2 = "%s_%s" % (mjd,str(int(identifier)-1).zfill(9))
            #if os.path.isfile(os.path.join(pulsardir,partnerfile1)):
            #    partnerfile=partnerfile1
            #elif os.path.isfile(os.path.join(pulsardir,partnerfile2)):
            #    partnerfile=partnerfile2
            #else:
            #    partnerfile=partnerfile1 #does not matter, just to define the partnerfile variable
            partnerfile= "%s_%s" % (mjd,str(int(identifier)+1).zfill(9))
            ##start processing
            if os.path.isfile(os.path.join(pulsardir,partnerfile)):  #if partnerfile exists
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
		    # identify files added for deletion
		    scheduled_files=[]
		    rdq_files=glob.glob(RDQ_PATH +"pulsar-*")
		    if len(rdq_files) !=0:
		    	for ii in rdq_files:
		    		data_file=open(ii)
				reader=data_file.readline()
				scheduled_files.append(reader.split()[1])
				data_file.close()
			
                    if len(result) != 0:
                    	print("Current source (%s) is being processed on %s:%s" % (result[0][0],result[0][1],result[0][2]))
                        #continue
                        break
		    elif (t1[0] in rdq_files) or (t1[1] in rdq_files):
			print("Current source (%s) is being scheduled for Deletion" % result[0][0])
			#continue
                        break
		    elif (os.access(t1[0], os.R_OK)==False) or (os.access(t1[1], os.R_OK)==False):
			print("Current source (%s) is being written" % pulsarname)
		    	#continue
                        break
                    else:
                        print(result)
                        
                    print("Starting new process : %s %s %s" % (pulsarname, basefilename, partnerfile))
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
	            makefilename = "Make_%s.psr" % pulsarname	
                    with open(makefilename,"w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()
                        
                    cmd = "touch singlebeam"
                    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    p.communicate()
                    print(hostname)
		    if hostname=="lwaucf3" or hostname=="lwaucf1" or hostname=="lwaucf2":
                        cmd = "(time make -j6 -l14 -f %s &)" % makefilename 
                        print(cmd)
                    else:
                        cmd = "(time make -j3 -l7 -f %s &)" % makefilename
                        print(cmd)
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
                    # identify files added for deletion
                    scheduled_files=[]
                    rdq_files=glob.glob(RDQ_PATH +"pulsar-*")
                    if len(rdq_files) !=0:
                        for ii in rdq_files:
                                data_file=open(ii)
                                reader=data_file.readline()
                                scheduled_files.append(reader.split()[1])
                                data_file.close()
                     
		    if len(result) != 0:
                        print("Current source (%s) is being processed on %s:%s" % (result[0][0], result[0][1], result[0][2]))
                        #continue
                        break
		    elif (t1[0] in rdq_files) or (t1[1] in rdq_files):
                        if len(result)!=0:
                            print("Current source (%s) is being scheduled for Deletion" % result[0][0])
                            #continue
                            break
		    elif (os.access(t1[0], os.R_OK)==False) or (os.access(t1[1], os.R_OK)==False):
			if len(result)!=0:
                            print("Current source (%s) is being written" % result[0][0])
                            #continue
                            break
		    else:	
                    	print(result)
                    print("Starting new process : %s %s %s" % (pulsarname, basefilename, partnerfile))
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
                    print(hostname)
		    if hostname=="lwaucf3" or hostname=="lwaucf1" or hostname=="lwaucf2" or hostname=="lwaucf6":    
                    	cmd = "(time make -j6 -l14 -f %s &)" % makefilename
		        print(cmd)
		    else:
		        cmd = "(time make -j3 -l7 -f %s &)" % makefilename
		        print(cmd)
                    with open("reducepulsar.out", "w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()
                        
                    sys.exit(0)
                
            elif not os.path.isfile(os.path.join(pulsardir,partnerfile)):  #if partnerfile does not exists
                basefilesize = os.stat(filename).st_size
                if basefilesize != 0:
                    print("%s,%s has no partnerfile, will start single beam process" % (pulsarname,basefilename))
                    sizeneeded = basefilesize
                    if available < sizeneeded:
                        print("%s,%s needs more space than available, skipping" % (pulsarname,basefilename))
                        continue
                    t1 = (filename, filename) #since both will be same file in database
                    c.execute("SELECT * FROM processing")
                    result = c.fetchall()
                    c.execute("SELECT object,node,dir FROM processing WHERE filename1=? AND filename2=?",t1)
                    result = c.fetchall()
                    # identify files added for deletion
                    scheduled_files=[]
                    rdq_files=glob.glob(RDQ_PATH +"pulsar-*")
                    if len(rdq_files) !=0:
                        for ii in rdq_files:
                                data_file=open(ii)
                                reader=data_file.readline()
                                scheduled_files.append(reader.split()[1])
                                data_file.close()

                    if len(result) != 0:
                        print("Current source (%s) is being processed on %s:%s" % (result[0][0],result[0][1],result[0][2]))
                        #continue
                        break
                    elif (t1[0] in rdq_files) or (t1[1] in rdq_files):
                        print("Current source (%s) is being scheduled for Deletion" % result[0][0])
                        #continue
                        break
                    elif (os.access(t1[0], os.R_OK)==False) or (os.access(t1[1], os.R_OK)==False):
                        print("Current source (%s) is being written" % pulsarname)
                        #continue
                        break
                    else:
                        print(result)

                    print("Starting new process : %s %s %s" % (pulsarname, basefilename, basefilename))
                    t1 = (pulsarname, filename, filename, hostname, mydir, 'processing')
                    c.execute("INSERT INTO processing (object,filename1,filename2,node,dir,status) VALUES (?,?,?,?,?,?)",t1)
                    conn.commit()
                    try:
                        os.mkdir(pulsarname)
                    except:
                        pass
                    os.chdir(pulsarname)
                    os.mkdir(str(int(mjd)))
                    os.chdir(str(int(mjd)))

                    cmd = "%s %s 0 %s" % (os.path.join(SCRIPT_PATH, "makereducepulsar.py"), pulsarname, filename)
                    makefilename = "Make_%s.psr" % pulsarname
                    with open(makefilename,"w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()

                    cmd = "touch singlebeam"
                    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    p.communicate()
                    print(hostname)
                    if hostname=="lwaucf3" or hostname=="lwaucf1" or hostname=="lwaucf2":
                        cmd = "(time make -j6 -l14 -f %s &)" % makefilename
                        print(cmd)
                    else:
                        cmd = "(time make -j3 -l7 -f %s &)" % makefilename
                        print(cmd)
                    with open("reducepulsar.out", "w") as outfile:
                        p = subprocess.Popen(cmd, shell=True, stdout=outfile, stderr=subprocess.STDOUT)
                        p.communicate()

                    sys.exit(0)
                
                else:
                    print ("only basefile exists with zero size for "+pulsarname)

print("Reached the end of file list, none met criteria")
conn.close()

