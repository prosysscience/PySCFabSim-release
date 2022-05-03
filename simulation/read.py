import io
import os
from collections import defaultdict
from os import environ

from simulation.dataset_preprocess import RemoveBreakdowns, RemoveWIP, RemoveRework, RemoveSampling, \
    RemovePreventiveMaintenance


def try_to_num(inp: str):
    try:
        return int(inp)
    except Exception:
        try:
            return float(inp)
        except Exception:
            return inp


def read_txt(path):
    with io.open(path, 'r') as f:
        lines = f.read().split('\n')
    headers, lines = lines[0].split('\t'), lines[1:]
    dicts = []
    for line in lines:
        cols = line.split('\t')
        d = defaultdict(lambda: None)
        all_none = True
        for header, col in zip(headers, cols):
            if header.upper() != 'IGNORE':
                col = try_to_num(col)
                d[header] = col
                if col is not None:
                    all_none = False
        if len(line) > 0 and len(d) > 0 and not all_none:
            dicts.append(d)
    return dicts


def read_all(d, preprocessors=None):
    files = defaultdict(lambda: [])
    for file in os.listdir(d):
        if '.txt' in file:
            files[file] = read_txt(os.path.join(d, file))
    if preprocessors is None:
        preprocessors = []
        if 'NOWIP' in environ:
            preprocessors.append(RemoveWIP())
        if 'NOBREAKDOWN' in environ:
            preprocessors.append(RemoveBreakdowns())
        if 'NOPM' in environ:
            preprocessors.append(RemovePreventiveMaintenance())
        if 'NOREWORK' in environ:
            preprocessors.append(RemoveRework())
        if 'NOSAMPLING' in environ:
            preprocessors.append(RemoveSampling())
    if preprocessors is not None:
        for p in preprocessors:
            files = p.preprocess(files)
    return files
