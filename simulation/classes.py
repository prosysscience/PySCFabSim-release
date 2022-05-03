from typing import List, Dict

from simulation.events import BreakdownEvent
from simulation.randomizer import Randomizer
from simulation.tools import get_interval, get_distribution, date_time_parse, ConstantDistribution

r = Randomizer()

machine_classes = {}


def alt(d, a1, a2):
    return d[a1] if a1 in d else (d[a2] if a2 is not None else None)


def default(d, a1, de):
    return d[a1] if a1 in d else de


def none_is_0(v):
    return 0 if v is None else v


class Machine:

    def __init__(self, idx, d, speed):
        self.idx = idx
        self.load_time = none_is_0(get_interval(d['LTIME'], d['LTUNITS']))
        self.unload_time = none_is_0(get_interval(d['ULTIME'], d['ULTUNITS']))
        self.group = d['STNGRP']
        if self.group not in machine_classes:
            machine_classes[self.group] = len(machine_classes)
        self.machine_class = machine_classes[self.group]
        self.loc = d['STNFAMLOC']
        self.family = d['STNFAM']
        self.cascading = True if type(d['STNCAP']) in [int, float] and int(d['STNCAP']) == 2 else False
        self.speed = speed
        self.minimize_setup_time = d['WAKERESRANK'] == 'wake_LeastSetupTime'

        self.available_from = None
        self.available_to = None

        self.piece_per_maintenance = []
        self.pieces_until_maintenance = []
        self.maintenance_time = []

        self.waiting_lots: List[Lot] = []

        self.utilized_time = 0
        self.setuped_time = 0
        self.pmed_time = 0
        self.bred_time = 0

        self.current_setup = ''

        self.events = []
        self.min_runs_left = None
        self.min_runs_setup = None

        # RL state space features
        self.pms: List[BreakdownEvent] = []
        self.last_actions = 4 * [999]

        self.last_setup_time = 0
        self.dispatch_failed = 0

        self.has_min_runs = False

        self.next_preventive_maintenance = None

    def __hash__(self):
        return self.idx

    def __repr__(self):
        return f'Machine {self.idx}'


class Product:
    def __init__(self, route, priority):
        self.route = route
        self.priority = priority


class Step:

    def __init__(self, idx, pieces_per_lot, d):
        self.idx = idx
        self.order = d['STEP']
        self.step_name = d['DESC']
        self.family = d['STNFAM']
        self.setup_needed = d['SETUP']
        self.setup_time = get_interval(d['STIME'], d['STUNITS']) if type(d['STIME']) is int else None
        self.rework_step = d['RWKSTEP']
        assert len(self.family) > 0
        self.cascading = False
        if type(d['PartInterval']) in [float, int]:
            assert d['PTPER'] == 'per_piece'
            per_piece = get_interval(d['PartInterval'], d['PartIntUnits'])
            self.processing_time = get_distribution(d['PDIST'], d['PTUNITS'], d['PTIME'], d['PTIME2'])
            self.processing_time.m += per_piece * (pieces_per_lot - 1)
            self.cascading_time = ConstantDistribution(per_piece * pieces_per_lot)
            self.cascading = True
        else:
            if d['PTPER'] == 'per_piece':
                m = pieces_per_lot
            else:
                m = 1
            self.processing_time = get_distribution(default(d, 'PDIST', 'constant'), d['PTUNITS'], d['PTIME'],
                                                    d['PTIME2'], multiplier=m)
            if type(d['BatchInterval']) in [float, int]:
                self.cascading_time = get_distribution('constant', d['BatchIntUnits'], d['BatchInterval'])
                self.cascading = True
            else:
                self.cascading_time = self.processing_time
        self.batching = d['PTPER'] == 'per_batch'
        self.batch_min = 1 if d['BATCHMN'] == '' else int(d['BATCHMN'] / pieces_per_lot)
        self.batch_max = 1 if d['BATCHMX'] == '' else int(d['BATCHMX'] / pieces_per_lot)
        self.sampling_percent = 100 if d['StepPercent'] in ['', None] else float(d['StepPercent'])
        self.rework_percent = 0 if d['REWORK'] in ['', None] else float(d['REWORK'])
        
        self.cqt_for_step = d['STEP_CQT'] if 'STEP_CQT' in d else None
        self.cqt_time = get_interval(d['CQT'], d['CQTUNITS']) if self.cqt_for_step is not None else None

        self.lot_to_lens_dedication = d['FORSTEP'] if d['SVESTN'] == 'yes' else None

        self.family_location = ''
        self.transport_time = ConstantDistribution(0)

        self.reworked = {}

    def has_to_perform(self):
        if self.sampling_percent == 100:
            return True
        return r.random.uniform(0, 100) <= self.sampling_percent

    def has_to_rework(self, lot_id):
        if self.rework_percent == 0 or lot_id in self.reworked:
            return False
        self.reworked[lot_id] = True
        return r.random.uniform(0, 100) <= self.rework_percent


class Lot:
    def __init__(self, idx, route, priority, release, relative_deadline, d):
        self.idx = idx
        self.remaining_steps = [step for step in route.steps]
        self.actual_step: Step = None
        self.processed_steps = []
        self.priority = priority
        self.release_at = release
        self.deadline_at = self.release_at + relative_deadline
        self.name: str = d['LOT']
        self.part_name: str = d['PART']
        if 'Init_' in self.name:
            self.name = self.name[self.name.index('_') + 1:self.name.rindex('_')]

        if 'CURSTEP' in d:
            cs = d['CURSTEP']
            self.processed_steps, self.remaining_steps = self.remaining_steps[:cs - 1], self.remaining_steps[cs - 1:]

        self.pieces = d['PIECES']

        self.waiting_machines = []

        self.done_at = None
        self.free_since = None

        self.remaining_steps_last = -1
        self.remaining_time_last = 0

        self.dedications = {}

        self.waiting_time = 0
        self.waiting_time_batching = 0
        self.processing_time = 0
        self.transport_time = 0

        self.cqt_waiting = None
        self.cqt_deadline = None

        self.ft = None

    def __hash__(self):
        return self.idx

    def __repr__(self):
        return f'Lot {self.idx}'

    def cr(self, time):
        rt = self.remaining_time
        return (self.deadline_at - time) / rt if rt > 0 else 1

    @property
    def full_time(self):
        if self.ft is None:
            self.ft = sum(
                [s.processing_time.avg() for s in self.processed_steps +
                 ([self.actual_step] if self.actual_step is not None else []) + self.remaining_steps])
        return self.ft

    @property
    def remaining_time(self):
        if self.remaining_steps_last != len(self.remaining_steps):
            if self.remaining_steps_last - 1 == len(self.remaining_steps):
                self.remaining_time_last -= self.processed_steps[-1].processing_time.avg()
            else:
                self.remaining_time_last = sum(
                    [s.processing_time.avg() for s in self.remaining_steps]) + self.actual_step.processing_time.avg()
            self.remaining_steps_last = len(self.remaining_steps)
        return self.remaining_time_last


class Route:

    def __init__(self, idx, steps: List[Step]):
        self.idx = idx
        self.steps = steps


class FileRoute(Route):

    def __init__(self, idx, pieces_per_lot, steps: List[Dict]):
        steps = [Step(i, pieces_per_lot, d) for i, d in enumerate(steps)]
        super().__init__(idx, steps)
