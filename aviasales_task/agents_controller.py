import json
import logging
from asyncio import wait
from typing import Dict, Optional, List

import pytz

from aviasales_task.agent import BaseAgent
from aviasales_task.agent.data_model import Route

logger = logging.getLogger(__name__)


class AgentsController:
    def __init__(self, agents_config: Dict):
        config = agents_config.get("agents_controller", {})
        self._agents_timeout = float(config.get("agents_timeout", 5))
        airports_timezones = self._load_timezone_file(config.get("airports_timezones"))
        self._agent_registry = self._load_agents(agents_config, airports_timezones)

    async def load_routes(self, source: str, destination: str, **kwargs) -> List[Route]:
        agents_tasks = [agent.load_routes(source, destination, **kwargs) for agent in self._agent_registry]
        tasks, _ = await wait(agents_tasks, timeout=self._agents_timeout)

        routes = []
        for task in tasks:
            try:
                agent_routes = task.result()
            except Exception:
                logger.exception("Error getting agent routes, skip.")
            else:
                routes.extend(agent_routes)

        return routes

    def _load_agents(self, agents_config: Dict, airports_timezones: Optional[Dict]):
        agents_cls = {cls.__name__.lower(): cls for cls in BaseAgent.__subclasses__()}
        agents_instance = []
        for name, config in agents_config.get("agents", {}).items():
            cls = agents_cls.get(f"{name}agent")
            if cls:
                config["airports_timezones"] = airports_timezones
                agents_instance.append(cls(config))

        return agents_instance

    @staticmethod
    def _load_timezone_file(airports_timezones: Optional[str]) -> Optional[Dict]:
        if airports_timezones:
            with open(airports_timezones) as file:
                airports_timezones = json.load(file)
                for airport, tz_name in airports_timezones.items():
                    airports_timezones[airport] = pytz.timezone(tz_name)
                return airports_timezones
