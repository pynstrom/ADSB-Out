#!/usr/bin/env python3

from HackRF import HackRF
from PPM import PPM
from ModeS import ModeS
from getopt import getopt, GetoptError
import os,csv,sys

class ADSB_Encoder:
	def _set_vars(self,alt,lat,lon,capability,imgap,nicsup,rp,gnd,sstat,tc,icao,callsign,time,filename,speed,vspeed,heading):
		self.altitude = float(alt)
		self.callsign = callsign
		self.capability = capability
		self.icao = int(icao,16)
		self.intermessagegap = imgap
		self.latitude = float(lat)
		self.longitude = float(lon)
		self.nicsupplementb = nicsup
		self.outputfilename = filename
		self.repeats = rp
		self.surface = gnd
		self.surveillancestatus = sstat
		self.time = time
		self.typecode = tc
		self.speed = float(speed)*0.53996
		self.vspeed = float(vspeed)
		while heading < 0:heading = heading + 360
		if 0 <= float(heading) <= 89:self.heading = float(heading) + 180
		elif 90 <= float(heading) <= 179:self.heading = float(heading)
		elif 180 <= float(heading) <= 269:self.heading = float(heading) - 180
		elif 270 <= float(heading) <= 359:self.heading = float(heading)
		else:
			if __name__ == "__main__":usage("Invalid bearing.")

	def encode(self):
		samples = bytearray()
		for i in range(0, self.repeats):
			modes = ModeS()

			(df17_pos_even, df17_pos_odd) = modes.df17_pos_rep_encode(self.capability, self.icao, self.typecode, \
				self.surveillancestatus, self.nicsupplementb, self.altitude, self.time, self.latitude, \
				self.longitude, self.surface)

			df17_velocity = modes.vel_heading_encode(self.capability, self.icao, self.speed, self.heading, self.vspeed) 

			df17_callsign = modes.callsign_encode(self.capability, self.icao, self.callsign)

			ppm = PPM()
			df17_array_position = ppm.frame_1090es_ppm_modulate(df17_pos_even, df17_pos_odd)
			df17_array_velocity = ppm.frame_1090es_ppm_modulate(df17_velocity, df17_velocity)
			df17_array_callsign = ppm.frame_1090es_ppm_modulate(df17_callsign, df17_callsign)

			hackrf = HackRF()
			#Position
			samples_array = hackrf.hackrf_raw_IQ_format(df17_array_position)
			samples = samples+samples_array
			gap_array = ppm.addGap(self.intermessagegap)
			samples_array = hackrf.hackrf_raw_IQ_format(gap_array)
			samples = samples+samples_array
			#Velocity
			samples_array = hackrf.hackrf_raw_IQ_format(df17_array_velocity)
			samples = samples+samples_array
			gap_array = ppm.addGap(self.intermessagegap)
			samples_array = hackrf.hackrf_raw_IQ_format(gap_array)
			samples = samples+samples_array
			#Callsign
			samples_array = hackrf.hackrf_raw_IQ_format(df17_array_callsign)
			samples = samples+samples_array
			gap_array = ppm.addGap(self.intermessagegap)
			samples_array = hackrf.hackrf_raw_IQ_format(gap_array)
			samples = samples+samples_array
		return samples

	def writeOutputFile(self, data):
		tmpfile = '%s.tmp'%(self.outputfilename)
		SamplesFile = open(tmpfile, 'wb')
		SamplesFile.write(data)
		SamplesFile.close()
		os.system('sync')
		os.system('rm -rf %s' % (self.outputfilename))
		os.system("dd if=%s of=%s bs=4k seek=63 > /dev/null 2>&1" % (tmpfile, self.outputfilename))
		os.system('sync')
		os.system('rm %s'%(tmpfile))


def usage(msg=False):
	if msg:print(msg)
	print("Usage: %s [options]\n" % sys.argv[0])
	print("-h | --help              Display help message.")
	print("-i | --icao <opt>        Callsign in hex, Default:0x75008F")
	print("--lat <opt>              Latitude for the plane in decimal degrees..")
	print("--long <opt>             Longitude for the place in decimal degrees.")
	print("-a | --altitude <opt>    Altitude in decimal feet, Default:27000.0")
	print("-s | --speed <opt>       Airspeed in decimal kph, Default:300")
	print("-v | --vspeed <opt>      Vertical speed, Default:0")
	print("-b | --bearing <opt>     Bearing in decimal degrees. Default:0")
	print("-c | --callsign <opt>    Callsign (8 chars max), Default:pynny")
	print("-t | --time <opt>        0 indicates time not synchronous with UTC, Default:0")
	print("-r | --repeats <opt>     Number of tx repeats, Default:1")
	print("-o | --output <opt>      iq8s output filename. Default:Samples_256K.iq8s")
	print("--capability <opt>       Capability, Default:5")
	print("--typecode <opt>         ADS-B message type, Default:11")
	print("--sstatus <opt>          Surveillance status, Default:0")
	print("--nicsupplementb <opt>   NIC supplement-B, Default:0")
	print("--intermessagegap <opt>  Delay between csv output(microSec), Default:99564")
	print("--surface                Aircraft located on ground, Default:False")
	print("")
	sys.exit(2)

def main():
	alt,lat,lon,capability,imgap,nicsup,rp,gnd,sstat,tc,icao,callsign,time,filename,speed,vspeed,heading = \
		27000,38.919909,-75.5884171,5,99564,0,1,False,0,11,'0x75008F','pynny',0,'Samples_256K.iq8s',300,0,0
	try:
		(opts, args) = getopt(sys.argv[1:], 'hi:a:s:v:b:c:t:r:o:', \
			['help','icao=','lat=','long=','altitude=','speed=','vspeed=','bearing=','callsign=',
			'time=','repeats=','output=','surface','capability=','typecode=','sstatus=',
			'nicsupplementb=','intermessagegap='])
	except GetoptError as err:
		usage("%s\n" % err)
	if len(opts) != 0:
		for (opt, arg) in opts:
			if opt in ('-h', '--help'):usage()
			elif opt in ('-a', '--altitude'):alt = arg
			elif opt in ('--lat'):lat = arg
			elif opt in ('--long'):lon = arg
			elif opt in ('-i', '--icao'):icao = arg
			elif opt in ('-s', '--speed'):speed = arg
			elif opt in ('-v', '--vspeed'):vspeed = arg
			elif opt in ('-b', '--bearing'):heading = arg
			elif opt in ('-c', '--callsign'):callsign = arg
			elif opt in ('-t', '--time'):time = arg
			elif opt in ('-r', '--repeats'):repeats = arg
			elif opt in ('-o', '--output'):filename = arg
			elif opt in ('--capability'):capability = arg
			elif opt in ('--typecode'):tc = arg
			elif opt in ('--sstatus'):sstat = arg
			elif opt in ('--nicsupplementb'):nicsup = arg
			elif opt in ('--intermessagegap'):imgap = arg
			elif opt in ('--surface'):gnd = True
			else:usage("Unknown option %s\n" % opt)

	encoder = ADSB_Encoder()
	encoder._set_vars(alt,lat,lon,capability,imgap,nicsup,rp,gnd,sstat,tc,icao,callsign,time,filename,speed,vspeed,heading)

	#attrs = vars(encoder)
	#print(', '.join("%s: %s" % item for item in attrs.items()))

	data = encoder.encode()
	encoder.writeOutputFile(data)

if __name__ == "__main__":
	main()





