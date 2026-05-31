import numpy as np
from typing import Dict, List, Tuple
from collections import deque

class DecisionExplainer:

    def __init__(self, num_servers: int=10, t_min: float=22.0, t_max: float=95.0, max_history=100):
        self.decision_history = deque(maxlen=max_history)
        self.num_servers = num_servers
        self.t_min = t_min
        self.t_max = t_max
        self.feature_names = [f'Server {i} Temp' for i in range(num_servers)] + [f'Server {i} Load' for i in range(num_servers)] + [f'Trend {i}' for i in range(num_servers)]

    def explain_action(self, observation: np.ndarray, action: np.ndarray, step: int) -> Dict:
        if len(observation.shape) > 1:
            observation = observation.flatten()
        if len(action.shape) > 1:
            action = action.flatten()
        num_servers = len(action)
        norm_temps = observation[:num_servers]
        temps = norm_temps * (self.t_max - self.t_min) + self.t_min
        loads = observation[num_servers:2 * num_servers]
        health = observation[2 * num_servers:3 * num_servers]
        trends = observation[3 * num_servers:4 * num_servers]
        feature_importance = self._calculate_feature_importance(temps, loads, action)
        reasoning = self._generate_reasoning(temps, loads, action)
        confidence = self._calculate_confidence(temps, action)
        decision = {'step': step, 'temperatures': temps.tolist(), 'loads': loads.tolist(), 'actions': action.tolist(), 'trends': trends.tolist(), 'reasoning': reasoning, 'feature_importance': feature_importance, 'confidence': confidence, 'avg_temp': float(np.mean(temps)), 'max_temp': float(np.max(temps)), 'avg_action': float(np.mean(action))}
        self.decision_history.append(decision)
        return decision

    def _calculate_feature_importance(self, temps: np.ndarray, loads: np.ndarray, action: np.ndarray) -> Dict[str, float]:
        num_servers = len(temps)
        importance = {}
        for i in range(num_servers):
            temp_influence = (temps[i] - 45.0) / 40.0
            importance[f'Server {i} Temp'] = float(np.clip(temp_influence, 0, 1))
        for i in range(num_servers):
            load_influence = loads[i] * 0.3
            importance[f'Server {i} Load'] = float(load_influence)
        total = sum(importance.values())
        if total > 0:
            importance = {k: v / total for k, v in importance.items()}
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_importance[:5])

    def _generate_reasoning(self, temps: np.ndarray, loads: np.ndarray, action: np.ndarray) -> List[str]:
        reasoning = []
        avg_temp = np.mean(temps)
        avg_action = np.mean(action)
        if avg_temp > 63:
            reasoning.append(f'🔴 CRITICAL: Hard Wall Breach ({avg_temp:.1f}°C) → Emergency Cooling')
        elif avg_temp > 55:
            reasoning.append(f'⚠️ High Temperature ({avg_temp:.1f}°C) → Increasing cooling')
        elif avg_temp > 48:
            reasoning.append(f'📊 Moderate Temperature ({avg_temp:.1f}°C) → Balanced optimization')
        else:
            reasoning.append(f'✅ Optimal temperature ({avg_temp:.1f}°C) → Minimal cooling needed')
        hot_servers = np.where(temps > 55)[0]
        if len(hot_servers) > 0:
            hottest_idx = np.argmax(temps)
            reasoning.append(f'🔥 Server {hottest_idx} is hottest ({temps[hottest_idx]:.1f}°C) → Cooling at {action[hottest_idx] * 100:.0f}%')
        loaded_servers = np.where(loads > 0.7)[0]
        if len(loaded_servers) > 0:
            reasoning.append(f'💻 {len(loaded_servers)} server(s) under heavy load → Increased cooling priority')
        cool_servers = np.where(temps < 50)[0]
        if len(cool_servers) > 0:
            reasoning.append(f'⚡ {len(cool_servers)} server(s) already cool → Reducing cooling for efficiency')
        if avg_action < 0.2:
            reasoning.append('🌱 Energy efficiency mode: Minimal cooling')
        elif avg_action > 0.7:
            reasoning.append('🛡️ Safety priority mode: Maximum cooling')
        return reasoning

    def _calculate_confidence(self, temps: np.ndarray, action: np.ndarray) -> float:
        temp_variance = np.std(temps)
        action_variance = np.std(action)
        temp_confidence = 1.0 - np.clip(temp_variance / 20.0, 0, 1)
        action_confidence = 1.0 - action_variance
        overall_confidence = (temp_confidence + action_confidence) / 2.0
        return float(np.clip(overall_confidence, 0.5, 0.99))

