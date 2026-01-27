# Sample decision log for demo/testing
SAMPLE_DECISIONS = [
    {
        "step": 100,
        "avgtemp": 52.3,
        "max_temp": 61.2,
        "avg_action": 0.25,
        "confidence": 0.87,
        "reasoning": [
            "✅ Optimal temperature (52.3°C) → Minimal cooling needed",
            "💻 3 server(s) under heavy load → Increased cooling priority",
            "🌱 Energy efficiency mode: Minimal cooling"
        ],
        "feature_importance": {
            "Server 3 Temp": 0.24,
            "Server 7 Temp": 0.18,
            "Server 1 Load": 0.15,
            "Server 5 Temp": 0.12,
            "Server 9 Load": 0.10
        }
    },
    {
        "step": 150,
        "avg_temp": 68.1,
        "max_temp": 82.5,
        "avg_action": 0.78,
        "confidence": 0.92,
        "reasoning": [
            "⚠️ High average temperature (68.1°C) → Aggressive cooling mode",
            "🔥 Server 4 is hottest (82.5°C) → Cooling at 95%",
            "🛡️ Safety priority mode: Maximum cooling"
        ],
        "feature_importance": {
            "Server 4 Temp": 0.35,
            "Server 8 Temp": 0.22,
            "Server 2 Temp": 0.16,
            "Server 6 Load": 0.11,
            "Server 1 Temp": 0.09
        }
    }
]
