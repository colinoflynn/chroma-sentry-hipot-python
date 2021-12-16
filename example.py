import time
from hipot.chroma import QuadTechSentry20

s = QuadTechSentry20("/dev/ttyS14")
print(s.identify())
#s.start()
#while s.get_last_result()[0]['result code'] == 'TESTING':
#    continue
#print(s.get_last_result())
#s.stop()

s.set_step_parameter_ac(2, 1000, 0.5, 3, 0.2, 5E-6, 0, 0)