import json
from colored import fg, attr

def compare_json_files(file1_path, file2_path, output_path):
    # JSON-Dateien lesen
    with open(file1_path, 'r') as file1:
        data1 = json.load(file1)

    with open(file2_path, 'r') as file2:
        data2 = json.load(file2)

    differences = {}

    def calculate_percentage_difference(value1, value2):
        try:
            percentage_difference = abs((value1 - value2) / ((value1 + value2) / 2)) * 100
            return round(percentage_difference, 2)
        except ZeroDivisionError:
            return 0

    # Funktion zur Vergleich der JSON-Strukturen
    def compare_dicts(d1, d2, path=""):
        nonlocal differences
        for key in d1:
            new_path = f"{path}.{key}" if path else key

            if key not in d2:
                differences[new_path] = {"RL": d1[key], "Det_Fifo": None}
            elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                compare_dicts(d1[key], d2[key], new_path)
            elif d1[key] != d2[key]:
                percentage_difference = calculate_percentage_difference(d1[key], d2[key])

                differences[new_path] = {"RL": d1[key], "Det_Fifo": d2[key], "percentage_difference": percentage_difference}


    # Vergleich der JSON-Strukturen starten
    compare_dicts(data1, data2)

    # Unterschiede in neue JSON-Datei schreiben
    with open(output_path, 'w') as output_file:
        json.dump(differences, output_file, indent=2)

# Beispielaufruf
compare_json_files('experiments/0_ds_HVLM_a9_tp365_reward2_di_fifo_Di/rl730_730days_HVLM_fifo.json', 'greedy\greedy_seedNone_730days_SMT2020_HVLM_fifo.json', 'differences.json')