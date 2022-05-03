import datetime
import json
import os
import sys
import time

import wandb

from stable_baselines3 import PPO

from wandb.integration.sb3 import WandbCallback

from simulation.gym.environment import DynamicSCFabSimulationEnvironment
from stable_baselines3.common.callbacks import CheckpointCallback

from sys import argv

from simulation.gym.sample_envs import DEMO_ENV_1


def main():
    to_train = 1000000
    t = time.time()

    class MyCallBack(CheckpointCallback):

        def on_step(self) -> bool:
            if self.num_timesteps % 100 == 0:
                ratio = self.num_timesteps / to_train
                perc = round(ratio * 100)
                remaining = (time.time() - t) / ratio * (1 - ratio) if ratio > 0 else 9999999999999
                remaining /= 3600

                sys.stderr.write(f'\r{self.num_timesteps} / {to_train} {perc}% {round(remaining, 2)} hours left    {env.instance.current_time_days}      ')
            return super().on_step()

    fn = argv[1]
    with open(fn, 'r') as config:
        p = json.load(config)['params']
    args = dict(num_actions=p['action_count'], active_station_group=p['station_group'],
                days=p['training_period'], dataset='SMT2020_' + p['dataset'],
                dispatcher=p['dispatcher'])
    env = DynamicSCFabSimulationEnvironment(**DEMO_ENV_1, **args, seed=p['seed'], max_steps=1000000, reward_type=p['reward'])
    eval_env = DynamicSCFabSimulationEnvironment(**DEMO_ENV_1, **args, seed=777, max_steps=10000, reward_type=p['reward'])
    model = PPO("MlpPolicy", env, verbose=1)

    p = os.path.dirname(os.path.realpath(fn))
    checkpoint_callback = MyCallBack(save_freq=100000, save_path=p, name_prefix='checkpoint_')
    model.learn(
        total_timesteps=to_train, eval_freq=4000000, eval_env=eval_env, n_eval_episodes=1,
        callback=checkpoint_callback
    )
    model.save(os.path.join(p, 'trained.weights'))


if __name__ == '__main__':
    main()
