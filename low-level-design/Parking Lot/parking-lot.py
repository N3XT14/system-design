from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from threading import Lock

class Vehicle(ABC):
    def __init__(self, license_plate: str):
        self.license_plate = license_plate

    @abstractmethod
    def get_type(self):
        pass

class Car(Vehicle):
    def get_type(self):
        return "Car"

class Bike(Vehicle):
    def get_type(self):
        return "Bike"

class Truck(Vehicle):
    def get_type(self):
        return "Truck"

class VehicleFactory:
    @staticmethod
    def create_vehicle(vehicle_type: str, license_plate: str) -> Vehicle:
        vehicle_type = vehicle_type.lower()
        if vehicle_type == "car":
            return Car(license_plate)
        elif vehicle_type == "bike":
            return Bike(license_plate)
        elif vehicle_type == "truck":
            return Truck(license_plate)
        else:
            raise ValueError(f"Unknown vehicle type: {vehicle_type}")

class ParkingSpot(ABC):
    def __init__(self, spot_id: str):
        self.spot_id = spot_id
        self.vehicle = None

    @abstractmethod
    def can_fit_vehicle(self, vehicle: Vehicle) -> bool:
        pass

    def is_free(self):
        return self.vehicle is None

    def park(self, vehicle: Vehicle) -> bool:
        if self.can_fit_vehicle(vehicle) and self.is_free():
            self.vehicle = vehicle
            return True
        return False

    def leave(self):
        self.vehicle = None

class CompactSpot(ParkingSpot):
    def can_fit_vehicle(self, vehicle: Vehicle) -> bool:
        return vehicle.get_type() in ["Car", "Bike"]

class LargeSpot(ParkingSpot):
    def can_fit_vehicle(self, vehicle: Vehicle) -> bool:
        return vehicle.get_type() in ["Car", "Bike", "Truck"]

class HandicappedSpot(ParkingSpot):
    def can_fit_vehicle(self, vehicle: Vehicle) -> bool:
        return vehicle.get_type() in ["Car", "Bike"]

class ParkingSpotFactory:
    @staticmethod
    def create_parking_spot(spot_type: str, spot_id: str) -> ParkingSpot:
        spot_type = spot_type.lower()
        if spot_type == "compact":
            return CompactSpot(spot_id)
        elif spot_type == "large":
            return LargeSpot(spot_id)
        elif spot_type == "handicapped":
            return HandicappedSpot(spot_id)
        else:
            raise ValueError(f"Unknown spot type: {spot_type}")

class Floor:
    def __init__(self, floor_number: int):
        self.floor_number = floor_number
        self.spots = []

    def add_spot(self, spot: ParkingSpot):
        self.spots.append(spot)

    def find_available_spot(self, vehicle: Vehicle):
        for spot in self.spots:
            if spot.is_free() and spot.can_fit_vehicle(vehicle):
                return spot
        return None

class ParkingTicket:
    def __init__(self, ticket_id: str, entry_time: datetime, spot: ParkingSpot, vehicle: Vehicle):
        self.ticket_id = ticket_id
        self.entry_time = entry_time
        self.exit_time = None
        self.spot = spot
        self.vehicle = vehicle
        self.price = 0.0

    def close_ticket(self, exit_time: datetime, price: float):
        self.exit_time = exit_time
        self.price = price

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, ticket: ParkingTicket) -> float:
        pass

class DefaultPricingStrategy(PricingStrategy):
    rates = {
        "Car": 10.0,
        "Bike": 5.0,
        "Truck": 15.0
    }

    def calculate_price(self, ticket: ParkingTicket) -> float:
        if ticket.exit_time is None:
            raise Exception("Ticket exit time not set")

        duration = ticket.exit_time - ticket.entry_time
        hours = int(duration.total_seconds() // 3600)
        if duration.total_seconds() % 3600 > 0:
            hours += 1

        rate = self.rates.get(ticket.vehicle.get_type(), 10)
        return hours * rate

class ParkingLot:
    _instance = None
    _lock = Lock()

    def __init__(self, name: str, floors_count: int):
        if ParkingLot._instance is not None:
            raise Exception("Use get_instance() to get ParkingLot instance")
        self.name = name
        self.floors = [Floor(i+1) for i in range(floors_count)]
        self.active_tickets = {}
        self.pricing_strategy = DefaultPricingStrategy()
        self.ticket_counter = 0

    @classmethod
    def get_instance(cls, name: str = None, floors_count: int = 0):
        with cls._lock:
            if cls._instance is None:
                if name is None or floors_count <= 0:
                    raise Exception("ParkingLot not initialized. Provide name and floors_count.")
                cls._instance = cls(name, floors_count)
            return cls._instance

    def add_parking_spot(self, floor_number: int, spot_type: str, spot_id: str):
        if floor_number < 1 or floor_number > len(self.floors):
            raise ValueError("Invalid floor number")
        spot = ParkingSpotFactory.create_parking_spot(spot_type, spot_id)
        self.floors[floor_number - 1].add_spot(spot)

    def park_vehicle(self, vehicle: Vehicle) -> ParkingTicket:
        for floor in self.floors:
            spot = floor.find_available_spot(vehicle)
            if spot:
                parked = spot.park(vehicle)
                if parked:
                    self.ticket_counter += 1
                    ticket_id = f"T{self.ticket_counter:05d}"
                    ticket = ParkingTicket(ticket_id, datetime.now(), spot, vehicle)
                    self.active_tickets[ticket_id] = ticket
                    print(f"Vehicle {vehicle.license_plate} parked at {spot.spot_id} on floor {floor.floor_number}")
                    print(f"Ticket issued: {ticket_id}, Entry Time: {ticket.entry_time}")
                    return ticket
        
        print("Parking Lot Full or No suitable spot available")
        return None

    def exit_vehicle(self, ticket_id: str) -> float:
        ticket = self.active_tickets.get(ticket_id)
        if not ticket:
            raise ValueError("Invalid ticket ID")
        if ticket.exit_time is not None:
            raise Exception("Vehicle already exited")

        exit_time = datetime.now()
        price = self.pricing_strategy.calculate_price(ticket)
        ticket.close_ticket(exit_time, price)
        ticket.spot.leave()
        del self.active_tickets[ticket_id]

        print(f"Vehicle {ticket.vehicle.license_plate} exited from spot {ticket.spot.spot_id}")
        print(f"Total price: ${price:.2f} for duration {(ticket.exit_time - ticket.entry_time)}")
        return price

    def get_available_spots_count(self):
        count = 0
        for floor in self.floors:
            count += sum(spot.is_free() for spot in floor.spots)
        return count

if __name__ == "__main__":
    
    parking_lot = ParkingLot.get_instance("Downtown Parking", 2)
    
    parking_lot.add_parking_spot(1, "compact", "1C1")
    parking_lot.add_parking_spot(1, "large", "1L1")
    parking_lot.add_parking_spot(1, "handicapped", "1H1")

    parking_lot.add_parking_spot(2, "compact", "2C1")
    parking_lot.add_parking_spot(2, "large", "2L1")

    car = VehicleFactory.create_vehicle("car", "ABC123")
    bike = VehicleFactory.create_vehicle("bike", "BIKE001")
    truck = VehicleFactory.create_vehicle("truck", "TRUCKX")

    ticket1 = parking_lot.park_vehicle(car)
    ticket2 = parking_lot.park_vehicle(bike)
    ticket3 = parking_lot.park_vehicle(truck)

    import time
    time.sleep(2)

    if ticket1:
        price1 = parking_lot.exit_vehicle(ticket1.ticket_id)
    if ticket2:
        price2 = parking_lot.exit_vehicle(ticket2.ticket_id)
    if ticket3:
        price3 = parking_lot.exit_vehicle(ticket3.ticket_id)
