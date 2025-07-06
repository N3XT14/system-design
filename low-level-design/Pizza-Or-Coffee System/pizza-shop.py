from abc import ABC, abstractmethod
import uuid

class Topping(ABC):
    def __init__(self, price):
        self._price = price
        
    @property
    def get_price(self):
        return self._price
    
class Cheese(Topping):
    def __init__(self):
        super().__init__(price=5)
    
class Peppers(Topping):
    def __init__(self):
        super().__init__(price=25)
    
class Olive(Topping):
    def __init__(self):
        super().__init__(price=15)
        
class Pizza(ABC):
    def __init__(self, name, price):
        self._name = name
        self._price = price
        self._toppings = []
        
    def add_topping(self, topping):
        self._toppings.append(topping)
    
    def calculate_price(self):
        return self._price + sum(t.get_price() for t in self._toppings)
    
class Margherita(Pizza):
    def __init__(self):
        super().__init__('Margherita', 100)
        
class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass

class CreditCard(PaymentStrategy):
    
    def pay(self, amount):
        print(f"Paid {amount} by Credit Card.")

class Cash(PaymentStrategy):
    
    def pay(self, amount):
        print(f"Paid {amount} by Cash.")
        
class PromotionStrategy(ABC):
    """Base promotion class."""
    @abstractmethod
    def apply(self, amount):
        pass

class FixedDiscount(PromotionStrategy):
    """Fixed discount promotion."""
    def __init__(self, discount):
        self._discount = discount

    def apply(self, amount):
        return max(0, amount - self._discount)
    
class Observer(ABC):
    
    @abstractmethod
    def update(self, order_id):
        pass
    
class CustomerNotifier(Observer):
    
    def update(self, order_id):
        print(f"Your Order with {order_id} is ready.")
        
class Order:
    def __init__(self, payments=None, promotions=None, observers=None):
        self.order_id = str(uuid.uuid4())[:8]
        self._pizzas = []
        self._payment = payments or CreditCard()
        self._promotion = promotions or FixedDiscount(0)
        self._observers = observers or []
        
    def add_pizza(self, pizza):
        self._pizzas.add(pizza)
        
    def calculate_total(self):
        total = sum(p.calculate_price() for p in self._pizzas)
        return self._promotion.apply(total)
    
    def process_payment(self):
        amount = self.calculate_total()
        self._payment.pay(amount)
        self.notify()
        
    def notify(self):
        for observer in self._observers:
            observer.update(self.order_id)
            
class PizzaShop:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_pizza(self, pizza_name):
        if pizza_name == 'Margherita':
            return Margherita()
        
if __name__ == "main":
    pizza_shop = PizzaShop()
    
    pizza = pizza_shop.create_pizza('Margherita')
    pizza.add_topping(Cheese())
    pizza.add_topping(Olive())
    
    order = Order(payments=Cash(), observers=CustomerNotifier())
    order.add_pizza(pizza)
    order.process_payment()
    