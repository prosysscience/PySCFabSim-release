class RemoveBreakdowns:

    def preprocess(self, files):
        files['attach.txt'] = [r for r in files['attach.txt'] if r['CALTYPE'] != 'down']
        files['downcal.txt'] = []
        return files


class RemovePreventiveMaintenance:

    def preprocess(self, files):
        files['attach.txt'] = [r for r in files['attach.txt'] if r['CALTYPE'] != 'pm']
        files['pmcal.txt'] = []
        return files


class RemoveWIP:

    def preprocess(self, files):
        files['WIP.txt'] = []
        return files


class RemoveRework:

    def preprocess(self, files):
        for name, val in files.items():
            if 'route' in name:
                for v in val:
                    v['REWORK'] = None
        return files


class RemoveSampling:

    def preprocess(self, files):
        for name, val in files.items():
            if 'route' in name:
                for v in val:
                    v['StepPercent'] = None
        return files
