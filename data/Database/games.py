from collections import OrderedDict

from data import Utils


class Games:
    def __init__(self, model, bot) -> None:
        self.model = model
        self.innerpath = "games"
        self.bot = bot

    """ CREATION & DELETION """

    @Utils.resolve_guild_path
    def create_game(
        self,
        guild_id: int,
        channel_id: int,
        game_id: int,
        players: dict,
        game_type: str,
        others=None,
    ) -> None:
        args = {
            "game_id": game_id,
            "players": {k: v.id for k, v in players.items()},
            "game_type": game_type,
        }

        if others:
            if "author" in others:
                others["author"] = others["author"].id

            if "players" in others:
                others["players"] = {k: v.id for k, v in others["players"].items()}

            args = args | others

        self.model.create(
            f"{self.path}/{channel_id}",
            args=args,
        )

    @Utils.resolve_guild_path
    def update_game(
        self,
        guild_id: int,
        channel_id: int,
        args,
    ):
        if "author" in args and not isinstance(args["author"], int):
            args["author"] = args["author"].id

        if "players" in args:
            args["players"] = {k: v.id for k, v in args["players"].items()}

        self.model.update(
            f"{self.path}/{channel_id}",
            args=args,
        )

    @Utils.resolve_guild_path
    def remove_game(self, guild_id: int, channel_id: int) -> None:
        self.model.delete(f"{self.path}/{channel_id}")

    """ OTHERS """

    @Utils.resolve_guild_path
    def set_game(self, guild_id: int, channel_id: int, _id: int) -> OrderedDict:
        return self.model.update(f"{self.path}/{channel_id}", args={"game_id": _id})

    @Utils.resolve_guild_path
    def get_game(self, guild_id: int, channel_id: int, _id: int) -> OrderedDict:
        return self.model.get(f"{self.path}/{channel_id}/{_id}")

    @Utils.resolve_guild_path
    def get_game_channel(self, guild_id: int, channel_id: int) -> OrderedDict:
        return self.model.get(f"{self.path}/{channel_id}")

    @Utils.resolve_guild_path
    def get_game_channels(self, guild_id: int) -> OrderedDict:
        return self.model.get(f"{self.path}")
