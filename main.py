from simulation.greedy import run_greedy
from rl_train import main as rl_train
from rl_test import main as rl_test 
import sys
import time

sys.path.insert(0, '.')


def greedy():
    profile = False
    if profile:
        from pyinstrument import Profiler

        p = Profiler()
        p.start()

    run_greedy()
    print()
    print()

    if profile:
        p.stop()
        p.open_in_browser()

def PPO():
    profile = False
    start = time.time()
    if profile:
        from pyinstrument import Profiler

        p = Profiler()
        p.start()

    rl_train()
    print('---------------------------------------')
    print()
    #rl_test()

    if profile:
        p.stop()
        p.open_in_browser()
    end = time.time()
    div = end - start
    print("Time: " + str(div))


if __name__ == '__main__':
    #PPO()
    greedy()