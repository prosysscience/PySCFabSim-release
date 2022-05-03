from collections import defaultdict


class MachineForLotDispatchManager:

    @staticmethod
    def init(self):
        self.lots_waiting_for_family = defaultdict(lambda: set())
        self.usable_lots = list()
        self.lot_in_usable = defaultdict(lambda: False)
        self.free_machines = [False for _ in self.machines]

    @staticmethod
    def free_up_lots(self, lot):
        self.lots_waiting_for_family[lot.actual_step.family].add(lot)
        for machine in self.family_machines[lot.actual_step.family]:
            if self.free_machines[machine.idx]:
                MachineForLotDispatchManager.assign_lot_if_dedication_ok(self, lot, machine)

    @staticmethod
    def assign_lot_if_dedication_ok(self, lot, machine):
        di = lot.actual_step.order
        if di not in lot.dedications or machine.idx == lot.dedications[di]:
            if machine not in lot.waiting_machines:
                lot.waiting_machines.append(machine)
            if lot not in machine.waiting_lots:
                machine.waiting_lots.append(lot)
            if not self.lot_in_usable[lot.idx]:
                self.lot_in_usable[lot.idx] = True
                assert lot not in self.usable_lots
                assert len(lot.waiting_machines) > 0
                self.usable_lots.append(lot)

    @staticmethod
    def free_up_machine(self, machine):
        self.free_machines[machine.idx] = True
        for lot in self.lots_waiting_for_family[machine.family]:
            MachineForLotDispatchManager.assign_lot_if_dedication_ok(self, lot, machine)

    @staticmethod
    def reserve(self, lots, machine):
        self.free_machines[machine.idx] = False
        for lot in machine.waiting_lots:
            lot.waiting_machines.remove(machine)
            if len(lot.waiting_machines) == 0 and self.lot_in_usable[lot.idx]:
                self.lot_in_usable[lot.idx] = False
                self.usable_lots.remove(lot)
        machine.waiting_lots.clear()
        for lot in lots:
            self.lots_waiting_for_family[lot.actual_step.family].remove(lot)
            for m in lot.waiting_machines:
                m.waiting_lots.remove(lot)
            lot.waiting_machines.clear()
        for lot in lots:
            if self.lot_in_usable[lot.idx]:
                self.lot_in_usable[lot.idx] = False
                self.usable_lots.remove(lot)
                assert lot not in self.usable_lots

    @staticmethod
    def next_decision_point(self):
        while len(self.usable_lots) == 0 and not self.done:
            self.next_step()
        return self.done
