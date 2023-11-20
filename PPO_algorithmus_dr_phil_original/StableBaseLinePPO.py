import gym
from stable_baselines3 import A2C, PPO  
from stable_baselines3.common.evaluation import evaluate_policy
from minimalenv import GridWorld

# Erstellen Sie eine Instanz des Grid World Environments
env = GridWorld()

# Erstellen und trainieren Sie den PPO-Agenten
model = A2C("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)  # Trainieren Sie den Agenten für eine bestimmte Anzahl von Zeitschritten

# Bewerten Sie die Leistung des trainierten Agenten
mean_reward, _ = evaluate_policy(model, env, n_eval_episodes=10)
print(f"Durchschnittliche Belohnung: {mean_reward}")

# Speichern Sie den trainierten Agenten
model.save("ppo_gridworld")

# Optional: Laden Sie den gespeicherten Agenten und verwenden Sie ihn
# loaded_model = PPO.load("ppo_gridworld")
# new_mean_reward, _ = evaluate_policy(loaded_model, env, n_eval_episodes=10)
# print(f"Durchschnittliche Belohnung des geladenen Agenten: {new_mean_reward}")
