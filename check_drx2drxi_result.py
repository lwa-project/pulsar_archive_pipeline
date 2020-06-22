from __future__ import print_function

import sys

with open(sys.argv[1],'r') as fh:
    print("file opened")
    for line in fh.readlines():
        if '\r' in line:
            pars = line.split('\r')
            print("got pars")
            res = pars[len(pars)-2].split()
            print(res)
            drx2drxi2_res = float(res[len(res)-2].strip('%'))
    if drx2drxi2_res < 99.0:
        sys.exit(1)
