import io
import json
import statistics
from collections import defaultdict
from os import listdir, path


def read_references():
    out = {}
    for t in ['lots', 'machines']:
        out[t] = {}
        for ds in ['HVLM', 'LVHM']:
            out[t][ds] = defaultdict(lambda: 0)
            file_name = f'datasets/{t}_SMT2020_{ds}.txt'
            with io.open(file_name, 'r') as f:
                lines = f.read().split('\n')
                headers = lines[0].split(' ')
                rows = [a.split(' ') for a in lines[1:]]
                for row in rows:
                    for h, c in zip(headers[1:], row[1:]):
                        out[t][ds][(h, row[0])] = c
    return out


def handle_obj(datas):
    o = {}
    for k, v in datas[0].items():
        its = [d[k] for d in datas]
        if type(v) is dict:
            o[k] = handle_obj(its)
        elif type(v) in [int, float]:
            o[k] = (statistics.mean(its), statistics.stdev(its))
        else:
            assert False
    return o


def loadfile(f):
    with io.open(f, 'r') as q:
        return q.read()


def main():
    dirs = ['greedy']

    results = {}
    names = set()

    runs = 10

    lots = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    machines = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for d in dirs:
        subs = listdir(d)
        for s in subs:
            if path.isfile(d + '/' + s) and 'seed0' in s and s.endswith('.json'):
                file_locs = [d + '/' + s.replace('seed0_', f'seed{r}_') for r in range(runs)]
                name = f'{len(file_locs)}x {s.replace("seed0_", "")}'
                results[name] = {'files': file_locs}
            elif path.isdir(d + '/' + s) and s.startswith('0_'):
                s = s[2:]
                ds = 'HVLM' if 'HVLM' in s else 'LVHM'
                dispatcher = 'fifo' if 'fifo' in s else 'cr'
                y2n = f'rl2y_730days_{ds}_{dispatcher}.json'
                d180n = f'rl180_180days_{ds}_{dispatcher}.json'
                file_locs_2y = [path.join(d, str(r) + '_' + s, y2n) for r in range(runs)]
                file_locs_180d = [path.join(d, str(r) + '_' + s, d180n) for r in range(runs)]
                name180 = f'{len(file_locs_2y)}x {d}_180days_{s}'
                name730 = f'{len(file_locs_2y)}x {d}_730days_{s}'
                results[name180] = {'files': file_locs_180d}
                results[name730] = {'files': file_locs_2y}

    for name in results.keys():
        names.add(name)
        d = results[name]
        files = d['files']
        datas = [json.loads(loadfile(f)) for f in files]
        r = d['avgs'] = handle_obj(datas)
        for k, v in sorted(r['lots'].items(), key=lambda k: k[0]):
            lots[k][name] = dict(
                act=round(v["ACT"][0], 2),
                th=round(v["throughput"][0], 2),
                on_time=round(v["on_time"][0] / v["throughput"][0] * 100),
                tardiness=round(v["tardiness"][0] / v["throughput"][0] / 24),
            )

        for k, v in sorted(r['machines'].items(), key=lambda k: k[0]):
            machines[k][name] = dict(
                avail=round(v["avail"][0] * 100, 2),
                util=round(v["util"][0] * 100, 2),
                pm=round(v["pm"][0] * 100, 2),
                br=round(v["br"][0] * 100, 2),
                setup=round(v["setup"][0] * 100, 2),
                waiting_time=round(v["waiting_time"][0], 2),
            )

    print('\t', end='')
    names = sorted(list(names))
    for name in names:
        print(name.replace(':', '').replace('\t', ''), '\t\t', end='')
    print()

    print('', end='\t')
    for name in names:
        print('act\tth\ton_time\ttardiness', end='\t')
    print()

    ref = read_references()

    for lot in sorted(lots.keys()):
        t = lots[lot]
        print(lot, end='\t')
        for name in names:
            i = ref['lots']['HVLM' if 'HVLM' in name else 'LVHM']
            for x in ['act', 'th', 'on_time']:
                i[(x, lot)] = float(i[(x, lot)])
                print(f"{i[(x, lot)]}->{t[name][x]} ({round(t[name][x] - i[(x, lot)], 2)})", end='\t')
            print(t[name]['tardiness'], end='\t')
        print()

    print('', end='\t')
    for name in names:
        print('avail\t\t\tutil\t\t\tpm\t\t\tbr\t\t\tsetup\t\t\twaiting_time_before', end='\t')
    print()
    print('', end='\t')
    for name in names:
        print('old\tnew\tdelta\told\tnew\tdelta\told\tnew\tdelta\told\tnew\tdelta\told\tnew\tdelta\tnew', end='\t')
    print()
    for machine in sorted(machines.keys()):
        t = machines[machine]
        print(machine, end='\t')
        for name in names:
            i = ref['machines']['HVLM' if 'HVLM' in name else 'LVHM']
            for x in ['avail', 'util', 'pm', 'br', 'setup']:
                i[(x, machine)] = float(i[(x, machine)])
                print(f"{i[(x, machine)]}\t{t[name][x]}\t{round(t[name][x] - i[(x, machine)], 2)}", end='\t')
                # print(f"{round(t[name][x] - i[(x, machine)], 2)}", end='\t')
            print(t[name]['waiting_time'], end='\t')
        print()


if __name__ == '__main__':
    main()
