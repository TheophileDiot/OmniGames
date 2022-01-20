from collections import OrderedDict
from typing import Union

from data import Utils


class Config:
    def __init__(self, model) -> None:
        self.model = model
        self.innerpath = "config"

    """ GAMES CATEGORY """

    @Utils.resolve_guild_path
    def set_games_category(self, guild_id: int, category_id: Union[int, None]) -> None:
        self.model.update(f"{self.path}", args={"games_category_id": category_id})

    @Utils.resolve_guild_path
    def get_games_category(self, guild_id: int) -> int:
        return self.model.get(f"{self.path}/games_category_id")
