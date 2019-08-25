from ModeSLocation import ModeSLocation
import math
import numpy
###############################################################
# Further work on fork
# Copyright (C) 2017 David Robinson
class ModeS:
    """This class handles the ModeS ADSB manipulation
    """
    
    def df17_pos_rep_encode(self, ca, icao, tc, ss, nicsb, alt, time, lat, lon, surface):
        """
        This will take the parameters for an ADSB type 17 message and reutrn the even and odd bytes
        """

        format = 17 #The format type of an ADSB message

        location = ModeSLocation()
        enc_alt =	location.encode_alt_modes(alt, surface)
        #print "Alt(%r): %X " % (surface, enc_alt)
        
        #encode that position
        (evenenclat, evenenclon) = location.cpr_encode(lat, lon, False, surface)
        (oddenclat, oddenclon)   = location.cpr_encode(lat, lon, True, surface)

        #print "Even Lat/Lon: %X/%X " % (evenenclat, evenenclon)
        #print "Odd  Lat/Lon: %X/%X " % (oddenclat, oddenclon)

        ff = 0
        df17_even_bytes = []
        df17_even_bytes.append((format<<3) | ca)
        df17_even_bytes.append((icao>>16) & 0xff)
        df17_even_bytes.append((icao>> 8) & 0xff)
        df17_even_bytes.append((icao    ) & 0xff)
        # data
        df17_even_bytes.append((tc<<3) | (ss<<1) | nicsb)
        df17_even_bytes.append((enc_alt>>4) & 0xff)
        df17_even_bytes.append((enc_alt & 0xf) << 4 | (time<<3) | (ff<<2) | (evenenclat>>15))
        df17_even_bytes.append((evenenclat>>7) & 0xff)
        df17_even_bytes.append(((evenenclat & 0x7f) << 1) | (evenenclon>>16))
        df17_even_bytes.append((evenenclon>>8) & 0xff)
        df17_even_bytes.append((evenenclon   ) & 0xff)

        df17_str = "{0:02x}{1:02x}{2:02x}{3:02x}{4:02x}{5:02x}{6:02x}{7:02x}{8:02x}{9:02x}{10:02x}".format(*df17_even_bytes[0:11])
        #print df17_str , "%X" % bin2int(crc(df17_str+"000000", encode=True)) , "%X" % get_parity(hex2bin(df17_str+"000000"), extended=True)
        df17_crc = self.bin2int(self.modes_crc(df17_str+"000000", encode=True))

        df17_even_bytes.append((df17_crc>>16) & 0xff)
        df17_even_bytes.append((df17_crc>> 8) & 0xff)
        df17_even_bytes.append((df17_crc    ) & 0xff)
     
        ff = 1
        df17_odd_bytes = []
        df17_odd_bytes.append((format<<3) | ca)
        df17_odd_bytes.append((icao>>16) & 0xff)
        df17_odd_bytes.append((icao>> 8) & 0xff)
        df17_odd_bytes.append((icao    ) & 0xff)
        # data
        df17_odd_bytes.append((tc<<3) | (ss<<1) | nicsb)
        df17_odd_bytes.append((enc_alt>>4) & 0xff)
        df17_odd_bytes.append((enc_alt & 0xf) << 4 | (time<<3) | (ff<<2) | (oddenclat>>15))
        df17_odd_bytes.append((oddenclat>>7) & 0xff)
        df17_odd_bytes.append(((oddenclat & 0x7f) << 1) | (oddenclon>>16))
        df17_odd_bytes.append((oddenclon>>8) & 0xff)
        df17_odd_bytes.append((oddenclon   ) & 0xff)

        df17_str = "{0:02x}{1:02x}{2:02x}{3:02x}{4:02x}{5:02x}{6:02x}{7:02x}{8:02x}{9:02x}{10:02x}".format(*df17_odd_bytes[0:11])
        df17_crc = self.bin2int(self.modes_crc(df17_str+"000000", encode=True))

        df17_odd_bytes.append((df17_crc>>16) & 0xff)
        df17_odd_bytes.append((df17_crc>> 8) & 0xff)
        df17_odd_bytes.append((df17_crc    ) & 0xff)
        
        return (df17_even_bytes, df17_odd_bytes)

    #From https://github.com/jaywilhelm/ADSB-Out_Python on 2019-08-18
    # TODO There is something up with the math and rounding or something need work on this more and understand the math actually going on
    def vel_heading_encode(self, ca, icao, in_velocity, in_heading_deg, vertical_rate):
        #(ca,icao,ew_dir,ew_vel,ns_dir,ns_vel)
        df = 17
        #ca = 5

        #1-5    downlink format
        #6-8    CA capability
        #9-32   ICAO
        #33-88  DATA -> 33-87 w/ 33-37 TC
        #89-112 Parity
        in_heading_rad = numpy.deg2rad(in_heading_deg)
        V_EW = abs(int(in_velocity*numpy.sin(in_heading_rad)))
        V_NS = abs(int(in_velocity*numpy.cos(in_heading_rad)))

        quadrant = numpy.floor(in_heading_deg / 90)

        if(quadrant == 0):
            S_EW = 1
            S_NS = 1
        elif(quadrant == 1):
            S_EW = 0
            S_NS = 1
        elif(quadrant == 2):
            S_EW = 0
            S_NS = 0
        else:
            S_EW = 1
            S_NS = 0

        S_Vr = 1
        Vr = int(vertical_rate)

        if(vertical_rate < 0):
            Vr = -Vr
            S_Vr = 0

        tc = 19     #33-37  1-5 type code
        st = 0x01   #38-40  6-8 subtype, 3 air, 1 ground speed
        ic = 0 #      #41     9 intent change flag
        resv_a = 0#1  #42     10
        NAC = 2#0     #43-45  11-13 velocity uncertainty
        #S_EW = 1#1    #46     14
        #V_EW = 97#9    #47-56  15-24
        #S_NS = 0#1    #57     25 north-south sign
        #V_NS = 379#0xA0 #58-67  26-35 160 north-south vel
        VrSrc = 1#0   #68     36 vertical rate source
        #S_Vr = 1#1    #69     37 vertical rate sign
        #Vr = 41#0x0E   #70-78  38-46 14 vertical rate
        RESV_B = 0  #79-80  47-48
        S_Dif = 0   #81     49 diff from baro alt, sign
        Dif = 0x1c#0x17  #82-88  50-66 23 diff from baro alt

        ca = 5
        #icao = 0xabcdef#0xa06703 #0x485020 #

        dfvel = []
        dfvel.append((df << 3) | ca)
        dfvel.append((icao >> 16) & 0xff)
        dfvel.append((icao >> 8) & 0xff)
        dfvel.append((icao) & 0xff)
        # data
        dfvel.append((tc << 3) | st)
        dfvel.append((ic << 7) | (resv_a << 6) | (NAC << 3) | (S_EW << 2) | ((V_EW >> 8) & 0x03))
        dfvel.append(0xFF & V_EW)
        dfvel.append((S_NS << 7) | ((V_NS >> 3))) #& 0x7F))
        dfvel.append(((V_NS << 5) & 0xE0) | (VrSrc << 4) | (S_Vr << 3) | ((Vr >> 6) & 0x03))
        dfvel.append(((Vr  << 2) & 0xFC) | (RESV_B))
        dfvel.append((S_Dif << 7) | (Dif))
        dfvel_str = "{0:02x} {1:02x} {2:02x} {3:02x} {4:02x} {5:02x} {6:02x} {7:02x} {8:02x} {9:02x} {10:02x}".format(
            *dfvel[0:11])
        dfvel_str2 = "{0:02x}{1:02x}{2:02x}{3:02x}{4:02x}{5:02x}{6:02x}{7:02x}{8:02x}{9:02x}{10:02x}".format(
            *dfvel[0:11])
        crc_str = "%X" % self.bin2int(self.modes_crc(dfvel_str2+"000000", encode=True))
        dfvel_crc = self.bin2int(self.modes_crc(dfvel_str2 + "000000", encode=True))
        dfvel.append((dfvel_crc >> 16) & 0xff)
        dfvel.append((dfvel_crc >> 8) & 0xff)
        dfvel.append((dfvel_crc) & 0xff)
        return dfvel

    #From https://github.com/jaywilhelm/ADSB-Out_Python on 2019-08-25
    # TODO the callsign must be 8 
    def callsign_encode(self, ca, icao, csname):
        if len(csname) > 8 or len(csname) <= 0:
            print ("Name length error")
            return null
        csname = csname.upper()

        df = 17
        #ca = 5
        #icao = 0xabcdef
        #csname = 'ABCD1234'
        tc = 1
        ec = 1

        #df = 17
        #ca = 5
        #icao = 0x4840D6
        #csname = 'KLM1023_'
        #tc = 4
        #ec = 0

        map = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ#####_###############0123456789######"

        dfname = []
        dfname.append((df << 3) | ca)
        dfname.append((icao >> 16) & 0xff)
        dfname.append((icao >> 8) & 0xff)
        dfname.append((icao) & 0xff)
        #2C C3 71 C3 2C E0
        dfname.append((tc << 3) | (ec))
        dfname.append((0xFC & (int(map.find(csname[0])) << 2)) | (0x03 & (int(map.find(csname[1])) >> 6)))
        dfname.append((0xF0 & (int(map.find(csname[1])) << 4)) | (0x0F & (int(map.find(csname[2])) >> 2)))
        dfname.append((0xF0 & (int(map.find(csname[2])) << 6)) | (0x3F & (int(map.find(csname[3])) >> 0)))
        dfname.append((0xFC & (int(map.find(csname[4])) << 2)) | (0x03 & (int(map.find(csname[5])) >> 4)))
        dfname.append((0xF0 & (int(map.find(csname[5])) << 4)) | (0x0F & (int(map.find(csname[6])) >> 2)))
        dfname.append((0xF0 & (int(map.find(csname[6])) << 6)) | (0x3F & (int(map.find(csname[7])) >> 0)))

        #for i in range(6):
        #    print("{0:02X}".format(dfname[i+5]))

        dfname_str = "{0:02x} {1:02x} {2:02x} {3:02x} {4:02x} {5:02x} {6:02x} {7:02x} {8:02x} {9:02x} {10:02x}".format(
            *dfname[0:11])
        #print(dfname_str)
        dfname_str2 = "{0:02x}{1:02x}{2:02x}{3:02x}{4:02x}{5:02x}{6:02x}{7:02x}{8:02x}{9:02x}{10:02x}".format(
            *dfname[0:11])
        crc_str = "%X" % self.bin2int(self.modes_crc(dfname_str2 + "000000", encode=True))
        #print(crc_str)
        # print(dfvel_str), " %X" % +"000000", encode=True))
        # , "%X" % get_parity(hex2bin(dfvel_str+"000000"), extended=True))
        dfname_crc = self.bin2int(self.modes_crc(dfname_str2 + "000000", encode=True))
        dfname.append((dfname_crc >> 16) & 0xff)
        dfname.append((dfname_crc >> 8) & 0xff)
        dfname.append((dfname_crc) & 0xff)
        #msg = []
        #dfname_str = "{0:02x}{1:02x}{2:02x}{3:02x}{4:02x}{5:02x}{6:02x}{7:02x}{8:02x}{9:02x}{10:02x}".format(
        #    *dfname[0:11])
        #print(csname)
        #print(decode_callsign(dfname_str))
        return dfname

###############################################################

# Copyright (C) 2015 Junzi Sun (TU Delft)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# the polynominal generattor code for CRC

        
    def modes_crc(self, msg, encode=False):
        """Mode-S Cyclic Redundancy Check
        Detect if bit error occurs in the Mode-S message
        Args:
            msg (string): 28 bytes hexadecimal message string
            encode (bool): True to encode the date only and return the checksum
        Returns:
            string: message checksum, or partity bits (encoder)
        """

        GENERATOR = "1111111111111010000001001" # Currently don't know what is magic about this number
        
        msgbin = list(self.hex2bin(msg))

        if encode:
            msgbin[-24:] = ['0'] * 24

        # loop all bits, except last 24 piraty bits
        for i in range(len(msgbin)-24):
            # if 1, perform modulo 2 multiplication,
            if msgbin[i] == '1':
                for j in range(len(GENERATOR)):
                    # modulo 2 multiplication = XOR
                    msgbin[i+j] = str((int(msgbin[i+j]) ^ int(GENERATOR[j])))

        # last 24 bits
        reminder = ''.join(msgbin[-24:])
        return reminder
    
            
        
    def hex2bin(self, hexstr):
        """Convert a hexdecimal string to binary string, with zero fillings. """
        scale = 16
        num_of_bits = len(hexstr) * math.log(scale, 2)
        binstr = bin(int(hexstr, scale))[2:].zfill(int(num_of_bits))
        return binstr

    def bin2int(self, binstr):
        """Convert a binary string to integer. """
        return int(binstr, 2)
