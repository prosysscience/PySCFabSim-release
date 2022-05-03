from simulation.greedy import run_greedy
import sys

sys.path.insert(0, '.')


def main():
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


if __name__ == '__main__':
    main()
