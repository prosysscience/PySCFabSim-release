import numpy as np
import gym
from gym.spaces import Discrete

class GridWorld(gym.Env):
    def __init__(self):
        self.grid_size = 3
        self.agent_pos = [0, 0]
        self.goal_pos = [2, 2]
        self.obstacle_pos = [1, 1]
        self.done = False
        self.highest_reward = 0
        self.observation_space = Discrete(self.grid_size * self.grid_size)
        self.action_space = Discrete(4)

    def reset(self):
        self.agent_pos = [0, 0]
        self.done = False
        return self._position_to_int(self.agent_pos)

    def step(self, action):
        info = 22
        if self.done:
            return tuple(self.agent_pos), 0, True

        if action == 0:  # Up
            self.agent_pos[0] = max(0, self.agent_pos[0] - 1)
        elif action == 1:  # Down
            self.agent_pos[0] = min(self.grid_size - 1, self.agent_pos[0] + 1)
        elif action == 2:  # Left
            self.agent_pos[1] = max(0, self.agent_pos[1] - 1)
        elif action == 3:  # Right
            self.agent_pos[1] = min(self.grid_size - 1, self.agent_pos[1] + 1)

        if self.agent_pos == self.goal_pos:
            self.done = True
            reward = 1
        elif self.agent_pos == self.obstacle_pos:
            self.done = True
            reward = -1
        else:
            reward = 0

        self.highest_reward = max(self.highest_reward, reward)

        return self._position_to_int(self.agent_pos), reward, self.done, info

    def get_highest_reward(self):
            return self.highest_reward
    
    def _position_to_int(self, position):
        return position[0] * self.grid_size + position[1]

    def _int_to_position(self, value):
        return [value // self.grid_size, value % self.grid_size]





