# config.py

# --- SIMULATION SETTINGS ---
SIMULATION_STEP_SIZE = 1  # segundos por iteración

# --- FÍSICA DEL AIRE (Air Cooling) ---
AIR_DENSITY = 1.225       # kg/m^3
AIR_HEAT_CAPACITY = 1005  # J/(kg*K) (Cp)

# --- FÍSICA DEL LÍQUIDO (Water Cooling) ---
WATER_DENSITY = 997       # kg/m^3
WATER_HEAT_CAPACITY = 4184 # J/(kg*K) (4 veces mejor que el aire)

# --- MODELO DE SERVIDOR (Jin et al. 2020) ---
# Coeficientes ficticios para un servidor moderno (ej. H100 node)
P_IDLE = 200.0  # Watts
P_MAX = 800.0   # Watts
R_COEFF = 0.5   # Coeficiente de no-linealidad (r)

# --- INERCIA TÉRMICA ---
# Masa térmica equivalente del servidor (Heat Sink + Componentes)
SERVER_THERMAL_MASS = 5000 # J/K (Inventado para simular retardo)