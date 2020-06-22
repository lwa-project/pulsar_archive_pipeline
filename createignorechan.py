import sys
import subprocess

class freq:
  def __init__(self,freq,weight):
    self.freq = freq
    self.weight = weight

  def unweight(self):
    self.weight = 0
    

def buildfreqarray(nchan,bandwidth,centerfreq):
  freqlist = []
  for i in range(nchan):
    freqlist.append(freq(centerfreq - bandwidth/nchan*(nchan/2.0-i),1))
  return freqlist

def removerolloff(freqlist,rolloff):
  startfreq = freqlist[0].freq
  i = 0
  while freqlist[i].freq - startfreq < rolloff:
    freqlist[i].unweight()
    i = i + 1
  endfreq = freqlist[len(freqlist) - 1].freq
  i = len(freqlist) - 1
  while endfreq - freqlist[i].freq < rolloff:
    freqlist[i].unweight()
    i = i - 1

def removeranges(freqlist,ranges):
  for i in range(0,len(freqlist)):
    for frange in ranges:
      startrange,endrange = frange.split(":")
      if freqlist[i].freq >= float(startrange) and freqlist[i].freq < float(endrange):
        freqlist[i].unweight()
  

def printranges(freqlist):
  inbadrange = False
  badrange = ""
  for i in range(len(freqlist)):
    if i == len(freqlist) - 1:
      badrange = badrange + ":%d," % i
    if freqlist[i].weight == 0:
      if inbadrange == True:
        continue
      else:
        badrange = badrange + "%d" % i
        inbadrange = True
    else:
      if inbadrange == True:
        badrange = badrange + ":%d," % i
        inbadrange = False
      else:
        continue
  if len(badrange) > 0:
    badrange = badrange[0:-1]
  print badrange

def main():
  if len(sys.argv) < 1:
    print "Usage: sys.argv[0] filename"
    sys.exit()
  infile = sys.argv[1]
  ranges= ["50.03:50.07","87.4:88.0"]
  cmd = "readfile %s | grep channels | grep -v Orig | awk '{print $5}'" % infile
  p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  out,err = p.communicate()
  nchan = int(out.strip('\n'))
  cmd = "readfile %s | grep Central | awk '{print $5}'" % infile
  p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  out,err = p.communicate()
  centerfreq = float("%0.4f" % float(out.strip('\n')))
  cmd = "readfile %s | grep Bandwidth | awk '{print $5}'" % infile
  p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  out,err = p.communicate()
  bandwidth = float("%0.1f" % float(out.strip('\n')))
#  nchan = int(sys.argv[1])
#  centerfreq = float(sys.argv[2])
#  bandwidth = float(sys.argv[3])
  rolloff=1.0
  freqlist = buildfreqarray(nchan,bandwidth,centerfreq)
  removerolloff(freqlist,rolloff)
  removeranges(freqlist,ranges)
  printranges(freqlist)

if __name__ == '__main__':
  main()
