from abc import abstractmethod, ABCMeta


class IPlugin(metaclass=ABCMeta):
    def on_sim_init(self, instance):
        pass

    def on_sim_done(self, instance):
        pass

    def on_lots_release(self, instance, lots):
        pass

    def on_lot_done(self, instance, lot):
        pass

    def on_step_done(self, instance, lot, step):
        pass

    def on_dispatch(self, instance, machine, lots, machine_end_time, lot_end_time):
        pass

    def on_machine_free(self, instance, machine):
        pass

    def on_lot_free(self, instance, lot):
        pass

    def on_breakdown(self, machine, breakdown_event):
        pass

    def on_preventive_maintenance(self, machine, preventive_maintenance_event):
        pass

    def get_output_name(self):
        return None

    def get_output_value(self):
        raise NotImplementedError()

    def on_cqt_violated(self, instance, machine, lot):
        pass
