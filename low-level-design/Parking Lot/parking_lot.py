from abc import ABC, abstractmethod
from datetime import datetime
from threading import Lock
from enum import Enum
import uuid


# =========================
# Enums
# =========================

class VehicleType(Enum):
    CAR = "Car"
    BIKE = "Bike"
    TRUCK = "Truck"


class SpotType(Enum):
    COMPACT = "Compact"
    LARGE = "Large"
    HANDICAPPED = "Handicapped"


# =========================
# Vehicles
# =========================

class Vehicle(ABC):
    def __init__(self, license_plate: str):
        self.license_plate = license_plate

    @property
    @abstractmethod
    def vehicle_type(self) -> VehicleType:
        pass


class Car(Vehicle):
    @property
    def vehicle_type(self):
        return VehicleType.CAR


class Bike(Vehicle):
    @property
    def vehicle_type(self):
        return VehicleType.BIKE


class Truck(Vehicle):
    @property
    def vehicle_type(self):
        return VehicleType.TRUCK


class VehicleFactory:
    @staticmethod
    def create_vehicle(
        vehicle_type: VehicleType,
        license_plate: str
    ) -> Vehicle:

        if vehicle_type == VehicleType.CAR:
            return Car(license_plate)

        if vehicle_type == VehicleType.BIKE:
            return Bike(license_plate)

        if vehicle_type == VehicleType.TRUCK:
            return Truck(license_plate)

        raise ValueError(
            f"Unsupported vehicle type: {vehicle_type}"
        )


# =========================
# Parking Spots
# =========================

class ParkingSpot(ABC):
    def __init__(self, spot_id: str):
        self.spot_id = spot_id
        self.vehicle = None

        # Protects occupancy of THIS spot.
        self._lock = Lock()

    @property
    @abstractmethod
    def spot_type(self) -> SpotType:
        pass

    @abstractmethod
    def can_fit_vehicle(
        self,
        vehicle: Vehicle
    ) -> bool:
        pass

    def is_free(self) -> bool:
        with self._lock:
            return self.vehicle is None

    def try_park(
        self,
        vehicle: Vehicle
    ) -> bool:
        """
        Check + park atomically.
        """

        with self._lock:

            if self.vehicle is not None:
                return False

            if not self.can_fit_vehicle(vehicle):
                return False

            self.vehicle = vehicle
            return True

    def leave(self) -> bool:
        with self._lock:

            if self.vehicle is None:
                return False

            self.vehicle = None
            return True


class CompactSpot(ParkingSpot):

    @property
    def spot_type(self):
        return SpotType.COMPACT

    def can_fit_vehicle(self, vehicle):
        return vehicle.vehicle_type in {
            VehicleType.CAR,
            VehicleType.BIKE
        }


class LargeSpot(ParkingSpot):

    @property
    def spot_type(self):
        return SpotType.LARGE

    def can_fit_vehicle(self, vehicle):
        return vehicle.vehicle_type in {
            VehicleType.CAR,
            VehicleType.BIKE,
            VehicleType.TRUCK
        }


class HandicappedSpot(ParkingSpot):

    @property
    def spot_type(self):
        return SpotType.HANDICAPPED

    def can_fit_vehicle(self, vehicle):
        # Simplified for interview.
        return vehicle.vehicle_type in {
            VehicleType.CAR,
            VehicleType.BIKE
        }


class ParkingSpotFactory:
    @staticmethod
    def create_parking_spot(
        spot_type: SpotType,
        spot_id: str
    ) -> ParkingSpot:

        if spot_type == SpotType.COMPACT:
            return CompactSpot(spot_id)

        if spot_type == SpotType.LARGE:
            return LargeSpot(spot_id)

        if spot_type == SpotType.HANDICAPPED:
            return HandicappedSpot(spot_id)

        raise ValueError(
            f"Unsupported parking spot type: {spot_type}"
        )


# =========================
# Floor
# =========================

class Floor:
    def __init__(self, floor_number: int):
        self.floor_number = floor_number
        self.spots = []

    def add_spot(self, spot: ParkingSpot):
        self.spots.append(spot)

    def try_park_vehicle(
        self,
        vehicle: Vehicle
    ):
        """
        Don't just find a free spot.

        Try to claim each compatible spot atomically.
        """

        for spot in self.spots:

            if spot.try_park(vehicle):
                return spot

        return None

    def available_spots_count(self):
        return sum(
            1
            for spot in self.spots
            if spot.is_free()
        )


# =========================
# Ticket
# =========================

class ParkingTicket:
    def __init__(
        self,
        vehicle: Vehicle,
        spot: ParkingSpot
    ):
        self.ticket_id = str(uuid.uuid4())

        self.vehicle = vehicle
        self.spot = spot

        self.entry_time = datetime.now()
        self.exit_time = None
        self.price = None

    def close(
        self,
        exit_time: datetime,
        price: float
    ):
        self.exit_time = exit_time
        self.price = price


# =========================
# Pricing Strategy
# =========================

class PricingStrategy(ABC):

    @abstractmethod
    def calculate_price(
        self,
        ticket: ParkingTicket,
        exit_time: datetime
    ) -> float:
        pass


class DefaultPricingStrategy(PricingStrategy):

    # In production this could come from
    # config / DB.
    RATES = {
        VehicleType.CAR: 10.0,
        VehicleType.BIKE: 5.0,
        VehicleType.TRUCK: 15.0
    }

    def calculate_price(
        self,
        ticket: ParkingTicket,
        exit_time: datetime
    ) -> float:

        duration = exit_time - ticket.entry_time

        total_seconds = duration.total_seconds()

        hours = int(total_seconds // 3600)

        if total_seconds % 3600 > 0:
            hours += 1

        # Minimum 1 hour
        hours = max(hours, 1)

        rate = self.RATES[
            ticket.vehicle.vehicle_type
        ]

        return hours * rate


# =========================
# Parking Lot
# =========================

class ParkingLot:
    def __init__(
        self,
        name: str,
        floors_count: int,
        pricing_strategy: PricingStrategy
    ):
        self.name = name

        self.floors = [
            Floor(i + 1)
            for i in range(floors_count)
        ]

        self.pricing_strategy = pricing_strategy

        self.active_tickets = {}

        # Protects active_tickets only.
        self._ticket_lock = Lock()

    def add_parking_spot(
        self,
        floor_number: int,
        spot_type: SpotType,
        spot_id: str
    ):

        if (
            floor_number < 1
            or floor_number > len(self.floors)
        ):
            raise ValueError(
                "Invalid floor number"
            )

        spot = (
            ParkingSpotFactory
            .create_parking_spot(
                spot_type,
                spot_id
            )
        )

        self.floors[
            floor_number - 1
        ].add_spot(spot)

    def park_vehicle(
        self,
        vehicle: Vehicle
    ) -> ParkingTicket | None:

        for floor in self.floors:

            spot = floor.try_park_vehicle(
                vehicle
            )

            if spot is None:
                continue

            ticket = ParkingTicket(
                vehicle,
                spot
            )

            # Only registry update needs
            # the ticket lock.
            with self._ticket_lock:
                self.active_tickets[
                    ticket.ticket_id
                ] = ticket

            print(
                f"{vehicle.license_plate} "
                f"parked at {spot.spot_id} "
                f"on floor {floor.floor_number}"
            )

            return ticket

        print(
            "Parking lot full or "
            "no suitable spot available."
        )

        return None

    def exit_vehicle(
        self,
        ticket_id: str
    ) -> float:

        # Get ticket safely.
        with self._ticket_lock:
            ticket = self.active_tickets.get(
                ticket_id
            )

        if ticket is None:
            raise ValueError(
                "Invalid ticket ID"
            )

        exit_time = datetime.now()

        price = (
            self.pricing_strategy
            .calculate_price(
                ticket,
                exit_time
            )
        )

        # Release parking spot.
        if not ticket.spot.leave():
            raise RuntimeError(
                "Parking spot already empty."
            )

        ticket.close(
            exit_time,
            price
        )

        # Remove from active tickets.
        with self._ticket_lock:
            self.active_tickets.pop(
                ticket_id,
                None
            )

        print(
            f"{ticket.vehicle.license_plate} "
            f"exited from {ticket.spot.spot_id}"
        )

        print(
            f"Total price: ${price:.2f}"
        )

        return price

    def get_available_spots_count(self):
        return sum(
            floor.available_spots_count()
            for floor in self.floors
        )


# =========================
# Example
# =========================

if __name__ == "__main__":

    parking_lot = ParkingLot(
        name="Downtown Parking",
        floors_count=2,
        pricing_strategy=DefaultPricingStrategy()
    )

    parking_lot.add_parking_spot(
        1,
        SpotType.COMPACT,
        "1C1"
    )

    parking_lot.add_parking_spot(
        1,
        SpotType.LARGE,
        "1L1"
    )

    parking_lot.add_parking_spot(
        1,
        SpotType.HANDICAPPED,
        "1H1"
    )

    parking_lot.add_parking_spot(
        2,
        SpotType.COMPACT,
        "2C1"
    )

    parking_lot.add_parking_spot(
        2,
        SpotType.LARGE,
        "2L1"
    )

    car = VehicleFactory.create_vehicle(
        VehicleType.CAR,
        "ABC123"
    )

    bike = VehicleFactory.create_vehicle(
        VehicleType.BIKE,
        "BIKE001"
    )

    truck = VehicleFactory.create_vehicle(
        VehicleType.TRUCK,
        "TRUCKX"
    )

    ticket1 = parking_lot.park_vehicle(car)
    ticket2 = parking_lot.park_vehicle(bike)
    ticket3 = parking_lot.park_vehicle(truck)

    if ticket1:
        parking_lot.exit_vehicle(ticket1.ticket_id)

    if ticket2:
        parking_lot.exit_vehicle(ticket2.ticket_id)

    if ticket3:
        parking_lot.exit_vehicle(ticket3.ticket_id)
