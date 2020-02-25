import datetime
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup, Tag

from aviasales_task.agent.data_model import Flight, PathInformation, Price, Route
from aviasales_task.agent.base_agent import BaseAgent


class ViaAgent(BaseAgent):
    def __init__(self, agent_config: Dict):
        super().__init__(agent_config)

        self._date_format = agent_config["date_format"]
        self._onward_response = Path(agent_config["onward_response"])
        self._onward_return_response = Path(agent_config["onward_return_response"])

    @staticmethod
    def _subtag_content(tag, subtag_name) -> str:
        subtag = tag.find(subtag_name)
        if subtag is None:
            raise ValueError(f"Subtag {subtag_name} not found")

        return subtag.text.strip()

    def _parse_date(self, date_string: str, airport_name: str) -> datetime.datetime:
        airport_tz = self.tzinfo(airport_name)
        date = datetime.datetime.strptime(date_string, self._date_format)
        return airport_tz.localize(date)

    def _parse_path_info(self, flight_elem: Tag) -> PathInformation:
        source = flight_elem.Source.text
        departure_time = flight_elem.DepartureTimeStamp.text
        departure_time = self._parse_date(departure_time, source)

        destination = flight_elem.Destination.text
        arrival_time = flight_elem.ArrivalTimeStamp.text
        arrival_time = self._parse_date(arrival_time, destination)

        return PathInformation(
            source=source,
            destination=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
        )

    def _parse_sub_flight(self, sub_flight: Tag) -> Flight:
        carrier: Tag = sub_flight.Carrier

        return Flight(
            carrier_id=carrier["id"],
            carrier_name=carrier.text.strip(),
            number=sub_flight.FlightNumber.text.strip(),
            path_info=self._parse_path_info(sub_flight),
            klass=sub_flight.Class.text.strip(),
            stops=int(sub_flight.NumberOfStops.text),
            fare_basis=sub_flight.FareBasis.text.strip(),
            ticket_type=sub_flight.TicketType.text.strip(),
        )

    def _parse_pricing(self, pricing: Tag) -> Price:
        currency = pricing["currency"]

        prices = {}
        for price in pricing.find_all("ServiceCharges", attrs={"ChargeType": "TotalAmount"}):
            prices[price["type"]] = float(price.text)

        return Price(
            currency=currency,
            adult=prices["SingleAdult"],
            child=prices.get("SingleChild", prices["SingleAdult"]),
            infant=prices.get("SingleInfant", prices["SingleAdult"]),
        )

    def _parse_flight(self, flight: Tag) -> Route:
        onward_flights, return_flights = [], []
        for sub_flight in flight.select("OnwardPricedItinerary Flights Flight"):
            onward_flights.append(self._parse_sub_flight(sub_flight))
        for sub_flight in flight.select("ReturnPricedItinerary Flights Flight"):
            return_flights.append(self._parse_sub_flight(sub_flight))
        price = self._parse_pricing(flight.Pricing)

        return Route(
            price=price,
            onward_flights=onward_flights,
            return_flights=return_flights,
        )

    async def load_routes(self, source: str, destination: str, **kwargs) -> List[Route]:
        data_file = self._onward_response
        if kwargs.get("with_return"):
            data_file = self._onward_return_response

        soup = BeautifulSoup(data_file.read_bytes(), "xml")

        routes = []
        for flight in soup.PricedItineraries.children:
            if isinstance(flight, Tag):
                routes.append(self._parse_flight(flight))

        return routes
