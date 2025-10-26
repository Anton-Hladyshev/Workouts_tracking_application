from abc import ABC, abstractmethod


class BaseRepository(ABC):
    '''Abstract base class for a repository pattern
    Defines the interface for data access operations.
    '''
    
    @abstractmethod
    def add(self, item):
        """Add an item to the repository"""
        pass

    @abstractmethod
    def get(self, item_id: int):
        """Retrieve an item by its ID from the repository"""
        pass

    @abstractmethod
    def remove(self, item_id: int):
        """Remove an item by its ID from the repository"""
        pass

    @abstractmethod
    def update(self, item_id: int, **kwargs):
        """Update an item by its ID in the repository"""
        pass

    @abstractmethod
    def list_all(self):
        """List all items in the repository"""
        pass