import gym
from stable_baselines3 import PPO
from minimalenv import GridWorld

# Ihre GridWorld-Umgebung
env = GridWorld()

# Erstellen Sie das PPO-Modell
model = PPO("MlpPolicy", env, verbose=1)

# Trainieren Sie das Modell
model.learn(total_timesteps=10000)

# Testen Sie das trainierte Modell
obs = env.reset()
for _ in range(100):
    action, _ = model.predict(obs)
    obs, reward, done, info = env.step(action)
    env.render()

# Schließen Sie die Umgebung am Ende
env.close()
