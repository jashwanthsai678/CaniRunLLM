from dataclasses import dataclass, asdict

from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.engine import CompatibilityResult


@dataclass
class ModelCheckResult:
    model: ModelSpec
    compatibility: CompatibilityResult

    def to_dict(self):
        return asdict(self)
