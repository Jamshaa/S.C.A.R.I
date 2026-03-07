import torch as th
import torch.nn as nn
from gymnasium import spaces
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.policies import ActorCriticPolicy
from typing import Dict, List, Any, Type, Union, Optional

class ThermalAttentionExtractor(BaseFeaturesExtractor):

    def __init__(self, observation_space: spaces.Box, features_dim: int=128, num_heads: int=4):
        super().__init__(observation_space, features_dim)
        self.num_servers = observation_space.shape[0] // 4
        self.embed_dim = 32
        self.encoder = nn.Linear(4, self.embed_dim)
        encoder_layer = nn.TransformerEncoderLayer(d_model=self.embed_dim, nhead=num_heads, dim_feedforward=128, dropout=0.1, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.flatten = nn.Flatten()
        self.projector = nn.Linear(self.num_servers * self.embed_dim, features_dim)

    def forward(self, observations: th.Tensor) -> th.Tensor:
        batch_size = observations.shape[0]
        server_states = observations.view(batch_size, 4, self.num_servers).transpose(1, 2)
        embeddings = th.relu(self.encoder(server_states))
        latent = self.transformer(embeddings)
        latent_flat = self.flatten(latent)
        return th.relu(self.projector(latent_flat))

class AttentionPolicy(ActorCriticPolicy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, features_extractor_class=ThermalAttentionExtractor, features_extractor_kwargs=dict(features_dim=128, num_heads=4))