import statistics
from collections import defaultdict
from typing import List

import gym
from gym import Env

from simulation.classes import Machine, Lot
from simulation.file_instance import FileInstance
from simulation.greedy import get_lots_to_dispatch_by_machine
from simulation.dispatching.dispatcher import Dispatchers, dispatcher_map
from simulation.gym.E import E
from simulation.randomizer import Randomizer
from simulation.read import read_all

r = Randomizer()

STATE_COMPONENTS_DEMO = (
    E.A.L4M.S.OPERATION_TYPE.NO_LOTS_PER_BATCH,
    E.A.L4M.S.OPERATION_TYPE.CR.MAX,
    E.A.L4M.S.OPERATION_TYPE.FREE_SINCE.MAX,
    E.A.L4M.S.OPERATION_TYPE.SETUP.MIN_RUNS_OK,
    E.A.L4M.S.OPERATION_TYPE.SETUP.NEEDED,
    E.A.L4M.S.OPERATION_TYPE.SETUP.LAST_SETUP_TIME,
)


class DynamicSCFabSimulationEnvironment(Env):

    def __init__(self, num_actions, active_station_group, days, dataset, dispatcher, seed, max_steps,
                 reward_type, action, state_components):
        self.did_reset = False
        self.files = read_all('datasets/' + dataset)
        self.instance = None
        self.num_actions = num_actions
        self.days = days
        self.action_space = gym.spaces.Discrete(num_actions)
        self.action = action
        self.observation_space = gym.spaces.Box(low=-100, high=1000000,
                                                shape=(4 + num_actions * len(state_components),))
        self._state = None
        self.station_group = active_station_group
        self.lots_done = 0
        self.seed_val = seed
        self.dispatcher = dispatcher_map[dispatcher]
        self.max_steps = max_steps
        self.reward_type = reward_type
        self.mavg = 0
        self.state_components = state_components
        self.reset()

    def seed(self, seed=None):
        if seed is None:
            seed = 0
        self.seed_val = seed
        self.reset()

    def step(self, action):
        self.did_reset = False
        self.actual_step += 1
        # apply_priority_rule(self._machine)
        waiting_lots = self._machine.actions
        lot_index = action
        if lot_index < len(waiting_lots) and waiting_lots[lot_index] is not None:
            lot_group = waiting_lots[lot_index]
            lot = lot_group[0]
            lots = lot_group[:min(len(lot_group), lot.actual_step.batch_max)]
            violated_minruns = self._machine.min_runs_left is not None and self._machine.min_runs_setup == lot.actual_step.setup_needed
            self.instance.dispatch(self._machine, lots)
            done = self.next_step() or self.max_steps < self.actual_step
            reward = 0
            if self.reward_type in [1, 2]:
                for i in range(self.lots_done, len(self.instance.done_lots)):
                    lot = self.instance.done_lots[i]
                    reward += 1000
                    if self.reward_type == 2:
                        reward += 1000 if lot.deadline_at >= lot.done_at else 0
                    else:
                        reward += 1000 if lot.deadline_at >= lot.done_at else -min(500, (
                                lot.done_at - lot.deadline_at) / 3600)
            elif self.reward_type == 3:
                reward += statistics.mean(
                    [min(1, j.cr(self.instance.current_time) - 1) for j in self.instance.active_lots])
            elif self.reward_type == 7:
                reward += statistics.mean(
                    [l.notlateness(self.instance.current_time) for l in self.instance.active_lots])
            else:
                pass
            if violated_minruns:
                reward += -10
            self.lots_done = len(self.instance.done_lots)
            return self.state, reward, done, {}
        else:
            return self.state, -100, self.max_steps < self.actual_step, {}

    def reset(self):
        if not self.did_reset:
            self.did_reset = True
            self.actual_step = 0
            self.lots_done = 0
            run_to = 3600 * 24 * self.days
            self.instance = FileInstance(self.files, run_to, True, [])
            Randomizer().random.seed(self.seed_val)
            self.seed_val += 1
            self.next_step()
        return self.state

    def next_step(self):
        found = False
        while not found:
            done = self.instance.next_decision_point()
            if done or self.instance.current_time > 3600 * 24 * self.days:
                return True
            for machine in self.instance.usable_machines:
                break
            if self.station_group is None or \
                    f'[{machine.group}]' in self.station_group or \
                    f'<{machine.family}>' in self.station_group:
                found = True
            else:
                machine, lots = get_lots_to_dispatch_by_machine(self.instance, machine=machine,
                                                                ptuple_fcn=self.dispatcher)
                if lots is None:
                    self.instance.usable_machines.remove(machine)
                else:
                    self.instance.dispatch(machine, lots)

        self._machine = machine
        actions = defaultdict(lambda: [])
        for lot in machine.waiting_lots:
            actions[lot.actual_step.step_name].append(lot)
        self.mavg = self.mavg * 0.99 + len(actions) * 0.01
        if len(actions) > self.num_actions:
            self._machine.actions = r.random.sample(list(actions.values()), self.num_actions)
        else:
            self._machine.actions = list(actions.values())
            while len(self._machine.actions) < self.num_actions:
                self._machine.actions.append(None)
            r.random.shuffle(self._machine.actions)
        self._state = None
        return False

    @property
    def state(self):
        if self._state is None:
            m: Machine = self._machine
            t = self.instance.current_time
            self._state = [
                m.pms[0].timestamp - t if len(m.pms) > 0 else 999999,  # next maintenance
                m.utilized_time / m.setuped_time if m.setuped_time > 0 else 0,  # ratio of setup time / processing time
                (m.setuped_time + m.utilized_time) / t if t > 0 else 0,  # ratio of non idle time
                m.machine_class,  # type of machine
            ]
            from statistics import mean, median
            for action in self._machine.actions:
                if action is None:
                    self._state += [-1000] * len(self.state_components)
                else:
                    action: List[Lot]
                    free_since = [self.instance.current_time - l.free_since for l in action]
                    work_rem = [len(l.remaining_steps) for l in action]
                    cr = [l.cr(self.instance.current_time) for l in action]
                    priority = [l.priority for l in action]
                    l0 = action[0]

                    self._machine: Machine
                    action_type_state_lambdas = {
                        E.A.L4M.S.OPERATION_TYPE.NO_LOTS: lambda: len(action),
                        E.A.L4M.S.OPERATION_TYPE.NO_LOTS_PER_BATCH: lambda: len(action) / l0.actual_step.batch_max,
                        E.A.L4M.S.OPERATION_TYPE.STEPS_LEFT.MEAN: lambda: mean(work_rem),
                        E.A.L4M.S.OPERATION_TYPE.STEPS_LEFT.MEDIAN: lambda: median(work_rem),
                        E.A.L4M.S.OPERATION_TYPE.STEPS_LEFT.MAX: lambda: max(work_rem),
                        E.A.L4M.S.OPERATION_TYPE.STEPS_LEFT.MIN: lambda: min(work_rem),
                        E.A.L4M.S.OPERATION_TYPE.FREE_SINCE.MEAN: lambda: mean(free_since),
                        E.A.L4M.S.OPERATION_TYPE.FREE_SINCE.MEDIAN: lambda: median(free_since),
                        E.A.L4M.S.OPERATION_TYPE.FREE_SINCE.MAX: lambda: max(free_since),
                        E.A.L4M.S.OPERATION_TYPE.FREE_SINCE.MIN: lambda: min(free_since),
                        E.A.L4M.S.OPERATION_TYPE.PROCESSING_TIME.AVERAGE: lambda: l0.actual_step.processing_time.avg(),
                        E.A.L4M.S.OPERATION_TYPE.BATCH.MIN: lambda: l0.actual_step.batch_min,
                        E.A.L4M.S.OPERATION_TYPE.BATCH.MAX: lambda: l0.actual_step.batch_max,
                        E.A.L4M.S.OPERATION_TYPE.BATCH.FULLNESS: lambda: min(1, len(action) / l0.actual_step.batch_max),
                        E.A.L4M.S.OPERATION_TYPE.PRIORITY.MEAN: lambda: mean(priority),
                        E.A.L4M.S.OPERATION_TYPE.PRIORITY.MEDIAN: lambda: median(priority),
                        E.A.L4M.S.OPERATION_TYPE.PRIORITY.MAX: lambda: max(priority),
                        E.A.L4M.S.OPERATION_TYPE.PRIORITY.MIN: lambda: min(priority),
                        E.A.L4M.S.OPERATION_TYPE.CR.MEAN: lambda: mean(cr),
                        E.A.L4M.S.OPERATION_TYPE.CR.MEDIAN: lambda: median(cr),
                        E.A.L4M.S.OPERATION_TYPE.CR.MAX: lambda: max(cr),
                        E.A.L4M.S.OPERATION_TYPE.CR.MIN: lambda: min(cr),
                        E.A.L4M.S.OPERATION_TYPE.SETUP.NEEDED: lambda: 0 if l0.actual_step.setup_needed == '' or l0.actual_step.setup_needed == m.current_setup else 1,
                        E.A.L4M.S.OPERATION_TYPE.SETUP.MIN_RUNS_LEFT: lambda: 0 if self._machine.min_runs_left is None else self._machine.min_runs_left,
                        E.A.L4M.S.OPERATION_TYPE.SETUP.MIN_RUNS_OK: lambda: 1 if l0.actual_step.setup_needed == '' or l0.actual_step.setup_needed == self._machine.min_runs_setup else 0,
                        E.A.L4M.S.OPERATION_TYPE.SETUP.LAST_SETUP_TIME: lambda: self._machine.last_setup_time,
                        E.A.L4M.S.MACHINE.MAINTENANCE.NEXT: lambda: 0,
                        E.A.L4M.S.MACHINE.IDLE_RATIO: lambda: 1 - (
                                    self._machine.utilized_time / self.instance.current_time) if self._machine.utilized_time > 0 else 1,
                        E.A.L4M.S.MACHINE.SETUP_PROCESSING_RATIO: lambda: (
                                    self._machine.setuped_time / self._machine.utilized_time) if self._machine.utilized_time > 0 else 1,
                        E.A.L4M.S.MACHINE.MACHINE_CLASS: lambda: 0,
                    }
                    self._state += [
                        action_type_state_lambdas[s]()
                        for s in self.state_components
                    ]
        return self._state

    def render(self, mode="human"):
        pass
