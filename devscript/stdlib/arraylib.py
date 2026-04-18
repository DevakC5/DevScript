import builtins
from typing import List, Union

class DevArray:
    def __init__(self, data: List[Union[int, float]]):
        self.data = data

    def __add__(self, other):
        if isinstance(other, DevArray):
            if len(self.data) != len(other.data):
                raise ValueError("Arrays must have the same length for addition")
            return DevArray([a + b for a, b in zip(self.data, other.data)])
        raise TypeError("Can only add DevArray to another DevArray")

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return DevArray([a * other for a in self.data])
        if isinstance(other, DevArray):
            if len(self.data) != len(other.data):
                raise ValueError("Arrays must have the same length for multiplication")
            return DevArray([a * b for a, b in zip(self.data, other.data)])
        raise TypeError("Can only multiply DevArray by a number or another DevArray")

    def __repr__(self):
        return f"array({self.data})"

    def __len__(self):
        return len(self.data)

def array(data_list: Union[List[Union[int, float]], 'DevArray']) -> DevArray:
    if isinstance(data_list, DevArray):
        return data_list
    return DevArray(data_list)

def sum(arr: DevArray) -> float:
    if not isinstance(arr, DevArray):
        raise TypeError("sum() expects a DevArray")
    return builtins.sum(arr.data)

def mean(arr: DevArray) -> float:
    if not isinstance(arr, DevArray):
        raise TypeError("mean() expects a DevArray")
    if len(arr) == 0:
        return 0.0
    return builtins.sum(arr.data) / len(arr)
