import io
import os
import subprocess
import time
from os import listdir, path, mkdir

root = 'experiments'

dirs = listdir(root)
while True:
    for d in sorted(dirs):
        for checkpoint in [50000, 100000, 150000, 200000, 300000, 400000, 500000, 600000, 800000, 1000000, 1200000, 1400000, 1600000, 1800000, 2000000]:
            report_loc = path.join(root, d, f'report_{checkpoint}.txt')
            weights_loc = f'checkpoint__{checkpoint}_steps.zip'
            if path.exists(path.join(root, d, weights_loc)) and not path.exists(report_loc):
                print(d)
                with io.open(report_loc, 'w') as f:
                    subprocess.call(['python3', 'rl_test.py', path.join(root, d), weights_loc],
                                    stdout=f)


    print('No more experiments to run.')
    time.sleep(10)

