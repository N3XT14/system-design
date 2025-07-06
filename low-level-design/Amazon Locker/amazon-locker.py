import threading

class Package:
    _id_counter = 0
    _lock = threading.Lock()

    def __init__(self, recipient_name, package_id=None):
        with Package._lock:
            Package._id_counter += 1
            self.package_id = package_id or Package._id_counter
        self.recipient_name = recipient_name

    @classmethod
    def create_new_package(cls, recipient_name):
        return cls(recipient_name)

class Locker:
    def __init__(self, locker_id):
        self.locker_id = locker_id
        self.lock = threading.Lock()
        self.package = None  # Currently, only 1 package per locker

        # If you want multiple packages per locker, you can do:
        # self.packages = []

    def is_empty(self):
        return self.package is None

    def put_package(self, package):
        with self.lock:
            if self.package is not None:
                raise Exception("Locker is already occupied.")
            self.package = package
            print(f"Package {package.package_id} delivered to Locker {self.locker_id}")

    def retrieve_package(self, recipient_name):
        with self.lock:
            if self.package and self.package.recipient_name == recipient_name:
                package = self.package
                self.package = None
                print(f"Package {package.package_id} retrieved by {recipient_name}.")
                return package
            return None

class LockerSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, num_lockers=10):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(LockerSystem, cls).__new__(cls)
                # Initialize lockers
                cls._instance.lockers = [Locker(i) for i in range(1, num_lockers+1)]
                print(f"Created a new Locker System with {num_lockers} lockers.")
        return cls._instance

    def delivery_package(self, recipient_name):
        package = Package.create_new_package(recipient_name)
        for locker in self.lockers:
            with locker.lock:
                if locker.is_empty():
                    locker.put_package(package)
                    return package, locker.locker_id
        raise Exception("No available lockers to delivery package.")


    def retrieve_package(self, recipient_name):
        for locker in self.lockers:
            with locker.lock:
                if (locker.package 
                    and locker.package.recipient_name == recipient_name):
                    return locker.retrieve_package(recipient_name)
        print(f"Package for {recipient_name} not found.")
        return None

def delivery_thread(system, recipient_name):
    try:
        package, locker_id = system.delivery_package(recipient_name)
        print(f"Thread delivering {package.package_id} to locker {locker_id}.")
    except Exception as e:
        print(f"Thread delivery failed for {recipient_name}: {str(e)}")

def retrieval_thread(system, recipient_name):
    package = system.retrieve_package(recipient_name)
    if package:
        print(f"Thread retrieved package {package.package_id}.")
    else:
        print(f"Thread found no package for {recipient_name}.")

if __name__ == "__main__":
    # Acquire a singleton instance
    locker_system = LockerSystem(num_lockers=5)

    # Simulating delivery from multiple threads
    delivery_thread(locker_system, "Alice")
    delivery_thread(locker_system, "Bob")
    delivery_thread(locker_system, "Charlie")

    # Simulating retrieval
    retrieval_thread(locker_system, "Alice")
    retrieval_thread(locker_system, "Charlie")
    retrieval_thread(locker_system, "David")  # not present
