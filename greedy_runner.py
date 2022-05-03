import io
import os
import subprocess
import threading
import time

threads = []

if not os.path.exists('greedy'):
    os.mkdir('greedy')

for seed in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
    for day in [365*2]:
        for dataset, dispatcher in [('HVLM', 'fifo'), ('LVHM', 'cr')]:
            def s(day_, dataset_, dispatcher_):
                name_ = f'greedy/greedy_seed{seed}_{day}days_{dataset}_{dispatcher}.txt'
                with io.open(name_, 'w') as f:
                    print(name_)
                    subprocess.call(['pypy3', 'main.py', '--days', str(day_),
                                     '--dataset', dataset_, '--dispatcher', dispatcher_, '--seed', str(seed),
                                     '--alg', 'l4m'], stdout=f)


            t = threading.Thread(target=s, args=(day, dataset, dispatcher))
            t.start()
            time.sleep(2)
            threads.append(t)

for t in threads:
    t.join()

print('Done')
