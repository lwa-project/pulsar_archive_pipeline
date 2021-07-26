import os
import sys
import glob


psrname=sys.argv[1]
processdirname=sys.argv[2]

path=processdirname+'/'+psrname+'/[5-9][0-9][0-9][0-9][0-9]'
path=glob.glob(path)[0] #this will create the path name using the wildcard from previous path
psrfile=processdirname+'/'+psrname+'.txt'

#this walks all sub-directories, summing all file sizes
def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return (total_size/(1024*1024))

# create txt file to store size if does not exist
if os.path.isfile(psrfile)==False:
	with open(psrfile, 'w') as ff:
		print >>ff, int(0)
	ff.close()
#update the value in text file if its smaller than current directory size
else:
	new_val=get_size(path)
	old_file=open(psrfile, 'r')
	lines=old_file.readlines()
	old_file.close()
	for line in lines:
		if int(line)<new_val:
			line=line.replace(line,str(new_val)+'\n')
			with open(psrfile, 'w') as ff:
				print >>ff, int(new_val)
			ff.close()
	
		
