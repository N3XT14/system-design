import threading
from abc import ABC, abstractmethod
from enum import Enum
from uuid import uuid4


class BookingStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"


class RoomStatus(Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"


class Customer:
    def __init__(self, customer_id, name):
        self.customer_id = customer_id
        self.name = name


class Room(ABC):
    def __init__(self, room_number):
        self.room_number = room_number
        self.status = RoomStatus.AVAILABLE

    @property
    @abstractmethod
    def room_type(self):
        pass

    @property
    @abstractmethod
    def price(self):
        pass


class StandardRoom(Room):
    @property
    def room_type(self):
        return "Standard"

    @property
    def price(self):
        return 100


class DeluxeRoom(Room):
    @property
    def room_type(self):
        return "Deluxe"

    @property
    def price(self):
        return 180


class SuiteRoom(Room):
    @property
    def room_type(self):
        return "Suite"

    @property
    def price(self):
        return 300


class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass


class CashPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"Cash payment of ${amount}")
        return True


class CreditCardPayment(PaymentStrategy):
    def __init__(self, card_number):
        self.card_number = card_number

    def pay(self, amount):
        print(f"Credit card payment of ${amount}")
        return True


class PayPalPayment(PaymentStrategy):
    def __init__(self, email):
        self.email = email

    def pay(self, amount):
        print(f"PayPal payment of ${amount}")
        return True


class Booking:
    def __init__(self, customer, rooms):
        self.booking_id = str(uuid4())
        self.customer = customer
        self.rooms = rooms
        self.status = BookingStatus.PENDING

    def confirm(self):
        if self.status != BookingStatus.PENDING:
            return False

        self.status = BookingStatus.CONFIRMED
        return True

    def cancel(self):
        if self.status == BookingStatus.CANCELED:
            return False

        self.status = BookingStatus.CANCELED
        return True


class BookingService:
    def __init__(self, rooms):
        self.rooms = {
            room.room_number: room
            for room in rooms
        }

        self.bookings = {}

        # Protects atomic check + hold for room booking.
        self._lock = threading.Lock()

    def get_available_rooms(self):
        return [
            room
            for room in self.rooms.values()
            if room.status == RoomStatus.AVAILABLE
        ]

    def book_rooms(
        self,
        customer,
        room_numbers,
        payment_strategy
    ):
        """
        Either all requested rooms are booked,
        or none of them are.
        """

        # -------------------------
        # 1. Validate + hold rooms
        # -------------------------
        with self._lock:

            rooms_to_book = []

            for room_number in room_numbers:
                room = self.rooms.get(room_number)

                if room is None:
                    print(f"Room {room_number} does not exist.")
                    return None

                if room.status != RoomStatus.AVAILABLE:
                    print(
                        f"Room {room_number} "
                        f"is not available."
                    )
                    return None

                rooms_to_book.append(room)

            # Only change state after ALL rooms
            # have passed validation.
            for room in rooms_to_book:
                room.status = RoomStatus.HELD

            booking = Booking(
                customer=customer,
                rooms=rooms_to_book
            )

            self.bookings[booking.booking_id] = booking

        # ------------------------------------
        # 2. Payment outside critical section
        # ------------------------------------

        amount = sum(
            room.price
            for room in rooms_to_book
        )

        payment_successful = payment_strategy.pay(amount)

        # -------------------------
        # 3. Finalize booking
        # -------------------------
        with self._lock:

            if not payment_successful:

                for room in rooms_to_book:
                    room.status = RoomStatus.AVAILABLE

                booking.cancel()

                print("Payment failed.")
                return None

            for room in rooms_to_book:
                room.status = RoomStatus.BOOKED

            booking.confirm()

        print(
            f"Booking {booking.booking_id} confirmed "
            f"for rooms "
            f"{[room.room_number for room in rooms_to_book]}"
        )

        return booking

    def cancel_booking(self, booking_id):

        with self._lock:

            booking = self.bookings.get(booking_id)

            if booking is None:
                print("Booking not found.")
                return False

            if booking.status == BookingStatus.CANCELED:
                return False

            for room in booking.rooms:
                room.status = RoomStatus.AVAILABLE

            booking.cancel()

            print(
                f"Booking {booking_id} canceled."
            )

            return True

    def get_booking(self, booking_id):
        return self.bookings.get(booking_id)


class HotelManagementSystem:
    """
    Facade exposed to clients.
    Business logic stays in BookingService.
    """

    def __init__(self, rooms):
        self.booking_service = BookingService(rooms)

    def book(
        self,
        customer,
        room_numbers,
        payment_strategy
    ):
        return self.booking_service.book_rooms(
            customer,
            room_numbers,
            payment_strategy
        )

    def cancel(self, booking_id):
        return self.booking_service.cancel_booking(
            booking_id
        )

    def view_available_rooms(self):
        return self.booking_service.get_available_rooms()

    def get_booking(self, booking_id):
        return self.booking_service.get_booking(
            booking_id
        )


if __name__ == "__main__":

    rooms = [
        StandardRoom(101),
        StandardRoom(102),
        DeluxeRoom(201),
        DeluxeRoom(202),
        SuiteRoom(301)
    ]

    hotel = HotelManagementSystem(rooms)

    customer = Customer(
        customer_id=1,
        name="Alice"
    )

    payment = CreditCardPayment(
        "1234-5678-9876-5432"
    )

    # Single room also works:
    #
    # hotel.book(customer, [101], payment)

    # Multiple-room booking
    booking = hotel.book(
        customer=customer,
        room_numbers=[101, 102],
        payment_strategy=payment
    )

    if booking:
        print(
            "Booking status:",
            booking.status.value
        )

    print("\nAvailable rooms:")

    for room in hotel.view_available_rooms():
        print(
            room.room_number,
            room.room_type
        )

    if booking:
        hotel.cancel(
            booking.booking_id
        )
