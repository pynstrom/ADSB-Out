#!/usr/bin/env python3

import sys, os
from getopt import getopt, GetoptError
from math import radians, sin, cos, sqrt, atan2, degrees, floor
from ADSB_Encoder import ADSB_Encoder
from HackRF import HackRF
from PPM import PPM
from ModeS import ModeS

def usage(msg=False):
	if msg:print(msg)
	print("Usage: %s [options]\n" % sys.argv[0])
	print("-h | --help        Display help message.")
	print("-v | --verbose     Show output messages.")
	print("-s | --start       Starting point (lat,long).")
	print("-e | --end         Finish point (lat,long).")
	print("-i | --icao        callsign in hex, Default:0x75008F")
	print("-a | --altitude    Starting altitude, Default:27000")
	print("-f | --final_alt   Final altitude, Default:altitude")
	print("-p | --speed       Airspeed in kph, Default:300")
	print("-r | --resolution  km(s) between transmissions, Default: 1")
	print("-n | --name        Unique name for file creation, Default:myRoute")
	print("-c | --callsign    Callsign, Default: pynny")
	print("")
	sys.exit(2)

def verify_coordinate(point):
    if len(point) != 2:
        usage("Point %s is incorrect length!" % str(point))
    lat, lon = float(point[0]), float(point[1])
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return (lat,lon)
    elif -90 <= lon <= 90 and -180 <= lat <= 180:
        usage("Point %s is probably reversed!" % str(point))
    else:
        usage("Point %s Cannot be interpreted!" % str(point))

def get_distance(start_point, end_point, R=6371.0088):
	lat1, lon1 = start_point
	lat2, lon2 = end_point
	dlat = radians(lat2-lat1)
	dlon = radians(lon2-lon1)
	a = sin(dlat/2) * sin(dlat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) * sin(dlon/2)
	c = 2 * atan2(sqrt(a), sqrt(1-a))
	return R * c

def intermediate_point(p1, p2, f=0.5):
	R = 6371008.8
	lat1, lon1 = radians(p1[0]), radians(p1[1])
	lat2, lon2 = radians(p2[0]), radians(p2[1])
	d = get_distance(p1, p2) / R
	a = sin((1 - f) * d) / sin(d)
	b = sin(f * d) / sin(d)
	x = a * cos(lat1) * cos(lon1) + b * cos(lat2) * cos(lon2)
	y = a * cos(lat1) * sin(lon1) + b * cos(lat2) * sin(lon2)
	z = a * sin(lat1) + b * sin(lat2)
	lat3 = degrees(atan2(z, sqrt(x * x + y * y)))
	lon3 = degrees(atan2(y, x))
	return (lat3, lon3)

def init_bearing(p1, p2):
    lat1, lon1 = radians(p1[0]), radians(p1[1])
    lat2, lon2 = radians(p2[0]), radians(p2[1])
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)
    y = sin(lon2 - lon1) * cos(lat2)
    course = atan2(y, x)
    return degrees(course)

def final_bearing(p1, p2):
    return (init_bearing(p2, p1) + 180) % 360

def main(argv=None):
	start,end,icao,alt,speed,name,resolution,falt,callsign,verbose = False,False,False,False,False,False,False,False,False,False
	try:
		(opts, args) = getopt(sys.argv[1:], 'hvs:e:i:a:p:n:r:f:c:', \
			['help','verbose','start=','end=','icao=','altitude=','speed=','name=','resolution=','final_alt=','callsign='])
	except GetoptError as err:
		usage("%s\n" % err)
	if len(opts) != 0:
		for (opt, arg) in opts:
			if opt in ('-h', '--help'):
				usage()
			elif opt in ('-v', '--verbose'):
				verbose = True
			elif opt in ('-s', '--start'):
				start = arg
			elif opt in ('-e', '--end'):
				end = arg
			elif opt in ('-i', '--icao'):
				icao = arg
			elif opt in ('-a', '--altitude'):
				alt = float(arg)
			elif opt in ('-f', '--final_alt'):
				falt = float(arg)
			elif opt in ('-p', '--speed'):
				speed = arg
			elif opt in ('-n', '--name'):
				name = arg
			elif opt in ('-c', '--callsign'):
				callsign = arg
			elif opt in ('-r', '--resolution'):
				resolution = float(arg)
			else:
				usage("Unknown option %s\n" % opt)
	else:
		usage()

	if not name:name = 'myRoute'

	if not icao:icao = '0x75008F'
	if not alt:alt = 27000
	if not start:usage("Starting point required.")
	if not end:usage("Finish point required.")
	if not resolution:resolution = 1
	if not falt:falt = alt
	if not callsign:callsign = 'pynny'

	if not speed:speed = 300

	sCrd = verify_coordinate((start.split(',')[0],start.split(',')[1]))
	eCrd = verify_coordinate((end.split(',')[0],end.split(',')[1]))

	distance = get_distance(sCrd,eCrd)
	div = 1 / floor(distance/resolution)

	if os.path.isdir(name):usage("Route directory '%s' already exists" % name)
	os.mkdir(name)

	file = open("%s/tx_samples.py"%name,"w+")
	baseCmd1,baseCmd2 = "hackrf_transfer -t "," -f 1090000000 -s 2000000 -x 20"
	file.write("#!/usr/bin/env python3\n\r")
	file.write("from os import system\n\r")
	file.write("import threading, time\n\n\r")

	i, mark = 0, floor(distance/resolution)
	interval = floor(((distance / mark) * 3600000) / float(speed))

	file.write("tx_interval = %s\n\n\r"%interval)
	
	file.write("def txCmd(name):\n\r")
	file.write("\tsystem(\"%s\"+name+\"%s\")\n\r"%(baseCmd1,baseCmd2))
	file.write("\t#print(\"%s\"+name+\"%s\")\n\n\r"%(baseCmd1,baseCmd2))
	file.write("smpFiles = (")
	coords = []
	while i < mark:
			
		curLocation = intermediate_point(sCrd,eCrd,((1 / mark) * i))
		curAltitude = int(alt + ((falt - alt) * ((1 / mark) * i)))
		filename = "%s_sample_%s.iq8s" % (name, i)
		command = "ADSB_Encoder.py --lat %s --lon %s -a %s -r 2 --callsign %s -i %s -o %s/%s" % \
			(curLocation[0],curLocation[1],curAltitude,callsign,icao,name,filename)

		coords.append([curLocation[0],curLocation[1],curAltitude,filename])
		file.write("'%s'"%filename)
		i+=1
		if i < mark:file.write(",")

	file.write(")\n\n\r")
	file.write("ticker = threading.Event()\n\r")
	
	file.write("cur = 1\n\r")
	file.write("txCmd(smpFiles[0])\n\r")
	file.write("while not ticker.wait(float(tx_interval/1000)):\n\r")
	file.write("\ttxCmd(smpFiles[cur])\n\r")
	file.write("\tcur +=1\n\r")
	file.write("\tif cur == len(smpFiles):break\n\n\r")

	file.close()
	os.chmod("%s/tx_samples.py"%name,0o755)
	if verbose:print("Transmit script written %s/tx_samples.py"%name)

	encoder = ADSB_Encoder()

	for i,coord in enumerate(coords):
		if i == (len(coords) - 1):coords[i].append(round(final_bearing((coords[i-1][0],coords[i-1][1]),(coord[0],coord[1]))))
		else:coords[i].append(round(init_bearing((coord[0],coord[1]),(coords[i+1][0],coords[i+1][1]))))

		curName = "%s/%s" % (name,coord[3])

		encoder._set_vars(coord[2],coord[0],coord[1],5,99564,0,2,False,0,11,icao,callsign,0,curName,speed,0,coord[4])
		if verbose:print("Encoding %s of %s" % (i+1, len(coords)))
		data = encoder.encode()
		if verbose:print("Writing %s/%s" % (name,coord[3]))
		encoder.writeOutputFile(data)


if __name__ == "__main__":
	main()















