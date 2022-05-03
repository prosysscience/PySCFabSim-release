import os
from random import Random


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Randomizer(metaclass=Singleton):
    def __init__(self):
        random_seed = int(os.environ['SEED']) if 'SEED' in os.environ else None
        self.random = Random(random_seed)
