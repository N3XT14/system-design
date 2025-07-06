from datetime import datetime
from typing import List, Optional
from abc import ABC, abstractmethod
import fnmatch
import os

# --- File System Model --- 
class FileSystemEntry(ABC):
    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def is_file(self) -> bool:
        pass
    
    @abstractmethod
    def is_folder(self) -> bool:
        pass


class File(FileSystemEntry):
    def is_file(self) -> bool:
        return os.path.isfile(self.path)
    
    def is_folder(self) -> bool:
        return os.path.isdir(self.path)


# --- Filter Interface --- 
class Filter(ABC):
    @abstractmethod
    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        pass


class NameFilter(Filter):
    def __init__(self, pattern: str):
        self.pattern = pattern

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        return fnmatch.fnmatch(os.path.basename(entry.path), self.pattern)


class SizeFilter(Filter):
    def __init__(self, min_size: int = 0, max_size: int = float('inf')):
        self.min_size = min_size
        self.max_size = max_size

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        if entry.is_file():
            size = os.path.getsize(entry.path)
            return self.min_size <= size <= self.max_size
        return False


class DateModifiedFilter(Filter):
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    def is_satisfied(self, entry: FileSystemEntry) -> bool:
        timestamp = datetime.fromtimestamp(os.path.getmtime(entry.path))
        return self.start <= timestamp <= self.end


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


# --- File Search --- 
class FileSearch:
    """Traverse directory and collect files or folders matching criteria."""
    def __init__(self, directory: str, recursive: bool = True):
        self.directory = directory
        self.recursive = recursive

    def search(self) -> List[FileSystemEntry]:
        """Return all files and folders under directory."""
        results = []
        for root, subdirs, files in os.walk(self.directory):
            for fname in files:
                results.append(File(os.path.join(root, fname)))
            for dname in subdirs:
                results.append(File(os.path.join(root, dname)))
            if not self.recursive:
                break
        return results


# --- File Reader --- 
class FileReader:
    """Read files' content safely."""
    def read(self, files: List[File]) -> List[str]:
        """Read the content of files into a list of strings."""
        contents = []
        for f in files:
            if f.is_file():
                with open(f.path, 'r') as infile:
                    contents.append(infile.readlines()) 
        return contents


# --- File Filter Service --- 
class FileFilterService:
    """Filters files or folders with specified filter conditions."""
    def filter(self, entries: List[FileSystemEntry], filter_condition: Filter) -> List[FileSystemEntry]:
        return [entry for entry in entries if filter_condition.is_satisfied(entry)]

# --- Example usage --- 
if __name__ == "__main__":
    directory = "/tmp/example"

    # Search files
    search = FileSearch(directory)
    all_entries = search.search()

    # Filter files by name
    filter_condition = NameFilter("*.txt")
    filter_service = FileFilterService()
    matching_entries = filter_service.filter(all_entries, filter_condition)

    # Filter files by size
    size_condition = SizeFilter(min_size=1000)
    matching_by_size = filter_service.filter(all_entries, size_condition)

    # Combine filters
    combined = AndFilter(filter_condition, size_condition)
    matching_combined = filter_service.filter(all_entries, combined)

    # Now read files
    files = [entry for entry in matching_combined if entry.is_file()]
    reader = FileReader()
    content = reader.read(files)

    print("Read files:")
    for fname, text in zip([f.path for f in files], content):
        print(f"- {fname}:\n{text}")

