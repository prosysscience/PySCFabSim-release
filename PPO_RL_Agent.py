import gym
import sys
from sys import argv
import os
import json
sys.path.append(os.path.join('C:/','Users','willi','OneDrive','Documents','Studium','Diplomarbeit','Programm + Datengrundlage','PySCFabSim-release','PPO_algorithmus_dr_phil'))

import numpy as np

from PPO import Agent
import torch as T


from simulation.gym.environment import DynamicSCFabSimulationEnvironment
from simulation.gym.sample_envs import DEMO_ENV_1
from utils import plot_learning_curve

import argparse

def create_agent(env):
    batch_size = 64
    n_epochs = 10
    alpha = 0.0003
    actions = 9
    input_dims = 81
    agent = Agent(n_actions=actions, batch_size=batch_size, 
                    alpha=alpha, n_epochs=n_epochs, 
                    input_dims=input_dims)
    return agent



def main():
    # fn = argv[1]
    # with open(fn, 'r') as config:
    #     p = json.load(config)['params']
    # args = dict(num_actions=p['action_count'], active_station_group=p['station_group'],
    #             days=p['training_period'], dataset='SMT2020_' + p['dataset'],
    #             dispatcher=p['dispatcher'])
    args = dict(num_actions=9, active_station_group="<Diffusion_FE_120>",
                days=10, dataset='SMT2020_' + "HVLM",
                dispatcher="fifo")
    env = DynamicSCFabSimulationEnvironment(**DEMO_ENV_1, **args, seed=0, max_steps=10000000, reward_type=2)
    #instance = env
    ##############################
    ###  RL Agent Erstellung   ###
    ##############################

    N = 20
    agent = create_agent(env)
    n_games = 100

    figure_file = 'PPO_algorithmus_dr_phil\plots/Semiconductor.png'

    #best_score = instance.reward_range[0] #???
    best_score = 0
    score_history = [] 

    learn_iters = 0
    avg_score = 0
    n_steps = 0

    for i in range(n_games):
        state = env.reset()
        state = state[4:]
        print("state wihtout 4", state)
        score = 0
        done = False
        
        while not done:
            #state = np.array(state)
            #action, prob, val = agent.choose_action(state)
            actions = 9
            one_length = len(state) // actions
            # descending = True
            index = 0
            # sortable = []
            available_actions = []
            for i in range(actions):
                available_actions.append((state[one_length * i + index] != -1000))
            print("available_actions", available_actions)
                
            #sortable.sort(reverse=descending)
            
            #### Old Version without Critic ####
            #sortable = np.array([element[0] for element in sortable])
            
            #action = sortable[0][1]

            #### New Version with Critic ####
            
            #sortable_array = np.array(sortable, dtype=float)
            action, prob, val = agent.choose_action(state, available_actions)
            if available_actions[action] == False:
                print("Der Agtent hat eine illigale Entscheidung getroffen!!!")
                print("availableActionSpace" , available_actions)
                print("action", action)
                print("prob" , prob)
                print("val" , val)
                die()
            #observation_, reward, done, info = env.step(action)
            state_, reward, done, info = env.step(action) 
                    
            n_steps += 1
            score += reward
            agent.remember(state, action,prob, val, reward, done)
            if n_steps % N == 0:
                agent.learn()
                learn_iters += 1
            state = state_
        score_history.append(score)
        avg_score = np.mean(score_history[-100:])

        if avg_score > best_score:
            best_score = avg_score
            agent.save_models()

        print('episode', i, 'score %.1f' % score, 'avg score %.1f' % avg_score,
                'time_steps', n_steps, 'learning_steps', learn_iters)
    x = [i+1 for i in range(len(score_history))]
    plot_learning_curve(x, score_history, figure_file)
    env.close()


if __name__ == '__main__':
    main()