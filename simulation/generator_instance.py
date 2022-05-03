import os
from typing import Dict, List

from simulation.classes import Machine, FileRoute, Lot, Step, Route
from simulation.events import BreakdownEvent
from simulation.instance import Instance
from simulation.randomizer import Randomizer
from simulation.tools import get_interval, get_distribution, UniformDistribution, date_time_parse

r = Randomizer()


class GeneratorRoute(Route):
    def __init__(self, idx, steps: int):
        fams = [r.random.choice(['S1', 'S2', 'S3', 'S4', 'B1', 'B2', 'B3',
                                 'C1', 'C2']) for i in range(steps)]
        steps = [Step(i, {
            'STEP': i + 1,
            'DESC': f'Step {i} for route {idx}',
            'STNFAM': fam,
            'SETUP': r.random.choice(['', '', '', '', 'Setup1', 'Setup2']),
            'STIME': 20,
            'STUNITS': 'min',
            'RWKSTEP': '',
            'PTPER': 'per_batch',
            'PDIST': 'uniform',
            'PTUNITS': 'min',
            'PTIME': r.random.choice([25, 45, 120, 10]),
            'PTIME2': 5,
            'BATCHMN': 75 if fam.startswith('B') else '',
            'BATCHMX': 125 if fam.startswith('B') else '',
            'StepPercent': '',
            'REWORK': '',
            'PartInterval': '',
            'BatchInterval': '',
        }) for i, fam in enumerate(fams)]
        super().__init__(idx, steps)


class GeneratorInstance(Instance):

    def __init__(self, run_to):
        print('New instance generated')
        machines = []
        machine_id = 0
        r = Randomizer()
        family_locations = {}
        for group, family, quantity, cascading in [
            ('Simple', 'S1', 4, 1),
            ('Simple', 'S2', 2, 1),
            ('Simple', 'S3', 3, 1),
            ('Simple', 'S4', 2, 1),
            ('Batching', 'B1', 5, 1),
            ('Batching', 'B2', 3, 1),
            ('Batching', 'B3', 2, 1),
            ('Cascading', 'C1', 3, 2),
            ('Cascading', 'C2', 1, 2),
        ]:
            for i in range(quantity):
                speed = r.random.uniform(0.7, 1.3)
                m = Machine(idx=machine_id, d={
                    'LTIME': 1,
                    'LTUNITS': 'min',
                    'ULTIME': 1,
                    'ULTUNITS': 'min',
                    'STNGRP': group,
                    'STNFAMLOC': 'Fab',
                    'STNFAM': family,
                    'STNCAP': cascading,
                }, speed=speed)
                family_locations[m.family] = m.loc
                machines.append(m)
                machine_id += 1

        from_to = {('Fab', 'Fav'): get_distribution('uniform', 'min', 5, 1)}

        routes = {}
        for rk in range(5):
            route = GeneratorRoute(rk, 10)
            last_loc = None
            for s in route.steps:
                s.family_location = family_locations[s.family]
                key = (last_loc, s.family_location)
                if last_loc is not None and key in from_to:
                    s.transport_time = from_to[key]
                last_loc = s.family_location
            routes[str(rk)] = route

        parts = {str(p): str(p) for p in range(5)}

        lots = []
        idx = 0
        lot_pre = {}
        for order in range(5):
            first_release = 0
            release_interval = 36000

            for i in range(10000):
                rel_time = first_release + i * release_interval

                route = routes[str(order)]

                relative_deadline = sum([s.processing_time.avg() for s in route.steps]) * 2

                lot = Lot(idx, route, 10, rel_time, relative_deadline, {'LOT': f'Lot {order}'})
                lots.append(lot)
                lot_pre[lot.name] = relative_deadline
                idx += 1
                if rel_time > run_to * 1.5:
                    break

        setups = {('Setup1', 'Setup2'): 1200, ('Setup1', 'Setup2'): 2400}

        super().__init__(machines, routes, lots, setups, [])
