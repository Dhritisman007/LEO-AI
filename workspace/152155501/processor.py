from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Person:
    name: str
    age: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Person':
        """Creates a Person instance from a dictionary, validating fields."""
        if 'name' not in data or 'age' not in data:
            raise ValueError(f"Missing required keys in data: {data}")
        if not isinstance(data['age'], int):
            raise TypeError(f"Age must be an integer, got {type(data['age']).__name__}")
        return cls(name=str(data['name']), age=data['age'])

def parse_and_sort_people(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parses a list of dictionaries into Person objects and sorts by age descending.
    
    Args:
        data_list: List of dictionaries containing 'name' and 'age'.
        
    Returns:
        List of dictionaries sorted by age descending.
        
    Raises:
        ValueError: If data is invalid.
    """
    if not isinstance(data_list, list):
        raise TypeError("Input must be a list of dictionaries.")

    people = [Person.from_dict(item) for item in data_list]
    
    # Sort by age descending
    sorted_people = sorted(people, key=lambda p: p.age, reverse=True)
    
    return [{"name": p.name, "age": p.age} for p in sorted_people]
