import os
import sys
sys.path.append(os.path.join('C:/','Users','willi','OneDrive','Documents','Studium','Diplomarbeit','Programm + Datengrundlage','PySCFabSim-release','simulation'))

from collections import defaultdict
from datetime import datetime
from typing import List

from classes import Lot, Machine
from dispatching.dispatcher import dispatcher_map
from file_instance import FileInstance
from plugins.cost_plugin import CostPlugin
from randomizer import Randomizer
from read import read_all
from stats import print_statistics
import copy

import argparse
import pandas as pd
import matplotlib.pyplot as plt

last_sort_time = -1


def dispatching_combined_permachine(ptuple_fcn, machine, time, setups):
    for lot in machine.waiting_lots:
        lot.ptuple = ptuple_fcn(lot, time, machine, setups)

# def get_machine_times_max(setups, lots, machine):
#         proc_t_samp = lots[0].actual_step.processing_time.max()
#         if lots[0].actual_step.processing_time == lots[0].actual_step.cascading_time:
#             cascade_t_samp = proc_t_samp
#         else:
#             cascade_t_samp = lots[0].actual_step.cascading_time.max()
#         machine_time = cascade_t_samp + (machine.load_time + machine.unload_time if not machine.cascading else 0)
#         new_setup = lots[0].actual_step.setup_needed
#         if new_setup != '' and machine.current_setup != new_setup:
#             if lots[0].actual_step.setup_time is not None:
#                 setup_time = lots[0].actual_step.setup_time             # SetupTime für in der Route geplante Setups
#             elif (machine.current_setup, new_setup) in setups:
#                 setup_time = setups[(machine.current_setup, new_setup)] # SetupTime für in setup.txt für DE_BE_ Maschinen
#             elif ('', new_setup) in setups:
#                 setup_time = setups[('', new_setup)]                    # SetupTime für in setup.txt für Implant_91/128/131
#             else:
#                 setup_time = 0                                          # SetupTime, wenn in DE_BE kein Setup vorhanden ist
#         else:
#             setup_time = 0
        
#         return machine_time, setup_time
        
def find_alternative_machine(instance, lots, machine):
    m: Machine
    for m in instance.family_machines[machine.family]: #hier wird eine Maschine gesucht, wo das Setup dem Los-Setup entspricht
        if m in instance.usable_machines and m.current_setup == lots[0].actual_step.setup_needed:  
            machine = m
            break

def get_lots_to_dispatch_by_machine(instance, ptuple_fcn, machine=None):
    time = instance.current_time
    if machine is None:
        for machine in instance.usable_machines:
            break
    dispatching_combined_permachine(ptuple_fcn, machine, time, instance.setups)
    wl = sorted(machine.waiting_lots, key=lambda k: k.ptuple)
    # select lots to dispatch
    lot = wl[0]
    if lot.actual_step.batch_max > 1:
        # construct batch
        lot_m = defaultdict(lambda: [])
        for w in wl:
            lot_m[w.actual_step.step_name].append(w)  # + '_' + w.part_name
        lot_l = sorted(list(lot_m.values()),
                       key=lambda l: (
                           l[0].ptuple[0],  # cqt
                           l[0].ptuple[1],  # min run setup is the most important
                           -min(1, len(l) / l[0].actual_step.batch_max),  # then maximize the batch size
                           0 if len(l) >= l[0].actual_step.batch_min else 1,  # then take min batch size into account
                           *(l[0].ptuple[2:]),  # finally, order based on prescribed priority rule
                       ))
        lots: List[Lot] = lot_l[0]
        if len(lots) > lots[0].actual_step.batch_max:
            lots = lots[:lots[0].actual_step.batch_max]
        if len(lots) < lots[0].actual_step.batch_max:
            lots = None
    else:
        # dispatch single lot
        lots = [lot]
    #1. Beachte wake up Least Setup Rule -> wenn maschine in idle mit setup schon drin -> nimm die 
    #2. bei mehr als 2 frei Maschinen dieser Familie wird die wake_LeastSetupTime verwendet -> Maschine mit der geringsten Setup Zeit
    # if lots is not None and machine.current_setup != lots[0].actual_step.setup_needed: #aktuelle Los-Setup nicht leer und stimmt nicht mit der machine-Setup überein
    #     m: Machine
    #     for m in instance.family_machines[machine.family]: #hier wird eine Maschine gesucht, wo das Setup dem Los-Setup entspricht
    #         if m in instance.usable_machines and m.current_setup == lots[0].actual_step.setup_needed:  
    #             machine = m
    #             break
    
    # if lots is not None:
    #     if len(lot.dedications) > 1:
    #         for d in lot.dedications:
    #             if lot.actual_step.idx +1 == d:
    #                 found_machine = False
    #                 for m in instance.usable_machines:
    #                     if lot.dedications[d] == m.idx:
    #                         machine = m
    #                         lot.dedications.pop(d)
    #                         found_machine = True
    #                         break
    #                 if found_machine:
    #                     break
                
    #                 machine = None  
    #         else:
    #             find_alternative_machine(instance, lots, machine)
    #     else:
    #         find_alternative_machine(instance, lots, machine)
    if lots is not None:
        if len(lot.dedications) > 1:
            for d in lot.dedications:
                if lot.actual_step.idx + 1 == d:
                    machine_dict = {m.idx: m for m in instance.usable_machines}
                    machine_idx = lot.dedications[d]
                    machine = machine_dict.get(machine_idx)
                    if machine:
                        lot.dedications.pop(d)
                        break
                    #machine = None
            else:
                find_alternative_machine(instance, lots, machine)
        else:
            find_alternative_machine(instance, lots, machine)
            # machine_list = []
            # machine_not_useable = []
            # for m in instance.usable_machines:
            #     machine_list.append(m.idx)
            # machine_time, setup_time = get_machine_times_max(instance.setups, lots, machine)
            # look_ahead_time = instance.current_time + machine_time + setup_time
            # machine = None
            # for event in instance.events.arr:
            #     if "BreakdownEvent" in str(event) and event.is_breakdown == False and event.machine.family == lots[0].actual_step.family and event.timestamp <= look_ahead_time:
            #         machine_not_useable.append(event.machine.idx)
                
            #     if event.timestamp > look_ahead_time:
            #         break
            # # Nutze Machine.next_PM_zeit-Attribut um zu prüfen, ob die Maschine in der Zukunft eine PM hat -> nicht möglich, da dort nur die größte Wartung drin steht
            # for ma in instance.usable_machines:
            #     if ma.idx not in machine_not_useable:
            #         if lot.actual_step.setup_needed == '':   
            #             machine = ma
            #             break
            #         else:
            #             if ma.current_setup == lots[0].actual_step.setup_needed:
            #                 machine = ma
            #                 break
            # if machine is None:
            #     for ma in instance.usable_machines:
            #         if ma.idx not in machine_not_useable:
            #             machine = ma
            #             break
        
     
    if machine.min_runs_left is not None and machine.min_runs_setup != lots[0].actual_step.setup_needed:
    #if machine.min_runs_left is not None and machine.min_runs_setup != lots[0].actual_step.setup_needed: # Test 5
        lots = None
    
    
        
        
    return machine, lots


def build_batch(lot, nexts):
    batch = [lot]
    if lot.actual_step.batch_max > 1:
        for bo_lot in nexts:
            if lot.actual_step.step_name == bo_lot.actual_step.step_name:
                batch.append(bo_lot)
            if len(batch) == lot.actual_step.batch_max:
                break
    return batch


def get_lots_to_dispatch_by_lot(instance, current_time, dispatcher):
    global last_sort_time
    if last_sort_time != current_time:
        for lot in instance.usable_lots:
            lot.ptuple = dispatcher(lot, current_time, None)
        last_sort_time = current_time
        instance.usable_lots.sort(key=lambda k: k.ptuple)
    lots = instance.usable_lots
    setup_machine, setup_batch = None, None
    min_run_break_machine, min_run_break_batch = None, None
    family_lock = None
    for i in range(len(lots)):
        lot: Lot = lots[i]
        if family_lock is None or family_lock == lot.actual_step.family:
            family_lock = lot.actual_step.family
            assert len(lot.waiting_machines) > 0
            for machine in lot.waiting_machines:
                if lot.actual_step.setup_needed == '' or lot.actual_step.setup_needed == machine.current_setup:
                    return machine, build_batch(lot, lots[i + 1:])
                else:
                    if setup_machine is None and machine.min_runs_left is None:
                        setup_machine = machine
                        setup_batch = i
                    if min_run_break_machine is None:
                        min_run_break_machine = machine
                        min_run_break_batch = i
    if setup_machine is not None:
        return setup_machine, build_batch(lots[setup_batch], lots[setup_batch + 1:])
    return min_run_break_machine, build_batch(lots[min_run_break_batch], lots[min_run_break_batch + 1:])


def run_greedy():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=str)
    p.add_argument('--days', type=int)
    p.add_argument('--dispatcher', type=str)
    p.add_argument('--seed', type=int)
    p.add_argument('--wandb', action='store_true', default=False)
    p.add_argument('--chart', action='store_true', default=False)
    p.add_argument('--alg', type=str, default='l4m', choices=['l4m', 'm4l'])
    a = p.parse_args()

    a.dataset = "SMT2020_HVLM"
    a.days = 730
    a.dispatcher = "fifo"
    #a.seed = 42

    sys.stderr.write('Loading ' + a.dataset + ' for ' + str(a.days) + ' days, using ' + a.dispatcher + '\n')
    sys.stderr.flush()

    start_time = datetime.now()

    files = read_all('datasets/' + a.dataset)

    run_to = 3600 * 24 * a.days
    Randomizer().random.seed(a.seed)
    l4m = a.alg == 'l4m'
    plugins = []
    if a.wandb:
        from plugins.wandb_plugin import WandBPlugin
        plugins.append(WandBPlugin())
    if a.chart:
        from plugins.chart_plugin import ChartPlugin
        plugins.append(ChartPlugin())
    plugins.append(CostPlugin())
    instance = FileInstance(files, run_to, l4m, plugins)

    dispatcher = dispatcher_map[a.dispatcher]

    sys.stderr.write('Starting simulation with dispatching rule\n\n')
    sys.stderr.flush()

    while not instance.done:
        done = instance.next_decision_point()
        instance.print_progress_in_days()
        if done or instance.current_time > run_to:
            break

        if l4m:
            machine, lots = get_lots_to_dispatch_by_machine(instance, dispatcher)
            if lots is None:
                instance.usable_machines.remove(machine)
            else:
                #action = Rl.choose()
                instance.dispatch(machine, lots)
        else:
            machine, lots = get_lots_to_dispatch_by_lot(instance, instance.current_time, dispatcher)
            if lots is None:
                instance.usable_lots.clear()
                instance.lot_in_usable.clear()
                instance.next_step()
            else:
                instance.dispatch(machine, lots)

    instance.finalize()
    interval = datetime.now() - start_time
    print(instance.current_time_days, ' days simulated in ', interval)
    print_statistics(instance, a.days, a.dataset, a.dispatcher, method='greedy_seed' + str(a.seed))
    # filename = 'pmbr_log.txt'
    
    # with open(filename, 'w') as file:
    #     titel = 'Maschine\tPM_count\tPM_in_std\tBD_count\tBD_in_std\n'
    #     file.write(f'{titel}\n\n')
    #     for machine in sorted(list(instance.pmsbd.keys())):
    #         if instance.pmsbd[machine]['PM_count'] > 0:
    #             file.write(str(machine) + "\t" + str(instance.pmsbd[machine]['PM_count']) + "\t" + str(instance.pmsbd[machine]['PM_in_std'])+"\t"+str(instance.pmsbd[machine]['BD_count']) + "\t" + str(instance.pmsbd[machine]['BD_in_std']) + "\n")
