#!/usr/bin/env python3
#
# Will generate a CSV with all ICAOS
import csv
import os

def writeFile(directory, filename, filenameExtension, data, count):
    csvFilename = os.path.join(directory, "%s-%s.%s"%(filename, count, filenameExtension))
    with open(csvFilename, 'w', newline='') as csvfile:
        output = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        output.writerow(['icao'])
        for row in data:
            output.writerow([row])
        csvfile.close()
        return "['%s', '%s-%s.iq8s'],"%(csvFilename, filename, count)

def main():
    directory = 'generated'
    filename = 'allICAO'
    filenameExtension = 'csv'
    scriptFilename = 'allICAO.py'
    hackRFScriptFilename = 'hackRFAllICAO.sh'

    minICAO = 0x0
    maxICAO = 0x3E8
    splitNumber = 10000

    try:
        os.stat(directory)
    except:
        os.mkdir(directory) 

    script = open(scriptFilename, 'w')
    script.write('#!/usr/bin/env python3\n')
    script.write('import time\n')
    script.write('import threading\n')
    script.write('from ADSB_Encoder import *\n')

    hackRFScript = open(hackRFScriptFilename, 'w')
    hackRFScript.write('#!/bin/bash\n')
    
    
    i = minICAO
    j = 0
    k = 0
    data = []
     
    files = ''
    while i <= maxICAO:
        if j == splitNumber:
            files += writeFile(directory, filename, filenameExtension, data, k)
            data = []
            k += 1
            j = 0
            hackRFScript.write("hackrf_transfer -t %s-%s.iq8s -f 915000000 -s 2000000 -x 10\n" % (filename, k))
        data.append(hex(i))
        i += 1
        j += 1
    files += writeFile(directory, filename, filenameExtension, data, k)
    data = []
    k += 1
    j = 0
    hackRFScript.write("hackrf_transfer -t %s-%s.iq8s -f 915000000 -s 2000000 -x 10\n" % (filename, k))
    files = files[:-1]
    script.write('files = (%s)\n' % (files))
    script.write('for file in files:\n')
    script.write('    t = threading.Thread(target=threadingCSV, args=(file,))\n')
    script.write('    t.start()\n')
    script.write('    print(file)\n')
    script.write('    time.sleep(1)\n')
    script.close()
    hackRFScript.close()

if __name__ == "__main__":
    main()

    
		
