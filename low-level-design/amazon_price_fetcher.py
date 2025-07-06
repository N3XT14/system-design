from abc import ABC, abstractmethod
from typing import List, Dict
import uuid

class Observer(ABC):
    
    @abstractmethod
    def update(self, product_id: str, new_price: float) -> None:
        pass
    
    
class User(Observer):
    
    def __init__(self, name, email):
        self._name = name
        self._email = email
        self._user_id = self._get_user_id()
        self._wishlist = {}
        self._notification_service = EmailNotification()
        
        
    @property
    def user_id(self) -> str:
        return self._user_id
    
    @property
    def email(self) -> str:
        return self.email
    
    def add_to_wishlist(self, product_id: str, drop_price: int) -> None:
        self._add_to_wishlist(product_id, drop_price)
        
    def _add_to_wishlist(self, product_id: str, drop_price: int) -> None:
        self._wishlist[product_id] = drop_price
    
    def get_wishlist(self) -> Dict[str, float]:
        self._wishlist.copy()
    
    def set_notification_service(self, service) -> None:
        self._notification_service = service
        
    def update(self, product_id, new_price):
        drop_price = self._wishlist.get(product_id)
        
        if drop_price is not None and new_price <= drop_price:
            self._notification_service.notify(self, product_id, new_price)
            
class Product():
    
    def __init__(self, product_id, price):
        self._product_id = product_id
        self._price = price
        self._observers: List[Observer] = []
        
    @property
    def product_id(self):
        return self._product_id
    
    @property
    def price(self):
        return self.price
    
    def set_price(self, new_price):
        self._price = new_price
        self.notify_observers()
        
    def add_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)
            
    def remove_observer(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)
        
    def notify_observers(self):
        for observer in self._observers:
            observer.update(self._product_id, self._price)
            
class NotificationService(ABC):
    @abstractmethod
    def notify(self, user, product_id, price):
        pass
    
class EmailNotification(NotificationService):
    
    def notify(self, user, product_id, price):
        print("Emailed")
        
class SMSNotification(NotificationService):
    
    def notify(self, user, product_id, price):
        print("SMS")
        
    
class ProductFetcher:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProductFetcher, cls).__new__(cls)
            cls._instance._products = {}
            cls._instance._users = {}
        return cls._instance
    
    @property
    def get_product(self, product_id):
        return self._products[product_id]
    
    def add_product(self, product):
        self._products[product.product_id] = product
        
    def add_user(self, user):
        self._users[user.user_id] = user
        
    def add_to_fetcher(self, user_id, product_id, price):
        user = self._users[user_id]
        product = self._products[product_id]
        user.add_to_wishlist(product_id, price)
        product.add_observer(user)
        
        
if __name__ == '__main__':
    fetcher = ProductFetcher()
    
    user1 = User('u1', 'u1@xyz.com')
    user2 = User('u2', 'u2@xyz.com')
    
    fetcher.add_user(user1)
    fetcher.add_user(user2)
    
    product1 = Product('p1', 100)
    product2 = Product('p2', 90)
    
    fetcher.add_product(product1)
    fetcher.add_product(product2)
    
    fetcher.add_to_fetcher("u1", "p1", 50)
    fetcher.add_to_fetcher("u2", "p2", 70)
    
    product1.set_price(40)
    product2.set_price(40)