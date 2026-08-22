from abc import ABC, abstractmethod
from threading import Lock
from enum import Enum
import uuid


# =========================
# Enums
# =========================

class NotificationType(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"


# =========================
# User
# =========================

class User:
    def __init__(self, name, email, phone=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.phone = phone


# =========================
# Product
# =========================

class Product:
    def __init__(self, name, price):
        self.id = str(uuid.uuid4())
        self.name = name
        self.price = price

    def update_price(self, new_price):
        self.price = new_price


# =========================
# Notification Strategy
# =========================

class NotificationService(ABC):

    @abstractmethod
    def notify(
        self,
        user: User,
        product: Product,
        price: float
    ):
        pass


class EmailNotificationService(NotificationService):

    def notify(self, user, product, price):
        print(
            f"Email sent to {user.email}: "
            f"{product.name} is now ${price}"
        )


class SMSNotificationService(NotificationService):

    def notify(self, user, product, price):
        print(
            f"SMS sent to {user.phone}: "
            f"{product.name} is now ${price}"
        )


# =========================
# Price Alert
# =========================

class PriceAlert:
    def __init__(
        self,
        user: User,
        product: Product,
        target_price: float,
        notification_service: NotificationService
    ):
        self.id = str(uuid.uuid4())

        self.user = user
        self.product = product
        self.target_price = target_price

        self.notification_service = (
            notification_service
        )

        self.active = True

    def should_notify(self):
        return (
            self.active
            and self.product.price
            <= self.target_price
        )

    def notify(self):
        self.notification_service.notify(
            self.user,
            self.product,
            self.product.price
        )

        # One-time alert.
        self.active = False


# =========================
# Price Alert Service
# =========================

class PriceAlertService:
    def __init__(self):
        # product_id -> list of alerts
        self.alerts = {}

        self._lock = Lock()

    def subscribe(
        self,
        user: User,
        product: Product,
        target_price: float,
        notification_service: NotificationService
    ) -> PriceAlert:

        alert = PriceAlert(
            user=user,
            product=product,
            target_price=target_price,
            notification_service=notification_service
        )

        with self._lock:
            self.alerts.setdefault(
                product.id,
                []
            ).append(alert)

        return alert

    def on_price_changed(
        self,
        product: Product,
        new_price: float
    ):

        product.update_price(new_price)

        # Take snapshot so we don't hold the
        # service lock while notifying users.
        with self._lock:
            product_alerts = list(
                self.alerts.get(
                    product.id,
                    []
                )
            )

        for alert in product_alerts:

            if alert.should_notify():
                alert.notify()


# =========================
# Product Catalog
# =========================

class ProductCatalog:
    def __init__(self):
        self.products = {}

    def add_product(self, product):
        self.products[product.id] = product

    def get_product(self, product_id):
        return self.products.get(product_id)


# =========================
# Example
# =========================

if __name__ == "__main__":

    catalog = ProductCatalog()
    alert_service = PriceAlertService()

    user1 = User(
        "Alice",
        "alice@example.com"
    )

    user2 = User(
        "Bob",
        "bob@example.com",
        phone="1234567890"
    )

    laptop = Product(
        "Laptop",
        100
    )

    headphones = Product(
        "Headphones",
        90
    )

    catalog.add_product(laptop)
    catalog.add_product(headphones)

    alert_service.subscribe(
        user=user1,
        product=laptop,
        target_price=50,
        notification_service=EmailNotificationService()
    )

    alert_service.subscribe(
        user=user2,
        product=headphones,
        target_price=70,
        notification_service=SMSNotificationService()
    )

    # No notification.
    alert_service.on_price_changed(
        laptop,
        80
    )

    # Alice gets notified.
    alert_service.on_price_changed(
        laptop,
        40
    )

    # Bob gets notified.
    alert_service.on_price_changed(
        headphones,
        60
    )
