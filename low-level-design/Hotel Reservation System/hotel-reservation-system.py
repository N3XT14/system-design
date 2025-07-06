import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

class ReservationStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELED = "Canceled"


class Customer:
    def __init__(self, customer_id, name):
        self.customer_id = customer_id
        self.name = name
        
class Room(ABC):
    def __init__(self, room_number):
        self._room_number = room_number
        self._lock = threading.Lock()
        self._reservation = None

    @property
    def room_number(self):
        return self._room_number

    @property
    @abstractmethod
    def room_type(self):
        pass

    @property
    @abstractmethod
    def price(self):
        pass

    @property
    def is_booked(self):
        return self._is_booked

    def is_available(self):
        with self._lock:
            if self._reservation is None:
                return True
            
            if self._reservation.status in [ReservationStatus.CANCELED]:
                self._reservation = None
                return True
            if self._reservation.status == ReservationStatus.PENDING:
            
                if datetime.now() - self._reservation.created_at > timedelta(minutes=10):
                    print(f"Reservation {self._reservation.id} expired.")
                    self._reservation.status = ReservationStatus.CANCELED
                    self._reservation = None
                    return True
            return False

    def tentative_reserve(self, customer, start, end):
        with self._lock:
            if not self.is_available():
                return False
            reservation = Reservation(customer, start, end)
            self._reservation.status = ReservationStatus.PENDING
            self._reservation = reservation
            return True

    def confirm_reservation(self):
        with self._lock:
            if self._reservation is None:
                return False
            self._reservation.status = ReservationStatus.CONFIRMED
            return True

    def cancel_reservation(self):
        with self._lock:
            if self._reservation is None:
                return False
            self._reservation.status = ReservationStatus.CANCELED
            self._reservation = None
            return True
        
class StandardRoom(Room):
    @property
    def price(self):
        return 100
    
    @property
    def room_type(self):
        return 'Standard'
    
class DeluxeRoom(Room):
    @property
    def price(self):
        return 180  # Higher price

    @property
    def room_type(self):
        return 'Deluxe'

class SuiteRoom(Room):
    @property
    def price(self):
        return 300  # Premium price

    @property
    def room_type(self):
        return 'Suite'
    
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass
    
class CashPayment(PaymentStrategy):
    def pay(self, amount):
        print("Cash payment done for amount: ", amount)
        return True
        
class CreditCardPayment(PaymentStrategy):
    def __init__(self, card_number):
        self.card_number = card_number
        
    def pay(self, amount):
        print("Credit Card payment done for amount: ", amount)
        return True
        
class PayPalPayment(PaymentStrategy):
    def __init__(self, email):
        self.email = email

    def pay(self, amount):
        print(f"Processing PayPal payment of ${amount} for account {self.email}")
        return True
    
class Reservation:
    _counter = 0
    _lock = threading.Lock()

    def __init__(self, customer, room, start, end):
        with Reservation._lock:
            Reservation._counter += 1
            self.id = Reservation._counter

        self.customer = customer
        self.room = room
        self.start = start
        self.end = end


class HotelReservationSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, num_rooms=10):
        with cls._lock:
            if not cls._instance:
                instance = super(HotelReservationSystem, cls).__new__(cls)
                instance._rooms = [Room(i) for i in range(1, num_rooms+1)]
                instance._reservations = {}
                print(f"Created hotel with {num_rooms} rooms.")
                cls._instance = instance
        return cls._instance

    def book_room(self, customer, start, end, payment_strategy):
        for room in self._rooms:
            if not room.is_available():
                if not room.tentative_reserve(customer, start, end):
                    continue
                
                reservation = room._reservtion
                
                if not payment_strategy.pay(room.price):
                    print("Payment failed. Canceling tentative reservation.")
                    room.cancel_reservation()
                    return None
                
                room.confirm_reservation()
                self._reservations[reservation.id] = reservation
                print(f"Room {room.room_number} ({room.room_type}) booked for {customer.name} at ${room.price}. Reservation ID: {reservation.id}")
                return reservation

        print("No available room.")
        return None

    def cancel_reservation(self, reservation_id):
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            print(f"Reservation {reservation_id} not found.")
            return False

        room = reservation.room
        if room.cancel_reservation():
            print(f"Reservation {reservation_id} canceled.")
            del self._reservations[reservation_id]
            return True

        print(f"Failed to cancel reservation {reservation_id}.")
        return False

    def view_available_rooms(self):
        return [room for room in self._rooms if not room.is_booked]

    def get_reservation(self, reservation_id):
        return self._reservations.get(reservation_id)

if __name__ == "__main__":
    rooms = [StandardRoom(i) for i in range(1, 6)]
    hotel = HotelReservationSystem(rooms)

    customer = Customer(1, "Alice")
    start = datetime(2025, 6, 15)
    end = datetime(2025, 6, 20)

    payment = CreditCardPayment("1234-5678-9876-5432")

    reservation = hotel.book_room(customer, start, end, payment)
    if reservation:
        print(f"Booking successful! Status: {reservation.status.value}, ID: {reservation.id}")

    print("\nAvailable rooms after booking:")
    for room in hotel.view_available_rooms():
        print(f"- Room {room.room_number} ({room.room_type})")

    # Optionally, implement
    # hotel.clean_expired_reservations()

    if reservation:
        hotel.cancel_reservation(reservation.id)

    print("\nAvailable rooms after cancel:")
    for room in hotel.view_available_rooms():
        print(f"- Room {room.room_number} ({room.room_type})")