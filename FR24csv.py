#!/usr/bin/env python3
#
# Will take a FR24 CSV and make a ADSB_Encoder CSV
import csv
import os
import argparse
import configparser

def auto_int(x):
    """Parses HEX into for argParser"""
    return int(x, 0)

def argParser():
    description = 'This script will take a FR24 CSV file and convert it into a format for ADSB_Encoder.py'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--icao', action='store', type=auto_int, dest='icao', default=cfg.get('plane', 'icao'), help='The ICAO number for the plane in hex. Ensure the ICAO is prefixed with \'0x\' to ensure this is parsed as a hex number. This is 24 bits long. Default: %(default)s')
    parser.add_argument('--csv', '--csvfile', '--in', '--input', action='store', type=str,  dest='csvfile', help='The name of the FR24 CSV file', required=True)  
    return parser.parse_args()

def main():
    global cfg
    cfg = configparser.ConfigParser()
    cfg.read('config.cfg')
    
    arguments = argParser()
    
    csvFilename = 'fr24.csv'
    
    time = 0
    
    with open(csvFilename, 'w', newline='') as csvfileout:
        output = csv.writer(csvfileout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        output.writerow(['time', 'icao', 'latitude', 'longitude', 'altitude'])
        with open(arguments.csvfile, newline='') as csvfilein:
            reader = csv.DictReader(csvfilein, delimiter=',')
            for row in reader:
                if time == 0:
                    time = int(row['Timestamp'])
                rowtime = int(row['Timestamp']) - time
                newrow = [rowtime, hex(arguments.icao), 'lat', 'long', row['Altitude']]
                output.writerow([newrow])
                print(newrow)
        csvfileout.close()

    
if __name__ == "__main__":
    main()