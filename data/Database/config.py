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

    """ GUILD DJS """

    @Utils.resolve_guild_path
    def add_dj(self, guild_id: int, dj_id: int, dj_name: str, dj_type: str) -> None:
        self.model.create(
            f"{self.path}/djs/{dj_id}",
            args={"name": dj_name, "type": dj_type},
        )

    @Utils.resolve_guild_path
    def remove_dj(self, guild_id: int, dj_id: int) -> None:
        self.model.delete(f"{self.path}/djs/{dj_id}")

    @Utils.resolve_guild_path
    def purge_djs(self, guild_id: int) -> None:
        self.model.delete(f"{self.path}/djs")

    @Utils.resolve_guild_path
    def get_djs(self, guild_id: int) -> OrderedDict:
        return self.model.get(f"{self.path}/djs")
