# Python2 compatibility
form __future__ import print_function

import rfifind, sys

a = rfifind.rfifind(sys.argv[1])

nzapchans = float(len(a.mask_zap_chans))
nzapints = float(len(a.mask_zap_ints))

if (nzapchans/float(a.nchan) > 0.4) or (nzapints/float(a.nint) > 0.4):
    print("%0.3f %0.3f" % ((nzapchans/float(a.nchan)),(nzapints/float(a.nint))))
    sys.exit(1)
else:
    print("%0.3f %0.3f" % ((nzapchans/float(a.nchan)),(nzapints/float(a.nint))))
    sys.exit(0)
