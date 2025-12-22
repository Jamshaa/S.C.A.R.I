import numpy as np
import config

class Server:
    def __init__(self, server_id, cooling_mode="AIR"):
        self.id = server_id
        self.cpu_load = 0.0      # 0.0 a 1.0
        self.temperature = 25.0  # Temperatura inicial (Ambient)
        self.power_draw = config.P_IDLE
        
        # Cada servidor tiene su sistema de refrigeración asignado
        self.cooling_system = config.CoolingSystem(mode=cooling_mode)

    def update_physics(self, cpu_load_input, cooling_action, dt=1):
        """
        Paso de simulación física (1 segundo).
        cpu_load_input: Carga de trabajo actual (0-1)
        cooling_action: Velocidad del ventilador/bomba decidida por la IA (0-1)
        """
        self.cpu_load = cpu_load_input
        
        # 1. CALCULAR GENERACIÓN DE CALOR (Modelo Jin et al. 2020)
        # P(u) = P_idle + (P_max - P_idle) * (2u - u^r)
        u = self.cpu_load
        r = config.R_COEFF
        dynamic_factor = (2 * u) - (u ** r)
        # Potencia eléctrica consumida por el chip = Calor generado (Joules/sec)
        self.power_draw = config.P_IDLE + (config.P_MAX - config.P_IDLE) * dynamic_factor
        heat_generated = self.power_draw 

        # 2. CALCULAR EXTRACCIÓN DE CALOR
        # Cuánto calor se lleva el sistema de refrigeración
        heat_removed = self.cooling_system.get_cooling_capacity(cooling_action)
        
        # Consumo energético del ventilador/bomba (para GreenDC)
        cooling_energy_cost = self.cooling_system.get_power_consumption(cooling_action)

        # 3. ACTUALIZAR TEMPERATURA (Inercia Térmica)
        # T_new = T_old + (Energía_Neta / Masa_Térmica) * tiempo
        net_heat = heat_generated - heat_removed
        delta_temp = (net_heat * dt) / config.SERVER_THERMAL_MASS
        
        self.temperature += delta_temp

        # Retornamos el estado para que la IA lo vea
        return {
            "temp": self.temperature,
            "it_power": self.power_draw,
            "cooling_power": cooling_energy_cost
        }