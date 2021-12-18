import time
from hipot.chroma import QuadTechSentry20

s = QuadTechSentry20("/dev/ttyS14")
print(s.identify())
s.start()
data = s.wait_and_return_results()
s.stop()

print(data)

s.clear_steps()

s.set_step_parameter_dc(1, voltage=1000,
                           ramp_time_sec=3,
                           test_time_sec=60,
                           high_limit_A=1E-6)

