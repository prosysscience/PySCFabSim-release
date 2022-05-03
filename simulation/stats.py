import datetime
import io
import json
import statistics
from collections import defaultdict

from simulation.classes import Lot, Step


def print_statistics(instance, days, dataset, disp, method='greedy', dir='greedy'):
    from simulation.instance import Instance
    instance: Instance
    lot: Lot
    lots = defaultdict(lambda: {'ACT': [], 'throughput': 0, 'on_time': 0, 'tardiness': 0, 'waiting_time': 0,
                                'processing_time': 0, 'transport_time': 0, 'waiting_time_batching': 0})
    apt = {}
    dl = {}
    for lot in instance.done_lots:
        lots[lot.name]['ACT'].append(lot.done_at - lot.release_at)
        lots[lot.name]['throughput'] += 1
        lots[lot.name]['tardiness'] += max(0, lot.done_at - lot.deadline_at)
        lots[lot.name]['waiting_time'] += lot.waiting_time
        lots[lot.name]['waiting_time_batching'] += lot.waiting_time_batching
        lots[lot.name]['processing_time'] += lot.processing_time
        lots[lot.name]['transport_time'] += lot.transport_time
        if lot.done_at <= lot.deadline_at:
            lots[lot.name]['on_time'] += 1
        if lot.name not in apt:
            apt[lot.name] = sum([s.processing_time.avg() for s in lot.processed_steps])
            dl[lot.name] = lot.deadline_at - lot.release_at
    print('Lot', 'APT', 'DL', 'ACT', 'TH', 'ONTIME', 'tardiness', 'wa', 'pr', 'tr')
    acts = []
    ths = []
    ontimes = []
    for lot_name in sorted(list(lots.keys())):
        l = lots[lot_name]
        avg = statistics.mean(l['ACT']) / 3600 / 24
        lots[lot_name]['ACT'] = avg
        acts += [avg]
        th = lots[lot_name]['throughput']
        ths += [th]
        ontime = round(l['on_time'] / l['throughput'] * 100)
        ontimes += [ontime]
        wa = lots[lot_name]['waiting_time'] / l['throughput'] / 3600 / 24
        wab = lots[lot_name]['waiting_time_batching'] / l['throughput'] / 3600 / 24
        pr = lots[lot_name]['processing_time'] / l['throughput'] / 3600 / 24
        tr = lots[lot_name]['transport_time'] / l['throughput'] / 3600 / 24
        print(lot_name, round(apt[lot_name] / 3600 / 24, 1), round(dl[lot_name] / 3600 / 24, 1), round(avg, 1), th,
              ontime, l['tardiness'], wa, wab, pr, tr)
    print('---------------')
    print(round(statistics.mean(acts), 2), statistics.mean(ths), statistics.mean(ontimes))
    print(round(sum(acts), 2), sum(ths), sum(ontimes))

    utilized_times = defaultdict(lambda: [])
    setup_times = defaultdict(lambda: [])
    pm_times = defaultdict(lambda: [])
    br_times = defaultdict(lambda: [])
    for machine in instance.machines:
        utilized_times[machine.family].append(machine.utilized_time)
        setup_times[machine.family].append(machine.setuped_time)
        pm_times[machine.family].append(machine.pmed_time)
        br_times[machine.family].append(machine.bred_time)

    print('Machine', 'Cnt', 'avail' 'util', 'br', 'pm', 'setup')
    machines = defaultdict(lambda: {})
    for machine_name in sorted(list(utilized_times.keys())):
        av = (instance.current_time - statistics.mean(pm_times[machine_name]) - statistics.mean(br_times[machine_name]))
        machines[machine_name]['avail'] = av / instance.current_time
        machines[machine_name]['util'] = statistics.mean(utilized_times[machine_name]) / av
        machines[machine_name]['pm'] = statistics.mean(pm_times[machine_name]) / instance.current_time
        machines[machine_name]['br'] = statistics.mean(br_times[machine_name]) / instance.current_time
        machines[machine_name]['setup'] = statistics.mean(setup_times[machine_name]) / instance.current_time
        r = instance.lot_waiting_at_machine[machine_name]
        machines[machine_name]['waiting_time'] = r[1] / r[0] / 3600 / 24
        print(machine_name, len(utilized_times[machine_name]),
              round(machines[machine_name]['avail'] * 100, 2),
              round(machines[machine_name]['util'] * 100, 2),
              round(machines[machine_name]['br'] * 100, 2),
              round(machines[machine_name]['pm'] * 100, 2),
              round(machines[machine_name]['setup'] * 100, 2))

    plugins = {}

    for plugin in instance.plugins:
        if plugin.get_output_name() is not None:
            plugins[plugin.get_output_name()] = plugin.get_output_value()

    with io.open(f'{dir}/{method}_{days}days_{dataset}_{disp}.json', 'w') as f:
        json.dump({
            'lots': lots,
            'machines': machines,
            'plugins': plugins,
        }, f)
