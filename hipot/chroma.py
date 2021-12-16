#
# pyhipot - Python interface for HiPot tester.
#
# This file is for Chroma / QuadTech products.
#
# Copyright (C) Colin O'Flynn, 2021.
#

import serial
import struct

class Chroma19073(object):
    name = "Chroma 19073"

    test_results = {
        0x70:'STOP',
        0x71:'USER INTERRUPT',
        0x72:'CANNOT TEST',
        0x73:'TESTING',
        0x74:'PASS',
        0x75:'SKIPPED',
        0x79:'GFI TRIPPED',
        0x7A:'SLAVE FAILED',
        0x7B:'Cs/SHORT FAIL',

        #AC
        0x11:'AC HIGH FAIL',
        0x12:'AC LOW FAIL',
        0x13:'AC ARC FAIL',
        0x14:'AC I/O FAIL',
        0x15:'AC NO OUTPUT',
        0x16:'AC VOLT OVER',
        0x17:'AC CURRENT OVER',

        #DC
        0x21:'DC HIGH FAIL',
        0x22:'DC LOW FAIL',
        0x23:'DC ARC FAIL',
        0x24:'DC I/O FAIL',
        0x25:'DC NO OUTPUT',
        0x26:'DC VOLT OVER',
        0x27:'DC CURRENT OVER',
        0x28:'DC INRUSH FAIL',

        #OS
        0x61:'OS SHORT FAIL',
        0x62:'OS OPEN FAIL',
        0x64:'OS I/O FAIL',
        0x66:'OS VOLT OVER',
        0x67:'OS CURRENT OVER'
    }

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

    def check_reply(self):
        """Check a 'reply message' for a success"""
        response = self.read()

        if response[0] != 0x7F:
            raise IOError("Sync Error")

        if response[1] == 0:
            return

        elif response[1] == 1:
            raise IOError("Command Error")

        elif response[1] == 2:
            raise ValueError("Parameter Error (check values to ranges from manual)")

        else:
            raise IOError("Unknown reply: %d"%response[1])


    def send_receive_commandecho(self, command, parameters=[]):
        """Sends a command & receives response, where first byte of response is same as 'command'"""
        self.send(command, parameters)
        result = self.read()
        if result[0] != command:
            raise IOError("sync error")
        return result[1:]

    def identify(self):
        """Send '*IDN?' command, return string result"""
        result = self.send_receive_commandecho(0x90)
        result = result.decode("utf-8")
        return result

    def start(self):
        """Send 'start' command"""
        self.send(0x22)
        self.check_reply()

    def stop(self):
        """Send 'stop' command"""
        self.send(0x21)
        self.check_reply()

    def set_step_parameter_ac(self, step, voltage, ramp_time_sec, test_time_sec, fall_time_sec, high_limit_A, low_limit_A, arc_limit_A):
        """Setup a AC step"""

        ramp_time_sec *= 10
        test_time_sec *= 10
        fall_time_sec *= 10
        high_limit_A *= 10E6
        low_limit_A *= 10E6
        arc_limit_A *= 10E6

        payload = struct.pack("<BBHHHHHLLLL", step, 1, int(voltage), int(ramp_time_sec), 0,
                                   int(test_time_sec), int(fall_time_sec),
                                   int(high_limit_A), int(low_limit_A), int(arc_limit_A), 0)

        self.send(0x24, list(payload))
        self.check_reply()

    def set_step_parameter_dc(self, step, voltage, ramp_time_sec, dwell_time_s, test_time_sec, fall_time_sec, high_limit_A, low_limit_A, arc_limit_A, inrush=False):
        """Setup a DC step"""

        ramp_time_sec *= 10
        dwell_time_s *= 10
        test_time_sec *= 10
        fall_time_sec *= 10
        high_limit_A *= 10E6
        low_limit_A *= 10E6
        arc_limit_A *= 10E6

        if inrush:
            inrush = 10000
        else:
            inrush = 0

        payload = struct.pack("<BBHHHHHLLLL", step, 2, int(voltage), int(ramp_time_sec), int(dwell_time_s),
                                   int(test_time_sec), int(fall_time_sec),
                                   int(high_limit_A), int(low_limit_A), int(arc_limit_A), inrush)

        self.send(0x24, list(payload))
        self.check_reply()

    def clear_steps(self):
        """Clear all programmed steps"""
        self.send(0x2C)
        self.check_reply()

    def bytearray_to_items(self, data):
        #Item number from command references PDF
        items = {}
        items[1] = data[0]
        items[2] = struct.unpack('<H', data[1:3])[0]
        items[4] = struct.unpack('<L', data[3:7])[0]
        items[8] = struct.unpack('<L', data[7:11])[0]
        items[16] = struct.unpack('<H', data[7:9])[0]
        items[32] = struct.unpack('<H', data[13:15])[0]
        items[64] = struct.unpack('<H', data[9:11])[0]
        items[128] = struct.unpack('<H', data[11:13])[0]
        return items

    def get_result(self, step=0):
        """Send 'result?' command for step, '0' returns current/last result"""
        result = self.send_receive_commandecho(0xb1, [step, 0xD7])

        idx = 0
        measurement = {}
        measurement_new_test_result = result[idx] #not sure what this is
        measurement['step'] = result[idx+1]

        measurement['result code'] = self.test_results[result[idx+2]]
        if result[idx+3] != 0xD7:
            raise IOError("Expected 'D7' here?")

        data = result[(idx+4):]
        items = self.bytearray_to_items(data)

        if data[0] == 1:
            #AC Mode
            measurement['mode'] = 'AC'
            measurement['voltage'] = items[2]
            measurement['current'] = items[4] * 100E-9
            measurement['ramp time'] = items[16] * 100E-3
            measurement['test time'] = items[64] * 100E-3
            measurement['fall time'] = items[128] * 100E-3
            pass
        elif data[0] == 2:
            #DC Mode
            measurement['mode'] = 'DC'
            # Sentry 20 doesn't seem to have these 'keys'. This has only been tested
            # on a sentry 20, so maybe none of them do?
            if 8 in items.keys():
                measurement['inrush']  = struct.unpack('<L', data[7:11])[0] * 100E-9
            measurement['ramp time'] = struct.unpack('<H', data[7:9])[0] * 100E-3
            if 32 in items.keys():
                measurement['dwell time'] = struct.unpack('<H', data[13:15])[0] * 100E-3
            measurement['voltage'] = items[2]
            measurement['current'] = items[4] * 100E-9
            measurement['ramp time'] = items[16] * 100E-3
            measurement['test time'] = items[64] * 100E-3
            measurement['fall time'] = items[128] * 100E-3

        elif data[0] == 3:
            #IR Mode
            measurement['mode'] = 'IR'
            raise NotImplementedError()
        elif data[0] == 4:
            #GC Mode
            measurement['mode'] = 'GC'
        elif data[0] == 5:
            #PA Mode
            measurement['mode'] = 'PA'
            raise NotImplementedError()
        elif data[0] == 6:
            #OS Mode
            measurement['mode'] = 'OS'
            measurement['voltage'] = struct.unpack('<H', data[1:3])[0]
            measurement['cap_pF'] = struct.unpack('<L', data[3:7])[0]
            measurement['test time'] = struct.unpack('<H', data[9:11])[0] * 100E-3
        else:
            raise IOError("Fail?")

        return measurement

    def wait_and_return_results(self):
        """Wait for test started with `start()` to finish, return all steps"""

        status = "TESTING"

        while status == "TESTING":
            resp = self.get_result()
            status = resp['result code']

        final_step = resp['step']

        measurements = []
        for i in range(1, final_step+1):
            measurements.append(self.get_result(i))

        return measurements

class QuadTechSentry20(Chroma19073):
    name = "QuadTech Sentry 20 Plus"

    def bytearray_to_items(self, data):
        items = {}
        items[1] = data[0]
        items[2] = struct.unpack('<H', data[1:3])[0]
        items[4] = struct.unpack('<L', data[3:7])[0]
        items[16] = struct.unpack('<H', data[7:9])[0]
        items[64] = struct.unpack('<H', data[9:11])[0]
        items[128] = struct.unpack('<H', data[11:13])[0]
        return items