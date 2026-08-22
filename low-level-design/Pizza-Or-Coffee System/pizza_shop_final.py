from abc import ABC, abstractmethod
from enum import Enum
import uuid


# =========================
# Enums
# =========================

class OrderStatus(Enum):
    CREATED = "Created"
    PAID = "Paid"
    PREPARING = "Preparing"
    READY = "Ready"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class PizzaType(Enum):
    MARGHERITA = "Margherita"


class ToppingType(Enum):
    CHEESE = "Cheese"
    PEPPERS = "Peppers"
    OLIVE = "Olive"


# =========================
# Toppings
# =========================

class Topping(ABC):
    def __init__(self, price):
        self._price = price

    @property
    def price(self):
        return self._price


class Cheese(Topping):
    def __init__(self):
        super().__init__(5)


class Peppers(Topping):
    def __init__(self):
        super().__init__(25)


class Olive(Topping):
    def __init__(self):
        super().__init__(15)


# =========================
# Pizza
# =========================

class Pizza(ABC):
    def __init__(self, name, base_price):
        self.name = name
        self.base_price = base_price
        self.toppings = []

    def add_topping(self, topping: Topping):
        self.toppings.append(topping)

    def calculate_price(self):
        topping_price = sum(
            topping.price
            for topping in self.toppings
        )

        return self.base_price + topping_price


class Margherita(Pizza):
    def __init__(self):
        super().__init__(
            name=PizzaType.MARGHERITA.value,
            base_price=100
        )


# =========================
# Factory
# =========================

class PizzaFactory:
    @staticmethod
    def create_pizza(
        pizza_type: PizzaType
    ) -> Pizza:

        if pizza_type == PizzaType.MARGHERITA:
            return Margherita()

        raise ValueError(
            f"Unsupported pizza type: {pizza_type}"
        )


# =========================
# Payment Strategy
# =========================

class PaymentStrategy(ABC):

    @abstractmethod
    def pay(self, amount) -> bool:
        pass


class CreditCardPayment(PaymentStrategy):

    def pay(self, amount):
        print(
            f"Paid ${amount} using Credit Card."
        )
        return True


class CashPayment(PaymentStrategy):

    def pay(self, amount):
        print(
            f"Paid ${amount} using Cash."
        )
        return True


# =========================
# Promotion Strategy
# =========================

class PromotionStrategy(ABC):

    @abstractmethod
    def apply(self, amount):
        pass


class NoPromotion(PromotionStrategy):

    def apply(self, amount):
        return amount


class FixedDiscount(PromotionStrategy):

    def __init__(self, discount):
        self.discount = discount

    def apply(self, amount):
        return max(
            0,
            amount - self.discount
        )


# =========================
# Observer
# =========================

class Observer(ABC):

    @abstractmethod
    def update(
        self,
        order_id,
        status
    ):
        pass


class CustomerNotifier(Observer):

    def update(
        self,
        order_id,
        status
    ):
        print(
            f"Order {order_id} "
            f"status changed to {status.value}."
        )


# =========================
# Order
# =========================

class Order:
    def __init__(
        self,
        payment_strategy: PaymentStrategy,
        promotion_strategy: PromotionStrategy = None
    ):
        self.order_id = str(uuid.uuid4())[:8]

        self.pizzas = []

        self.payment_strategy = payment_strategy

        self.promotion_strategy = (
            promotion_strategy
            or NoPromotion()
        )

        self.status = OrderStatus.CREATED

        self._observers = []

    def add_pizza(self, pizza: Pizza):
        if self.status != OrderStatus.CREATED:
            raise Exception(
                "Cannot modify order after payment."
            )

        self.pizzas.append(pizza)

    def add_observer(self, observer: Observer):
        self._observers.append(observer)

    def calculate_total(self):
        total = sum(
            pizza.calculate_price()
            for pizza in self.pizzas
        )

        return self.promotion_strategy.apply(
            total
        )

    def process_payment(self):
        if self.status != OrderStatus.CREATED:
            return False

        amount = self.calculate_total()

        if not self.payment_strategy.pay(amount):
            return False

        self._update_status(
            OrderStatus.PAID
        )

        return True

    def start_preparation(self):
        if self.status != OrderStatus.PAID:
            return False

        self._update_status(
            OrderStatus.PREPARING
        )

        return True

    def mark_ready(self):
        if self.status != OrderStatus.PREPARING:
            return False

        self._update_status(
            OrderStatus.READY
        )

        return True

    def complete(self):
        if self.status != OrderStatus.READY:
            return False

        self._update_status(
            OrderStatus.COMPLETED
        )

        return True

    def cancel(self):
        if self.status in (
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED
        ):
            return False

        self._update_status(
            OrderStatus.CANCELLED
        )

        return True

    def _update_status(
        self,
        status: OrderStatus
    ):
        self.status = status

        for observer in self._observers:
            observer.update(
                self.order_id,
                status
            )


# =========================
# Pizza Shop / Facade
# =========================

class PizzaShop:

    def create_order(
        self,
        payment_strategy,
        promotion_strategy=None
    ):
        return Order(
            payment_strategy,
            promotion_strategy
        )

    def create_pizza(
        self,
        pizza_type
    ):
        return PizzaFactory.create_pizza(
            pizza_type
        )


# =========================
# Example
# =========================

if __name__ == "__main__":

    pizza_shop = PizzaShop()

    pizza = pizza_shop.create_pizza(
        PizzaType.MARGHERITA
    )

    pizza.add_topping(
        Cheese()
    )

    pizza.add_topping(
        Olive()
    )

    order = pizza_shop.create_order(
        payment_strategy=CashPayment(),
        promotion_strategy=FixedDiscount(10)
    )

    order.add_observer(
        CustomerNotifier()
    )

    order.add_pizza(
        pizza
    )

    print(
        "Total:",
        order.calculate_total()
    )

    order.process_payment()

    order.start_preparation()

    order.mark_ready()

    order.complete()
