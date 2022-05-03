import datetime
import io
import json
import os
from sys import argv, stdout

from stable_baselines3 import PPO

from simulation.gym.environment import DynamicSCFabSimulationEnvironment
from simulation.gym.sample_envs import DEMO_ENV_1
from simulation.stats import print_statistics


def main():
    t = datetime.datetime.now()
    ranag = 'random' in argv[2]
    if not ranag:
        model = PPO.load(os.path.join(argv[1], argv[2]))
    with io.open(os.path.join(argv[1], "config.json"), "r") as f:
        config = json.load(f)['params']

    args = dict(seed=0, num_actions=config['action_count'], active_station_group=config['station_group'], days=365 * 2,
                dataset='SMT2020_' + config['dataset'], dispatcher=config['dispatcher'], reward_type=config['reward'])
    env = DynamicSCFabSimulationEnvironment(**DEMO_ENV_1, **args, max_steps=1000000000)
    obs = env.reset()
    reward = 0

    checkpoints = [180, 365]
    current_checkpoint = 0

    steps = 0
    shown_days = 0
    deterministic = True
    while True:
        if not ranag:
            action, _states = model.predict(obs, deterministic=deterministic)
        if ranag:
            if argv[2] == 'random':
                action = env.action_space.sample()
            else:
                state = obs[4:]
                actions = config['action_count']
                one_length = len(state) // actions
                descending = True
                index = 0
                sortable = []
                for i in range(actions):
                    sortable.append((state[one_length * i + index], i))
                sortable.sort(reverse=descending)
                action = sortable[0][1]
        obs, r, done, info = env.step(action)
        if r < 0:
            deterministic = False
        else:
            deterministic = True
        reward += r
        steps += 1
        di = int(env.instance.current_time_days)

        if di % 10 == 0 and di > shown_days:
            print(f'Step {steps} day {shown_days}')
            shown_days = di
            stdout.flush()

        chp = checkpoints[current_checkpoint]
        if env.instance.current_time_days > chp:
            print(f'{checkpoints[current_checkpoint]} days')
            print_statistics(env.instance, chp, config['dataset'], config['dispatcher'], method=f'rl{chp}', dir=argv[1])
            print('=================')
            stdout.flush()
            current_checkpoint += 1
            if len(checkpoints) == current_checkpoint:
                break

        if done:
            print('Exiting with DONE')
            break

    print(f'Reward is {reward}')
    dt = datetime.datetime.now() - t
    print('Elapsed', str(dt))
    env.close()


if __name__ == '__main__':
    main()
