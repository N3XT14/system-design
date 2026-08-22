from threading import Lock, Thread
from collections import deque
from abc import ABC, abstractmethod


class PurchaseRequest:
    def __init__(self, item_id: str, qty: int):
        self.item_id = item_id
        self.qty = qty


class Item:
    def __init__(self, item_id: str, name: str, quantity: int):
        self.item_id = item_id
        self.name = name
        self.quantity = quantity

        self._pending_requests = deque()
        self._lock = Lock()

    def purchase(self, request: PurchaseRequest) -> bool:
        """
        Atomically:
        - fulfill request if stock exists
        - otherwise queue it
        """
        with self._lock:
            if self.quantity >= request.qty:
                self.quantity -= request.qty

                print(
                    f"Purchase fulfilled: {request.qty} "
                    f"{self.name}. Remaining: {self.quantity}"
                )
                return True

            self._pending_requests.append(request)

            print(
                f"Insufficient stock for {self.name}. "
                f"Request queued."
            )
            return False

    def restock(self, qty: int):
        """
        Atomically:
        - add stock
        - fulfill queued requests in FIFO order
        """
        with self._lock:
            self.quantity += qty

            print(
                f"{self.name} restocked by {qty}. "
                f"Current quantity: {self.quantity}"
            )

            self._process_pending_requests()

    def _process_pending_requests(self):
        """
        Called only while Item lock is already held.
        Do NOT acquire the same Lock again here.
        """

        while self._pending_requests:
            request = self._pending_requests[0]

            if self.quantity < request.qty:
                break

            self._pending_requests.popleft()
            self.quantity -= request.qty

            print(
                f"Queued purchase fulfilled: "
                f"{request.qty} {self.name}. "
                f"Remaining: {self.quantity}"
            )


class Inventory:
    def __init__(self):
        self._items = {}
        self._lock = Lock()

    def add_item(self, item: Item):
        # Inventory lock protects inventory structure only.
        with self._lock:
            if item.item_id in self._items:
                raise ValueError(
                    f"Item {item.item_id} already exists."
                )

            self._items[item.item_id] = item

    def get_item(self, item_id: str):
        with self._lock:
            return self._items.get(item_id)


class Request(ABC):
    @abstractmethod
    def process(self, inventory: Inventory):
        pass


class PurchaseInventoryRequest(Request):
    def __init__(self, item_id: str, qty: int):
        self.item_id = item_id
        self.qty = qty

    def process(self, inventory: Inventory):
        item = inventory.get_item(self.item_id)

        if item is None:
            print(f"Item {self.item_id} not found.")
            return

        request = PurchaseRequest(
            item_id=self.item_id,
            qty=self.qty
        )

        item.purchase(request)


class RestockRequest(Request):
    def __init__(self, item_id: str, qty: int):
        self.item_id = item_id
        self.qty = qty

    def process(self, inventory: Inventory):
        item = inventory.get_item(self.item_id)

        if item is None:
            print(f"Item {self.item_id} not found.")
            return

        item.restock(self.qty)


class InventoryManager:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory

    def handle_request(self, request: Request):
        # Only to demonstrate concurrent requests.
        thread = Thread(
            target=request.process,
            args=(self.inventory,)
        )
        thread.start()

        return thread


if __name__ == "__main__":

    inventory = Inventory()

    inventory.add_item(
        Item(
            item_id="1",
            name="Laptop",
            quantity=1
        )
    )

    manager = InventoryManager(inventory)

    threads = []

    # First request succeeds.
    threads.append(
        manager.handle_request(
            PurchaseInventoryRequest("1", 1)
        )
    )

    # No stock left, so this gets queued.
    threads.append(
        manager.handle_request(
            PurchaseInventoryRequest("1", 1)
        )
    )

    for thread in threads:
        thread.join()

    # Restock automatically processes pending request.
    thread = manager.handle_request(
        RestockRequest("1", 1)
    )

    thread.join()
