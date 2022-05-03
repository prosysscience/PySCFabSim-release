import statistics
import time
from collections import defaultdict
from typing import List

from simulation.classes import Machine, Lot
from simulation.plugins.interface import IPlugin

import wandb

WANDB_LOG_INTERVAL = 5000


def meanor0(li):
    if len(li) > 0:
        return statistics.mean(li)
    else:
        return 0


class WandBPlugin(IPlugin):
    def on_sim_init(self, instance):
        wandb.init()
        self.wandb_start = time.time()
        self.wandb_machine_free_count = []
        self.wandb_machine_usable_count = []
        self.wandb_steps_performed = 0
        self.wandb_lots_already_done = 0
        self.wandb_time_done = 0
        self.wandb_initial_waiting_lots = len(instance.dispatchable_lots)
        self.wandb_batch_util = []
        self.wandb_step_count = 0

        self.wandb_last_setup = defaultdict(lambda: None)
        self.wandb_same_setup_count = defaultdict(lambda: 0)
        self.wandb_avg_steps_after_setup = [0]
        self.wandb_avg_steps_after_setup_1 = [0]
        self.wandb_avg_steps_after_setup_2 = [0]
        self.wandb_resetups = 0
        self.wandb_setup_machines = set()
        self.wandb_cqt_violations  = 0

    def on_sim_done(self, instance):
        self.step(instance, force=True)
        columns = ['lot name', 'in progress', 'completed', 'completed on time', 'on time percent', 'average cycle time',
                   'theoretical processing time']

        groups = defaultdict(lambda: defaultdict(lambda: 0))
        for lot in instance.active_lots:
            groups[lot.name]['in progress'] += 1
        for lot in instance.done_lots:
            groups[lot.name]['completed'] += 1
            if lot.done_at <= lot.deadline_at:
                groups[lot.name]['completed on time'] += 1
            groups[lot.name]['on time percent'] = round(
                groups[lot.name]['completed on time'] / groups[lot.name]['completed'] * 100, 2)
            groups[lot.name]['act_sum'] += lot.done_at - lot.release_at
            groups[lot.name]['average cycle time'] = round(
                groups[lot.name]['act_sum'] / groups[lot.name]['completed'] / 3600 / 24, 2)
            groups[lot.name]['theoretical processing time'] = round(lot.full_time / 3600 / 24, 2)

        rows = []
        for k, v in groups.items():
            r = [k]
            for c in columns[1:]:
                r.append(v[c])
            rows.append(r)
        rows.sort(key=lambda k: k[0])

        html = '<table border="1"><thead><tr>' + \
               ''.join([f'<th>{c}</th>' for c in columns]) + \
               '</tr></thead><tbody>' + \
               ''.join(['<tr>' + ''.join([f'<td>{c}</td>' for c in row]) + '</tr>' for row in rows]) + \
               '</tbody></table>'
        wandb.log({
            'lot_stats': wandb.Html(html)
        })
        wandb.finish()

    def on_dispatch(self, instance, machine, lots, machine_end_time, lot_end_time):
        machine: Machine
        lots: List[Lot]
        s = lots[0].actual_step.setup_needed
        if s not in [None, '']:
            if machine.last_setup != machine.current_setup:
                self.wandb_setup_machines.add(machine.idx)
                self.wandb_resetups += 1
                if self.wandb_same_setup_count[machine.idx] != 0:
                    self.wandb_avg_steps_after_setup.append(self.wandb_same_setup_count[machine.idx])
                    if machine.has_min_runs:
                        self.wandb_avg_steps_after_setup_2.append(self.wandb_same_setup_count[machine.idx])
                    else:
                        self.wandb_avg_steps_after_setup_1.append(self.wandb_same_setup_count[machine.idx])
                self.wandb_same_setup_count[machine.idx] = 1
            else:
                self.wandb_same_setup_count[machine.idx] += 1
            self.wandb_last_setup[machine.idx] = s
        self.wandb_step_count += 1
        self.wandb_machine_free_count.append(sum(instance.free_machines))
        self.wandb_machine_usable_count.append(len(instance.usable_machines))
        self.wandb_steps_performed += len(lots)
        if lots[0].actual_step.batch_max > 1:
            self.wandb_batch_util.append(len(lots) / lots[0].actual_step.batch_max)
        self.step(instance)

    def step(self, instance, force=False):
        if self.wandb_step_count % WANDB_LOG_INTERVAL == 0 or force:
            now_done = len(instance.done_lots) - self.wandb_lots_already_done
            elapsed_time = instance.current_time_days - self.wandb_time_done
            wandb.log({
                'lots/wip': len(instance.active_lots),
                'lots/done': len(instance.done_lots),
                'machines/free': meanor0(self.wandb_machine_free_count),
                'machines/free_with_lots_waiting': meanor0(self.wandb_machine_usable_count),
                'lots/steps_performed': self.wandb_steps_performed,
                'lots/now_done': now_done,
                'sim/simulated_time_seconds': instance.current_time,
                'sim/simulated_time_days': instance.current_time_days,
                'sim/running_time_minutes': (time.time() - self.wandb_start) / 60,
                'sim/running_time_hours': (time.time() - self.wandb_start) / 3600,
                'sim/speed': instance.current_time / (time.time() - self.wandb_start),
                'lots/throughput_per_day': now_done / elapsed_time,
                'lots/released': self.wandb_initial_waiting_lots - len(instance.dispatchable_lots),
                'machines/batch_util': meanor0(self.wandb_batch_util),
                'machines/setups_executed': self.wandb_resetups / max(1, len(self.wandb_setup_machines)),
                'machines/avg_run_per_setup': statistics.mean(self.wandb_avg_steps_after_setup),
                'machines/avg_run_per_setup_for_enforced': statistics.mean(self.wandb_avg_steps_after_setup_2),
                'machines/avg_run_per_setup_NOT_enforced': statistics.mean(self.wandb_avg_steps_after_setup_1),
                'lots/done_in_time': len([l for l in instance.done_lots if l.done_at <= l.deadline_at]),
                'lots/done_late': len([l for l in instance.done_lots if l.done_at > l.deadline_at]),
                'lots/cqt_violations': self.wandb_cqt_violations,
            })
            self.wandb_lots_already_done = len(instance.done_lots)
            self.wandb_machine_free_count.clear()
            self.wandb_machine_usable_count.clear()
            self.wandb_batch_util.clear()
            self.wandb_steps_performed = 0
            self.wandb_time_done = instance.current_time_days

    def on_cqt_violated(self, instance, machine, lot):
        super().on_cqt_violated(instance, machine, lot)
        self.wandb_cqt_violations += 1

