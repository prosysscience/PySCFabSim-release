import io
import os
from collections import defaultdict
import random

from simulation.plugins.interface import IPlugin

CHART_INTERVAL = 10


def random_color():
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())


class ChartPlugin(IPlugin):
    def on_sim_init(self, instance):
        self.debug_step_count = 0
        self.visualization_data_jobs = defaultdict(lambda: [])
        self.visualization_data_jobs_colors = defaultdict(lambda: [])
        self.visualization_data_tools = defaultdict(lambda: [])
        self.visualization_data_tools_colors = defaultdict(lambda: [])
        self.visualization_task_colors = defaultdict(random_color)
        self.visualization_tool_colors = defaultdict(random_color)

    def on_dispatch(self, instance, machine, lots, machine_end_time, lot_end_time):
        machine_name = f"{machine.idx}_{machine.family}"
        self.add_chart_tools(machine_name, ','.join([lot.name + ' ' + str(lot.idx) for lot in lots]),
                             ','.join([lot.actual_step.step_name for lot in lots]), instance.current_time,
                             machine_end_time)
        for lot in lots:
            self.add_chart_jobs(lot.name + ' ' + str(lot.idx), machine_name, lot.actual_step.order,
                                instance.current_time, lot_end_time)

        if self.debug_step_count % CHART_INTERVAL == 0:
            self.print_html()

    @property
    def act_dir(self):
        return os.path.dirname(os.path.realpath(__file__))

    def print_html(self):
        d = os.path.join(self.act_dir, 'visualization_template.html')
        with io.open(d, 'r') as f:
            template = f.read()
        for name, li, colors in [('tools', self.visualization_data_tools, self.visualization_data_tools_colors),
                                 ('jobs', self.visualization_data_jobs, self.visualization_data_jobs_colors)]:
            vis_data = []
            color_data = []
            keyss = sorted(li.keys())
            for k in keyss:
                vis_data += li[k]
                color_data += colors[k]
            data = template.replace('["DATA"]', ',\n'.join(vis_data))
            with io.open(f'chart_{name}.html', 'w') as f:
                f.write(data)

    def add_chart_tools(self, tool_name, job_name, task_name, t_from: int, t_to: int):
        self.visualization_data_tools[tool_name].append(
            f"['{tool_name}', '{task_name}', 'fill-color: {self.visualization_task_colors[job_name]}', " +
            f"new Date({t_from * 1000}), new Date({t_to * 1000})]")
        self.visualization_data_tools_colors[tool_name].append(f"'{self.visualization_task_colors[job_name]}'")

    def add_chart_jobs(self, job_name, tool_name, step, t_from, t_to):
        self.visualization_data_jobs[tool_name].append(
            f"['{job_name}', '{tool_name} s{step}', 'fill-color: {self.visualization_tool_colors[tool_name]}', " +
            f"new Date({t_from * 1000}), new Date({t_to * 1000})]")
        self.visualization_data_jobs_colors[tool_name].append(f"'{self.visualization_tool_colors[tool_name]}'")
