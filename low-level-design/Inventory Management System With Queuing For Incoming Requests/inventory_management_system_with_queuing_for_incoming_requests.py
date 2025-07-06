from threading import Lock, Thread
from queue import Queue
from abc import ABC, abstractmethod
import time

class Item:
    def __init__(self, item_id: str, name: str, quantity: int):
        self.item_id = item_id
        self.name = name
        self.quantity = quantity
        self.lock = Lock()

    def add_stock(self, qty: int):
        with self.lock:
            self.quantity += qty
            print(f"[{self.name}] Stock increased by {qty}. New qty: {self.quantity}")

    def remove_stock(self, qty: int) -> bool:
        with self.lock:
            if self.quantity >= qty:
                self.quantity -= qty
                print(f"[{self.name}] Stock decreased by {qty}. Remaining qty: {self.quantity}")
                return True
            return False

class Request(ABC):
    @abstractmethod
    def process(self, inventory: 'Inventory'):
        pass

class PurchaseRequest(Request):
    def __init__(self, item_id: str, qty: int):
        self.item_id = item_id
        self.qty = qty

    def process(self, inventory):
        item = inventory.get_item(self.item_id)
        if item and item.remove_stock(self.qty):
            print(f"Purchase fulfilled for {item.name}")
        else:
            print(f"Not enough stock for {item.name}, queued")
            inventory.queue_request(self)


class RestockRequest(Request):
    def __init__(self, item_id: str, qty: int):
        self.item_id = item_id
        self.qty = qty

    def process(self, inventory):
        item = inventory.get_item(self.item_id)
        if item:
            item.add_stock(self.qty)
            inventory.process_queued_requests(item)

class Inventory:
    def __init__(self):
        self.items = {}
        self.request_queue = {}
        self.lock = Lock()

    def add_item(self, item: Item):
        with self.lock:
            self.items[item.item_id] = item
            item.add_stock(item.quantity)
            self.request_queue[item.item_id] = Queue()
            print(f"Item added: {item.name}")

    def get_item(self, item_id):
        return self.items.get(item_id)

    def queue_request(self, request: PurchaseRequest):
        self.request_queue[request.item_id].put(request)

    def process_queued_requests(self, item: Item):
        queue = self.request_queue[item.item_id]
        while not queue.empty():
            req = queue.get()
            if item.remove_stock(req.qty):
                print(f"Queued purchase for {item.name} fulfilled")
            else:
                # Still not enough, requeue and break
                self.queue_request(req)
                break

class InventoryManager:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory

    def handle_request(self, request: Request):
        Thread(target=request.process, args=(self.inventory,)).start()

if __name__ == "__main__":
    inventory = Inventory()

    item = Item("1", "Laptop", 1)
    inventory.add_item(item)

    manager = InventoryManager(inventory)

    # Simulate multiple requests
    manager.handle_request(PurchaseRequest("1", 1))
    manager.handle_request(PurchaseRequest("1", 1))  # This will be queued
    time.sleep(1)

    manager.handle_request(RestockRequest("1", 1))  # This should fulfill the queued request
    time.sleep(1)
