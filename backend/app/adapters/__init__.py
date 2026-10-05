from app.adapters.base import BaseJobSourceAdapter
from app.adapters.manual import ManualJobSourceAdapter
from app.adapters.remotive import RemotiveJobSourceAdapter
from app.adapters.adzuna import AdzunaJobSourceAdapter

__all__ = [
    "BaseJobSourceAdapter",
    "ManualJobSourceAdapter",
    "RemotiveJobSourceAdapter",
    "AdzunaJobSourceAdapter",
]
