from asyncio import exceptions
from collections import Counter
from io import BytesIO
from itertools import chain, cycle
from math import ceil
from random import sample, randint, shuffle
from requests import get
from re import findall
from typing import Iterator, List, Union, Any, Optional

from PIL import Image, ImageDraw, ImageOps, JpegImagePlugin, PngImagePlugin
from disnake import (
    ButtonStyle,
    Color,
    Embed,
    Enum,
    File,
    Member,
    Message,
    MessageInteraction,
    SelectOption,
)
from disnake.errors import NotFound
from disnake.ui import Button, Select, View

from bot import OmniGames

NUM2EMOJI = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
}


class SpecialCardsType(Enum):
    CHANCE = 0
    COMMUNITY_CHEST = 1


class PublicServiceCompanyType(Enum):
    ELECTRICITY = 0
    WATER = 1


class SpecialCard:
    id: int
    description: str
    card_type: SpecialCardsType
    can_be_kept: bool

    def __init__(
        self,
        id: int,
        description: str,
        card_type: SpecialCardsType,
        can_be_kept: bool = False,
    ):
        self.id = id
        self.description = description
        self.card_type = card_type
        self.can_be_kept = can_be_kept

    def get_embed(self) -> Embed:
        return Embed(
            title="**"
            + (
                "Chance"
                if self.card_type == SpecialCardsType.CHANCE
                else "Community Chest"
            )
            + " Card**",
            description=self.description,
            color=Color.from_rgb(98, 42, 0)
            if self.card_type == SpecialCardsType.CHANCE
            else Color.from_rgb(0, 57, 88),
        )


class Case:
    name: str
    price: int
    location: int
    owner: int
    mortgaged: bool
    color: Color

    def get_embed(self) -> Embed:
        pass


class Station(Case):
    rent: int

    def __init__(
        self,
        name: str,
        location: int,
        price: int = 200,
        rent: int = 25,
        owner: int = -1,
        mortgaged: bool = False,
        color: dict = {"r": 12, "g": 11, "b": 11},
    ):
        self.name = name
        self.price = price
        self.location = location
        self.rent = rent
        self.owner = owner
        self.mortgaged = mortgaged
        self.color = Color.from_rgb(**color)

    def get_rent(self, number_of_stations: int):
        if number_of_stations == 1:
            return self.rent
        elif number_of_stations == 2:
            return self.rent * 2
        elif number_of_stations == 3:
            return self.rent * 4
        elif number_of_stations == 4:
            return self.rent * 8
        else:
            return 0

    def get_embed(self):
        em = Embed(
            title=f"**{self.name}**",
            description=f"**Rent price:**\n\nWith 1 train station: `${self.get_rent(1)}`\nWith 2 train stations: `${self.get_rent(2)}`\nWith 3 train stations: `${self.get_rent(3)}`\nWith 4 train stations: `${self.get_rent(4)}`",
            color=self.color,
        )
        em.set_footer(text=f"Case {self.location}")

        em.add_field(name="**Price:**", value=f"{self.price}€", inline=False)
        em.add_field(
            name="**Mortgage value:**",
            value=f"${ceil(self.price / 2)}",
            inline=False,
        )

        return em


class PublicServiceCompany(Case):
    card_type: PublicServiceCompanyType

    def __init__(
        self,
        name: str,
        location: int,
        card_type: PublicServiceCompanyType,
        price: int = 150,
        owner: int = -1,
        mortgaged: bool = False,
        color: dict = None,
    ):
        self.name = name
        self.price = price
        self.location = location
        self.card_type = card_type
        self.owner = owner
        self.mortgaged = mortgaged

        if not color:
            color = (
                {"r": 95, "g": 100, "b": 0}
                if card_type == PublicServiceCompanyType.ELECTRICITY
                else {"r": 212, "g": 241, "b": 249}
            )

        self.color = Color.from_rgb(**color)

    def get_rent(self, dice_value: int, number_of_companies: int) -> int:
        if number_of_companies == 1:
            return dice_value * 4
        elif number_of_companies == 2:
            return dice_value * 10
        else:
            return 0

    def get_embed(self) -> Embed:
        em = Embed(
            title=f"**{self.name}**",
            description=f"**Rent price:**\n\nWith 1 Company: `4 times the amount of the dice`\nWith 2 Companies: `10 times the amount of the dice`",
            color=self.color,
        )
        em.set_footer(text=f"Case {self.location}")

        em.add_field(name="**Price:**", value=f"{self.price}€", inline=False)
        em.add_field(
            name="**Mortgage value:**",
            value=f"${ceil(self.price / 2)}",
            inline=False,
        )

        return em


class Property(Case):
    rent: dict
    houses_price: int
    houses: int
    hotel: bool

    def __init__(
        self,
        name: str,
        price: int,
        location: int,
        rent: dict,
        houses_price: int,
        color: dict,
        houses: int = 0,
        hotel: bool = False,
        owner: int = -1,
        mortgaged: bool = False,
    ):
        self.name = name
        self.price = price
        self.location = location
        self.rent = rent
        self.houses_price = houses_price
        self.houses = houses
        self.hotel = hotel
        self.color = Color.from_rgb(**color)
        self.owner = owner
        self.mortgaged = mortgaged

    def get_rent(self) -> int:
        if self.hotel:
            return self.rent["hotel"]

        if self.houses:
            return self.rent[f"{self.houses}_houses"]

        return self.rent["default"]

    def get_embed(self) -> Embed:
        em = Embed(
            title=f"**{self.name}**",
            description=f"**Rent price:**\n\nwithout houses: `{self.rent['default']}€`\nWith 1 house: `${self.rent['1_houses']}`\nWith 2 houses: `${self.rent['2_houses']}`\nWith 3 houses: `${self.rent['3_houses']}`\nWith 4 houses: `${self.rent['4_houses']}`\nWith an hotel: `${self.rent['hotel']}`",
            color=self.color,
        )
        em.set_footer(text=f"Case {self.location}")

        em.add_field(
            name="**House price:**", value=f"{self.houses_price}€", inline=False
        )
        em.add_field(
            name="**Hotel price:**",
            value=f"{self.houses_price}€ (plus 4 houses)",
            inline=False,
        )

        em.add_field(name="**Price:**", value=f"{self.price}€", inline=False)
        em.add_field(
            name="**Mortgage value:**",
            value=f"{ceil(self.price / 2)}€",
            inline=False,
        )

        return em

    def buy_house(self):
        if self.hotel:
            return

        if self.houses == 4:
            self.houses = 0
            self.hotel = True
        else:
            self.houses += 1

    def sell_house(self):
        if self.hotel:
            self.hotel = False
            self.houses = 4
        elif self.houses == 0:
            return
        else:
            self.houses -= 1


class Player:
    id: int
    name: str
    member: Member
    balance: int
    avatar: Any
    location: int
    special_cards: list
    in_jail: bool
    bankrupted: bool
    last_dice: dict
    jail_time: int

    def __init__(
        self,
        id: int,
        name: str,
        member: Member,
        avatar: Any,
        last_dice: dict = {},
        balance: int = 1500,
        location: int = 0,
        special_cards: list = [],
        in_jail: bool = False,
        bankrupted: bool = False,
        jail_time: int = 0,
    ):
        self.id = id
        self.name = name
        self.member = member
        self.balance = balance
        self.avatar = avatar
        self.location = location
        self.special_cards = special_cards
        self.in_jail = in_jail
        self.bankrupted = bankrupted
        self.last_dice = last_dice
        self.jail_time = jail_time


total_houses: int = 32
total_hotels: int = 12
monopoly_chance_cards = [
    SpecialCard(
        id=0,
        description="Advance to Boardwalk",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=1,
        description="Advance to Go (Collect $200)",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=2,
        description="Advance to Illinois Avenue. If you pass Go, collect $200",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=3,
        description="Advance to St. Charles Place. If you pass Go, collect $200",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=4,
        description="Make general repairs on all your property. For each house pay $40. For each hotel pay $115.",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=5,
        description="Take a trip to Pennsylvania Railroad. If you pass Go, collect $200",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=6,
        description="Your building loan matures. Collect $100",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=7,
        description="Bank pays you dividend of $50",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=8,
        description="Get Out of Jail Free",
        card_type=SpecialCardsType.CHANCE,
        can_be_kept=True,
    ),
    SpecialCard(
        id=9, description="Go Back 3 Spaces", card_type=SpecialCardsType.CHANCE
    ),
    SpecialCard(
        id=10,
        description="Go to Jail. Go directly to Jail, do not pass Go, do not collect $200",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=11,
        description="Make general repairs on all your property. For each house pay $40. For each hotel pay $115.",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=12,
        description="Speeding fine $15",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=13,
        description="Pay tuition fees of $150",
        card_type=SpecialCardsType.CHANCE,
    ),
    SpecialCard(
        id=14, description="Fine for drunkenness $20", card_type=SpecialCardsType.CHANCE
    ),
    SpecialCard(
        id=15,
        description="Your building and your loan pay off. You should receive $150",
        card_type=SpecialCardsType.CHANCE,
    ),
]

monopoly_community_chest_cards = [
    SpecialCard(
        id=0,
        description="Advance to Go (Collect $200)",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=1,
        description="Bank error in your favor. Collect $200",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=2,
        description="Doctor’s fee. Pay $50",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=3,
        description="From sale of stock you get $50",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=4,
        description="Get Out of Jail Free",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
        can_be_kept=True,
    ),
    SpecialCard(
        id=5,
        description="Go to Jail. Go directly to jail, do not pass Go, do not collect $200",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=6,
        description="Return to Mediterranean Avenue. If you pass Go, collect $200",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=7,
        description="Holiday fund matures. Receive $100",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=8,
        description="It is your birthday. Collect $10 from every player",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=9,
        description="Income tax refund. Collect $20",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=10,
        description="Receive $25 consultancy fee",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=11,
        description="Pay insurance fees of $50",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=12,
        description='Pay a €10 fine or draw a "CHANCE" card',
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=13,
        description="Advance token to nearest Utility. If unowned, you may buy it from the Bank. If you pass Go, collect $200",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=14,
        description="You have won second prize in a beauty contest. Collect $10",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
    SpecialCard(
        id=15,
        description="You inherit $100",
        card_type=SpecialCardsType.COMMUNITY_CHEST,
    ),
]

monopoly_properties: dict = {
    1: Property(
        name="Mediterranean Avenue",
        price=60,
        location=1,
        rent={
            "default": 2,
            "1_houses": 10,
            "2_houses": 30,
            "3_houses": 90,
            "4_houses": 160,
            "hotel": 250,
        },
        houses_price=50,
        color={"r": 58, "g": 28, "b": 16},
    ),
    3: Property(
        name="Baltic Avenue",
        price=60,
        location=3,
        rent={
            "default": 4,
            "1_houses": 20,
            "2_houses": 60,
            "3_houses": 180,
            "4_houses": 320,
            "hotel": 450,
        },
        houses_price=50,
        color={"r": 58, "g": 28, "b": 16},
    ),
    5: Station(name="Reading Railroad", location=5),
    6: Property(
        name="Oriental Avenue",
        price=100,
        location=6,
        rent={
            "default": 6,
            "1_houses": 30,
            "2_houses": 90,
            "3_houses": 270,
            "4_houses": 400,
            "hotel": 550,
        },
        houses_price=50,
        color={"r": 73, "g": 89, "b": 98},
    ),
    8: Property(
        name="Vermont Avenue",
        price=100,
        location=8,
        rent={
            "default": 6,
            "1_houses": 30,
            "2_houses": 90,
            "3_houses": 270,
            "4_houses": 400,
            "hotel": 550,
        },
        houses_price=50,
        color={"r": 73, "g": 89, "b": 98},
    ),
    9: Property(
        name="Connecticut Avenue",
        price=120,
        location=9,
        rent={
            "default": 8,
            "1_houses": 40,
            "2_houses": 100,
            "3_houses": 300,
            "4_houses": 450,
            "hotel": 600,
        },
        houses_price=50,
        color={"r": 73, "g": 89, "b": 98},
    ),
    11: Property(
        name="St. Charles Place",
        price=140,
        location=11,
        rent={
            "default": 10,
            "1_houses": 50,
            "2_houses": 150,
            "3_houses": 450,
            "4_houses": 625,
            "hotel": 750,
        },
        houses_price=100,
        color={"r": 86, "g": 18, "b": 54},
    ),
    12: PublicServiceCompany(
        name="Electric Company",
        location=12,
        card_type=PublicServiceCompanyType.ELECTRICITY,
    ),
    13: Property(
        name="States Avenue",
        price=140,
        location=13,
        rent={
            "default": 10,
            "1_houses": 50,
            "2_houses": 150,
            "3_houses": 450,
            "4_houses": 625,
            "hotel": 750,
        },
        houses_price=100,
        color={"r": 86, "g": 18, "b": 54},
    ),
    14: Property(
        name="Virginia Avenue",
        price=160,
        location=14,
        rent={
            "default": 12,
            "1_houses": 60,
            "2_houses": 180,
            "3_houses": 500,
            "4_houses": 700,
            "hotel": 900,
        },
        houses_price=100,
        color={"r": 86, "g": 18, "b": 54},
    ),
    15: Station(name="Pennsylvania Railroad", location=15),
    16: Property(
        name="St. James Place",
        price=180,
        location=16,
        rent={
            "default": 14,
            "1_houses": 70,
            "2_houses": 200,
            "3_houses": 550,
            "4_houses": 750,
            "hotel": 950,
        },
        houses_price=100,
        color={"r": 96, "g": 57, "b": 0},
    ),
    18: Property(
        name="Tennessee Avenue",
        price=180,
        location=18,
        rent={
            "default": 14,
            "1_houses": 70,
            "2_houses": 200,
            "3_houses": 550,
            "4_houses": 750,
            "hotel": 950,
        },
        houses_price=100,
        color={"r": 96, "g": 57, "b": 0},
    ),
    19: Property(
        name="New York Avenue",
        price=200,
        location=19,
        rent={
            "default": 16,
            "1_houses": 80,
            "2_houses": 220,
            "3_houses": 600,
            "4_houses": 800,
            "hotel": 1000,
        },
        houses_price=100,
        color={"r": 96, "g": 57, "b": 0},
    ),
    21: Property(
        name="Kentucky Avenue",
        price=220,
        location=21,
        rent={
            "default": 18,
            "1_houses": 90,
            "2_houses": 250,
            "3_houses": 700,
            "4_houses": 875,
            "hotel": 1050,
        },
        houses_price=150,
        color={"r": 89, "g": 0, "b": 6},
    ),
    23: Property(
        name="Indiana Avenue",
        price=220,
        location=23,
        rent={
            "default": 18,
            "1_houses": 90,
            "2_houses": 250,
            "3_houses": 700,
            "4_houses": 875,
            "hotel": 1050,
        },
        houses_price=150,
        color={"r": 89, "g": 0, "b": 6},
    ),
    24: Property(
        name="Illinois Avenue",
        price=240,
        location=24,
        rent={
            "default": 20,
            "1_houses": 100,
            "2_houses": 300,
            "3_houses": 750,
            "4_houses": 925,
            "hotel": 1100,
        },
        houses_price=150,
        color={"r": 89, "g": 0, "b": 6},
    ),
    25: Station(name="B. & O. Railroad", location=25),
    26: Property(
        name="Atlantic Avenue",
        price=260,
        location=26,
        rent={
            "default": 22,
            "1_houses": 110,
            "2_houses": 330,
            "3_houses": 800,
            "4_houses": 975,
            "hotel": 1150,
        },
        houses_price=150,
        color={"r": 100, "g": 93, "b": 0},
    ),
    27: Property(
        name="Ventnor Avenue",
        price=260,
        location=27,
        rent={
            "default": 22,
            "1_houses": 110,
            "2_houses": 330,
            "3_houses": 800,
            "4_houses": 975,
            "hotel": 1150,
        },
        houses_price=150,
        color={"r": 100, "g": 93, "b": 0},
    ),
    28: PublicServiceCompany(
        name="Water Works",
        location=28,
        card_type=PublicServiceCompanyType.WATER,
    ),
    29: Property(
        name="Marvin Gardens",
        price=280,
        location=29,
        rent={
            "default": 24,
            "1_houses": 120,
            "2_houses": 360,
            "3_houses": 850,
            "4_houses": 1025,
            "hotel": 1200,
        },
        houses_price=150,
        color={"r": 100, "g": 93, "b": 0},
    ),
    31: Property(
        name="Pacific Avenue",
        price=300,
        location=31,
        rent={
            "default": 26,
            "1_houses": 130,
            "2_houses": 390,
            "3_houses": 900,
            "4_houses": 1100,
            "hotel": 1275,
        },
        houses_price=200,
        color={"r": 11, "g": 65, "b": 30},
    ),
    32: Property(
        name="North Carolina Avenue",
        price=300,
        location=32,
        rent={
            "default": 26,
            "1_houses": 130,
            "2_houses": 390,
            "3_houses": 900,
            "4_houses": 1100,
            "hotel": 1275,
        },
        houses_price=200,
        color={"r": 11, "g": 65, "b": 30},
    ),
    34: Property(
        name="Pennsylvania Avenue",
        price=320,
        location=34,
        rent={
            "default": 28,
            "1_houses": 150,
            "2_houses": 450,
            "3_houses": 1000,
            "4_houses": 1200,
            "hotel": 1400,
        },
        houses_price=200,
        color={"r": 11, "g": 65, "b": 30},
    ),
    35: Station(name="Short Line", location=35),
    37: Property(
        name="Park Place",
        price=350,
        location=37,
        rent={
            "default": 35,
            "1_houses": 175,
            "2_houses": 500,
            "3_houses": 1100,
            "4_houses": 1300,
            "hotel": 1500,
        },
        houses_price=200,
        color={"r": 0, "g": 41, "b": 70},
    ),
    39: Property(
        name="Boardwalk",
        price=400,
        location=39,
        rent={
            "default": 50,
            "1_houses": 200,
            "2_houses": 600,
            "3_houses": 1400,
            "4_houses": 1700,
            "hotel": 2000,
        },
        houses_price=200,
        color={"r": 0, "g": 41, "b": 70},
    ),
}

board_places: dict = {
    0: {
        1: {"locations": [(1131, 1131)], "size": (60, 60)},
        2: {"locations": [(1101, 1101), (1161, 1161)], "size": (60, 60)},
        3: {"locations": [(1091, 1101), (1171, 1101), (1131, 1161)], "size": (60, 60)},
        4: {
            "locations": [(1091, 1096), (1171, 1096), (1171, 1168), (1091, 1168)],
            "size": (60, 60),
        },
        5: {
            "locations": [
                (1091, 1091),
                (1176, 1091),
                (1176, 1176),
                (1091, 1176),
                (1133, 1134),
            ],
            "size": (55, 55),
        },
        6: {
            "locations": [
                (1101, 1086),
                (1176, 1086),
                (1176, 1136),
                (1176, 1186),
                (1101, 1136),
                (1101, 1186),
            ],
            "size": (45, 45),
        },
        7: {
            "locations": [
                (1086, 1086),
                (1186, 1086),
                (1186, 1136),
                (1186, 1186),
                (1086, 1136),
                (1086, 1186),
                (1136, 1136),
            ],
            "size": (45, 45),
        },
        8: {
            "locations": [
                (1086, 1086),
                (1186, 1086),
                (1186, 1136),
                (1186, 1186),
                (1086, 1136),
                (1086, 1186),
                (1136, 1106),
                (1136, 1166),
            ],
            "size": (45, 45),
        },
    },
    1: {
        1: {"locations": [(1000, 1158)], "size": (60, 60)},
        2: {"locations": [(983, 1154), (1030, 1175)], "size": (45, 45)},
        3: {"locations": [(983, 1154), (1030, 1175), (1030, 1125)], "size": (45, 45)},
        4: {
            "locations": [(983, 1146), (983, 1194), (1030, 1175), (1030, 1125)],
            "size": (45, 45),
        },
        5: {
            "locations": [
                (985, 1155),
                (985, 1199),
                (985, 1110),
                (1032, 1180),
                (1032, 1135),
            ],
            "size": (40, 40),
        },
        6: {
            "locations": [
                (985, 1155),
                (985, 1199),
                (985, 1110),
                (1032, 1155),
                (1032, 1199),
                (1032, 1110),
            ],
            "size": (40, 40),
        },
        7: {
            "locations": [
                (982, 1163),
                (982, 1203),
                (982, 1122),
                (1041, 1163),
                (1041, 1203),
                (1041, 1122),
                (1012, 1143),
            ],
            "size": (35, 35),
        },
        8: {
            "locations": [
                (982, 1163),
                (982, 1203),
                (982, 1122),
                (1041, 1163),
                (1041, 1203),
                (1041, 1122),
                (1012, 1143),
                (1012, 1183),
            ],
            "size": (35, 35),
        },
    },
    10: {
        "no_jail": {
            1: {"locations": [(2, 1085)], "size": (39, 39)},
            2: {"locations": [(2, 1085), (2, 1127)], "size": (39, 39)},
            3: {"locations": [(2, 1085), (2, 1127), (2, 1169)], "size": (39, 39)},
            4: {
                "locations": [(4, 1084), (4, 1123), (4, 1161), (4, 1200)],
                "size": (35, 35),
            },
            5: {
                "locations": [(4, 1085), (4, 1124), (4, 1162), (4, 1201), (43, 1201)],
                "size": (35, 35),
            },
            6: {
                "locations": [
                    (4, 1085),
                    (4, 1124),
                    (4, 1162),
                    (4, 1201),
                    (43, 1201),
                    (82, 1201),
                ],
                "size": (35, 35),
            },
            7: {
                "locations": [
                    (4, 1085),
                    (4, 1124),
                    (4, 1162),
                    (4, 1201),
                    (43, 1201),
                    (82, 1201),
                    (121, 1201),
                ],
                "size": (35, 35),
            },
            8: {
                "locations": [
                    (6, 1085),
                    (6, 1117),
                    (6, 1149),
                    (6, 1181),
                    (26, 1206),
                    (59, 1206),
                    (92, 1206),
                    (125, 1206),
                ],
                "size": (30, 30),
            },
        },
        "jail": {
            1: {"locations": [(73, 1105)], "size": (60, 60)},
            2: {"locations": [(50, 1085), (97, 1133)], "size": (60, 60)},
            3: {"locations": [(53, 1090), (107, 1090), (80, 1140)], "size": (45, 45)},
            4: {
                "locations": [(53, 1090), (107, 1090), (53, 1140), (107, 1140)],
                "size": (45, 45),
            },
            5: {
                "locations": [
                    (50, 1085),
                    (115, 1085),
                    (50, 1150),
                    (115, 1150),
                    (82, 1119),
                ],
                "size": (40, 40),
            },
            6: {
                "locations": [
                    (55, 1083),
                    (115, 1083),
                    (55, 1121),
                    (115, 1121),
                    (55, 1159),
                    (115, 1159),
                ],
                "size": (35, 35),
            },
            7: {
                "locations": [
                    (50, 1083),
                    (121, 1083),
                    (50, 1121),
                    (121, 1121),
                    (50, 1159),
                    (121, 1159),
                    (85, 1121),
                ],
                "size": (35, 35),
            },
            8: {
                "locations": [
                    (50, 1083),
                    (121, 1083),
                    (50, 1121),
                    (121, 1121),
                    (50, 1159),
                    (121, 1159),
                    (85, 1101),
                    (85, 1141),
                ],
                "size": (35, 35),
            },
        },
    },
    11: {
        1: {"locations": [(23, 1000)], "size": (60, 60)},
        2: {"locations": [(20, 983), (45, 1030)], "size": (45, 45)},
        3: {"locations": [(20, 983), (45, 1030), (70, 983)], "size": (45, 45)},
        4: {
            "locations": [(30, 983), (55, 1030), (80, 983), (5, 1030)],
            "size": (45, 45),
        },
        5: {
            "locations": [(5, 983), (80, 1030), (80, 983), (5, 1030), (42, 1007)],
            "size": (40, 40),
        },
        6: {
            "locations": [
                (0, 982),
                (82, 1035),
                (82, 982),
                (0, 1035),
                (41, 982),
                (41, 1035),
            ],
            "size": (40, 40),
        },
        7: {
            "locations": [
                (0, 982),
                (84, 1040),
                (84, 982),
                (0, 1040),
                (41, 982),
                (41, 1040),
                (20, 1011),
            ],
            "size": (35, 35),
        },
        8: {
            "locations": [
                (0, 982),
                (84, 1040),
                (84, 982),
                (0, 1040),
                (41, 982),
                (41, 1040),
                (20, 1011),
                (62, 1011),
            ],
            "size": (35, 35),
        },
    },
    20: {
        1: {"locations": [(50, 50)], "size": (60, 60)},
        2: {"locations": [(20, 20), (80, 80)], "size": (60, 60)},
        3: {"locations": [(10, 20), (90, 20), (50, 80)], "size": (60, 60)},
        4: {
            "locations": [(10, 10), (90, 10), (10, 85), (90, 85)],
            "size": (60, 60),
        },
        5: {
            "locations": [(10, 10), (95, 10), (10, 95), (95, 95), (53, 53)],
            "size": (55, 55),
        },
        6: {
            "locations": [(25, 5), (95, 5), (25, 105), (95, 105), (25, 55), (95, 55)],
            "size": (45, 45),
        },
        7: {
            "locations": [
                (10, 5),
                (110, 5),
                (10, 105),
                (110, 105),
                (10, 55),
                (110, 55),
                (60, 55),
            ],
            "size": (45, 45),
        },
        8: {
            "locations": [
                (10, 5),
                (110, 5),
                (10, 105),
                (110, 105),
                (10, 55),
                (110, 55),
                (60, 25),
                (60, 85),
            ],
            "size": (45, 45),
        },
    },
}

board_places_houses: dict = {
    1: {
        "houses": [(978, 1081), (1002, 1094), (1025, 1081), (1049, 1094)],
        "hotel": [(1011, 1083)],
    },
    11: {
        "houses": [(128, 981), (128, 1005), (128, 1029), (128, 1053)],
        "hotel": [(125, 1013)],
    },
}

monopoly_families: List[List[int]] = [
    [1, 3],
    [6, 8, 9],
    [11, 13, 14],
    [16, 18, 19],
    [21, 23, 24],
    [26, 27, 29],
    [31, 32, 34],
    [37, 39],
]

monopoly_families_color: dict = {
    Color.from_rgb(58, 28, 16): "🟤",
    Color.from_rgb(73, 89, 98): "🔵",
    Color.from_rgb(86, 18, 54): "🟣",
    Color.from_rgb(96, 57, 0): "🟠",
    Color.from_rgb(89, 0, 6): "🔴",
    Color.from_rgb(100, 93, 0): "🟡",
    Color.from_rgb(11, 65, 30): "🟢",
    Color.from_rgb(0, 41, 70): "⚫",
}


def throw_dice() -> dict:
    return {"d1": randint(1, 6), "d2": randint(1, 6)}


class MonopolyGame:
    bot: OmniGames
    participants: List[Player]
    properties: dict
    green_house: PngImagePlugin.PngImageFile
    hotel: PngImagePlugin.PngImageFile
    community_chest_cards: Iterator
    chance_cards: Iterator
    game_message: Message
    board: JpegImagePlugin.JpegImageFile
    default_board: JpegImagePlugin.JpegImageFile
    current_turn: int

    def __init__(
        self,
        bot: OmniGames,
        participants: Union[List[Member], List[Player]],
        game_message: Message,
        community_chest_cards: List[SpecialCard] = None,
        chance_cards: List[SpecialCard] = None,
        properties: dict = None,
        board: bytes = None,
        current_turn: int = 0,
        *args,
        **kwargs,
    ):
        self.bot = bot
        self.green_house = Image.open(
            BytesIO(self.bot.games_repo.download_monopoly_green_house())
        )
        self.hotel = Image.open(BytesIO(self.bot.games_repo.download_monopoly_hotel()))

        if isinstance(participants[0], Member):
            dices: List[dict] = []

            for x in range(len(participants)):
                dice = throw_dice()
                dices.append(dice)

            dices = sorted(dices, key=lambda d: d["d1"] + d["d2"], reverse=True)
            shuffle(participants)

            members: List[Player] = []
            mask: Image = Image.new("L", (128, 128), 0)
            draw: ImageDraw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 128, 128), fill=255)  # draw the ellipse

            for x in range(len(participants)):
                if participants[x].avatar:
                    with get(participants[x].avatar.url) as f:
                        avatar = Image.open(BytesIO(f.content))

                    if avatar.format == "GIF":
                        avatar_bytes: BytesIO = BytesIO()
                        avatar.save(avatar_bytes, transparency=0, format="PNG")
                        avatar = Image.open(avatar_bytes)

                    avatar = avatar.convert("RGBA")

                    bg = Image.new(
                        "RGB", avatar.size, (255, 255, 255)
                    )  # Create a white background
                    # copy the image on the background
                    bg.paste(avatar, avatar)

                    avatar = ImageOps.fit(
                        bg, mask.size, centering=(0.5, 0.5)
                    )  # fit the image in the middle
                    avatar.putalpha(mask)  # put alpha channel on the image
                    avatar = avatar.resize(
                        board_places[0][len(participants)]["size"], Image.ANTIALIAS
                    )
                else:
                    avatar = Image.open(
                        BytesIO(self.bot.games_repo.download_default_monopoly_avatar())
                    )

                members.append(
                    Player(
                        id=x,
                        name=participants[x].name,
                        member=participants[x],
                        avatar=avatar,
                        last_dice=dices[x],
                    )
                )

            self.participants = members
        else:
            self.participants = participants

        self.properties = properties or monopoly_properties
        self.community_chest_cards = cycle(
            community_chest_cards
            or sample(
                monopoly_community_chest_cards, len(monopoly_community_chest_cards)
            )
        )
        self.chance_cards = cycle(
            chance_cards or sample(monopoly_chance_cards, len(monopoly_chance_cards))
        )
        self.game_message = game_message
        self.default_board = Image.open(
            BytesIO(self.bot.games_repo.download_default_monopoly_game())
        )
        self.current_turn = current_turn

        if board:
            self.board = Image.open(BytesIO(board))
            board_bytes: BytesIO = BytesIO()
            self.board.save(board_bytes, format="JPEG")
            board_bytes.seek(0)
            self.bot.utils_class.task_launcher(
                self.game_message.channel.send,
                {
                    "content": "ℹ - I have just restarted, here is what I had saved - ℹ",
                    "files": [
                        File(
                            board_bytes,
                            filename=f"monopoly_{self.game_message.channel.id}.jpg",
                        )
                    ],
                },
                count=1,
            )
            self.bot.utils_class.task_launcher(self.turn, (), count=1)
        else:
            self.board = Image.open(
                BytesIO(self.bot.games_repo.download_default_monopoly_game())
            )

            x = 0
            for player in self.participants:
                self.board.paste(
                    player.avatar,
                    board_places[0][len(participants)]["locations"][x],
                    player.avatar,
                )
                x += 1

    def save(self):
        community_chest_cards = [
            next(self.community_chest_cards).__dict__
            for _ in range(len(monopoly_community_chest_cards))
        ]
        chance_cards = [
            next(self.chance_cards).__dict__ for _ in range(len(monopoly_chance_cards))
        ]

        self.bot.games_repo.update_game(
            self.game_message.guild.id,
            self.game_message.channel.id,
            args={
                "current_turn": self.current_turn,
                "participants": [
                    {
                        k: (
                            v.id
                            if k == "member"
                            else (
                                None
                                if k == "avatar"
                                else (
                                    [c.__dict__ for c in v]
                                    if k == "special_cards"
                                    else v
                                )
                            )
                        )
                        for k, v in p.__dict__.items()
                    }
                    for p in self.participants
                ],
                "properties": {
                    f"p{k}": {
                        k1: (v1 if k1 != "color" else {"r": v1.r, "g": v1.g, "b": v1.b})
                        for k1, v1 in v.__dict__.items()
                    }
                    for k, v in self.properties.items()
                },
                "community_chest_cards": community_chest_cards,
                "chance_cards": chance_cards,
            },
        )

        board_bytes: BytesIO = BytesIO()
        self.board.save(board_bytes, format="JPEG")
        board_bytes.seek(0)
        self.bot.games_repo.update_monopoly_game(
            self.game_message.channel.id, board_bytes
        )

    def get_board(self) -> BytesIO:
        board_bytes: BytesIO = BytesIO()
        self.board.save(board_bytes, format="JPEG")
        board_bytes.seek(0)
        return board_bytes

    def get_players(self) -> List[Player]:
        return self.participants

    def get_player(self, p_id: int = None, member: Member = None) -> Optional[Player]:
        if p_id:
            if 0 > p_id > len(self.participants):
                return None

            return self.participants[p_id]
        elif member:
            players_members = [p.member.id for p in self.participants]
            if member.id not in players_members:
                return None

            return self.participants[players_members.index(member.id)]

    def get_player_embed(self, p_id: int) -> Embed:
        player: Player = self.participants[p_id]
        properties: List[Case] = [
            p for p in self.properties.values() if p.owner == p_id
        ]
        em = Embed(
            title=f"**Player's information {player.name}**",
            description=f"**Amount of money:** `{player.balance}€`\n**Number of properties:** `{len(properties)}`\n**Case:** `{player.location}`\n**Is in jail:** `{'oui' if player.in_jail else 'non'}`\n**Went bankrupt:** `{'yes' if player.bankrupted else 'no'}`",
            color=player.member.color,
        )

        avatar_bytes: BytesIO = BytesIO()
        player.avatar.save(avatar_bytes, format="PNG")
        avatar_bytes.seek(0)
        em.set_thumbnail(
            file=File(avatar_bytes, filename=f"avatar_monopoly_{player.name}.png")
        )

        return em

    async def turn(self):
        in_turn: bool = True
        threw: bool = False
        double_num: int = 0
        msg: Message = None

        while in_turn:
            properties: List[Case] = [
                p for p in self.properties.values() if p.owner == self.current_turn
            ]
            view: View = View(timeout=None)

            if self.participants[self.current_turn].in_jail:
                view.add_item(
                    Button(emoji="🚨", custom_id="monopoly_jail", disabled=threw)
                )
            else:
                view.add_item(
                    Button(emoji="🎲", custom_id="monopoly_die", disabled=threw)
                )

            view.add_item(Button(emoji="ℹ️", custom_id="monopoly_infos"))
            view.add_item(
                Button(emoji="🏘️", custom_id="monopoly_houses", disabled=not properties)
            )
            view.add_item(
                Button(
                    emoji="🏡", custom_id="monopoly_buy_houses", disabled=not properties
                )
            )
            view.add_item(
                Button(
                    emoji="📜",
                    custom_id="monopoly_buy_mortgaged",
                    disabled=not any(p.mortgaged for p in properties),
                )
            )
            view.add_item(
                Button(emoji="🔚", custom_id="monopoly_end", disabled=not threw)
            )
            view.add_item(
                Button(style=ButtonStyle.danger, emoji="💀", custom_id="monopoly_skull")
            )

            em = Embed(
                title=f"**It's {self.participants[self.current_turn].name}'s turn**"
                + (
                    " - *In jail*"
                    if self.participants[self.current_turn].in_jail
                    else ""
                ),
                description="**What would you like to do ?**\n\n"
                + (
                    "🚨 - Trying to get out of jail - 🚨"
                    if self.participants[self.current_turn].in_jail
                    else "🎲 - Roll the dice - 🎲"
                )
                + "\n\nℹ️ - View your information - ℹ️\n\n🏘️ - See the list of your properties - 🏘️\n\n🏡 - Buying houses for a property - 🏡\n\n📜 - Re-buying mortgaged properties - 📜\n\n🔚 - End your round - 🔚\n\n💀 - Abandon the game - 💀",
                color=self.participants[self.current_turn].member.color,
            )

            avatar_bytes: BytesIO = BytesIO()
            self.participants[self.current_turn].avatar.save(avatar_bytes, format="PNG")
            avatar_bytes.seek(0)
            em.set_thumbnail(
                file=File(
                    avatar_bytes,
                    filename=f"avatar_monopoly_{self.participants[self.current_turn].name}.png",
                )
            )

            if msg:
                em_temp = em.to_dict()
                del em_temp["thumbnail"]
                em_msg = msg.embeds[0].to_dict()
                del em_msg["thumbnail"]

                if em_temp != em_msg or view.to_components() != [
                    c.to_dict() for c in msg.components
                ]:
                    await msg.edit(embed=em, view=view)
            else:
                msg = await self.game_message.channel.send(embed=em, view=view)

            def select_button(interaction: MessageInteraction) -> bool:
                return (
                    interaction.message.id == msg.id
                    and interaction.author.id
                    == self.participants[self.current_turn].member.id
                )

            interaction: MessageInteraction = await self.bot.wait_for(
                "button_click", timeout=None, check=select_button
            )

            await interaction.response.defer()

            if interaction.component.custom_id == "monopoly_die":
                dice = throw_dice()
                self.participants[self.current_turn].last_dice = dice
                content = f"🎲 - {self.participants[self.current_turn].member.mention} - You've just made a `{dice['d1']}` and a `{dice['d2']}` (`{dice['d1'] + dice['d2']}`){' **a double!**' if dice['d1'] == dice['d2'] else ''} - 🎲"

                try:
                    await interaction.followup.send(content)
                except NotFound:
                    await interaction.response.send_message(content)

                await self.move(dice["d1"] + dice["d2"])

                if dice["d1"] != dice["d2"]:
                    threw = True
                    msg = None

                    if msg:
                        try:
                            await msg.delete()
                        except NotFound:
                            pass
                    continue
                elif double_num == 2:
                    threw = True
                    content = f"🚔 - {self.participants[self.current_turn].member.mention} - You've just made 3 doubles in a row, now you're going to jail - 🚔"

                    try:
                        await interaction.followup.send(content)
                    except NotFound:
                        await interaction.response.send_message(content)

                    self.participants[self.current_turn].in_jail = True
                    await self.move(10, exact=True)
                    msg = None

                    if msg:
                        try:
                            await msg.delete()
                        except NotFound:
                            pass
                    continue

                double_num += 1
                msg = None

                if msg:
                    try:
                        await msg.delete()
                    except NotFound:
                        pass
            elif interaction.component.custom_id == "monopoly_jail":
                if self.participants[self.current_turn].special_cards:
                    content = "🃏 - You have a get-out-of-jail-free card, do you want to use it? - 🃏"
                    view = View(timeout=25)
                    view.add_item(Button(emoji="✅", custom_id="jail_valid"))
                    view.add_item(Button(emoji="❌", custom_id="jail_nope"))

                    try:
                        temp_msg: Message = await interaction.followup.send(
                            content,
                            embed=self.participants[self.current_turn]
                            .special_cards[0]
                            .get_embed(),
                            view=view,
                        )
                    except NotFound:
                        temp_msg: Message = await interaction.response.send_message(
                            content,
                            embed=self.participants[self.current_turn]
                            .special_cards[0]
                            .get_embed(),
                            view=view,
                        )

                    def select_button(interaction: MessageInteraction) -> bool:
                        return (
                            interaction.message.id == temp_msg.id
                            and interaction.author.id
                            == self.participants[self.current_turn].member.id
                        )

                    try:
                        temp_interaction: MessageInteraction = await self.bot.wait_for(
                            "button_click", timeout=20.0, check=select_button
                        )
                    except exceptions.TimeoutError:
                        content = f"ℹ - You have taken too long to answer, returning to the main menu - ℹ"
                        try:
                            await interaction.followup.send(content, ephemeral=True)
                        except NotFound:
                            await interaction.response.send_message(
                                content, ephemeral=True
                            )

                        continue
                    else:
                        await temp_interaction.response.defer()

                        if temp_interaction.component.custom_id == "jail_valid":
                            del self.participants[self.current_turn].special_cards[0]
                            self.participants[self.current_turn].in_jail = False
                            self.participants[self.current_turn].jail_time = 0
                            content = f"👮 - {self.participants[self.current_turn].member.mention} - You are released from jail - 👮"

                            try:
                                await temp_interaction.followup.send(content)
                            except NotFound:
                                await temp_interaction.response.send_message(content)
                            continue
                        else:
                            content = f"👮🃏 - {self.participants[self.current_turn].member.mention} - You have decided not to use your get-out-of-jail-free card - 🃏👮"

                            try:
                                await temp_interaction.followup.send(content)
                            except NotFound:
                                await temp_interaction.response.send_message(content)

                content = "💳 - Would you like to pay `$50` to the bank to be released directly from jail or would you like to roll the dice? - 💳"
                view = View(timeout=25)
                view.add_item(Button(emoji="💳", custom_id="jail_pay"))
                view.add_item(Button(emoji="🎲", custom_id="jail_dice"))

                try:
                    temp_msg: Message = await interaction.followup.send(
                        content, view=view
                    )
                except NotFound:
                    temp_msg: Message = await interaction.response.send_message(
                        content, view=view
                    )

                def select_button(interaction: MessageInteraction) -> bool:
                    return (
                        interaction.message.id == temp_msg.id
                        and interaction.author.id
                        == self.participants[self.current_turn].member.id
                    )

                try:
                    temp_interaction: MessageInteraction = await self.bot.wait_for(
                        "button_click", timeout=20.0, check=select_button
                    )
                except exceptions.TimeoutError:
                    content = f"ℹ - {self.participants[self.current_turn].member.mention} - You have taken too long to answer, returning to the main menu - ℹ"
                    try:
                        await interaction.followup.send(content, ephemeral=True)
                    except NotFound:
                        await interaction.response.send_message(content, ephemeral=True)

                    continue
                else:
                    await temp_interaction.response.defer()

                    if temp_interaction.component.custom_id == "jail_pay":
                        if self.participants[self.current_turn].balance >= 50:
                            await self.pay(50)
                            self.participants[self.current_turn].in_jail = False
                            self.participants[self.current_turn].jail_time = 0
                            content = f"👮💳 - {self.participants[self.current_turn].member.mention} - You have paid your debt and are released from jail - 💳👮"

                            try:
                                await temp_interaction.followup.send(content)
                            except NotFound:
                                await temp_interaction.response.send_message(content)
                            continue
                        else:
                            content = f"👮🎲 - {self.participants[self.current_turn].member.mention} - You don't have enough money to pay your debt, so you will try to roll the dice - 🎲👮"

                            try:
                                await temp_interaction.followup.send(content)
                            except NotFound:
                                await temp_interaction.response.send_message(content)

                    dice = throw_dice()
                    self.participants[self.current_turn].last_dice = dice
                    self.participants[self.current_turn].jail_time += 1

                    content = f"👮🎲 - {self.participants[self.current_turn].member.mention} - You've just made a `{dice['d1']}` and a `{dice['d2']}` (`{dice['d1'] + dice['d2']}`){' **a double! You are therefore released from jail and moved from the value of the dice**' if dice['d1'] == dice['d2'] else (f' Better luck next time! (*{self.participants[self.current_turn].jail_time}' + ('st' if self.participants[self.current_turn].jail_time == 1 else ('nd' if self.participants[self.current_turn].jail_time == 2 else 'rd')) + ' attempt*)')} - 🎲👮"

                    try:
                        await temp_interaction.followup.send(content)
                    except NotFound:
                        await temp_interaction.response.send_message(content)

                    if dice["d1"] == dice["d2"]:
                        self.participants[self.current_turn].in_jail = False
                        self.participants[self.current_turn].jail_time = 0
                        await self.move(dice["d1"] + dice["d2"])

                        if msg:
                            try:
                                await msg.delete()
                            except NotFound:
                                pass
                    elif self.participants[self.current_turn].jail_time == 3:
                        self.participants[self.current_turn].jail_time = 0
                        await self.pay(50)

                    threw = True
                    msg = None
            elif interaction.component.custom_id == "monopoly_infos":
                try:
                    await interaction.followup.send(
                        embed=self.get_player_embed(self.current_turn),
                        ephemeral=True,
                    )
                except NotFound:
                    await interaction.response.send_message(
                        embed=self.get_player_embed(self.current_turn),
                        ephemeral=True,
                    )
            elif interaction.component.custom_id == "monopoly_houses":
                em_houses = Embed(title="**List of your properties**")
                em_houses1 = None

                x = 0
                for p in properties:
                    field = {
                        "name": f"**{p.name}**",
                        "value": f"**Case:** `{p.location}`\n**Rent price:** `{f'${p.get_rent()}' if isinstance(p, Property) else (f'${p.get_rent(len([s for s in properties if isinstance(s, Station)]))}' if isinstance(p, Station) else ('10 times the amount of the dice' if len([s for s in properties if isinstance(s, PublicServiceCompany)]) > 1 else '4 times the amount of the dice'))}`"
                        + (
                            f"\n**Number of houses (or hotel):** `{(f'{p.houses} house' + ('s' if p.houses > 1 else '')) if not p.hotel else '1 hotel'}`"
                            if isinstance(p, Property)
                            else f"\n**Number of {'train stations' if isinstance(p, Station) else 'public service companies'}:** `{len([c for c in properties if isinstance(c, Station if isinstance(p, Station) else PublicServiceCompany)])}`"
                        )
                        + ("\n***Mortgaged***" if p.mortgaged else ""),
                        "inline": False,
                    }

                    if x < 25:
                        em_houses.add_field(**field)
                    else:
                        if not em_houses1:
                            em_houses.title = "**List of your properties (1/2)**"
                            em_houses1 = Embed(
                                title="**List of your properties (2/2)**"
                            )

                        em_houses1.add_field(**field)

                try:
                    await interaction.followup.send(embed=em_houses, ephemeral=True)
                except NotFound:
                    await interaction.response.send_message(
                        embed=em_houses, ephemeral=True
                    )

                if em_houses1:
                    try:
                        await interaction.followup.send(
                            embed=em_houses1, ephemeral=True
                        )
                    except NotFound:
                        await interaction.response.send_message(
                            embed=em_houses1, ephemeral=True
                        )
            elif interaction.component.custom_id == "monopoly_buy_houses":
                families: List[int] = [
                    p.location for p in properties if isinstance(p, Property)
                ]
                compatible_families: List[int] = [
                    x
                    for x in range(len(monopoly_families))
                    if monopoly_families[x] in families
                ]

                if not compatible_families:
                    content = f"ℹ - You currently have no family, so you cannot build a house - ℹ"
                    try:
                        await interaction.followup.send(content, ephemeral=True)
                    except NotFound:
                        await interaction.response.send_message(content, ephemeral=True)
                    continue

                family_properties: List[List[int]] = [
                    monopoly_families[x] for x in compatible_families
                ]

                if all(
                    all(self.properties[p].hotel for p in family_properties[x])
                    for x in range(len(family_properties))
                ):
                    content = f"ℹ - All the families you own have hotels built, so you can't build anything more - ℹ"
                    try:
                        await interaction.followup.send(content, ephemeral=True)
                    except NotFound:
                        await interaction.response.send_message(content, ephemeral=True)
                    continue

                buying_houses: bool = True
                temp_msg: Optional[Message] = None

                while buying_houses:
                    if len(family_properties) > 1:
                        endl = "\n"
                        view = View(timeout=None)
                        em = Embed(
                            title="**Choose a familly...**",
                            description=f"On which family do you want to build one or more houses ?\n\n{endl.join([f'{NUM2EMOJI[x + 1]} - ' + ', '.join([f'*`{self.properties[p].name}`*' for p in family_properties[x]]) + f' - {NUM2EMOJI[x + 1]}' for x in range(len(family_properties))])}",
                        )
                        em.description += "\n\n*🔙 - Return to main menu - 🔙*"

                        used_emojies: List[str] = ["🔙"]
                        for x in range(1, len(family_properties) + 1):
                            view.add_item(
                                Button(
                                    emoji=NUM2EMOJI[x],
                                    custom_id=f"{temp_msg.id}_{x}",
                                    disabled=all(
                                        self.properties[p].hotel
                                        for p in family_properties[x - 1]
                                    ),
                                )
                            )
                            used_emojies.append(NUM2EMOJI[x])

                        view.add_item(
                            Button(emoji="🔙", custom_id=f"{temp_msg.id}_back")
                        )

                        if not temp_msg:
                            try:
                                temp_msg: Message = await interaction.followup.send(
                                    embed=em,
                                    view=view,
                                    ephemeral=True,
                                )
                            except NotFound:
                                temp_msg: Message = (
                                    await interaction.response.send_message(
                                        embed=em,
                                        view=view,
                                        ephemeral=True,
                                    )
                                )
                        else:
                            await temp_msg.edit(embed=em, view=view)

                        try:
                            temp_interaction: MessageInteraction = (
                                await self.bot.wait_for(
                                    "button_click", timeout=20.0, check=select_button
                                )
                            )
                        except exceptions.TimeoutError:
                            content = f"ℹ - You have taken too long to answer, returning to the main menu - ℹ"
                            try:
                                await interaction.followup.send(content, ephemeral=True)
                            except NotFound:
                                await interaction.response.send_message(
                                    content, ephemeral=True
                                )

                            try:
                                await temp_msg.delete()
                            except NotFound:
                                pass

                            buying_houses = False
                            continue
                        else:
                            if (
                                temp_interaction.component.custom_id
                                == f"{temp_msg.id}_back"
                            ):
                                try:
                                    await temp_msg.delete()
                                except NotFound:
                                    pass

                                buying_houses = False
                                continue

                            family: List[int] = family_properties[
                                int(temp_interaction.component.custom_id.split("_")[1])
                                - 1
                            ]
                    else:
                        family: List[int] = family_properties[0]

                    if (
                        self.participants[self.current_turn].balance
                        < self.properties[family[0]].houses_price
                    ):
                        content = f"ℹ - You do not have enough money to buy a house from this family (price of a house: `${self.properties[family[0]].houses_price}`, your money: `${self.participants[self.current_turn].balance}` - ℹ"
                        try:
                            await interaction.followup.send(content, ephemeral=True)
                        except NotFound:
                            await interaction.response.send_message(
                                content, ephemeral=True
                            )
                        continue

                    buying_family_houses: bool = True

                    while buying_family_houses:
                        view: View = View(timeout=None)
                        endl: str = "\n"
                        em: Embed = Embed(
                            title="**Choice of the property...**",
                            description=f"On which property do you want to build an extra house (or hotel if 4 houses) (`${self.properties[family[0]].houses_price}` / house) ?\n\n{endl.join([f'{NUM2EMOJI[x + 1]} - ' + f'*`{self.properties[family[x]].name}`* - ' + (f'{self.properties[family[x]].houses} house' + ('s' if self.properties[family[x]].houses > 1 else '') if not self.properties[family[x]].hotel else 'an hotel') + f' - {NUM2EMOJI[x + 1]}' for x in range(len(family))])}",
                            color=self.properties[family[0]].color,
                        )
                        em.description += f"\n\n*🏘️ - All family properties at once (`${self.properties[family[0]].houses_price * len(family)}`) - 🏘️*"
                        em.description += "\n\n*🔙 - Return to the last menu - 🔙*"

                        used_emojies: List[str] = ["🔙"]
                        for x in range(1, len(family) + 1):
                            view.add_item(
                                Button(
                                    emoji=NUM2EMOJI[x],
                                    custom_id=f"{temp_msg.id}_{x}",
                                    disabled=self.properties[family[x - 1]].hotel
                                    or self.properties[family[x - 1]].houses
                                    > min(self.properties[p].houses for p in family),
                                )
                            )
                            used_emojies.append(NUM2EMOJI[x])

                        view.add_item(
                            Button(
                                emoji="🏘",
                                custom_id=f"{temp_msg.id}_all",
                                disabled=any(
                                    self.properties[family[x]].hotel
                                    or self.properties[family[x]].houses
                                    > min(self.properties[p].houses for p in family)
                                    for x in range(len(family))
                                ),
                            )
                        )
                        view.add_item(
                            Button(emoji="🔙", custom_id=f"{temp_msg.id}_back")
                        )

                        if not temp_msg:
                            try:
                                temp_msg: Message = await interaction.followup.send(
                                    embed=em,
                                    view=view,
                                    ephemeral=True,
                                )
                            except NotFound:
                                temp_msg: Message = (
                                    await interaction.response.send_message(
                                        embed=em,
                                        view=view,
                                        ephemeral=True,
                                    )
                                )
                        else:
                            await temp_msg.edit(embed=em, view=view)

                        try:
                            temp_interaction: MessageInteraction = (
                                await self.bot.wait_for(
                                    "button_click", timeout=20.0, check=select_button
                                )
                            )
                        except exceptions.TimeoutError:
                            content = f"ℹ - You have taken too long to answer, returning to the main menu - ℹ"
                            try:
                                await interaction.followup.send(content, ephemeral=True)
                            except NotFound:
                                await interaction.response.send_message(
                                    content, ephemeral=True
                                )

                            try:
                                await temp_msg.delete()
                            except NotFound:
                                pass

                            buying_family_houses = False
                            buying_houses = False
                            continue
                        else:
                            if (
                                temp_interaction.component.custom_id
                                == f"{temp_msg.id}_back"
                            ):
                                if len(family_properties) < 2:
                                    try:
                                        await temp_msg.delete()
                                    except NotFound:
                                        pass

                                    buying_houses = False

                                buying_family_houses = False
                                continue
                            elif (
                                temp_interaction.component.custom_id
                                == f"{temp_msg.id}_all"
                            ):
                                family_property: int = -1
                            else:
                                family_property: int = family[
                                    int(
                                        temp_interaction.component.custom_id.split("_")[
                                            1
                                        ]
                                    )
                                    - 1
                                ]

                        if family_property == -1:
                            if self.participants[
                                self.current_turn
                            ].balance < self.properties[family[0]].houses_price * len(
                                family
                            ):
                                content = (
                                    f"ℹ - You don't have enough money to buy {len(family)} houses for this family (price for {len(family)} house"
                                    + ("s" if len(family) > 1 else "")
                                    + f": `${self.properties[family[0]].houses_price * len(family)}`, your money: `${self.participants[self.current_turn].balance}` - ℹ"
                                )
                                try:
                                    await interaction.followup.send(
                                        content, ephemeral=True
                                    )
                                except NotFound:
                                    await interaction.response.send_message(
                                        content, ephemeral=True
                                    )
                                continue

                            await self.pay(
                                self.properties[family_property].houses_price
                                * len(family)
                            )

                            for p in family:
                                self.properties[p].buy_house()

                        else:
                            await self.pay(
                                self.properties[family_property].houses_price
                            )
                            self.properties[family_property].buy_house()

                msg = None
            elif interaction.component.custom_id == "monopoly_buy_mortgaged":
                mortgaged_properties: List[Case] = [
                    p for p in properties if p.mortgaged
                ]

                if not any(
                    ceil(m.price / 2) * 1.1
                    <= self.participants[self.current_turn].balance
                    for m in mortgaged_properties
                ):
                    content = f"ℹ - You don't have enough money to buy one of your mortgaged properties back - ℹ"
                    try:
                        await interaction.followup.send(content, ephemeral=True)
                    except NotFound:
                        await interaction.response.send_message(content, ephemeral=True)
                    continue

                buying_back: bool = True
                while buying_back:
                    content = f"📜 - Which mortgaged property(ies) would you like to buy back ? - 📜\n\n*You have 1 minute to make your choice*"
                    options: List[SelectOption] = []

                    for m_p in mortgaged_properties:
                        options.append(
                            SelectOption(
                                label=f"*`{m_p.name}`*",
                                value=str(m_p.location),
                                description=f"`- {ceil(m_p.price / 2) * 1.1}€`",
                                emoji=monopoly_families_color[m_p.color]
                                if isinstance(m_p, Property)
                                else None,
                            )
                        )

                    options.append(
                        SelectOption(
                            label="Return to main menu", value="back", emoji="🔙"
                        )
                    )

                    view = View(timeout=65.0)
                    view.add_item(
                        Select(
                            custom_id=f"monopoly_buy_back_mortgage_{self.current_turn}",
                            placeholder="Mortgaged property(ies) to be bought back",
                            min_values=1,
                            max_values=len(options),
                            options=options,
                        )
                    )

                    try:
                        temp_msg = await interaction.followup.send(
                            content, view=view, ephemeral=True
                        )
                    except NotFound:
                        temp_msg = await interaction.response.send_message(
                            content, view=view, ephemeral=True
                        )

                    def select_dropdown(interaction: MessageInteraction) -> bool:
                        return (
                            interaction.message.id == temp_msg.id
                            and interaction.author.id
                            == self.participants[self.current_turn].member.id
                        )

                    try:
                        temp_interaction: MessageInteraction = await self.bot.wait_for(
                            "dropdown", timeout=60.0, check=select_dropdown
                        )
                    except exceptions.TimeoutError:
                        content = f"ℹ - You did not answer the message quickly enough, return to the main menu - ℹ"
                        try:
                            await interaction.followup.send(content, ephemeral=True)
                        except NotFound:
                            await interaction.response.send_message(
                                content, ephemeral=True
                            )
                        buying_back = False
                        continue
                    else:
                        if "back" in temp_interaction.values:
                            content = f"🔙 - Return to main menu - 🔙"
                            try:
                                await interaction.followup.send(content, ephemeral=True)
                            except NotFound:
                                await interaction.response.send_message(
                                    content, ephemeral=True
                                )
                            buying_back = False
                            continue

                        total = sum(
                            ceil(self.properties[int(v)].price / 2) * 1.1
                            for v in temp_interaction.values
                        )
                        if self.participants[self.current_turn].balance < total:
                            content = f"ℹ - You do not have enough money to buy back all the properties you have selected, please select less properties (mortgage price of selected properties: `${total}`, your money: `${self.participants[self.current_turn].balance}`) - ℹ"
                            try:
                                await interaction.followup.send(content, ephemeral=True)
                            except NotFound:
                                await interaction.response.send_message(
                                    content, ephemeral=True
                                )
                            continue

                        for value in temp_interaction.values:
                            self.properties[int(value)].mortgaged = False

                        await self.pay(total)
                        buying_back = False

                msg = None
            elif interaction.component.custom_id == "monopoly_skull":
                content = f"💀 - Are you sure you want to leave the game? - 💀"
                view = View(timeout=25)
                view.add_item(Button(emoji="✅", custom_id="skull_valid"))
                view.add_item(Button(emoji="❌", custom_id="skull_nope"))

                try:
                    temp_msg = await interaction.followup.send(
                        content, view=view, ephemeral=True
                    )
                except NotFound:
                    temp_msg = await interaction.response.send_message(
                        content, view=view, ephemeral=True
                    )

                def select_button(interaction: MessageInteraction) -> bool:
                    return (
                        interaction.message.id == temp_msg.id
                        and interaction.author.id
                        == self.participants[self.current_turn].member.id
                    )

                try:
                    temp_interaction: MessageInteraction = await self.bot.wait_for(
                        "button_click", timeout=None, check=select_button
                    )
                except exceptions.TimeoutError:
                    content = f"✅ - The game was not abandoned because you did not react after the 20 second delay - ✅"
                    try:
                        await interaction.followup.send(content, ephemeral=True)
                    except NotFound:
                        await interaction.response.send_message(content, ephemeral=True)
                else:
                    await temp_interaction.response.defer()

                    if temp_interaction.component.custom_id == "skull_valid":
                        em = self.get_player_embed(self.current_turn)
                        em.title = f"**{self.participants[self.current_turn].name}**"
                        em.description = "Just gave up the game, so he gave all his savings and properties to the bank"
                        try:
                            await temp_interaction.followup.send(embed=em)
                        except NotFound:
                            await temp_interaction.response.send_message(embed=em)

                        self.participants[self.current_turn].bankrupted = True

                        if properties:
                            for x in self.properties:
                                if self.properties[x].owner == self.current_turn:
                                    self.properties[x].owner = -1

                        in_turn = False
                        msg = None
                    else:
                        content = f"✅ - The game has not been abandoned - ✅"
                        try:
                            await temp_interaction.followup.send(
                                content, ephemeral=True
                            )
                        except NotFound:
                            await temp_interaction.response.send_message(
                                content, ephemeral=True
                            )
            elif interaction.component.custom_id == "monopoly_end":
                in_turn = None

        if msg:
            try:
                await msg.delete()
            except NotFound:
                pass

        await self.next_turn()
        self.save()

    async def next_turn(self):
        self.current_turn += 1

        if self.current_turn >= len(self.participants):
            self.current_turn = 0

        while self.participants[self.current_turn].bankrupted:
            del self.participants[self.current_turn]

            if self.current_turn >= len(self.participants):
                self.current_turn = 0

        if len([p for p in self.participants if not p.bankrupted]) == 1:
            msg: Message = await self.game_message.channel.send(
                f"🎉🥳💰 - The player {self.participants[self.current_turn].member.mention} has just won the game - 💰🥳🎉"
            )
            return await msg.add_reaction("💥")

        self.bot.utils_class.task_launcher(
            self.turn,
            (),
            count=1,
        )

    async def auction(self, p_id: int, msg: Message = None):
        to_auction: Case = self.properties[p_id]
        bet: int = ceil(to_auction.price * 0.75)
        players: List[dict] = [
            {"player": p, "bet": bet, "passed": False}
            for p in self.participants
            if p.id != self.current_turn
        ]

        if len(players) == 1:
            return await self.game_message.channel.send(
                f"🪙 - Since there are only two players in this game the auction is cancelled, the property remains with the bank - 🪙",
            )

        shuffle(players)
        x: int = 0
        going: bool = True
        number_passed: int = 0
        winner: Optional[Player] = None
        property_embed: Embed = to_auction.get_embed()

        if not msg:
            msg: Message = await self.game_message.channel.send("** **")

        while going:
            view = View(timeout=25)
            view.add_item(Button(emoji="✅", custom_id="bid_valid"))
            view.add_item(Button(emoji="❌", custom_id="bid_nope"))

            await msg.edit(
                content=f"**🪙 - Auctions - {players[x]['player'].member.mention} - The stake in this property is `${bet}`, do you want to outbid ? - 🪙**\n\n*You have 20 seconds to choose*",
                view=view,
                embed=property_embed,
            )

            def select_button(interaction: MessageInteraction) -> bool:
                return (
                    interaction.message.id == msg.id
                    and interaction.author.id == players[x]["player"].member.id
                )

            chances: int = 1
            confirming: bool = True

            while confirming:
                try:
                    temp_interaction: MessageInteraction = await self.bot.wait_for(
                        "button_click", timeout=20.0, check=select_button
                    )
                except exceptions.TimeoutError:
                    if chances == 0:
                        await self.game_message.channel.send(
                            f"⚠️ - {self.participants[self.current_turn].member.mention} - You did not react quickly enough to the auction message and you have used up all your chances. Your turn is over. - ⚠️",
                            delete_after=10,
                        )
                        players[x]["passed"] = True
                        number_passed += 1
                        confirming = False
                        continue

                    await self.game_message.channel.send(
                        f"⚠️ - {self.participants[self.current_turn].member.mention} - You did not react quickly enough to the auction message. - ⚠\n\n**You have one last chance to react to the message, *20 seconds***",
                        delete_after=10,
                    )
                    chances -= 1
                else:
                    await temp_interaction.response.defer()

                    if temp_interaction.component.custom_id == "bid_nope":
                        await temp_interaction.followup.send(
                            f"🪙 - Auctions - {players[x]['player'].member.mention} - You have passed your turn - 🪙"
                        )
                        players[x]["passed"] = True
                        number_passed += 1

                    confirming = False

            if not players[x]["passed"]:
                old_bet: int = players[x]["bet"]
                chances: int = 1
                confirming: bool = True

                await temp_interaction.edit_original_message(
                    content=f"**🪙 - Auctions - {players[x]['player'].member.mention} - The stake of this property is `${bet}`, what will be the amount of your overbid ? - 🪙**\n\n*You have 20 seconds to send a message to this game room containing the new amount*",
                    embed=property_embed,
                )

                def confirm_message(message: Message) -> bool:
                    return (
                        message.channel.id == msg.channel.id
                        and message.author.id == players[x]["player"].member.id
                    )

                while confirming:
                    try:
                        message = await self.bot.wait_for(
                            "message", timeout=20.0, check=confirm_message
                        )
                    except exceptions.TimeoutError:
                        if chances == 0:
                            await self.game_message.channel.send(
                                f"⚠️ - {players[x]['player'].member.mention} - You have not sent any messages containing the amount of your bid and you have exhausted all your chances. Your turn is over. - ⚠️",
                                delete_after=10,
                            )
                            players[x]["passed"] = True
                            number_passed += 1
                            confirming = False
                            continue

                        await self.game_message.channel.send(
                            f"⚠️ - {players[x]['player'].member.mention} - You have not sent any messages containing the amount of your bid. - ⚠\n\n**You have one last chance to send your message, *20 seconds*.**",
                            delete_after=10,
                        )
                        chances -= 1
                    else:
                        number: list = findall(r"\d+", message.clean_content)

                        if not number:
                            await self.game_message.channel.send(
                                f"⚠️ - {players[x]['player'].member.mention} - The bid amount you specified is invalid. - ⚠\n\n**You have *20 seconds* to send a new message with a valid amount**",
                                delete_after=10,
                            )
                            continue

                        number: int = int(number[0])

                        if number <= old_bet:
                            await self.game_message.channel.send(
                                f"⚠️ - {players[x]['player'].member.mention} - The overbid amount must be higher than the current bid (amount: `${number}`, current stake: `${bet}`). - ⚠\n\n**You have *20 seconds* to send a new message with a higher amount than the current stake**️",
                                delete_after=20,
                            )
                        elif players[x]["player"].balance > number:
                            players[x]["bet"] = number
                            bet = number
                            confirming = False
                        else:
                            if chances == 0:
                                await self.game_message.channel.send(
                                    f"⚠️ - {players[x]['player'].member.mention} - You have provided an amount greater than you can afford (amount: `${number}`, your amount of money: `${players[x]['player'].balance}`) and you have exhausted all your chances. Your turn is over. - ⚠️",
                                    delete_after=20,
                                )
                                players[x]["passed"] = True
                                number_passed += 1
                                confirming = False
                                continue

                            await self.game_message.channel.send(
                                f"⚠️ - {players[x]['player'].member.mention} - You have provided an amount greater than you can afford (amount: `${number}`, your amount of money: `${players[x]['player'].balance}`). - ⚠\n\n**You have one last chance to send a new message with a lower amount, *20 seconds***️",
                                delete_after=20,
                            )
                            chances -= 1

            x += 1

            if x == len(players):
                x = 0

            if number_passed == len(players) - 1:
                for player in players:
                    if player["passed"]:
                        continue

                    winner = player["player"]
                    break

                going = False
            elif number_passed == len(players):
                winner = None
                going = False

        if winner:
            await msg.edit(
                content=f"**🪙 - Auctions - The winner of the auction is `{winner.name}` with an amount of `${bet}` - 🪙**",
                embed=property_embed,
            )

            await self.pay(bet, winner.id)
            self.properties[p_id].owner = winner.id
        else:
            await msg.edit(
                content=f"**🪙 - Auctions - No player has bid, so the property is sold to nobody - 🪙**",
                embed=property_embed,
            )

    async def buy(self, p_id: int):
        if self.participants[self.current_turn].balance < self.properties[p_id].price:
            await self.game_message.channel.send(
                f"ℹ️ - {self.participants[self.current_turn].member.mention} - You don't have enough money to buy the property. So the property is put up for auction. - ℹ️",
                delete_after=10,
            )
            return await self.auction(p_id)

        property_embed = self.properties[p_id].get_embed()

        view = View(timeout=25)
        view.add_item(Button(emoji="✅", custom_id="property_valid"))
        view.add_item(Button(emoji="❌", custom_id="property_nope"))

        msg: Message = await self.game_message.channel.send(
            f"**💶 - {self.participants[self.current_turn].member.mention} - Do you want to buy this property ? - 💶**\n\n*You have 20 seconds to choose*",
            view=view,
            embed=property_embed,
        )

        going: bool = True
        chances: int = 1

        def select_button(interaction: MessageInteraction) -> bool:
            return (
                interaction.message.id == msg.id
                and interaction.author.id
                == self.participants[self.current_turn].member.id
            )

        while going:
            try:
                temp_interaction: MessageInteraction = await self.bot.wait_for(
                    "button_click", timeout=None, check=select_button
                )
            except exceptions.TimeoutError:
                if chances == 0:
                    await self.game_message.channel.send(
                        f"⚠️ - {self.participants[self.current_turn].member.mention} - You didn't choose quickly enough during the sales message and you have exhausted all your chances. The property is therefore put up for auction. - ⚠️",
                        delete_after=20,
                    )
                    break

                await self.game_message.channel.send(
                    f"⚠️ - {self.participants[self.current_turn].member.mention} - You didn't choose quickly enough during the sales message. - ⚠\n\n**You have one last chance to choose, *20 seconds*.**",
                    delete_after=20,
                )
                chances -= 1
            else:
                await temp_interaction.response.defer()
                going = False

        if chances == 0:
            return await self.auction(p_id, msg)

        if temp_interaction.component.custom_id == "property_nope":
            await temp_interaction.followup.send(
                f"ℹ️ - {self.participants[self.current_turn].member.mention} - You have refused to buy this property. The property is therefore put up for auction. - ℹ️",
                delete_after=10,
            )
            return await self.auction(p_id, msg)

        await temp_interaction.edit_original_message(
            content=f"**✅ - {self.participants[self.current_turn].member.mention} - You are now the owner of this property - ✅**",
            view=None,
            embed=property_embed,
        )
        await self.pay(self.properties[p_id].price)
        self.properties[p_id].owner = self.current_turn

    async def mortgage(
        self, p_id: int, to_pay: int
    ):  # TODO handle more than 25 houses/properties to sell (in mortgage) <--- test this (seems alright at first look)
        mortgaging: bool = True
        msg: Message = None

        while mortgaging:
            page: int = 1
            choosing: bool = True

            while choosing:
                em = self.get_player_embed(p_id)
                em.title = f"**{self.participants[p_id].name} - You don't have enough money to pay**"
                em.description = f"**Which properties do you want to mortgage ?**\n\n**You can also sell houses (if you have any) (houses should be sold fairly among families)**\n\n**Your money →** `${self.participants[p_id].balance}` 🆚 `${to_pay}` **← What you owe**\n\n*You have 3 minutes to make your choice (otherwise you will be automatically bankrupted)*"

                properties: List[Case] = [
                    p
                    for p in self.properties.values()
                    if p.owner == p_id and not p.mortgaged
                ]
                options: List[SelectOption] = []
                families: List[int] = [
                    p.location
                    for p in properties
                    if not p.mortgaged and isinstance(p, Property)
                ]
                compatible_families: List[int] = [
                    x
                    for x in range(len(monopoly_families))
                    if monopoly_families[x] in families
                ]
                family_properties: List[List[int]] = []
                family_properties_chained: Iterator[int] = []

                if compatible_families:
                    family_properties = [
                        monopoly_families[x] for x in compatible_families
                    ]
                    family_properties_chained = chain.from_iterable(family_properties)

                counts = Counter(p.location for p in properties)
                properties.sort(key=lambda p: (-counts[p.location], p.location))
                x: int = 0

                for p in properties:
                    if isinstance(p, Property) and (p.hotel or p.houses):
                        options.append(
                            SelectOption(
                                label=f"1 house of {p.name}",
                                value=f"{p.location}_house",
                                description=f"+ {ceil(p.houses_price / 2)}€",
                                emoji=monopoly_families_color[p.color],
                            )
                        )

                        if p.hotel or p.houses > 1:
                            options.append(
                                SelectOption(
                                    label=f"All the houses of {p.name} (hotel included)",
                                    value=f"{p.location}_all",
                                    description=f"+ {ceil(p.houses_price / 2) * (5 if p.hotel else p.houses)}€",
                                    emoji=monopoly_families_color[p.color],
                                )
                            )
                    else:
                        options.append(
                            SelectOption(
                                label=f"{p.name}",
                                value=str(p.location),
                                description=f"+ {ceil(p.price / 2)}€",
                                emoji=monopoly_families_color[p.color],
                            )
                        )

                    x += 1

                options1 = None
                if len(options) > 24:
                    options1 = options[25::]
                    options = options[::24]
                else:
                    page = 1

                view = View(timeout=185.0)
                view.add_item(
                    Select(
                        custom_id=f"monopoly_mortgage_{p_id}",
                        placeholder="Choose the properties to mortgage or houses to sell (1 hotel = 5 houses)"
                        + (f" page {page}/2" if options1 else ""),
                        min_values=1,
                        max_values=len(options if page == 1 else options1)
                        + (1 if options1 else 0),
                        options=(options if page == 1 else options1)
                        + (
                            (
                                [
                                    SelectOption(
                                        label="Next page",
                                        value="next",
                                        description=f"You have only 24 options displayed out of the {len(options) + len(options1)}",
                                    )
                                ]
                                if page == 1
                                else [
                                    SelectOption(
                                        label="Previous page",
                                        value="before",
                                        description=f"You only have {len(options1)} options displayed out of the {len(options) + len(options1)}",
                                    )
                                ]
                            )
                            if options1
                            else []
                        ),
                    )
                )

                if not msg:
                    msg: Message = await self.game_message.channel.send(
                        embed=em, view=view
                    )
                else:
                    await msg.edit(embed=em, view=view)

                def select_dropdown(interaction: MessageInteraction) -> bool:
                    return (
                        interaction.message.id == msg.id
                        and interaction.author.id == self.participants[p_id].member.id
                    )

                try:
                    temp_interaction: MessageInteraction = await self.bot.wait_for(
                        "dropdown", timeout=180.0, check=select_dropdown
                    )
                except exceptions.TimeoutError:
                    await self.game_message.channel.send(
                        f"☠️ - {self.participants[p_id].member.mention} - You took too long to respond, so you're out of business - ☠️"
                    )

                    self.participants[p_id].bankrupted = True
                    mortgaging = False
                    continue
                else:
                    if "back" in temp_interaction.values:
                        page = 1
                        continue
                    elif "next" in temp_interaction.values:
                        page = 2
                        continue

                    await temp_interaction.response.defer()
                    white_list: List[str] = []
                    rejected_values: List[str] = []

                    for value in temp_interaction.values:
                        value_split: List[str] = []

                        if value not in white_list:
                            if "house" in value or "all" in value:
                                value_split = value.split("_")
                                number: int = int(value_split[0])

                                if (
                                    self.properties[number].location
                                    in family_properties_chained
                                ):
                                    family: List[int] = family_properties[
                                        [
                                            self.properties[number].location in f
                                            for f in family_properties
                                        ].index(True)
                                    ]
                                    if len(family) != sum(
                                        1
                                        for _p in family_properties_chained
                                        if _p in family
                                    ):
                                        if value_split[1] == "house":
                                            min_houses: int = min(
                                                self.properties[_p].houses
                                                for _p in family
                                            )

                                            if (
                                                not all(
                                                    self.properties[_p].houses
                                                    == min_houses
                                                    for _p in family
                                                )
                                                and self.properties[number].houses
                                                == min_houses
                                            ):
                                                rejected_values.append(value)
                                                continue
                                        else:
                                            rejected_values.append(value)
                                            continue
                                    else:
                                        white_list.extend(
                                            [f"{_p}_house" for _p in family]
                                        )
                            else:
                                number: int = int(value)
                        else:
                            if "_" in value:
                                value_split = value.split("_")
                                number: int = int(value_split[0])
                            else:
                                number: int = int(value)

                        if value_split:
                            if value_split[1] == "house":
                                self.properties[number].sell_house()
                                self.participants[p_id].balance += ceil(
                                    self.properties[number].houses_price / 2
                                )
                            else:
                                self.participants[p_id].balance += self.properties[
                                    number
                                ].houses_price * (
                                    self.properties[number].houses
                                    if not self.properties[number].hotel
                                    else 5
                                )
                                self.properties[number].houses = 0
                                self.properties[number].hotel = False
                        else:
                            self.properties[number].mortgaged = True
                            self.participants[p_id].balance += ceil(
                                self.properties[number].price / 2
                            )

                    content: str = (
                        "💸 - The properties and houses you have selected have been sold"
                    )

                    if rejected_values:
                        content += "\n\n**You cannot sell:**\n"
                        for value in rejected_values:
                            value_split = value.split("_")
                            p: Property = self.properties[int(value_split[0])]
                            content += f"\n{p.name} car " + (
                                "the houses of this family were not sold fairly"
                                if value_split[0] == "house"
                                else "to sell all the houses in a family you have to select the whole family"
                            )

                    content += " - 💸"

                    try:
                        await temp_interaction.followup.send(content, ephemeral=True)
                    except NotFound:
                        await temp_interaction.response.send_message(
                            content, ephemeral=True
                        )

                    if self.participants[p_id].balance >= to_pay:
                        choosing = False
                        mortgaging = False

        if not self.participants[p_id].bankrupted:
            await temp_interaction.followup.send(
                f"💸 - You have reached the necessary amount of money to be able to pay your debts - 💸",
                ephemeral=True,
            )

    async def pay(self, amount: int, p_id: int = None, to_pay: int = None):
        player_id = p_id or self.current_turn

        em = self.get_player_embed(player_id)

        em.title = f"**{self.participants[player_id].name}**"

        if self.participants[player_id].balance >= amount:
            self.participants[player_id].balance -= amount
            em.description = f"Just gave `${amount}` to " + (
                f"`{self.participants[to_pay].name}`"
                if to_pay is not None
                else "the bank"
            )
        else:
            properties: List[Case] = [
                p for p in self.properties.values() if p.owner == player_id
            ]

            if (
                not properties
                or sum(
                    [
                        ceil(p.price / 2)
                        + (
                            (ceil(p.houses_price / 2) * (5 if p.hotel else p.houses))
                            if isinstance(p, Property)
                            else 0
                        )
                        for p in properties
                        if not p.mortgaged
                    ]
                )
                + self.participants[player_id].balance
                < amount
            ):
                self.participants[player_id].bankrupted = True
            else:
                await self.mortgage(player_id, amount)

                if not self.participants[player_id].bankrupted:
                    em.description = f"Has just sold goods to pay `${amount}` to " + (
                        f"`{self.participants[to_pay].name}`"
                        if to_pay is not None
                        else "the bank"
                    )

            if self.participants[player_id].bankrupted:
                if to_pay is not None:
                    for x in self.properties:
                        if self.properties[x].owner == player_id:
                            if isinstance(self.properties[x], Property) and (
                                self.properties[x].houses or self.properties[x].hotel
                            ):
                                self.participants[to_pay].balance += self.properties[
                                    x
                                ].houses_price * (
                                    self.properties[x].houses
                                    if not self.properties[x].hotel
                                    else 5
                                )
                                self.properties[x].houses = 0
                                self.properties[x].hotel = False

                            self.properties[x].owner = to_pay

                    self.participants[to_pay].balance += self.participants[
                        player_id
                    ].balance
                    self.participants[player_id].balance = 0
                else:
                    for x in self.properties:
                        if self.properties[x].owner == player_id:
                            if isinstance(self.properties[x], Property):
                                self.properties[x].houses = 0
                                self.properties[x].hotel = False

                            self.properties[x].owner = -1

                em.description = (
                    f"Just lost the game, so he gave all his savings and properties to "
                    + (
                        f"`{self.participants[to_pay].name}`"
                        if to_pay is not None
                        else "the bank"
                    )
                )

        await self.game_message.channel.send(embed=em)

    async def draw_community_chest_card(self):
        card: SpecialCard = next(self.community_chest_cards)

        await self.game_message.channel.send(embed=card.get_embed())

        if card.id == 0:
            await self.move(40, exact=True)
        elif card.id == 1:
            self.participants[self.current_turn].balance += 200
        elif card.id in (2, 11):
            await self.pay(50)
        elif card.id == 3:
            self.participants[self.current_turn].balance += 50
        elif card.id == 4:
            self.participants[self.current_turn].special_cards.append(card)
        elif card.id == 5:
            self.participants[self.current_turn].in_jail = True
            await self.move(10, exact=True)
        elif card.id == 6:
            if self.participants[self.current_turn].location > 1:
                await self.move(41, exact=True)
            else:
                await self.move(1, exact=True)
        elif card.id in (7, 15):
            self.participants[self.current_turn].balance += 100
        elif card.id == 8:
            for x in range(len(self.participants)):
                if x != self.current_turn:
                    await self.pay(10, p_id=x, to_pay=self.current_turn)
                    self.participants[self.current_turn].balance += 10
        elif card.id == 9:
            self.participants[self.current_turn].balance += 20
        elif card.id == 10:
            self.participants[self.current_turn].balance += 25
        elif card.id == 12:
            pass
        elif card.id == 13:
            if self.participants[self.current_turn].location < 5:
                await self.move(5, exact=True)
            elif self.participants[self.current_turn].location < 15:
                await self.move(15, exact=True)
            elif self.participants[self.current_turn].location < 25:
                await self.move(25, exact=True)
            elif self.participants[self.current_turn].location < 35:
                await self.move(35, exact=True)
            elif self.participants[self.current_turn].location < 40:
                await self.move(45, exact=True)
        elif card.id == 14:
            self.participants[self.current_turn].balance += 10

    async def draw_chance_card(self):
        card: SpecialCard = next(self.chance_cards)

        await self.game_message.channel.send(embed=card.get_embed())

        if card.id == 0:
            await self.move(39, exact=True)
        elif card.id == 1:
            await self.move(40, exact=True)
        elif card.id == 2:
            if self.participants[self.current_turn].location > 24:
                await self.move(64, exact=True)
            else:
                await self.move(24, exact=True)
        elif card.id == 3:
            if self.participants[self.current_turn].location > 11:
                await self.move(51, exact=True)
            else:
                await self.move(11, exact=True)
        elif card.id in (4, 11):
            properties: List[Property] = [
                p
                for p in self.properties.values()
                if isinstance(p, Property) and p.owner == self.current_turn
            ]
            houses = 0
            hotels = 0

            for p in properties:
                if p.houses:
                    houses += p.houses
                elif p.hotel:
                    hotels += 1

            await self.pay(
                (40 if card.id == 4 else 25) * houses
                + ((115 if card.id == 4 else 100) * hotels)
            )
        elif card.id == 5:
            if self.participants[self.current_turn].location > 15:
                await self.move(55, exact=True)
            else:
                await self.move(15, exact=True)
        elif card.id == 6:
            self.participants[self.current_turn].balance += 100
        elif card.id == 7:
            self.participants[self.current_turn].balance += 50
        elif card.id == 8:
            self.participants[self.current_turn].special_cards.append(card)
        elif card.id == 9:
            if self.participants[self.current_turn].location > 2:
                await self.move(-3)
            else:
                await self.move(self.participants[self.current_turn].location + 37)
        elif card.id == 10:
            self.participants[self.current_turn].in_jail = True
            await self.move(10, exact=True)
        elif card.id == 12:
            await self.pay(15)
        elif card.id == 13:
            await self.pay(150)
        elif card.id == 14:
            await self.pay(20)
        elif card.id == 15:
            self.participants[self.current_turn].balance += 150

    def get_house_location(self, p: Property, x: int = 0):
        location = board_places_houses[
            1 if p.location < 10 or 20 < p.location < 30 else 11
        ]["hotel"][x]

        if p.location < 10:
            location = (
                location[0] - (102 * (p.location - 1)),
                location[1],
            )
        elif p.location < 20:
            location = (
                location[0],
                location[1] - (102 * (p.location - 11)),
            )
        elif p.location < 30:
            location = (
                (
                    self.board.width
                    - location[0]
                    + (102 * (p.location - 21))
                    - (self.hotel if p.hotel else self.green_house).width
                ),
                self.board.height
                - location[1]
                - (self.hotel if p.hotel else self.green_house).height,
            )
        elif p.location < 40:
            location = (
                self.board.width
                - location[0]
                - (self.hotel if p.hotel else self.green_house).width,
                self.board.height
                - (
                    location[1]
                    - (102 * (p.location - 31))
                    + (self.hotel if p.hotel else self.green_house).height
                ),
            )

        return location

    async def move(self, dice_value: int, exact: bool = False):
        if exact:
            new_location: int = dice_value
        else:
            new_location: int = (
                self.participants[self.current_turn].location + dice_value
            )

        if new_location > 39:
            new_location = new_location - 40
            self.participants[self.current_turn].balance += 200

        self.participants[self.current_turn].location = new_location

        if new_location in (2, 17, 33):
            await self.draw_community_chest_card()
        elif new_location in (7, 22, 36):
            await self.draw_chance_card()

        if new_location == 30:
            self.participants[self.current_turn].in_jail = True
            self.participants[self.current_turn].location = 10

        locations: List[int] = [p.location for p in self.participants]
        players_avatar: dict = {}
        back_im = self.default_board.copy()

        for x in range(len(self.participants)):
            same_location: int = locations.count(locations[x])
            case: int = self.participants[x].location

            if case not in players_avatar:
                players_avatar[case] = []

            if len(locations) != len(set(locations)) and same_location > 1:
                if case in (0, 20):
                    players_avatar[case].append(
                        {
                            "avatar": self.participants[x]
                            .avatar.copy()
                            .resize(
                                board_places[0][same_location]["size"], Image.ANTIALIAS
                            )
                        }
                    )
                elif case == 10:
                    in_jails: int = sum(
                        [
                            1
                            for p in self.participants
                            if p.in_jail and p.location == case
                        ]
                    )

                    if self.participants[x].in_jail:
                        same_location = in_jails
                    else:
                        same_location = same_location - in_jails

                    players_avatar[case].append(
                        {
                            "avatar": self.participants[x]
                            .avatar.copy()
                            .resize(
                                board_places[case][
                                    "jail"
                                    if self.participants[x].in_jail
                                    else "no_jail"
                                ][same_location]["size"],
                                Image.ANTIALIAS,
                            ),
                            "jail": self.participants[x].in_jail,
                        }
                    )
                else:
                    players_avatar[case].append(
                        {
                            "avatar": self.participants[x]
                            .avatar.copy()
                            .resize(
                                board_places[1][same_location]["size"], Image.ANTIALIAS
                            )
                        }
                    )
            else:
                if case == 10:
                    players_avatar[case].append(
                        {
                            "avatar": self.participants[x]
                            .avatar.copy()
                            .resize(
                                board_places[case][
                                    "jail"
                                    if self.participants[x].in_jail
                                    else "no_jail"
                                ][1]["size"],
                                Image.ANTIALIAS,
                            ),
                            "jail": self.participants[x].in_jail,
                        }
                    )
                else:
                    players_avatar[case].append({"avatar": self.participants[x].avatar})

        for case, players in players_avatar.items():
            for x in range(len(players)):
                if case == 0:
                    back_im.paste(
                        players[x]["avatar"],
                        board_places[0][len(players)]["locations"][x],
                        players[x]["avatar"],
                    )
                elif case < 10:
                    back_im.paste(
                        players[x]["avatar"],
                        (
                            board_places[1][len(players)]["locations"][x][0]
                            - (102 * (case - 1)),
                            board_places[1][len(players)]["locations"][x][1],
                        ),
                        players[x]["avatar"],
                    )
                elif case == 10:
                    back_im.paste(
                        players[x]["avatar"],
                        board_places[case][
                            "jail"
                            if "jail" in players[x] and players[x]["jail"]
                            else "no_jail"
                        ][len(players)]["locations"][x],
                        players[x]["avatar"],
                    )
                elif case < 20:
                    back_im.paste(
                        players[x]["avatar"],
                        (
                            board_places[11][len(players)]["locations"][x][0],
                            board_places[11][len(players)]["locations"][x][1]
                            - (102 * (case - 11)),
                        ),
                        players[x]["avatar"],
                    )
                elif case == 20:
                    back_im.paste(
                        players[x]["avatar"],
                        board_places[case][len(players)]["locations"][x],
                        players[x]["avatar"],
                    )
                elif case < 30:
                    back_im.paste(
                        players[x]["avatar"],
                        (
                            (
                                back_im.width
                                - board_places[1][len(players)]["locations"][x][0]
                                + (102 * (case - 21))
                                - players[x]["avatar"].width
                            ),
                            back_im.height
                            - board_places[1][len(players)]["locations"][x][1]
                            - players[x]["avatar"].height,
                        ),
                        players[x]["avatar"],
                    )
                elif case < 40:
                    back_im.paste(
                        players[x]["avatar"],
                        (
                            back_im.width
                            - board_places[11][len(players)]["locations"][x][0]
                            - players[x]["avatar"].width,
                            back_im.height
                            - (
                                board_places[11][len(players)]["locations"][x][1]
                                - (102 * (case - 31))
                                + players[x]["avatar"].height
                            ),
                        ),
                        players[x]["avatar"],
                    )

        for p in self.properties:
            if not isinstance(p, Property) or p.hotel or not p.houses:
                continue

            if p.hotel:
                back_im.paste(self.hotel, self.get_house_location(p), self.hotel)
            else:
                for x in range(p.houses):
                    back_im.paste(
                        self.green_house,
                        self.get_house_location(p, x),
                        self.green_house,
                    )

        self.board = back_im
        board_bytes: BytesIO = BytesIO()
        back_im.save(board_bytes, format="JPEG")
        board_bytes.seek(0)
        self.game_message = await self.game_message.channel.send(
            files=[
                File(
                    board_bytes, filename=f"monopoly_{self.game_message.channel.id}.jpg"
                )
            ],
        )

        if new_location in (0, 10, 20, 30, 2, 17, 33, 7, 22, 36):
            pass
        elif new_location == 4:
            await self.pay(200)
        elif new_location == 38:
            await self.pay(100)
        else:
            if self.properties[new_location].owner != -1 and (
                self.properties[new_location].mortgaged
                or self.properties[new_location].owner == self.current_turn
            ):
                pass
            elif self.properties[new_location].owner != -1:
                if isinstance(self.properties[new_location], Property):
                    rent = self.properties[new_location].get_rent()

                    if (
                        self.properties[new_location].houses == 0
                        and not self.properties[new_location].hotel
                    ):
                        families: List[int] = [
                            p.location
                            for p in self.properties.values()
                            if isinstance(p, Property)
                            and p.owner == self.properties[new_location].owner
                        ]
                        compatible_families: List[int] = [
                            x
                            for x in range(len(monopoly_families))
                            if monopoly_families[x] in families
                        ]

                        if compatible_families:
                            family_properties: List[List[int]] = [
                                monopoly_families[x] for x in compatible_families
                            ]

                            if new_location in chain.from_iterable(family_properties):
                                rent *= 2

                elif isinstance(self.properties[new_location], Station):
                    rent = self.properties[new_location].get_rent(
                        sum(
                            [
                                1
                                for x in range(5, 45, 10)
                                if self.properties[x].owner
                                == self.properties[new_location].owner
                            ]
                        )
                    )
                else:
                    rent = self.properties[new_location].get_rent(
                        dice_value,
                        int(
                            self.properties[12].owner
                            == self.properties[new_location].owner
                        )
                        + int(
                            self.properties[28].owner
                            == self.properties[new_location].owner
                        ),
                    )

                await self.pay(rent, to_pay=self.properties[new_location].owner)

                if not self.participants[self.current_turn].bankrupted:
                    self.participants[
                        self.properties[new_location].owner
                    ].balance += rent
            else:
                await self.buy(self.participants[self.current_turn].location)
