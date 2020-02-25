import abc
from typing import Dict, List

from pytz import tzinfo

from .data_model import Route


class BaseAgent(abc.ABC):
    def __init__(self, agent_config: Dict):
        self._timezones = agent_config["airports_timezones"]

    def tzinfo(self, airport_name: str) -> tzinfo:
        return self._timezones[airport_name]

    @abc.abstractmethod
    async def load_routes(self, source: str, destination: str, **kwargs) -> List[Route]:
        ...
