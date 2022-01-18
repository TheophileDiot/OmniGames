from collections import OrderedDict

from data import Utils


class User:
    def __init__(self, model, bot) -> None:
        self.model = model
        self.innerpath = "users"
        self.bot = bot

    """ CHECKS """

    def __check_user_exists(function):
        """Checks if the user exists in the database

        Keyword arguments:
        function -- the function to be invoked after the check
        """

        def check(self, guild_id: int, user_id: int, *args, **kargs):
            if not self.model.get(f"{self.path}/{user_id}"):
                self.create_user(
                    guild_id,
                    user_id,
                    f"{self.bot.get_guild(guild_id).get_member(user_id)}",
                )
            return function(self, guild_id, user_id, *args, **kargs)

        return check

    """ CREATION & DELETION """

    @Utils.resolve_guild_path
    def create_user(self, guild_id: int, _id: int, name: str) -> None:
        self.model.create(
            f"{self.path}/{_id}",
            args={
                "id": _id,
                "name": name,
            },
        )

    @Utils.resolve_guild_path
    @__check_user_exists
    def update_user(self, guild_id: int, _id: int, name: str) -> None:
        self.model.update(
            f"{self.path}/{_id}",
            args={
                "name": name,
            },
        )

    """ GETTERS """

    @Utils.resolve_guild_path
    @__check_user_exists
    def get_user(self, guild_id: int, _id: int) -> OrderedDict:
        return self.model.get(f"{self.path}/{_id}")

    @Utils.resolve_guild_path
    def get_users(self, guild_id: int) -> OrderedDict:
        return self.model.get(f"{self.path}")
