import threading
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from uuid import uuid4


class BookingStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class SeatStatus(Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"


class User:
    def __init__(self, user_id, name, email):
        self.user_id = user_id
        self.name = name
        self.email = email


class Movie:
    def __init__(self, movie_id, title, duration):
        self.movie_id = movie_id
        self.title = title
        self.duration = duration


class Seat:
    def __init__(self, seat_id, seat_type="standard"):
        self.seat_id = seat_id
        self.seat_type = seat_type
        self.status = SeatStatus.AVAILABLE

    @property
    def is_available(self):
        return self.status == SeatStatus.AVAILABLE

    def mark_booked(self):
        self.status = SeatStatus.BOOKED

    def mark_available(self):
        self.status = SeatStatus.AVAILABLE


class CinemaScreen:
    def __init__(self, screen_id, seat_count=100):
        self.screen_id = screen_id
        self.seats = {
            seat_id: Seat(seat_id)
            for seat_id in range(1, seat_count + 1)
        }


class Showtime:
    def __init__(
        self,
        showtime_id,
        movie,
        cinema_screen,
        showtime_dt
    ):
        self.showtime_id = showtime_id
        self.movie = movie
        self.cinema_screen = cinema_screen
        self.showtime_dt = showtime_dt

        # Lock belongs to THIS showtime only.
        self._lock = threading.Lock()

    def reserve_seats(self, seat_numbers):
        """
        Atomically reserve all requested seats.

        Either:
        - all requested seats are reserved
        - none are reserved
        """

        with self._lock:

            seats_to_book = []

            # Step 1: validate all seats
            for seat_number in seat_numbers:
                seat = self.cinema_screen.seats.get(seat_number)

                if seat is None:
                    print(f"Seat {seat_number} does not exist.")
                    return None

                if not seat.is_available:
                    print(f"Seat {seat_number} is already booked.")
                    return None

                seats_to_book.append(seat)

            # Step 2: only after ALL seats pass validation,
            # modify them.
            for seat in seats_to_book:
                seat.mark_booked()

            return seats_to_book

    def release_seats(self, seats):
        """
        Cancellation must use the same synchronization
        strategy as booking.
        """

        with self._lock:
            for seat in seats:
                seat.mark_available()


class Payment(ABC):

    @abstractmethod
    def pay(self, amount):
        pass


class CreditCardPayment(Payment):

    def pay(self, amount):
        print(f"Processing credit card payment: ${amount}")
        return True


class Booking:
    def __init__(
        self,
        user,
        showtime,
        seats,
        amount
    ):
        # Avoid shared mutable booking counter.
        self.booking_id = str(uuid4())

        self.user = user
        self.showtime = showtime
        self.seats = seats
        self.amount = amount
        self.timestamp = datetime.now()

        self.status = BookingStatus.PENDING

    def confirm(self):
        if self.status != BookingStatus.PENDING:
            return False

        self.status = BookingStatus.CONFIRMED
        return True

    def cancel(self):
        if self.status == BookingStatus.CANCELLED:
            return False

        self.showtime.release_seats(self.seats)
        self.status = BookingStatus.CANCELLED

        return True


class BookingSystem:

    def __init__(self):
        self.users = {}
        self.movies = {}
        self.screens = {}
        self.showtimes = {}
        self.bookings = {}

    def add_user(self, user):
        self.users[user.user_id] = user

    def add_movie(self, movie):
        self.movies[movie.movie_id] = movie

    def add_screen(self, screen):
        self.screens[screen.screen_id] = screen

    def add_showtime(self, showtime):
        self.showtimes[showtime.showtime_id] = showtime

    def book(
        self,
        user_id,
        showtime_id,
        seat_numbers,
        payment,
        amount
    ):
        user = self.users.get(user_id)
        showtime = self.showtimes.get(showtime_id)

        if user is None:
            print("Invalid user.")
            return None

        if showtime is None:
            print("Invalid showtime.")
            return None

        # Atomically reserve ALL seats.
        seats = showtime.reserve_seats(seat_numbers)

        if seats is None:
            print("Booking failed.")
            return None

        booking = Booking(
            user=user,
            showtime=showtime,
            seats=seats,
            amount=amount
        )

        # In a real system payment is more complicated.
        # For interview LLD this keeps it simple.
        payment_successful = payment.pay(amount)

        if not payment_successful:
            showtime.release_seats(seats)
            return None

        booking.confirm()

        self.bookings[booking.booking_id] = booking

        print(
            f"Booking {booking.booking_id} confirmed "
            f"for seats {[seat.seat_id for seat in seats]}"
        )

        return booking

    def cancel_booking(self, booking_id):
        booking = self.bookings.get(booking_id)

        if booking is None:
            return False

        return booking.cancel()


if __name__ == "__main__":

    booking_system = BookingSystem()

    # User
    user = User(
        user_id=1,
        name="Alice",
        email="alice@example.com"
    )
    booking_system.add_user(user)

    # Movie
    movie = Movie(
        movie_id=1,
        title="Avengers Endgame",
        duration=180
    )
    booking_system.add_movie(movie)

    # Screen
    screen = CinemaScreen(
        screen_id=1,
        seat_count=100
    )
    booking_system.add_screen(screen)

    # Showtime
    showtime = Showtime(
        showtime_id=1,
        movie=movie,
        cinema_screen=screen,
        showtime_dt=datetime(2026, 8, 22, 18, 0)
    )
    booking_system.add_showtime(showtime)

    payment = CreditCardPayment()

    booking = booking_system.book(
        user_id=1,
        showtime_id=1,
        seat_numbers=[1, 2, 3],
        payment=payment,
        amount=30
    )

    # Another user/thread attempting seat 2
    # will fail because the complete first operation
    # already reserved [1, 2, 3].
