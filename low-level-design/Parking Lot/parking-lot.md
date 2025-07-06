Parking lot with different parking spot sizes (compact, large, handicapped).
    - Vehicle can park in appropriate spot.
    - Tickets are issued upon entry.
    - The ticket contains entry time, spot number, and vehicle details.
    - The vehicle exits, and we compute parking price based on duration and vehicle kind.
    - Support for multiple floors in the parking structure.
    - Handle full/available spot gracefully.

Design Patterns We Will Use:
    - Singleton — for ParkingLot (so there’s a single instance).
    - Factory Method — to create different parking spot/vehicle.
    - Strategy — for pricing algorithm (depending on vehicle or promotions).
    - Composite — if we want, for floors/rows/spots (each floor contains many spots).

