import serial

class Chroma19073(object):
    name = "Chroma 19073"

    def __init__(self, comport, baud=19200):
        self.ser = serial.Serial(comport, baud)
        self.destaddr = 1
        self.srcaddr = 0x70

    def send(self, command, parameters=[]):
        """Send a command to the tester unit and return"""
        length = len(parameters)+1

        if parameters:
            payload = [command] + parameters
        else:
            payload = [command]

        packet = [0xAB, self.destaddr, self.srcaddr, length] + payload

        #Checksum in 2's complement
        cs = self.destaddr + self.srcaddr + length
        for i in payload:
            cs += i
        cs = (-cs) % 256
        
        packet = packet + [cs]

        self.ser.write(packet)
    
    def read(self, blocking=True):
        """Wait for a response from the tester unit"""
        if blocking is False:
            raise NotImplementedError("Oops, I did it again!")

        while self.ser.read(1)[0] != 0xAB:
            continue
        
        destaddr = self.ser.read(1)[0]
        srcaddr = self.ser.read(1)[0]
        length = self.ser.read(1)[0]
        payload = self.ser.read(length)
        checksum = self.ser.read(1)[0]

        if destaddr != self.srcaddr:
            raise("IOError - packet not for us?")

        if srcaddr != self.destaddr:
            raise("IOError - packet not from them?")

        calc_checksum = destaddr + srcaddr + length
        for i in payload:
            calc_checksum += i     
        calc_checksum = (-calc_checksum) % 256

        if calc_checksum != checksum:
            print("%02x %02x %02x %s %02x"%(destaddr, srcaddr, length, payload, checksum))
            raise IOError("Calculated checksum (%02x) does not match received (%02x)"%(calc_checksum, checksum))
        
        return payload

    def identify(self):
        """Send '*IDN?' command, return string result"""
        self.send(0x90)
        result = self.read()
        if result[0] != 0x90:
            raise IOError("Sync error")
        result = result[1:]
        result = result.decode("utf-8")
        return result
    
    def start(self):
        """Send 'start' command"""
        self.send(0x22)
        result = self.read()
    
    def get_last_result(self):
        """Send 'result?' command for last result"""
        self.send(0xb1, [0x00, 0xD7])
        result = self.read()
        print(result)




class QuadTechSentry20(Chroma19073):
    name = "QuadTech Sentry 20 Plus"

import time

s = QuadTechSentry20("/dev/ttyS14")
print(s.identify())
s.start()
s.get_last_result()
time.sleep(5)
s.get_last_result()