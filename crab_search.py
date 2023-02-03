import scipy, scipy.signal, scipy.stats
import numpy as np
import matplotlib
#matplotlib.use("macosx")
import matplotlib.pyplot as plt
import sys
from presto.infodata import infodata
import math

#numpoints=524288
numpoints=131072
#numpoints=65536
#numpoints=32768
#numpoints=16384
#numpoints=8192
statcutoff=4.0
#taud=512
overlap=8192
whichstat=1 #snr=0,snr2=1,chi2=2,mat_cov=3
ploteachpulse=0

def scatter(t,taud=100.0,beta=0.42,phase=0,A=1.0):
    beta=abs(beta)
    taud=abs(taud)
    A=abs(A)
    return np.piecewise(t,[t<phase,t>=phase],[0,lambda t: A*(t-phase)**beta*np.exp(-(t-phase)/taud)])

def rms(num):
	return math.sqrt(float(sum(n*n for n in num))/len(num))

def prune(candlist):
  close = 100
  toremove = []
  for i in range(len(candlist)):
    if candlist[i][3] < close:
      toremove.append(i)
  toremove = sorted(toremove, reverse=True)
  for i in toremove:
    del(candlist[i])
  return candlist

def prune_related(candlist):
  returnlist = []
  close = 150
  while len(candlist)!=0:
    maxindex = argmaxsigma(candlist)
    toremove = []
    #print candlist[maxindex]
    returnlist.append(candlist[maxindex])
    for i in range(len(candlist)):
      if abs(candlist[i][3]-candlist[maxindex][3])<close:
        toremove.append(i)
    toremove = sorted(toremove, reverse=True)
    for i in toremove:
      del(candlist[i])
  return returnlist
  
def getpulsewindow(pulseindex,data,cutoff=1.0):
  while data[pulseindex] > cutoff:
    if pulseindex>=0:
      pulseindex=pulseindex-1
    else:
      break
  minpulseindex=pulseindex
  pulseindex=pulseindex+1
  while data[pulseindex] > cutoff:
    if pulseindex<len(data)-1:
      pulseindex=pulseindex+1
    else:
      break
  maxpulseindex=pulseindex
  return minpulseindex,maxpulseindex
 
def argmaxsigma(candlist):
  maxsigma = 0.0
  maxindex = -1
  j = 0
  for cand in candlist:
    if cand[1] > maxsigma:
      maxsigma = cand[1]
      maxindex = j
    j=j+1
  return maxindex

t1 = np.arange(0.0, 4096, 1.0)
t2 = np.arange(0.0, numpoints, 1.0)

searchpulse = []
taud = []
area = []
candlist = []
#for i in range(50,51,50):
#  for j in [0.0,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90]:
#for i in [10,20,30,50,100,200]:
for i in [40.0,80.0,120.0,200.0,400.0,800.0,1600.0,3200.0]:
  for j in [0.40]:
    searchpulse1 = scatter(t1,i,beta=j)
    searchpulse1 = searchpulse1/np.amax(searchpulse1)
    searchpulse.append(searchpulse1)
    taud.append([i,j])
    areaundercurve=sum(searchpulse1)
    area.append(areaundercurve)

filenm=sys.argv[1]
filenmbase = filenm[:filenm.rfind(".dat")]
signal = np.fromfile(filenm, dtype=np.float32, count=numpoints)
info = infodata(filenmbase+".inf")
DMs = []
DMstr = "%.4f"%info.DM
DMs.append(info.DM)
DM = info.DM
N, dt = int(info.N), info.dt
obstime = N * dt
outfile = open(filenmbase+'.scatteredsearch', mode='w')
outfile.write("# DM      SNR      Time (s)     Sample    t_d    beta\n")
outfile2 = open(filenmbase+'.statistics', mode='w')
outfile.write("# DM      SNR     SNR2     Red_Chi2     Time (s)     Sample    t_d    beta\n")
data = np.fromfile(filenm, dtype=np.float32, count=N)
offsetatbeginning=500
startN=offsetatbeginning
endN=numpoints+offsetatbeginning
datarms=rms(data)
mean=np.mean(data)
data=data/datarms
datarms=rms(data)
while endN<N:
  sys.stdout.write("%f\r" % (float(endN)/float(N)))
  sys.stdout.flush()
  #signal = data[startN:endN]
  for j in range(len(searchpulse)):
    signal = data[startN:endN]
    result = np.correlate(signal,searchpulse[j],mode='valid')
    pulseindex = result.argmax(axis=0)
    p0 = scipy.array([taud[j][0],taud[j][1],pulseindex,1.0])
    #print "Fitting"
    try:
      popt, pcov = scipy.optimize.curve_fit(scatter, t2, signal,p0)
    except RuntimeError:
      popt=[1,0,0,0]
    if popt[0]==0:
      popt[0]=1
    #print "Done"
    #print popt
    modelpulse=scatter(t2,popt[0],popt[1],popt[2],popt[3])
    #print "Done"
    minpulseindex,maxpulseindex=getpulsewindow(pulseindex,modelpulse,cutoff=0.0001)
    snr=sum(modelpulse[minpulseindex:maxpulseindex])/math.sqrt(maxpulseindex-minpulseindex)
    snr2=sum(signal[minpulseindex:maxpulseindex])/math.sqrt(maxpulseindex-minpulseindex)
    chi2 = sum(((scatter(t2,*popt)-signal)/1.0)**2)
    dof = len(signal) - len(popt)
    rchi2 = chi2/dof
    if whichstat==0:
      stat=snr
    elif whichstat==1:
      stat=snr2
    elif whichstat==2:
      stat=rchi2
    while stat>statcutoff:
      b=signal[minpulseindex-50:maxpulseindex+50]
      R=4
      pad_size = int(math.ceil(float(b.size)/R)*R - b.size)
      b_padded = np.append(b, np.zeros(pad_size)*np.NaN)
      dataplot=np.nanmean(b_padded.reshape(-1,R), axis=1)
      times=np.arange(0,len(dataplot),1)
      times=(times+startN+minpulseindex-50)*dt
      #plt.plot(times,newplot)
      b=modelpulse[minpulseindex-50:maxpulseindex+50]
      b_padded = np.append(b, np.zeros(pad_size)*np.NaN)
      modelplot=np.nanmean(b_padded.reshape(-1,R), axis=1)
      #plt.plot(times,newplot)
      signal=signal-modelpulse
      b=signal[minpulseindex-50:maxpulseindex+50]
      b_padded = np.append(b, np.zeros(pad_size)*np.NaN)
      data2plot=np.nanmean(b_padded.reshape(-1,R), axis=1)
      #plt.plot(times,newplot)
      pulseindex=pulseindex+startN
      candlist.append([DM,stat,(pulseindex*dt),pulseindex,popt[0],popt[1],times,dataplot,modelplot,data2plot,snr,snr2,rchi2])
      #plt.ylabel("Flux(Arbitrary)")
      #plt.xlabel("Time(s)")
      #if whichstat==0:
      #  plt.title("SNR:%f" % stat)
      #  filename="DM%0.2f_%08d_%0.2fs_snr%0.1f_taud%f_beta%f.png" % (DM,pulseindex,(pulseindex*dt),stat,taud[j][0],taud[j][1])
      result = np.correlate(signal,searchpulse[j],mode='valid')
      pulseindex = result.argmax(axis=0)
      p0 = scipy.array([100.0,0.4,pulseindex,1.0])
      #print "Fitting"
      try:
        popt, pcov = scipy.optimize.curve_fit(scatter, t2, signal,p0)
      except RuntimeError:
        popt=[0,0,0,0]
      if popt[0]==0:
        popt[0]=1
      #print "Done"
      #print popt
      modelpulse=scatter(t2,popt[0],popt[1],popt[2],popt[3])
      #print "Done"
      minpulseindex,maxpulseindex=getpulsewindow(pulseindex,modelpulse,cutoff=0.0001)

      snr=sum(modelpulse[minpulseindex:maxpulseindex])/math.sqrt(maxpulseindex-minpulseindex)
      snr2=sum(signal[minpulseindex:maxpulseindex])/math.sqrt(maxpulseindex-minpulseindex)
      chi2 = sum(((scatter(t2,*popt)-signal)/1.0)**2)
      dof = len(signal) - len(popt)
      rchi2 = chi2/dof
      if whichstat==0:
        stat=snr
      elif whichstat==1:
        stat=snr2
      elif whichstat==2:
        stat=rchi2
      #plt.savefig(filename)
      #plt.close()
  startN=startN+numpoints-overlap
  endN=endN+numpoints-overlap
candlist=prune_related(candlist)
candlist=prune(candlist)
candlist.sort(key=lambda tup: tup[3])
for cand in candlist:
  outfile.write("%7.4f %7.3f %13.6f %10d     %3d   %0.2f\n" % (cand[0],cand[1],cand[2],cand[3],cand[4],cand[5]))
  outfile2.write("%7.4f %7.3f %7.3f %7.3f %13.6f %10d     %3d   %0.2f\n" % (cand[0],cand[10],cand[11],cand[12],cand[2],cand[3],cand[4],cand[5]))
  if ploteachpulse!=0:
    plt.plot(cand[6],cand[7])
    plt.plot(cand[6],cand[8])
    plt.plot(cand[6],cand[9])
    plt.ylabel("Flux(Arbitrary)")
    plt.xlabel("Time(s)")
    if whichstat==0:
      plt.title("SNR:%f" % stat)
      filename="DM%0.2f_%08d_%0.2fs_snr%0.1f.png" % (cand[0],cand[3],cand[2],cand[1])
    elif whichstat==1:
      plt.title("SNR2:%f" % stat)
      filename="DM%0.2f_%08d_%0.2fs_2snr%0.1f.png" % (cand[0],cand[3],cand[2],cand[1])
    plt.savefig(filename)
    plt.close()
