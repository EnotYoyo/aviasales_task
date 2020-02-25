import os
from datetime import timedelta
from pathlib import Path
from typing import Dict, Tuple, Callable, Optional, List

import yaml
from aiohttp import web
from aiohttp.abc import Request
from aiohttp.web_exceptions import HTTPNotFound

from aviasales_task.agent.data_model import Route
from aviasales_task.agents_controller import AgentsController
from aviasales_task.exception import AviasalesTaskValueError
from aviasales_task.helpers import load_data
from aviasales_task.schemas import flight_get_schema, routes_schema, Order, diff_get_schema


def sort_by_price(adult: int = 1, child: int = 0, infant: int = 0) -> Callable:
    def _sort_by_price_key(route: Route) -> Tuple[float, Optional[timedelta]]:
        return route.full_price(adult, child, infant), route.onward_time

    return _sort_by_price_key


def sort_by_time(adult: int = 1, child: int = 0, infant: int = 0) -> Callable:
    def _sort_by_time_key(route: Route) -> Tuple[Optional[timedelta], float]:
        return route.onward_time, route.full_price(adult, child, infant)

    return _sort_by_time_key


def sort_by_optimal(routes: List[Route], adult: int = 1, child: int = 0, infant: int = 0):
    assert len(routes) > 0

    min_price = routes[0].full_price(adult, child, infant)
    min_time = routes[0].full_time
    for route in routes:
        price = route.full_price(adult, child, infant)
        if price < min_price:
            min_price = price
        if route.full_time < min_time:
            min_time = route.full_time

    def _sort_by_optimal(item: Route) -> float:
        return item.full_price(adult, child, infant) / min_price + item.full_time / min_time

    return _sort_by_optimal


def _get_routes_difference(
        first_routes: List[Route], second_routes: List[Route], use_extended_info: bool = False
) -> List[Route]:
    first_routes_map = {route.itinerary_info(use_extended_info): route for route in first_routes}
    second_routes_map = {route.itinerary_info(use_extended_info): route for route in second_routes}

    result = []
    for route_id, route in second_routes_map.items():
        if route_id not in first_routes_map:
            result.append(route)

    return result


async def get_diff(request: Request):
    data = load_data(request.query, diff_get_schema)
    agents_controller: AgentsController = request.app["agents_controller"]

    first_routes = await agents_controller.load_routes("DXB", "BKK")
    second_routes = await agents_controller.load_routes("DXB", "BKK", with_return=True)

    difference = _get_routes_difference(first_routes, second_routes, data["use_extended_info"])

    return web.json_response(
        body=routes_schema.dumps(difference)
    )


async def route(request: Request):
    data = load_data(request.query, flight_get_schema)
    agents_controller: AgentsController = request.app["agents_controller"]
    routes = await agents_controller.load_routes(**data)

    if not routes:
        raise HTTPNotFound(text="Flights not found")

    order_by = data["order_by"]
    if order_by is Order.price:
        sort_key = sort_by_price(data["adult"], data["child"], data["infant"])
    elif order_by is Order.time:
        sort_key = sort_by_time(data["adult"], data["child"], data["infant"])
    else:
        sort_key = sort_by_optimal(routes, data["adult"], data["child"], data["infant"])

    sorted_routes = sorted(routes, key=sort_key, reverse=data["reverse"])
    return web.json_response(
        body=routes_schema.dumps(sorted_routes)
    )


def load_configs() -> Tuple[Dict, Dict]:
    default_config_path = os.path.join(os.path.dirname(__file__), "config")
    config_path = Path(os.environ.get("AVIASALES_TASK_CONFIGS_PATH", default_config_path))
    if not config_path.exists() or not config_path.is_dir():
        raise AviasalesTaskValueError("Incorrect path to configs")

    server_config = config_path / "server.yaml"
    agents_config = config_path / "agents.yaml"

    if not server_config.exists() or not agents_config.exists():
        raise AviasalesTaskValueError("Server or agents config not found")

    server_config = yaml.load(server_config.read_bytes(), Loader=yaml.Loader)
    agents_config = yaml.load(agents_config.read_bytes(), Loader=yaml.Loader)
    return server_config, agents_config


def start_server():
    server_config, agents_config = load_configs()

    app = web.Application()
    app["agents_controller"] = AgentsController(agents_config)

    app.add_routes([
        web.get("/route", route),
        web.get("/diff", get_diff),
    ])

    web.run_app(
        app,
        host=server_config["server"].get("host"),
        port=server_config["server"].get("port"),
    )


if __name__ == "__main__":
    start_server()
