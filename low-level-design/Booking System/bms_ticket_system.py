import threading
from datetime import datetime

class User:
    """Represents a user of the booking system."""
    def __init__(self, user_id, name, email):
        self._user_id = user_id
        self._name = name
        self._email = email

    @property
    def user_id(self):
        return self._user_id

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

class Movie:
    """Represents a movie that is shown in a cinema."""
    def __init__(self, movie_id, title, duration):
        self._movie_id = movie_id
        self._title = title
        self._duration = duration

    @property
    def movie_id(self):
        return self._movie_id

    @property
    def title(self):
        return self._title

    @property
    def duration(self):
        return self._duration

class CinemaScreen:
    """Represents a cinema hall with seats."""
    def __init__(self, screen_id, seat_count=100):
        self._screen_id = screen_id
        self._seats = {i: Seat(i) for i in range(1, seat_count + 1)}

    @property
    def screen_id(self):
        return self._screen_id

    @property
    def seats(self):
        return self._seats

class Seat:
    """Represents a seat in a cinema hall."""
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

    @property
    def booked(self):
        return self._booked

    def book(self) -> bool:
        """Thread-safe seat booking."""
        with self._lock:
            if self._booked:
                return False
            self._booked = True
            return True

class Showtime:
    """Represents a showtime for a movie at a cinema."""
    _lock = threading.Lock()

    def __init__(self, showtime_id, movie, cinema_screen, showtime_dt):
        self._showtime_id = showtime_id
        self._movie = movie
        self._cinema_screen = cinema_screen
        self._showtime_dt = showtime_dt

    @property
    def showtime_id(self):
        return self._showtime_id

    @property
    def movie(self):
        return self._movie

    @property
    def cinema_screen(self):
        return self._cinema_screen

    @property
    def showtime_dt(self):
        return self._showtime_dt

    def book_seats(self, seat_numbers):
        seats_to_book = []

        with Showtime._lock:
            for seat_number in seat_numbers:
                seat = self._cinema_screen.seats.get(seat_number)
                if seat is None:
                    print(f"Seat {seat_number} not found.")
                    return None

                if seat.booked:
                    print(f"Seat {seat_number} is already booked.")
                    return None

                seats_to_book.append(seat)

            for seat in seats_to_book:
                seat.book()

        return seats_to_book

from abc import ABC, abstractmethod

class Payment(ABC):
    """Represents a payments strategy."""
    @abstractmethod
    def pay(self, amount):
        pass


class CreditCardPayment(Payment):
    """Concrete Credit Card Payment."""
    def pay(self, amount):
        print(f"Processing Credit Card Payment of {amount}")

class Booking:
    """Represents a booking made by a user for seats in a showtime."""
    booking_counter = 0

    def __init__(self, user, showtime, seats, payment=None, amount=0.0):
        Booking.booking_counter += 1
        self._booking_id = Booking.booking_counter
        self._user = user
        self._showtime = showtime
        self._seats = seats
        self._payment = payment
        self._amount = amount
        self._timestamp = datetime.now()
        self._status = "PENDING"

        if payment:
            payment.pay(amount)

    @property
    def booking_id(self):
        return self._booking_id

    @property
    def status(self):
        return self._status

    def confirm(self):
        """Confirm booking after payments or additional checks."""
        if self._status == "PENDING":
            self._status = "CONFIRMED"
            print(f"Booking {self._booking_id} is now CONFIRMED.")
        else:
            print(f"Booking {self._booking_id} cannot be CONFIRMED. Currently {self._status}")

    def cancel(self):
        """Release seats and cancel booking."""
        if self._status == "CANCELLED":
            print(f"Booking {self._booking_id} is already CANCELLED.")
            return

        if self._status == "CONFIRMED" or self._status == "PENDING":
            for seat in self._seats:
                seat._booked = False
            self._status = "CANCELLED"

            print(f"Booking {self._booking_id} is CANCELLED.")
        else:
            print(f"Booking {self._booking_id} cannot be CANCELLED in its current state.")

class BookingSystem:
    """Singleton Booking System."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with BookingSystem._lock:
            if BookingSystem._instance is None:
                BookingSystem._instance = super(BookingSystem, cls).__new__(cls)
                BookingSystem._instance.users = {}
                BookingSystem._instance.movies = {}
                BookingSystem._instance.cinema_screens = {}
                BookingSystem._instance.showtimes = {}
                BookingSystem._instance.bookings = {}
        return BookingSystem._instance

    def add_user(self, user):
        self.users[user.user_id] = user

    def add_movie(self, movie):
        self.movies[movie.movie_id] = movie

    def add_cinema_screen(self, cinema_screen):
        self.cinema_screens[cinema_screen.screen_id] = cinema_screen

    def add_showtime(self, showtime):
        self.showtimes[showtime.showtime_id] = showtime

    def book(self, user_id, showtime_id, seat_numbers, payment=None, amount=0.0):
        user = self.users[user_id]
        showtime = self.showtimes[showtime_id]

        seats = showtime.book_seats(seat_numbers)
        if seats is None:
            print("Booking failed.")
            return None

        booking = Booking(user, showtime, seats, payment, amount)
        self.bookings[booking.booking_id] = booking

        print(f"Booking {booking.booking_id} successful.")
        return booking

if __name__ == "__main__":
    booking_system = BookingSystem()

    user = User(1, "Alice", "alice@example.com")
    booking_system.add_user(user)

    movie = Movie(1, "Avengers Endgame", 180)
    booking_system.add_movie(movie)

    cinema = CinemaScreen(1)
    booking_system.add_cinema_screen(cinema)

    showtime = Showtime(1, movie, cinema, datetime(2025, 6, 11, 18, 0, 0))
    booking_system.add_showtime(showtime)

    booking = booking_system.book(1, 1, [1, 2, 3], CreditCardPayment(), amount=30)
    if booking:
        print(f"Booking {booking.booking_id} completed.")


# Additional change would be to use Enums