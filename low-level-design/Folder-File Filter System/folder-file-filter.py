from datetime import datetime
from typing import List
from abc import ABC, abstractmethod

class FileSystemEntry(ABC):
    def __init__(self, name: str, size: int, modified_at: datetime):
        self.name = name
        self.size = size
        self.modified_at = modified_at
        # or self.path
    
    @abstractmethod
    def is_file(self) -> bool:
        pass
    
    @abstractmethod
    def is_folder(self) -> bool:
        pass
    
    
class File(FileSystemEntry):
    def is_file(self) -> bool:
        return True # or use os.path.isfile(self.path)
    
    def is_folder(self) -> bool:
        return False


class Folder(FileSystemEntry):
    def __init__(self, name: str, size: int, modified_at: datetime, children=None):
        super().__init__(name, size, modified_at)
        self.children = children or []

    def is_file(self) -> bool:
        return False
    
    def is_folder(self) -> bool:
        return True
    
    def add(self, entry: FileSystemEntry):
        self.children.append(entry)
        
        
class Filter(ABC):
    @abstractmethod
    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        pass
    
class NameFilter(Filter):
    def __init__(self, pattern: str):
        self.pattern = pattern

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        import fnmatch
        return fnmatch.fnmatch(entry.name, self.pattern)


class SizeFilter(Filter):
    def __init__(self, min_size: int = 0, max_size: int = float('inf')):
        self.min_size = min_size
        self.max_size = max_size

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        return self.min_size <= entry.size <= self.max_size

class FileExtensionFilter(Filter):
    def __init__(self, extension: str):
        self.extension = extension.startswith('.') and self.extension or f'.{extension}'
        self.extension = self.extension.lower()

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        return entry.is_file() and entry.path.lower().endswith(self.extension)
    
class DateModifiedFilter(Filter):
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        return self.start <= entry.modified_at <= self.end


class AndFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        return all(f.is_satisfied(entry) for f in self.filters)


class OrFilter(Filter):
    def __init__(self, *filters: Filter):
        self.filters = filters

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        return any(f.is_satisfied(entry) for f in self.filters)
    
    
class FileFilterService:
    def filter(self, entries: List[FileSystemEntry], filter_condition: Filter, deep: bool = False) -> List[FileSystemEntry]:
        matching = []

        for entry in entries:
            if filter_condition.is_satisfied(entry):
                matching.append(entry)

            if deep and entry.is_folder():
                matching.extend(self.filter(entry.children, filter_condition, deep=True))

        return matching
    
        # If Deep Filter is allowed/interviewer asks then add condition where the entry is entry.isFolder() and then recursively call the filter function and extend the result.

class FileSearch:
    """Search files by filter with deep search into folders"""

    def search(self, entries: List[FileSystemEntry], filter_condition: Filter) -> List[FileSystemEntry]:
        """Search matching files with deep search into folders."""
        matching = []

        for entry in entries:
            if filter_condition.is_satisfied(entry):
                matching.append(entry)

            if entry.is_folder():
                matching.extend(self.search(entry.children, filter_condition))

        return matching


class FileReader:
    # Here we just return dummy content for simplicity
    # In a real-world scenario, you'd read from disk
    def read(self, file: File) -> str:
        if not file.is_file():
            raise ValueError("Can't read from a folder.")
        return f"Content of {file.name}"  # Mocked content

if __name__ == "main":
    file1 = File("report.txt", 500, datetime(2025, 6, 10))
    file2 = File("photo.png", 1500, datetime(2025, 6, 5))
    folder = Folder("backup", 0, datetime(2025, 6, 1), children=[file1, file2])

    entries = [file1, file2, folder]

    name_filter = NameFilter("*.txt")
    size_filter = SizeFilter(min_size=1000)
    date_filter = DateModifiedFilter(start=datetime(2025, 6, 1), end=datetime(2025, 6, 30))

    combined_filter = AndFilter(name_filter, size_filter)

    filter_service = FileFilterService()
    filtered = filter_service.filter(entries, combined_filter)

    print("Filtered files:")
    for entry in filtered:
        print(f"- {entry.name} (size: {entry.size})")

    or_filter = OrFilter(name_filter, size_filter)
    filtered_or = filter_service.filter(entries, or_filter)

    print("\nFiltered with OR:")
    for entry in filtered_or:
        print(f"- {entry.name} (size: {entry.size})")
