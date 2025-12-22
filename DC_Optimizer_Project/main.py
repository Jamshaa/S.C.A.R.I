import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from models.server import Server

SIMULATION_STEPS = 300
server_air = Server(id=1, cooling_mode= "AIR")
server_liquid = Server(id=2, cooling_mode= "LIQUID")

results_air = []
results_liquid = []

for t in range(SIMULATION_STEPS):
    load = 0.1
    if 50 < t < 150:
        load = 0.9
    
    action = 1.0 if load > 0.5 else 0.2

    stats_air = server_air.update_physics(load,action)
    stats_liquid = server_liquid.update_physics(load,action)
    results_air.append(stats_air)
    results_liquid.append(stats_liquid)

df_air = pd.DataFrame(results_air)
df_liquid = pd.DataFrame(results_liquid)
plt.figure(figsize=(12,5))
plt.subplot(1, 2, 1)
plt.plot(df_air['temp'], label='Air Cooling', color='orange')
plt.plot(df_liquid['temp'], label='Liquid Cooling', color='blue')
plt.title("Comparativa Temperatura CPU")
plt.ylabel("Temp (ºC)")
plt.xlabel("Tiempo (s)")
plt.legend()

# Gráfica de Consumo Refrigeración
plt.subplot(1, 2, 2)
plt.plot(df_air['cooling_power'], label='Consumo Ventilador (W)', color='orange')
plt.plot(df_liquid['cooling_power'], label='Consumo Bomba (W)', color='blue')
plt.title("Consumo Energético del Sistema de Frío")
plt.ylabel("Watts")
plt.xlabel("Tiempo (s)")
plt.legend()

plt.tight_layout()
plt.show()