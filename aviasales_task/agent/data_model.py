from dataclasses import dataclass, astuple
from datetime import datetime, timedelta
from functools import cached_property
from typing import List, Tuple, Optional


@dataclass
class Price:
    adult: float
    child: float
    infant: float
    currency: str


@dataclass
class PathInformation:
    source: str
    destination: str
    departure_time: datetime
    arrival_time: datetime


@dataclass
class Flight:
    carrier_id: str
    carrier_name: str
    number: str
    path_info: PathInformation
    klass: str
    stops: int
    fare_basis: str
    ticket_type: str

    def basic_info(self) -> Tuple[str, str, str, str]:
        return (
            self.carrier_id,
            self.number,
            self.path_info.source,
            self.path_info.destination,
        )

    def extended_info(self) -> Tuple[str, str, str, str, str, int, str]:
        return (
            *self.basic_info(),
            self.klass,
            self.stops,
            self.ticket_type,
        )


@dataclass
class Route:
    price: Price
    onward_flights: List[Flight]
    return_flights: List[Flight]

    def __init__(self, price: Price, onward_flights: List[Flight], return_flights: List[Flight]):
        self.price = price
        self.onward_flights = onward_flights
        self.return_flights = return_flights

    @cached_property
    def onward_info(self) -> PathInformation:
        return self._build_path_info(self.onward_flights)

    @cached_property
    def return_info(self) -> Optional[PathInformation]:
        return self._build_path_info(self.return_flights)

    @cached_property
    def onward_is_direct(self) -> bool:
        return self._is_direct(self.onward_flights)

    @cached_property
    def return_is_direct(self) -> bool:
        return self._is_direct(self.return_flights)

    @cached_property
    def onward_time(self) -> timedelta:
        return self._time_in_route(self.onward_info)

    @cached_property
    def return_time(self) -> Optional[timedelta]:
        return self._time_in_route(self.return_info)

    @cached_property
    def full_time(self) -> timedelta:
        return self.onward_time + (self.return_time or timedelta())

    def full_price(self, adult: int = 1, child: int = 0, infant: int = 0) -> float:
        return self.price.adult * adult + self.price.child * child + self.price.infant * infant

    @staticmethod
    def _is_direct(flights) -> bool:
        return len(flights) == 1

    @staticmethod
    def _time_in_route(path_info: Optional[PathInformation]) -> Optional[timedelta]:
        if path_info:
            return path_info.arrival_time - path_info.departure_time

    def itinerary_info(self, extended=False) -> Tuple[Tuple, ...]:
        if not extended:
            return tuple(flight.basic_info() for flight in self.onward_flights)
        else:
            return tuple(flight.extended_info() for flight in self.onward_flights)

    @staticmethod
    def _build_path_info(flights: List[Flight]) -> Optional[PathInformation]:
        if not flights:
            return None
        return PathInformation(
            source=flights[0].path_info.source,
            destination=flights[-1].path_info.destination,
            departure_time=flights[0].path_info.departure_time,
            arrival_time=flights[-1].path_info.arrival_time,
        )
