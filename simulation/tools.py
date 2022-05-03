import datetime

from simulation.randomizer import Randomizer

r = Randomizer()


def get_interval(num, unit):
    units = {'sec': 1, 's': 1, 'min': 60, 'hr': 3600, 'day': 86400, 'pieces': 1, '': 1}
    if num is None:
        return None
    if unit in units:
        return num * units[unit]
    else:
        raise ValueError(f'Unit {unit} not known.')


class UniformDistribution:

    def __init__(self, m, l):
        self.m, self.l = m, l

    def sample(self):
        return r.random.uniform(self.m - self.l / 2, self.m + self.l / 2)

    def avg(self):
        return self.m


class ConstantDistribution:

    def __init__(self, c):
        self.c = c

    def sample(self):
        return self.c

    def avg(self):
        return self.c


class ExponentialDistribution:

    def __init__(self, p):
        self.p = p

    def sample(self):
        return r.random.expovariate(1 / self.p)


def get_distribution(typ, unit, *args, multiplier=1):
    arr = [multiplier * get_interval(a, unit) for a in args if a is not None]
    if typ == 'uniform':
        return UniformDistribution(*arr)
    if typ == 'constant':
        return ConstantDistribution(*arr)
    if typ == 'exponential':
        return ExponentialDistribution(*arr)


def date_time_parse(st):
    return datetime.datetime.strptime(st, '%m/%d/%y %H:%M:%S')
