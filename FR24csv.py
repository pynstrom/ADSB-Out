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
    description = 'This script will take a FR24 CSV file and convert it into a format for FR24csv.py'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--icao', action='store', type=auto_int, dest='icao', default=cfg.get('plane', 'icao'), help='The ICAO number for the plane in hex. Ensure the ICAO is prefixed with \'0x\' to ensure this is parsed as a hex number. This is 24 bits long. Default: %(default)s')
    parser.add_argument('--csv', '--csvfile', '--in', '--input', action='store', type=str,  dest='csvfile', help='The name of the FR24 CSV file', required=True)  
    return parser.parse_args()

def reverseCSV(csvfile):
    """Reverse a CSV. Returns a dictionary of the CSV"""
    data = []
    with open(csvfile, newline='') as csvfilein:
        reader = csv.DictReader(csvfilein, delimiter=',')
        for row in reader:
            data.append(row)
    csvfilein.close()
    return reversed(data)

def main():
    global cfg
    cfg = configparser.ConfigParser()
    cfg.read('config.cfg')
    
    arguments = argParser()
    
    csvFilename = 'fr24.csv'
    
    time = 0
    #Need to reverse the FR24 CSV as it is in reverse order i.e. the most recent record is row 2 and the first ADS-B message of the flight is the last row in the CSV
    data = reverseCSV(arguments.csvfile)
    with open(csvFilename, 'w', newline='') as csvfileout:
        fieldnames = ['timestamp', 'icao', 'latitude', 'longitude', 'altitude']
        output = csv.DictWriter(csvfileout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)
        output.writeheader()
        for row in data:
            if time == 0:
                time = int(row['Timestamp'])
            rowtime = int(row['Timestamp']) - time
            position = row['Position'].split(',')
            newrow = {'timestamp':rowtime, 'icao':hex(arguments.icao), 'latitude':position[0], 'longitude':position[1], 'altitude':row['Altitude']}
            output.writerow(newrow)
        csvfileout.close()

    
if __name__ == "__main__":
    main()