
class LotForMachineDispatchManager:

    @staticmethod
    def init(self):
        self.free_machines = [False for _ in self.machines]
        self.usable_machines = set()

    @staticmethod
    def free_up_lots(self, lot):
        for machine in self.family_machines[lot.actual_step.family]:
            di = lot.actual_step.order
            if di not in lot.dedications or machine.idx == lot.dedications[di]:
                machine.waiting_lots.append(lot)
                lot.waiting_machines.append(machine)
                if self.free_machines[machine.idx]:
                    self.usable_machines.add(machine)

    @staticmethod
    def free_up_machine(self, machine):
        assert not self.free_machines[machine.idx]
        self.free_machines[machine.idx] = True
        if len(machine.waiting_lots) > 0:
            self.usable_machines.add(machine)

    @staticmethod
    def reserve(self, lots, machine):
        self.free_machines[machine.idx] = False
        self.usable_machines.remove(machine)
        for lot in lots:
            for mx in lot.waiting_machines:
                mx.waiting_lots.remove(lot)
                if len(mx.waiting_lots) == 0 and mx in self.usable_machines:
                    self.usable_machines.remove(mx)
            lot.waiting_machines.clear()

    @staticmethod
    def next_decision_point(self):
        while len(self.usable_machines) == 0 and not self.done:
            self.next_step()
        return self.done

