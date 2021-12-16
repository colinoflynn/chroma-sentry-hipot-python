import time
from hipot.chroma import QuadTechSentry20

s = QuadTechSentry20("/dev/ttyS14")
print(s.identify())
s.start()
data = s.wait_and_return_results()
s.stop()

print(data)

s.clear_steps()

#s.set_step_parameter_ac(2, 1000, 0.5, 3, 0.2, 5E-6, 0, 0)