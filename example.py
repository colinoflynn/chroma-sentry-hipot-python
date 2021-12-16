import time
from hipot.chroma import QuadTechSentry20

s = QuadTechSentry20("/dev/ttyS14")
print(s.identify())
s.start()
while s.get_last_result()[0]['result code'] == 'TESTING':
    continue
print(s.get_last_result())
s.stop()