#!/usr/bin/python

import subprocess,sys,socket,os
from lsl.reader.ldp import DRXFile
#import psr_utils as pu
import sqlite3
import numpy as np

from common import *

psrname = sys.argv[1]
combine = sys.argv[2]
drx2drxi_res = []
freqs1 = []
freqs2 = []
filename1 = []
filename2 = []
node = socket.gethostname()
lofreqnodestring = "-t1"
hifreqnodestring = "-t1"
backupnodestring = "-t1"
cmd = "grep PSR %s/%s.par | awk '{print $2}'" % (TZPAR_PATH, psrname)
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out,err = p.communicate()
try:
    out = out.decode()
    err = err.decode()
except AttributeError:
    # Python2 catch
    pass
parpsrname = out.strip("JB\n")

conn = sqlite3.connect(os.path.join(DATABASE_PATH, 'LWAPulsarsList.db'))
c = conn.cursor()
c.execute("SELECT name,dm,writepsrnchan,ra,dec,ntbin,nsub,nsbin,dspsrbins,dspsrchans,dspsrT,writepsrnsblk,subbanddstime,dosinglepulse,searchsinglepulse,searchscatteredpulse FROM LWAPulsars WHERE name=?",(psrname,))
result = c.fetchall()
if len(result) != 1:
    if len(result) == 0:
        print("%s not found" % psrname)
    else:
        print("%s has multiple entries in LWAPulsar DB" % psrname)
    sys.exit(1)
    
pars = result[0]
dm = pars[1]
writepsrnchan = pars[2]
ra = pars[3]
dec = pars[4]
ntbin = pars[5]
nsub = pars[6]
nsbin = pars[7]
dspsrbins = pars[8]
dspsrchans = pars[9]
dspsrT = pars[10]
writepsrnsblk = pars[11]
dstime = pars[12]
dosinglepulse = pars[13]
searchsinglepulse = pars[14]
searchscatteredpulse = pars[15]
basefilename=os.path.basename(sys.argv[3])
mjd = basefilename[1:6]

drxfiles = sys.argv[3:]
if len(drxfiles) != 2:
    print("#Currently unable to join more or less than 2 files: setting combine=0")
    combine = "0"
    
nprepsub = 128
#nprepsubfull = "256"
#if float(dm) > 35.0:
#    nprepsub = "256"
#    nprepsubfull = "512"

drxbeams = []
drxfreqs = []

for drxfile in drxfiles:
    idf = DRXFile(drxfile)
    
    # Load in basic information about the data
    ## What's in the data?
    beam = idf.get_info('beam')
    srate = idf.get_info('sample_rate') # samples/s
    
    ## Date
    beginTime = idf.get_info('start_time').datetime
    mjd = idf.get_info('start_time').mjd
    mjd_day = int(mjd)
    mjd_sec = (mjd-mjd_day)*86400

    ## Tuning frequencies
    centralFreq1 = idf.get_info('freq1') / 1e6  # MHz
    centralFreq2 = idf.get_info('freq2') / 1e6  # MHz
    
    # Save it
    drxbeams.append(beam)
    drxfreqs.append([round(centralFreq1,1),round(centralFreq2,1)])
    idf.close()
    
intermediates = ".INTERMEDIATE:"
make = "make:\n\tpython " + ' '.join(sys.argv[:]) + " > Make.psr\n\n"
ars = "ar:"
fits = "fits:"
subs = "subs:"
dats = "dats:"
pfds = "pfds:"
masks = "masks:"
weights = "weights:"
fitsstamp = "fits.stamp:"
singlepulse = "singlepulse:"
combinerules = ""
drxdats = ""
arrules = ""
rfirules = ""
pfdrules = ""
subrules = ""
datrules = ""
sprules = ""
drx2drxi_num = 1
for drxfile,beam,drxfreq in zip(drxfiles,drxbeams,drxfreqs):
    scannum = False
    basedrxfile = os.path.basename(drxfile)
    if len(basedrxfile.split("_")) == 3:
        scannum = "_%04d"% (int(basedrxfile.split("_")[2])+1)
    else:
        scannum = ""
    if combine == "1":
        subs = subs + " drx_%d_%s_subs_0001.fits" % (mjd,psrname)
        dats = dats + " drx_%d_%s_DM%s_topo_masked.dat" % (mjd,psrname,dm)
        dats = dats + " drx_%d_%s_DM%s_topo_unmasked.dat" % (mjd,psrname,dm)
        dats = dats + " drx_%d_%s_DM0.00_topo_masked.dat" % (mjd,psrname)
        dats = dats + " drx_%d_%s_DM0.00_topo_unmasked.dat" % (mjd,psrname)
        pfds = pfds + " drx_%d_%s_timing_masked_PSR_%s.pfd" % (mjd,psrname,parpsrname)
        pfds = pfds + " drx_%d_%s_timing_unmasked_PSR_%s.pfd" % (mjd,psrname,parpsrname)
        pfds = pfds + " drx_%d_%s_search_masked_PSR_%s.pfd" % (mjd,psrname,parpsrname)
        pfds = pfds + " drx_%d_%s_search_unmasked_PSR_%s.pfd" % (mjd,psrname,parpsrname)
        masks = masks + " drx_%d_%s_rfifind.mask" % (mjd,psrname)
        weights = weights + " drx_%d_%s_rfifind.weights" % (mjd,psrname)
        fits = fits + " drx_%d_%s_0001.fits" % (mjd,psrname)
    intermediates = intermediates + " %s_b%dt1.dat" % (os.path.basename(drxfile),beam)
    intermediates = intermediates + " %s_b%dt2.dat" % (os.path.basename(drxfile),beam)
    intermediates = intermediates + " drx_%d_%s_b%d_0001.fits" % (mjd,psrname,beam)
    if dosinglepulse == "1":
        if scannum == "":
            ars = ars + " %d_%s_%sMHz_SP.ar" % (mjd,psrname,drxfreq[0])
            ars = ars + " %d_%s_%sMHz_SP.ar" % (mjd,psrname,drxfreq[1])
        else:
            ars = ars + " %d_%s_%sMHz%s_SP.ar" % (mjd,psrname,drxfreq[0],scannum)
            ars = ars + " %d_%s_%sMHz%s_SP.ar" % (mjd,psrname,drxfreq[1],scannum)
    if scannum == "":
        ars = ars + " %d_%s_%sMHz.ar" % (mjd,psrname,drxfreq[0])
        ars = ars + " %d_%s_%sMHz.ar" % (mjd,psrname,drxfreq[1])
    else:
        ars = ars + " %d_%s_%sMHz%s.ar" % (mjd,psrname,drxfreq[0],scannum)
        ars = ars + " %d_%s_%sMHz%s.ar" % (mjd,psrname,drxfreq[1],scannum)
#        scannum = scannum + "_"
    if searchsinglepulse == "1":
        if combine == "1":
            singlepulse = singlepulse + " drx_%d_%s%s_singlepulse.ps" % (mjd,psrname,scannum)
            singlepulse = singlepulse + " drx_%d_%s%s_singlepulse.tgz" % (mjd,psrname,scannum)
    if searchscatteredpulse == "1":
        if combine == "1":
            singlepulse = singlepulse + " drx_%d_%s%s_scatteredsearch.ps" % (mjd,psrname,scannum)
            singlepulse = singlepulse + " drx_%d_%s%s_scattersearch.tgz" % (mjd,psrname,scannum)
    fits = fits + " fits.stamp"
    if scannum == "":
        arfilename = "%d_%s_%sMHz" % (mjd,psrname,drxfreq[0])
    else:
        arfilename = "%d_%s_%sMHz%s" % (mjd,psrname,drxfreq[0],scannum)
    arrules = arrules + "%s.ar: %s_b%dt1.dat %s_%s.hdr\n" % (arfilename,os.path.basename(drxfile),beam,psrname,drxfreq[0])
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -cuda 2 %s_%s.hdr > dspsr_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[0],drxfreq[0])
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -cuda 1 %s_%spsr_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[0],drxfreq[0])
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -cuda 0 %s_%s.hdr > dspsr_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[0],drxfreq[0])
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -t1 %s_%s.hdr > dspsr_%sMHz.out ; fi ; fi ; fi\n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[0],drxfreq[0])
    if dosinglepulse != "1":
        arrules = arrules + "\ttest -e $@ && rm $<\n\n"
    else:
        arrules = arrules + "\n"

    if scannum == "":
        arfilename = "%d_%s_%sMHz" % (mjd,psrname,drxfreq[1])
        prevarfilename = "%d_%s_%sMHz" % (mjd,psrname,drxfreq[0])
    else:
        arfilename = "%d_%s_%sMHz%s" % (mjd,psrname,drxfreq[1],scannum)
        prevarfilename = "%d_%s_%sMHz%s" % (mjd,psrname,drxfreq[0],scannum)
    arrules = arrules + "%s.ar: %s_b%dt2.dat %s_%s.hdr %s.ar\n" % (arfilename,os.path.basename(drxfile),beam,psrname,drxfreq[1],prevarfilename)
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -cuda 2 %s_%s.hdr > dspsr_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[1],drxfreq[1])
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -cuda 1 %s_%s.hdr > dspsr_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[1],drxfreq[1])
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -cuda 0 %s_%s.hdr > dspsr_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[1],drxfreq[1])
    arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -L%s -A -O %s -a PSRFITS -minram=256 -t1 %s_%s.hdr > dspsr_%sMHz.out ; fi ; fi ; fi \n" % (dspsrchans,dspsrbins,TZPAR_PATH,psrname,dspsrT,arfilename,psrname,drxfreq[1],drxfreq[1])
    if dosinglepulse != "1":
        arrules = arrules + "\ttest -e $@ && rm $<\n\n"
    else:
        arrules = arrules + "\n"
        
    if dosinglepulse == "1":
        if scannum == "":
            arfilename = "%d_%s_%sMHz_SP" % (mjd,psrname,drxfreq[0])
            prevarfilename = "%d_%s_%sMHz" % (mjd,psrname,drxfreq[0])
        else:
            arfilename = "%d_%s_%sMHz%s_SP" % (mjd,psrname,drxfreq[0],scannum)
            prevarfilename = "%d_%s_%sMHz%s" % (mjd,psrname,drxfreq[0],scannum)
        if dspsrchans > 1024:
            spdspsrchans = 1024
        else:
            spdspsrchans = dspsrchans
        arrules = arrules + "%s.ar: %s_b%dt1.dat %s_%s.hdr %s.ar\n" % (arfilename,os.path.basename(drxfile),beam,psrname,drxfreq[0],prevarfilename)
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -cuda 2 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[0],drxfreq[0])
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -cuda 1 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[0],drxfreq[0])
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -cuda 0 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[0],drxfreq[0])
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -t1 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; fi ; fi ; fi \n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[0],drxfreq[0])
        arrules = arrules + "\tpsrsh %s/median_6.psh %s_*.ar\n" % (SCRIPT_PATH, arfilename)
        arrules = arrules + "\tpam -e 64fchan --setnchn=64 %s_*.zz\n" % (arfilename)
        arrules = arrules + "\tpsradd -o %s.ar %s_*.64fchan\n" % (arfilename,arfilename)
        arrules = arrules + "\trm %s_*.ar %s_*.zz %s_*.64fchan\n" % (arfilename,arfilename,arfilename)
        arrules = arrules + "\ttest -e $@ && rm $<\n\n"
        if scannum == "":
            arfilename = "%d_%s_%sMHz_SP" % (mjd,psrname,drxfreq[1])
            prevarfilename = "%d_%s_%sMHz" % (mjd,psrname,drxfreq[1])
        else:
            arfilename = "%d_%s_%sMHz%s_SP" % (mjd,psrname,drxfreq[1],scannum)
            prevarfilename = "%d_%s_%sMHz%s" % (mjd,psrname,drxfreq[1],scannum)
        arrules = arrules + "%s.ar: %s_b%dt2.dat %s_%s.hdr %s.ar\n" % (arfilename,os.path.basename(drxfile),beam,psrname,drxfreq[1],prevarfilename)
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -cuda 2 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[1],drxfreq[1])
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -cuda 1 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[1],drxfreq[1])
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -cuda 0 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; if [ $$? -ne 0 ] ; then \\\n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[1],drxfreq[1])
        arrules = arrules + "\tdspsr -F%s:D -b%s -E %s/%s.par -turns 1 -nsub 100 -O %s -a PSRFITS -minram=256 -t1 %s_%s.hdr > dspsr_singlepulse_%sMHz.out ; fi ; fi ; fi \n" % (spdspsrchans,"1024",TZPAR_PATH,psrname,arfilename,psrname,drxfreq[1],drxfreq[1])

        arrules = arrules + "\tpsrsh %s/median_6.psh %s_*.ar\n" % (SCRIPT_PATH, arfilename)
        arrules = arrules + "\tpam -e 64fchan --setnchn=64 %s_*.zz\n" % (arfilename)
        arrules = arrules + "\tpsradd -o %s.ar %s_*.64fchan\n" % (arfilename,arfilename)
        arrules = arrules + "\trm %s_*.ar %s_*.zz %s_*.64fchan\n" % (arfilename,arfilename,arfilename)
        arrules = arrules + "\ttest -e $@ && rm $<\n\n"

#    if scannum == "" or scannum == "_0001":
    arrules = arrules + "%s_%s.hdr: %s/hdr/%s.hdr\n" % (psrname,drxfreq[0],TZPAR_PATH,psrname)
    arrules = arrules + "\tcp $^ %s_%s.hdr\n" % (psrname,drxfreq[0])
    arrules = arrules + "\techo \"FREQ %s\" >> %s_%s.hdr\n" % (drxfreq[0],psrname,drxfreq[0])
    arrules = arrules + "\techo \"DATAFILE %s_b%st1.dat\" >> %s_%s.hdr\n\n" % (os.path.basename(drxfile),beam,psrname,drxfreq[0])
    arrules = arrules + "%s_%s.hdr: %s/hdr/%s.hdr\n" % (psrname,drxfreq[1],TZPAR_PATH,psrname)
    arrules = arrules + "\tcp $^ %s_%s.hdr\n" % (psrname,drxfreq[1])
    arrules = arrules + "\techo \"FREQ %s\" >> %s_%s.hdr\n" % (drxfreq[1],psrname,drxfreq[1])
    arrules = arrules + "\techo \"DATAFILE %s_b%st2.dat\" >> %s_%s.hdr\n\n" % (os.path.basename(drxfile),beam,psrname,drxfreq[1])
    subs = subs + " drx_%d_%s_b%dt1%s_subs_0001.fits" % (mjd,psrname,beam,scannum) 
    subs = subs + " drx_%d_%s_b%dt2%s_subs_0001.fits" % (mjd,psrname,beam,scannum)
    dats = dats + " drx_%d_%s_b%dt1%s_DM%s_topo_masked.dat" % (mjd,psrname,beam,scannum,dm)
    dats = dats + " drx_%d_%s_b%dt1%s_DM%s_topo_unmasked.dat" % (mjd,psrname,beam,scannum,dm)
    dats = dats + " drx_%d_%s_b%dt1%s_DM0.00_topo_masked.dat" % (mjd,psrname,beam,scannum)
    dats = dats + " drx_%d_%s_b%dt1%s_DM0.00_topo_unmasked.dat" % (mjd,psrname,beam,scannum)
    dats = dats + " drx_%d_%s_b%dt2%s_DM%s_topo_masked.dat" % (mjd,psrname,beam,scannum,dm)
    dats = dats + " drx_%d_%s_b%dt2%s_DM%s_topo_unmasked.dat" % (mjd,psrname,beam,scannum,dm)
    dats = dats + " drx_%d_%s_b%dt2%s_DM0.00_topo_masked.dat" % (mjd,psrname,beam,scannum)
    dats = dats + " drx_%d_%s_b%dt2%s_DM0.00_topo_unmasked.dat" % (mjd,psrname,beam,scannum)
    pfds = pfds + " drx_%d_%s_b%dt1%s_timing_masked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    pfds = pfds + " drx_%d_%s_b%dt1%s_timing_unmasked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    pfds = pfds + " drx_%d_%s_b%dt1%s_search_masked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    pfds = pfds + " drx_%d_%s_b%dt1%s_search_unmasked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    pfds = pfds + " drx_%d_%s_b%dt2%s_timing_masked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    pfds = pfds + " drx_%d_%s_b%dt2%s_timing_unmasked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    pfds = pfds + " drx_%d_%s_b%dt2%s_search_masked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    pfds = pfds + " drx_%d_%s_b%dt2%s_search_unmasked_PSR_%s.pfd" % (mjd,psrname,beam,scannum,parpsrname)
    if searchsinglepulse == "1":
        singlepulse = singlepulse + " drx_%d_%s_b%dt1%s_singlepulse.ps" % (mjd,psrname,beam,scannum)
        singlepulse = singlepulse + " drx_%d_%s_b%dt2%s_singlepulse.ps" % (mjd,psrname,beam,scannum)
        singlepulse = singlepulse + " drx_%d_%s_b%dt1%s_singlepulse.tgz" % (mjd,psrname,beam,scannum)
        singlepulse = singlepulse + " drx_%d_%s_b%dt2%s_singlepulse.tgz" % (mjd,psrname,beam,scannum)
    if searchscatteredpulse == "1":
        singlepulse = singlepulse + " drx_%d_%s_b%dt1%s_scatteredsearch.ps" % (mjd,psrname,beam,scannum)
        singlepulse = singlepulse + " drx_%d_%s_b%dt2%s_scatteredsearch.ps" % (mjd,psrname,beam,scannum)
        singlepulse = singlepulse + " drx_%d_%s_b%dt1%s_scattersearch.tgz" % (mjd,psrname,beam,scannum)
        singlepulse = singlepulse + " drx_%d_%s_b%dt2%s_scattersearch.tgz" % (mjd,psrname,beam,scannum)
    masks = masks + " drx_%d_%s_b%dt1%s_rfifind.mask" % (mjd,psrname,beam,scannum)
    masks = masks + " drx_%d_%s_b%dt2%s_rfifind.mask" % (mjd,psrname,beam,scannum)
    weights = weights + " drx_%d_%s_b%dt1%s_rfifind.weights" % (mjd,psrname,beam,scannum)
    weights = weights + " drx_%d_%s_b%dt2%s_rfifind.weights" % (mjd,psrname,beam,scannum)
    drxdats = drxdats + "%%_b%dt1.dat %%_b%dt2.dat: %s/%%\n\t-/usr/local/extensions/Pulsar/drx2drxi.py $^ > drx2drxi_%d.out\n" % (beam,beam,os.path.dirname(drxfile),drx2drxi_num)
    drxdats = drxdats + "\tpython /home/pulsar/bin/check_drx2drxi_result.py drx2drxi_%d.out\n\n" % drx2drxi_num
    drx2drxi_num = drx2drxi_num + 1

if combine == "1":
    for drxfile in drxfiles:
        fitsstamp = fitsstamp + " %s" % drxfile
    fitsstamp = fitsstamp + "\n"
    fitsstamp = fitsstamp + "\t@rm -f fits.temp\n"
    fitsstamp = fitsstamp + "\t@touch fits.temp\n"
    fitsstamp = fitsstamp + "\t-/usr/local/extensions/Pulsar/writePsrfits2DMulti.py --source=%s --ra=%s --dec=%s --nchan=%s --nsblk=%s --yes %s $^ > writepsrfits.out\n" % (psrname,ra,dec,writepsrnchan,writepsrnsblk,dm)
    fitsstamp = fitsstamp + "\tpython /home/pulsar/bin/check_writepsrfits_result.py writepsrfits.out\n"
    fitsstamp = fitsstamp + "\t@mv -f fits.temp $@\n\n"

    for i,beam in enumerate(drxbeams):
        if i == len(drxbeams)-1:
            fitsstamp = fitsstamp + "drx_%d_%s_b%dt1_0001.fits drx_%d_%s_b%dt2_0001.fits" % (mjd,psrname,beam,mjd,psrname,beam)
        else:
            fitsstamp = fitsstamp + "drx_%d_%s_b%dt1_0001.fits drx_%d_%s_b%dt2_0001.fits " % (mjd,psrname,beam,mjd,psrname,beam)
    fitsstamp = fitsstamp + ":fits.stamp\n"
    fitsstamp = fitsstamp + "\t@if test -f $@; then :; else \\\n"
    fitsstamp = fitsstamp + "\t\ttrap 'rm -rf fits.lock fits.stamp' 1 2 13 15; \\\n"
    fitsstamp = fitsstamp + "\t\tif mkdir fits.lock 2> /dev/null; then \\\n"
    fitsstamp = fitsstamp + "\t\t\trm -f fits.stamp; \\\n"
    fitsstamp = fitsstamp + "\t\t\t$(MAKE) fits.stamp; \\\n"
    fitsstamp = fitsstamp + "\t\t\tresult = $$?; rm -rf fits.lock; exit $$result; \\\n"
    fitsstamp = fitsstamp + "\t\telse \\\n"
    fitsstamp = fitsstamp + "\t\t\twhile test -d fits.lock; do sleep 60; done; \\\n"
    fitsstamp = fitsstamp + "\t\t\ttest -f fits.stamp; \\\n"
    fitsstamp = fitsstamp + "\t\tfi; \\\n"
    fitsstamp = fitsstamp + "\tfi\n\n"
    for beam in drxbeams:
        combinerules = combinerules + "drx_%d_%s_b%d_0001.fits: drx_%d_%s_b%dt2_0001.fits drx_%d_%s_b%dt1_0001.fits\n" % (mjd,psrname,beam,mjd,psrname,beam,mjd,psrname,beam)
        combinerules = combinerules + "\t combine_lwa2 -o drx_%d_%s_b%d drx_%d_%s_b%dt2_0001.fits drx_%d_%s_b%dt1_0001.fits\n\n" % (mjd,psrname,beam,mjd,psrname,beam,mjd,psrname,beam)
    combinerules = combinerules + "drx_%d_%s_0001.fits:" % (mjd,psrname)
    for beam in drxbeams:
        combinerules = combinerules + " drx_%d_%s_b%d_0001.fits" % (mjd,psrname,beam)
#    print("drxbeams=",drxbeams)
#    print("drxfreqs=",drxfreqs)
    switchbeams = False
    if (drxbeams[0] > drxbeams[1]) and (drxfreqs[0][0] < drxfreqs[1][0]):
        switchbeams = True
    if (drxbeams[0] < drxbeams[1]) and (drxfreqs[0][0] > drxfreqs[1][0]):
        switchbeams = True
#    print("switchbeams=",switchbeams)
    sorteddrxbeams = sorted(drxbeams)
    if switchbeams:
        combinerules = combinerules + "\n\tcombine_lwa2 -o drx_%d_%s drx_%d_%s_b%d_0001.fits drx_%d_%s_b%d_0001.fits\n\n" % (mjd,psrname,mjd,psrname,sorteddrxbeams[0],mjd,psrname,sorteddrxbeams[1])
    else:
        combinerules = combinerules + "\n\tcombine_lwa2 -o drx_%d_%s drx_%d_%s_b%d_0001.fits drx_%d_%s_b%d_0001.fits\n\n" % (mjd,psrname,mjd,psrname,sorteddrxbeams[1],mjd,psrname,sorteddrxbeams[0])
else:
    for drxfile in drxfiles:
        fitsstamp = fitsstamp + " %s" % drxfile
    fitsstamp = fitsstamp + "\n"
    fitsstamp = fitsstamp + "\t@rm -f fits.temp\n"
    fitsstamp = fitsstamp + "\t@touch fits.temp\n"
    fitsstamp = fitsstamp + "\t-/usr/local/extensions/Pulsar/writePsrfits2D.py --source=%s --ra=%s --dec=%s --nchan=%s --nsblk=%s %s $^ > writepsrfits.out\n" % (psrname,ra,dec,writepsrnchan,writepsrnsblk,dm)
    fitsstamp = fitsstamp + "\tpython /home/pulsar/bin/check_writepsrfits_result.py writepsrfits.out\n"
    fitsstamp = fitsstamp + "\t@mv -f fits.temp $@\n\n"
    for i,beam in enumerate(drxbeams):
        if i == len(drxbeams)-1:
            fitsstamp = fitsstamp + "drx_%d_%s_b%dt1_0001.fits drx_%d_%s_b%dt2_0001.fits" % (mjd,psrname,beam,mjd,psrname,beam)
        else:
            fitsstamp = fitsstamp + "drx_%d_%s_b%dt1_0001.fits drx_%d_%s_b%dt2_0001.fits " % (mjd,psrname,beam,mjd,psrname,beam)
    fitsstamp = fitsstamp + ":fits.stamp\n"
    fitsstamp = fitsstamp + "\t@if test -f $@; then :; else \\\n"
    fitsstamp = fitsstamp + "\t\ttrap 'rm -rf fits.lock fits.stamp' 1 2 13 15; \\\n"
    fitsstamp = fitsstamp + "\t\tif mkdir fits.lock 2> /dev/null; then \\\n"
    fitsstamp = fitsstamp + "\t\t\trm -f fits.stamp; \\\n"
    fitsstamp = fitsstamp + "\t\t\t$(MAKE) fits.stamp; \\\n"
    fitsstamp = fitsstamp + "\t\t\tresult = $$?; rm -rf fits.lock; exit $$result; \\\n"
    fitsstamp = fitsstamp + "\t\telse \\\n"
    fitsstamp = fitsstamp + "\t\t\twhile test -d fits.lock; do sleep 60; done; \\\n"
    fitsstamp = fitsstamp + "\t\t\ttest -f fits.stamp; \\\n"
    fitsstamp = fitsstamp + "\t\tfi; \\\n"
    fitsstamp = fitsstamp + "\tfi\n\n"
    if scannum != "":
        fitsstamp = fitsstamp + "%%%s_0001.fits: %%_0001.fits\n" % (scannum)
        fitsstamp = fitsstamp + "\tmv $< $@" 

rfirules = rfirules + "%.ignorechan: %_0001.fits\n"
rfirules = rfirules + "\tpython %s/create_ignore_chan.py $< > $*.ignorechan\n\n" % SCRIPT_PATH

rfirules = rfirules + "%_rfifind.mask: %_0001.fits %.ignorechan\n"
rfirules = rfirules + "\trfifind -time 30 -o $* $< -ignorechan $*.ignorechan > $*_rfifind.out\n\n"
rfirules = rfirules + "%_rfifind.weights: %_rfifind.mask\n"
rfirules = rfirules + "\t-python3 /usr/local/presto/python/presto/rfifind.py $^\n\n"

pfdrules = pfdrules + "%%_timing_masked_PSR_%s.pfd: %%_0001.fits %%_rfifind.mask %%.ignorechan\n" % (parpsrname)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*2,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*4,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*8,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*16,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*32,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*13,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_masked -dm %s $< > $*_timing_masked.out; fi ; fi ; fi ; fi ; fi ; fi ; fi\n\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*26,dm)

pfdrules = pfdrules + "%%_search_masked_PSR_%s.pfd: %%_0001.fits %%_rfifind.mask %%.ignorechan\n" % (parpsrname)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*2,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*4,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*8,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %s -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*16,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %s -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out ; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*32,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %s -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out ; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*13,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -mask $*_rfifind.mask -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %s -noxwin -o $*_search_masked -dm %s $< > $*_search_masked.out ; fi ; fi ; fi ; fi ; fi ; fi ; fi\n\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*26,dm)

pfdrules = pfdrules + "%%_timing_unmasked_PSR_%s.pfd: %%_0001.fits %%.ignorechan\n" % (parpsrname)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*2,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*4,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*8,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*16,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*32,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*13,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -timing %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_timing_unmasked -dm %s $< > $*_timing_unmasked.out; fi ; fi ; fi ; fi ; fi ; fi ; fi\n\n" % (TZPAR_PATH,psrname,ntbin,nprepsub*26,dm)

pfdrules = pfdrules + "%%_search_unmasked_PSR_%s.pfd: %%_0001.fits %%.ignorechan\n" % (parpsrname)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*2,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*4,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*8,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out;    if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*16,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*32,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out; if [ $$? -ne 0 ] ; then \\\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*13,dm)
pfdrules = pfdrules + "\tprepfold -ncpus 2 -par %s/%s.par -ignorechan $*.ignorechan -n %s -nsub %d -noxwin -o $*_search_unmasked -dm %s $< > $*_search_unmasked.out; fi ; fi ; fi ; fi ; fi ; fi ; fi\n\n" % (TZPAR_PATH,psrname,nsbin,nprepsub*26,dm)

subrules = subrules + "%_subs_0001.fits: %_0001.fits %_rfifind.weights\n"
subrules = subrules + "\tpsrfits_subband -weights $*_rfifind.weights -o $*_subs -nsub %s -dm %s -dstime %s $* > $*_subs.out; if [ $$? -ne 0 ] ; then \\\n" % (nprepsub,dm,dstime)
subrules = subrules + "\tpsrfits_subband -o $*_subs -nsub %s -dm %s -dstime %s $* > $*_subs.out; if [ $$? -ne 0 ] ; then \\\n" % (nprepsub,dm,dstime)
subrules = subrules + "\tpsrfits_subband -weights $*_rfifind.weights -o $*_subs -nsub %d -dm %s -dstime %s $* > $*_subs.out; if [ $$? -ne 0 ] ; then \\\n" % (nprepsub*2,dm,dstime)
subrules = subrules + "\tpsrfits_subband -o $*_subs -nsub %d -dm %s -dstime %s $* > $*_subs.out; fi ; fi ; fi\n\n" % (nprepsub*2,dm,dstime)

datrules = datrules + "%%_DM%s_topo_masked.dat: %%_0001.fits %%_rfifind.mask %%_DM%s_topo_unmasked.dat %%.ignorechan\n" % (dm,dm)
datrules = datrules + "\t-prepdata -ncpus 2 -dm %s -mask $*_rfifind.mask -ignorechan $*.ignorechan -nobary -o $*_DM%s_topo_masked $<\n\n" % (dm,dm)
datrules = datrules + "%%_DM%s_topo_unmasked.dat: %%_0001.fits %%.ignorechan\n" % dm
datrules = datrules + "\t-prepdata -ncpus 2 -dm %s -ignorechan $*.ignorechan -nobary -o $*_DM%s_topo_unmasked $<\n\n" % (dm,dm)
datrules = datrules + "%_DM0.00_topo_masked.dat: %_0001.fits %_rfifind.mask\n"
datrules = datrules + "\t-prepdata -ncpus 2 -dm 0.00 -mask $*_rfifind.mask -nobary -o $*_DM0.00_topo_masked $<\n\n"
datrules = datrules + "%_DM0.00_topo_unmasked.dat: %_0001.fits %.ignorechan\n"
datrules = datrules + "\t-prepdata -ncpus 2 -dm 0.00 -ignorechan $*.ignorechan -nobary -o $*_DM0.00_topo_unmasked $<\n\n"
if searchsinglepulse == "1":
    startdm=float(dm)-0.50
    enddm=float(dm)+0.50
    dmstep=0.1
    sprules = sprules + "%_singlepulse.ps: %_singlepulse\n"
    sprules = sprules + "\t%s/single_pulse_search.py -t 5.5 $*_singlepulse/*.singlepulse\n" % SCRIPT_PATH
    sprules = sprules + "\t mv $*_singlepulse/$@ .\n\n"
    sprules = sprules + "%_singlepulse.tgz: %_singlepulse %_singlepulse.ps\n"
    sprules = sprules + "\ttar -czf $@ $<\n"
    sprules = sprules + "\trm -rf $<\n\n"
    sprules = sprules + "%_singlepulse: "
    for trialdm in np.arange(startdm,enddm,dmstep):
        sprules = sprules + " %%_DM%0.3f_singlepulse" % (trialdm)
    sprules = sprules + "\n"
    sprules = sprules + "\tmkdir $@\n"
    for trialdm in np.arange(startdm,enddm,dmstep):
        sprules = sprules + "\tmv $*_DM%0.03f_singlepulse/* $@\n" % (trialdm)
        sprules = sprules + "\trmdir $*_DM%0.03f_singlepulse\n" % (trialdm)
    sprules = sprules + "\n"
    for trialdm in np.arange(startdm,enddm,dmstep):
        sprules = sprules + "%%_DM%0.3f_singlepulse: %%_0001.fits %%_rfifind.mask %%.ignorechan\n" % (trialdm)
        sprules = sprules + "\tmkdir $*_DM%0.3f_singlepulse\n" % (trialdm)
        sprules = sprules + "\tpython %s/get_mask_percentage.py $*_rfifind.mask ; if [ $$? -ne 0 ] ; then \\\n" % SCRIPT_PATH
        sprules = sprules + "\tprepsubband -lodm %0.3f -numdms 100 -dmstep 0.001 -dmprec 3 -ignorechan $*.ignorechan -nsub 256 -o $*_DM%0.3f_singlepulse/$* $*_0001.fits ; else \\\n" % (trialdm,trialdm)
        sprules = sprules + "\tprepsubband -lodm %0.3f -numdms 100 -dmstep 0.001 -dmprec 3 -ignorechan $*.ignorechan -nsub 256 -o $*_DM%0.3f_singlepulse/$* $*_0001.fits -mask $*_rfifind.mask ; fi\n" % (trialdm,trialdm)
        sprules = sprules + "\t%s/single_pulse_search.py -m 1 -b -p -g $*_DM%0.3f_singlepulse/*.dat\n" % (SCRIPT_PATH, trialdm)
        sprules = sprules + "\trm $*_DM%0.3f_singlepulse/*.dat\n\n" % trialdm
if searchscatteredpulse == "1":
    startdm=float(dm)-5.00
    enddm=float(dm)+5.00
    dmstep=1.0
    sprules = sprules + "%_scatteredsearch.ps: %_scattersearch\n"
    sprules = sprules + "\tpython %s/crab_plot.py $*_scattersearch/*.scatteredsearch\n" % SCRIPT_PATH
    sprules = sprules + "\t mv $*_scattersearch/$@ .\n\n"
    sprules = sprules + "%_scattersearch.tgz: %_scattersearch %_scatteredsearch.ps\n"
    sprules = sprules + "\ttar -czf $@ $<\n"
    sprules = sprules + "\trm -rf $<\n\n"
    sprules = sprules + "%_scattersearch: "
    for trialdm in np.arange(startdm,enddm,dmstep):
        sprules = sprules + " %%_DM%0.2f_scattersearch" % (trialdm)
    sprules = sprules + "\n"
    sprules = sprules + "\tmkdir $@\n"
    for trialdm in np.arange(startdm,enddm,dmstep):
        sprules = sprules + "\tmv $*_DM%0.02f_scattersearch/* $@\n" % (trialdm)
        sprules = sprules + "\trmdir $*_DM%0.02f_scattersearch\n" % (trialdm)
    sprules = sprules + "\n"
    for trialdm in np.arange(startdm,enddm,dmstep):
        sprules = sprules + "%%_DM%0.2f_scattersearch: %%_0001.fits %%_rfifind.mask    %%.ignorechan\n" % (trialdm)
        sprules = sprules + "\tmkdir $*_DM%0.2f_scattersearch\n" % (trialdm)
        sprules = sprules + "\tprepsubband -lodm %0.2f -numdms 100 -dmstep 0.01 -nsub 512 -ignorechan $*.ignorechan -o $*_DM%0.2f_scattersearch/$* $*_0001.fits -mask $*_rfifind.mask\n" % (trialdm,trialdm)
        sprules = sprules + "\tfor file in `ls $*_DM%0.2f_scattersearch/*.dat` ; \\\n" % trialdm
        sprules = sprules + "\t\tdo python %s/crab_search.py $$file ; done\n" % SCRIPT_PATH
        sprules = sprules + "\trm $*_DM%0.2f_scattersearch/*.dat\n\n" % trialdm


intermediates = intermediates + "\n"
ars = ars + "\n"
dats = dats + "\n"
pfds = pfds + "\n"
masks = masks + "\n"
weights = weights + "\n"
singlepulse = singlepulse + "\n"
fits = fits + "\n"
print(".DEFAULT_GOAL := all\n")
print(intermediates)
if searchsinglepulse == "1" or searchscatteredpulse == "1":
    if psrname == "J1005+3015":
        print("all: fits masks weights subs dats singlepulse\n")
    else:
        print("all: fits masks weights pfds subs dats ar singlepulse\n")
else:
    print("all: fits masks weights pfds subs dats ar\n")
print(make)
print(ars)
print(fits)
print(subs)
print(dats)
print(pfds)
print(masks)
print(weights)
print(drxdats)
if searchsinglepulse == "1" or searchscatteredpulse == "1":
    print(singlepulse)
print(arrules)
print(fitsstamp)
print(combinerules)
print(rfirules)
print(pfdrules)
print(subrules)
print(datrules)
if searchsinglepulse == "1" or searchscatteredpulse == "1":
    print(sprules)
