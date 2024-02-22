from typing import Dict, List

from classes import Machine, FileRoute, Lot
from events import BreakdownEvent
from instance import Instance
from randomizer import Randomizer
from tools import get_interval, get_distribution, UniformDistribution, date_time_parse


class FileInstance(Instance):

    def __init__(self, files: Dict[str, List[Dict]], run_to, lot_for_machine, plugins):
        machines = []
        machine_id = 0
        r = Randomizer()
        family_locations = {}
        for d_m in files['tool.txt.1l']:
            for i in range(int(d_m['STNQTY'])):
                speed = 1  # r.random.uniform(0.7, 1.3)
                m = Machine(idx=machine_id, d=d_m, speed=speed)
                family_locations[m.family] = m.loc
                machines.append(m)
                machine_id += 1

        from_to = {(a['FROMLOC'], a['TOLOC']): get_distribution(a['DDIST'], a['DUNITS'], a['DTIME'], a['DTIME2']) for a
                   in files['fromto.txt']}

        pieces = max([a['PIECES'] for a in files['order.txt'] + files['WIP.txt']])
        routes = {}
        route_keys = [key for key in files.keys() if 'route' in key]
        for rk in route_keys:
            route = FileRoute(rk, pieces, files[rk])
            last_loc = None
            for s in route.steps:
                s.family_location = family_locations[s.family]
                key = (last_loc, s.family_location)
                if last_loc is not None and key in from_to:
                    s.transport_time = from_to[key]
                last_loc = s.family_location
            routes[rk] = route

        parts = {p['PART']: p['ROUTEFILE'] for p in files['part.txt']}

        lots = []
        idx = 0
        lot_pre = {}
        for order in files['order.txt']:
            assert pieces == order['PIECES']
            first_release = 0
            release_interval = get_interval(order['REPEAT'], order['RUNITS'])
            relative_deadline = (date_time_parse(order['DUE']) - date_time_parse(order['START'])).total_seconds()

            for i in range(order['RPT#']):
                rel_time = first_release + i * release_interval
                lot = Lot(idx, routes[parts[order['PART']]], order['PRIOR'], rel_time, relative_deadline, order)
                lots.append(lot)
                lot_pre[lot.name] = relative_deadline
                idx += 1
                if rel_time > run_to:
                    break

        for wip in files['WIP.txt']:
            assert pieces == wip['PIECES']
            first_release = 0
            relative_deadline = (date_time_parse(wip['DUE']) - date_time_parse(wip['START'])).total_seconds()
            if wip['CURSTEP'] < len(routes[parts[wip['PART']]].steps) - 1:
                lot = Lot(idx, routes[parts[wip['PART']]], wip['PRIOR'], first_release, relative_deadline, wip)
                lots.append(lot)
                lot.release_at = lot.deadline_at - lot_pre[lot.name]
            idx += 1

        setups = {(s['CURSETUP'], s['NEWSETUP']): get_interval(s['STIME'], s['STUNITS']) for s in files['setup.txt']}
        setup_min_run = {s['SETUP']: s['MINRUN'] for s in files['setupgrp.txt']}

        downcals = {}
        for dc in files['downcal.txt']:
            downcals[dc['DOWNCALNAME']] = (get_distribution(dc['MTTFDIST'], dc['MTTFUNITS'], dc['MTTF']),
                                           get_distribution(dc['MTTRDIST'], dc['MTTRUNITS'], dc['MTTR']))
        pmcals = {}
        for dc in files['pmcal.txt']:
            pmcals[dc['PMCALNAME']] = (get_distribution('constant', dc['MTBPMUNITS'], dc['MTBPM']),
                                       get_distribution(dc['MTTRDIST'], dc['MTTRUNITS'], dc['MTTR'], dc['MTTR2']))

        breakdowns = []
        for a in files['attach.txt']:
            if a['RESTYPE'] == 'stngrp':
                m_break = [m for m in machines if m.group == a['RESNAME']]
            else:
                m_break = [m for m in machines if m.family == a['RESNAME']]
            distribution = get_distribution(a['FOADIST'], a['FOAUNITS'], a['FOA'])
            if a['CALTYPE'] == 'down':
                is_breakdown = True
                ne, le = downcals[a['CALNAME']]
            else:
                is_breakdown = False
                ne, le = pmcals[a['CALNAME']]
            if distribution is None:
                distribution = ne
            if a['FOAUNITS'] == '':
                for num,m in enumerate(m_break):
                    m.piece_per_maintenance.append(ne.c)
                    if a['FOADIST']=='constant':
                        foa_sample = a['FOA']/len(m_break)
                        spec_foa = foa_sample*(num+1)
                        m.pieces_until_maintenance.append(spec_foa)
                    m.maintenance_time.append(le)
            else:
                for num,m in enumerate(m_break):
                    if a['FOADIST']=='constant':
                        dist_sample = (distribution.sample())/len(m_break)
                        spec_dist = dist_sample*(num+1)
                        br = BreakdownEvent(spec_dist, le, ne, m, is_breakdown, spec_dist)
                    else:
                        br = BreakdownEvent(distribution.sample(), le, ne, m, is_breakdown, 0)
                    if not is_breakdown:
                        m.pms.append(br)
                    breakdowns.append(br)

        super().__init__(machines, routes, lots, setups, setup_min_run, breakdowns, lot_for_machine, plugins)
