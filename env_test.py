import gym
import simulation.gym
from simulation.gym.environment import DynamicSCFabSimulationEnvironment

env = gym.make('DynamicSCFabSimulation-10days-v0')
state, done = env.reset(), False
ret = 0
steps = 0
while not done:
    action = env.action_space.sample()
    state, reward, done, info = env.step(action)
    ret += reward
    steps += 1

print(f"Return {ret} steps {steps}")

