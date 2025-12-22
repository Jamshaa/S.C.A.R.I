import numpy as np

class CoolingSystem:
    def __init__(self, mode="AIR"):
        self.mode = mode # "AIR", "LIQUID", "HYBRID"

    def get_power_consumption(self, flow_rate):
        """
        Calcula cuánta electricidad gastamos para enfriar.
        flow_rate: % de velocidad (0.0 a 1.0)
        """
        power_draw = 0.0

        if self.mode == "AIR":
            # LEY DEL VENTILADOR: Potencia proprocional al CUBOR de la velocidad
            # Supongamos un ventilador de servidor potente gasta 50W al 100%
            MAX_FAN_POWER = 50.0 
            power_draw = MAX_FAN_POWER * (flow_rate ** 3)

        elif self.mode == "LIQUID":
            # LEY DE LA BOMBA: Proporcional al cuadrado (o lineal según diseño)
            # Más el consumo base de la CDU
            BASE_PUMP_POWER = 10.0
            MAX_PUMP_POWER = 30.0
            if flow_rate > 0:
                power_draw = BASE_PUMP_POWER + (MAX_PUMP_POWER * (flow_rate ** 2))
        
        elif self.mode == "HYBRID":
            # Mezcla: Aire al 30% + Líquido al 70% (simplificado)
            power_draw = (50.0 * (0.3 * flow_rate)**3) + (30.0 * (0.7 * flow_rate))

        return power_draw

    def get_cooling_capacity(self, flow_rate):
        """
        Devuelve cuántos Watts de calor somos capaces de extraer (J/s)
        """
        # Aquí defines la superioridad del agua
        if self.mode == "AIR":
            return flow_rate * 1000 # Aire saca hasta 1000W (aprox)
        elif self.mode == "LIQUID":
            return flow_rate * 5000 # Agua saca hasta 5000W (mucho más)
        return 0