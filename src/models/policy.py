# src/models/policy.py
import torch as th
import torch.nn as nn
from gymnasium import spaces
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.policies import ActorCriticPolicy
from typing import Dict, List, Any, Type, Union, Optional

class ThermalAttentionExtractor(BaseFeaturesExtractor):
    """
    Custom feature extractor for S.C.A.R.I. using Multi-Head Self-Attention.
    Treats each server as a node in a thermal network.
    """
    
    def __init__(self, observation_space: spaces.Box, features_dim: int = 128, num_heads: int = 4):
        super().__init__(observation_space, features_dim)
        
        # Observation space is (4 * num_servers,) -> [Temps..., Loads..., Health..., Trends...]
        self.num_servers = observation_space.shape[0] // 4
        self.embed_dim = 32
        
        # Input embeddings for each server state
        # Each server has 4 features: Temperature, Load, Health, Trend
        self.encoder = nn.Linear(4, self.embed_dim)
        
        # Transformer Layer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.embed_dim,
            nhead=num_heads,
            dim_feedforward=128,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        
        # Projection to output dimension
        self.flatten = nn.Flatten()
        self.projector = nn.Linear(self.num_servers * self.embed_dim, features_dim)
        
    def forward(self, observations: th.Tensor) -> th.Tensor:
        # observations: (batch_size, 4 * num_servers)
        batch_size = observations.shape[0]
        
        # Reshape to (batch_size, num_servers, 4)
        temps = observations[:, :self.num_servers].unsqueeze(-1)
        loads = observations[:, self.num_servers:2*self.num_servers].unsqueeze(-1)
        health = observations[:, 2*self.num_servers:3*self.num_servers].unsqueeze(-1)
        trends = observations[:, 3*self.num_servers:].unsqueeze(-1)
        server_states = th.cat([temps, loads, health, trends], dim=-1)
        
        # Embed each server
        embeddings = th.relu(self.encoder(server_states)) # (batch_size, num_servers, embed_dim)
        
        # Apply Self-Attention
        # This allows each server node to "see" the thermal state of neighbors
        latent = self.transformer(embeddings)
        
        # Project to features_dim
        latent_flat = self.flatten(latent)
        return th.relu(self.projector(latent_flat))

class AttentionPolicy(ActorCriticPolicy):
    """Custom Actor-Critic policy using the ThermalAttentionExtractor."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            features_extractor_class=ThermalAttentionExtractor,
            features_extractor_kwargs=dict(features_dim=128, num_heads=4),
        )
