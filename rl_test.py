import datetime
import io
import json
import os
from sys import argv, stdout
import sys

from stable_baselines3 import PPO
sys.path.append(os.path.join('C:/','Users','willi','OneDrive','Documents','Studium','Diplomarbeit','Programm + Datengrundlage','PySCFabSim-release','simulation'))
sys.path.append(os.path.join('data','horse','ws','wiro085f-WsRodmann','Final_Version','PySCFabSim', 'simulation'))
from simulation.gym.environment import DynamicSCFabSimulationEnvironment
from simulation.gym.sample_envs import DEMO_ENV_1
from simulation.stats import print_statistics


def main():
    print("Starting Test")
    wandb = True
    testing_days = 365 * 2
    t = datetime.datetime.now()
    #ranag = 'random' in argv[2]
    ranag =  "trained.weights"
    arg1 = "experiments/0_ds_HVLM_a9_tp365_reward2_di_fifo_Di"
    #if not ranag:
    model = PPO.load(os.path.join(arg1, ranag))
    with io.open(os.path.join(arg1, "config.json"), "r") as f:
        config = json.load(f)['params']
    args = dict(seed=0, num_actions=9, active_station_group='<Diffusion_FE_120>', days=testing_days,
                dataset='SMT2020_' + 'HVLM', dispatcher='fifo', reward_type=2)
    
    #args = dict(seed=0, num_actions=config['action_count'], active_station_group=config['station_group'], days=testing_days,
    #            dataset='SMT2020_' + config['dataset'], dispatcher=config['dispatcher'], reward_type=config['reward'])
    
    
    plugins = []
    if wandb:
        from plugins.wandb_plugin import WandBPlugin
        plugins.append(WandBPlugin())
    env = DynamicSCFabSimulationEnvironment(**DEMO_ENV_1, **args, max_steps=1000000000, plugins=plugins)
    obs = env.reset()
    #print("obs", obs)
    reward = 0

    checkpoints = [180, 365, testing_days]
    current_checkpoint = 0

    steps = 0
    shown_days = 0
    deterministic = True
    print("Starting Loop")
    while True:
        
        action, _states = model.predict(obs, deterministic=deterministic)
        #print("action", action)
        if ranag:
            if ranag == 'random':
                action = env.action_space.sample()
            else:
                state = obs[4:]
                #print("State", state)
                actions = config['action_count']
                one_length = len(state) // actions
                #print("one_length", one_length)
                descending = True
                index = 0
                sortable = []
                for i in range(actions):
                    sortable.append((state[one_length * i + index], i))
                sortable.sort(reverse=descending)
                #print("sortable", sortable)
                action = sortable[0][1]
        #         print("action",action)
        obs, r, done, info = env.step(action)
       # print("obs", obs)   
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
