from dataclasses import dataclass


@dataclass
class Apartment:
    link: str
    title: str
    region: str
    address: str
    description: str
    pictures: list[str]
    date: str
    price: int
    room_amount: int
    square: int
