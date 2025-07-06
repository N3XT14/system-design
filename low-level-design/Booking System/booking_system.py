import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

class User:
    def __init__(self, user_id, name):
        self._user_id = user_id
        self._name = name
        
class Seat(ABC):
    """Represents a seat in a cinema or event hall."""
    def __init__(self, seat_id, seat_type='standard'):
        self._seat_id = seat_id
        self._seat_type = seat_type
        self._booked = False
        self._lock = threading.Lock()

    @property
    def seat_id(self):
        return self._seat_id

    @property
    def seat_type(self):
        return self._seat_type

    def book(self) -> bool:
        """Thread-safe seat booking."""
        with self._lock:
            if self._booked:
                return False
            self._booked = True
            return True

    def is_booked(self) -> bool:
        return self._booked

class Booking:
    _booking_counter = 0
    
    def __init__(self, user, seats):
        Booking._booking_counter += 1
        self._booking_id = Booking._booking_counter
        self._user = user
        self._seats = seats
        self._timestamp = datetime.now()

    @property
    def booking_id(self):
        return self._booking_id
    
    @property
    def seats(self):
        return self._seats
        
class Payment(ABC):
    """Represents a payments strategy."""
    @abstractmethod
    def pay(self, amount):
        pass


class CreditCardPayment(Payment):
    """Concrete Credit Card Payment."""
    def pay(self, amount):
        print(f"Processing Credit Card Payment of {amount}")
        
class BookingSystem:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BookingSystem, cls).__new__(cls)
                cls._instance._seats = {i: Seat(i) for i in range(1, 101)}
                cls._instance._lock = threading.Lock()
                cls._instance._bookings = []
        return cls._instance

    def book_seats(self, user, seat_numbers, payment=None, amount=0.0):
        seats_to_book = []
        for seat_number in seat_numbers:
            seat = self._seats.get(seat_number)
            if seat is None:
                print(f"Seat {seat_number} not found.")
                return None

            if not seat.book():
                print(f"Seat {seat_number} is already booked.")
                return None

            seats_to_book.append(seat)

        booking = Booking(user, seats_to_book)
        self._bookings.append(booking)

        if payment:
            payment.pay(amount)
            print(f"Seats {[s.seat_id for s in seats_to_book]} successfully booked.")
        return booking


if __name__ == "__main__":
    booking_system = BookingSystem()
    user = User(1, "Alice")

    # Book seats 1, 2, and 3
    booking = booking_system.book_seats(user, [1, 2, 3], CreditCardPayment(), amount=100)
    if booking:
        print(f"Booking successful with Booking IDs: {booking.booking_id}")

    # Attempt booking seats 2, 3 (should fail due to already booking)
    booking = booking_system.book_seats(user, [2, 3], CreditCardPayment(), amount=100)
    if booking is None:
        print("Booking failed due to seats already booked.")