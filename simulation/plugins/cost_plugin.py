from simulation.plugins.interface import IPlugin


class CostPlugin(IPlugin):

    def on_sim_done(self, instance):
        super().on_sim_done(instance)
        self.cost = 0
        for lot in instance.done_lots:
            self.cost += 25 if lot.deadline_at < lot.done_at else 0
            self.cost += max(0, lot.done_at - lot.deadline_at) / 3600 / 24
        self.cost += len(instance.active_lots) * 200
        self.done_lots = len(instance.done_lots)

    def get_output_name(self):
        super().get_output_name()
        return 'cost'

    def get_output_value(self):
        return self.cost
