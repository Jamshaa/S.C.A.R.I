# src/utils/explainability.py
import numpy as np
from typing import Dict, List, Tuple
from collections import deque

class DecisionExplainer:
    """Explains SCARI agent decisions in human-readable format."""
    
    def __init__(self, max_history=100):
        self.decision_history = deque(maxlen=max_history)
        self.feature_names = [
            "Server 0 Temp", "Server 1 Temp", "Server 2 Temp", "Server 3 Temp", "Server 4 Temp",
            "Server 5 Temp", "Server 6 Temp", "Server 7 Temp", "Server 8 Temp", "Server 9 Temp",
            "Server 0 Load", "Server 1 Load", "Server 2 Load", "Server 3 Load", "Server 4 Load",
            "Server 5 Load", "Server 6 Load", "Server 7 Load", "Server 8 Load", "Server 9 Load"
        ]
    
    def explain_action(self, observation: np.ndarray, action: np.ndarray, step: int) -> Dict:
        """
        Generate human-readable explanation for why the agent took this action.
        
        Args:
            observation: Current state [temps, loads]
            action: Cooling actions taken
            step: Current timestep
            
        Returns:
            Dictionary with reasoning, feature importance, and confidence
        """
        num_servers = len(action)
        temps = observation[:num_servers]
        loads = observation[num_servers:]
        
        # Calculate feature importance (simple gradient-based attribution)
        feature_importance = self._calculate_feature_importance(temps, loads, action)
        
        # Generate natural language reasoning
        reasoning = self._generate_reasoning(temps, loads, action)
        
        # Calculate confidence based on action consistency
        confidence = self._calculate_confidence(temps, action)
        
        decision = {
            "step": step,
            "temperatures": temps.tolist(),
            "loads": loads.tolist(),
            "actions": action.tolist(),
            "reasoning": reasoning,
            "feature_importance": feature_importance,
            "confidence": confidence,
            "avg_temp": float(np.mean(temps)),
            "max_temp": float(np.max(temps)),
            "avg_action": float(np.mean(action))
        }
        
        self.decision_history.append(decision)
        return decision
    
    def _calculate_feature_importance(self, temps: np.ndarray, loads: np.ndarray, 
                                     action: np.ndarray) -> Dict[str, float]:
        """Calculate which features most influenced the decision."""
        num_servers = len(temps)
        importance = {}
        
        # Temperature influence (higher temps → more important)
        for i in range(num_servers):
            temp_influence = (temps[i] - 45.0) / 40.0  # Normalized around 45°C target
            importance[f"Server {i} Temp"] = float(np.clip(temp_influence, 0, 1))
        
        # Load influence (higher loads → slightly more important)
        for i in range(num_servers):
            load_influence = loads[i] * 0.3  # Weighted lower than temperature
            importance[f"Server {i} Load"] = float(load_influence)
        
        # Normalize to sum to 1
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
        
        # Return top 5 most important features
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_importance[:5])
    
    def _generate_reasoning(self, temps: np.ndarray, loads: np.ndarray, 
                           action: np.ndarray) -> List[str]:
        """Generate human-readable reasoning for the decision."""
        reasoning = []
        
        # Overall strategy
        avg_temp = np.mean(temps)
        avg_action = np.mean(action)
        
        if avg_temp > 65:
            reasoning.append(f"⚠️ High average temperature ({avg_temp:.1f}°C) → Aggressive cooling mode")
        elif avg_temp > 55:
            reasoning.append(f"📊 Moderate temperature ({avg_temp:.1f}°C) → Balanced cooling")
        else:
            reasoning.append(f"✅ Optimal temperature ({avg_temp:.1f}°C) → Minimal cooling needed")
        
        # Identify hottest servers
        hot_servers = np.where(temps > 60)[0]
        if len(hot_servers) > 0:
            hottest_idx = np.argmax(temps)
            reasoning.append(
                f"🔥 Server {hottest_idx} is hottest ({temps[hottest_idx]:.1f}°C) "
                f"→ Cooling at {action[hottest_idx]*100:.0f}%"
            )
        
        # Identify servers with high load
        loaded_servers = np.where(loads > 0.7)[0]
        if len(loaded_servers) > 0:
            reasoning.append(
                f"💻 {len(loaded_servers)} server(s) under heavy load "
                f"→ Increased cooling priority"
            )
        
        # Efficiency optimization
        cool_servers = np.where(temps < 50)[0]
        if len(cool_servers) > 0:
            reasoning.append(
                f"⚡ {len(cool_servers)} server(s) already cool "
                f"→ Reducing cooling for efficiency"
            )
        
        # Energy vs Safety tradeoff
        if avg_action < 0.2:
            reasoning.append("🌱 Energy efficiency mode: Minimal cooling")
        elif avg_action > 0.7:
            reasoning.append("🛡️ Safety priority mode: Maximum cooling")
        
        return reasoning
    
    def _calculate_confidence(self, temps: np.ndarray, action: np.ndarray) -> float:
        """
        Calculate confidence score based on decision consistency.
        High confidence = clear action (all high or all low)
        Low confidence = mixed actions (some high, some low)
        """
        # If all temps are in safe range and actions are consistent → high confidence
        temp_variance = np.std(temps)
        action_variance = np.std(action)
        
        # Low variance = high confidence
        temp_confidence = 1.0 - np.clip(temp_variance / 20.0, 0, 1)
        action_confidence = 1.0 - action_variance
        
        # Average the two
        overall_confidence = (temp_confidence + action_confidence) / 2.0
        
        return float(np.clip(overall_confidence, 0.5, 0.99))  # Never 100% confident
    
    def get_recent_decisions(self, n: int = 10) -> List[Dict]:
        """Get the last N decisions."""
        return list(self.decision_history)[-n:]
    
    def get_decision_summary(self) -> Dict:
        """Get summary statistics of recent decisions."""
        if not self.decision_history:
            return {}
        
        recent = list(self.decision_history)[-20:]
        
        return {
            "avg_confidence": float(np.mean([d["confidence"] for d in recent])),
            "avg_temp": float(np.mean([d["avg_temp"] for d in recent])),
            "avg_cooling": float(np.mean([d["avg_action"] for d in recent])),
            "max_temp_seen": float(max([d["max_temp"] for d in recent])),
            "total_decisions": len(self.decision_history)
        }
