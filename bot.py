# -----------------------------------------------------------
# A discord bot that has every games you want in a discord server !
#
# (C) 2022 TheophileDiot
# Released under MIT License (MIT)
# email theophile.diot900@gmail.com
# linting: black
# -----------------------------------------------------------
from asyncio import get_event_loop
from datetime import date
from itertools import chain
from logging import basicConfig, DEBUG, error, info
from os import getenv, listdir, makedirs, name, path, system
from sys import exc_info
from traceback import format_exc
from typing import Union

from aiohttp import ClientSession
from disnake import (
    ApplicationCommandInteraction,
    Colour,
    Forbidden,
    Intents,
    Member,
    Message,
    OptionType,
)
from disnake.ext.commands import Bot, Context
from disnake.ext.commands.errors import (
    BotMissingPermissions,
    BadArgument,
    BadUnionArgument,
    CheckFailure,
    CommandOnCooldown,
    MaxConcurrencyReached,
    MissingAnyRole,
    MissingRequiredArgument,
    MissingPermissions,
    NoPrivateMessage,
    NotOwner,
)
from dotenv import load_dotenv


def get_qualified_name_from_interaction(inter: ApplicationCommandInteraction) -> str:
    cmd_name = inter.data.name
    options = bool(inter.data.options)
    data = inter.data

    while options:
        data = data.options[0]

        if data.type not in (OptionType.sub_command_group, OptionType.sub_command):
            options = False
            continue

        cmd_name += f" {data.name}"

        if not data.options:
            options = False

    return cmd_name


class OmniGames(Bot):
    def __init__(self, **kwargs):
        """Initialize the bot"""
        super().__init__(
            command_prefix="",
            intents=self.get_intents(),
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            self_bot=False,
            sync_commands_debug=True,
            test_guilds=[872500404540280893]
            if getenv("ENV") == "DEVELOPMENT"
            else [914948087888363590],
            **kwargs,
        )

        dirs = chain.from_iterable(
            [
                [
                    f"{f}.{_f.replace('.py', '')}"
                    if path.isfile(path.join("cogs", f, _f))
                    else f"{f}.{_f}"
                    for _f in listdir(path.join("cogs", f))
                    if _f not in "__pycache__"
                ]
                for f in listdir("cogs")
                if path.isdir(path.join("cogs", f))
                and f not in ("__init__", "__pycache__")
            ]
        )
        self._extensions = [f for f in dirs]
        self.load_extensions()
        self.session = ClientSession(loop=self.loop)

        self.starting = True
        self.last_check = None
        self.model = Model.setup()

        self.utils_class = Utils(self)
        self.main_repo = Main(self.model)
        self.config_repo = Config(self.model)
        self.user_repo = User(self.model, self)
        self.games_repo = Games(self.model, self)
        print("Database successfully initialized.")
        info("Database loaded")

        self.configs = {}
        self.color = Colour(BOT_COLOR) or self.user.color

    """ EVENTS """

    async def on_slash_command_error(
        self, inter: ApplicationCommandInteraction, _error
    ) -> None:
        """Override default slash command error handler to log errors and prevent the bot from crashing."""
        await self.handle_error(inter, _error)

    async def on_error(self, event, *args, **kwargs):
        error(
            f"{exc_info()[0]}\n{exc_info()[1]}\n{exc_info()[2]}\n\n{format_exc()}\n\nIn guild `{args[0].guild if args else 'not found'}` (ID: `{args[0].guild.id if args else 'not found'}`)"
        )
        print(
            f"{exc_info()[0]}\n{exc_info()[1]}\n{exc_info()[2]}\n\n{format_exc()}\n\nIn guild `{args[0].guild if args else 'not found'}` (ID: `{args[0].guild.id if args else 'not found'}`)"
        )
        _error = exc_info()[1]

        if isinstance(_error, Forbidden):
            try:
                await self.utils_class.send_message_to_owner(
                    _error.text, args[0].guild.id
                )
            except AttributeError:
                await self.utils_class.send_message_to_owner(
                    _error.text, args[0].guild_id
                )
        else:
            # Log that the bot had an error
            source = args[0]

            if isinstance(source, Member):
                await source.send(
                    f"⚠️ - An error happened, the developer has been informed about this! If you want help contact `Batgregate900#2562`"
                )
            else:
                await source.response.send_message(
                    f"⚠️ - An error happened, the developer has been informed about this! If you want help contact `Batgregate900#2562`",
                    ephemeral=True,
                )

            bot_owner = self.owner

            if not bot_owner:
                bot_owner = await self.fetch_user(
                    int(
                        self.owner_id or list(self.owner_ids)[0]
                        if self.owner_ids
                        else self.get_ownerid()
                    )
                )

            return await bot_owner.send(
                f"{exc_info()[0]}\n{exc_info()[1]}\n{exc_info()[2]}\n\n{format_exc()}\n\nIn guild `{args[0].guild if args else 'not found'}` (ID: `{args[0].guild.id if args else 'not found'}`)"
            )

    """ METHOD(S) """

    async def handle_error(self, source: ApplicationCommandInteraction, _error):
        cmd_name = get_qualified_name_from_interaction(source)

        if isinstance(_error, NoPrivateMessage):
            resp = f"⚠️ - this command is deactivated outside of guilds!"
        elif isinstance(_error, MissingRequiredArgument):
            resp = f"ℹ️ - The `{cmd_name}` command is missing an argument! Missing parameter: `{_error.param.name}`."
        elif isinstance(_error, MissingPermissions):
            resp = f"⛔ - You do not have the necessary perms to run this command! Required perms: `{', '.join(_error.missing_permissions)}`"
        elif isinstance(_error, MissingAnyRole):
            resp = f"⛔ - You do not have one of the required roles to run this command! One of these roles is required: `{', '.join(_error.missing_roles)}`"
        elif isinstance(_error, NotOwner):
            resp = f"⛔ - The `{cmd_name}` command is reserved for the bot owner!"
        elif isinstance(_error, BotMissingPermissions):
            resp = f"⛔ - I don't have the necessary perms to run this command! Required perms: `{', '.join(_error.missing_permissions)}`"
        elif isinstance(_error, CommandOnCooldown):
            resp = f"ℹ️ - The `{cmd_name}` command is currently in cooldown, please try again in `{'%.2f' % _error.retry_after}` seconds, this command can be used `{_error.cooldown.rate}` times every `{_error.cooldown.per}` seconds."
        elif isinstance(_error, MaxConcurrencyReached):
            resp = f"ℹ️ - The `{cmd_name}` command has too many executions in progress (`{_error.number}` executions), please try again in a few seconds, this command can only be used a maximum of `{_error.number}` times simultaneously."
        elif isinstance(_error, BadArgument):
            resp = f"⚠️ - Please provide valid arguments!"
        elif isinstance(_error, BadUnionArgument):
            resp = f"⚠️ - Please provide valid arguments! The argument `{_error.param.name}` should be within these types: ({', '.join([f'`{c.__name__}`' for c in _error.converters])})!"
        elif isinstance(_error, CheckFailure):
            if self.last_check == "moderator":
                resp = f"⛔ - {source.author.mention} - You must be an administrator of this server to use this command!"
            else:
                raise _error

            self.last_check = None
        else:
            raise _error.original

        try:
            await source.response.send_message(resp, ephemeral=True)
        except Forbidden as f:
            f.text = f"⚠️ - I don't have the right permissions to send messages in the channel {source.channel.mention} (message (replying to {source.author}): `{resp}`)!"
            raise

    def load_extensions(self, cogs: Context = None, path: str = "cogs."):
        """Loads the default set of extensions or a seperate one if given"""
        for extension in cogs or self._extensions:
            try:
                self.load_extension(f"{path}{extension}")
                print(f"Loaded cog: {extension}")
            except Exception as e:
                print(f"LoadError: {extension}\n" f"{type(e).__name__}: {e}")
                error(f"LoadError: {extension}\n" f"{type(e).__name__}: {e}")
        info("All cogs loaded")

    @staticmethod
    def get_ownerid():
        """Returns the owner id."""
        return getenv("OWNER_ID") or OWNER_ID or 559057271737548810

    @staticmethod
    def get_intents():
        """Configure the intents for the bot"""
        intents = Intents(
            guilds=True,
            guild_messages=True,
            guild_reactions=True,
            members=True,
        )
        return intents

    @classmethod
    async def setup(self, **kwargs):
        """Setup the bot with a token from data.constants or the .env file"""
        bot = self()
        try:
            await bot.start(
                getenv("BOT_TOKEN_DEV")
                if getenv("ENV") == "DEVELOPMENT"
                else BOT_TOKEN or getenv("BOT_TOKEN"),
                **kwargs,
            )
        except KeyboardInterrupt:
            await bot.close()


if __name__ == "__main__":
    from data import (
        Model,
        Utils,
        BOT_TOKEN,
        BOT_PREFIX,
        BOT_COLOR,
        OWNER_ID,
    )
    from data.Database import Main, Config, Games, User

    load_dotenv(path.join(".", ".env"))  # Load data from the .env file

    if not path.exists("logs"):  # Create logs folder if it doesn't exist
        makedirs("logs")

    basicConfig(
        filename=f"logs/{date.today().strftime('%d-%m-%Y_')}app.log",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
        level=DEBUG,
    )  # Configure the logging

    system("cls" if name == "nt" else "clear")
    print("OmniGames is starting...")
    loop = get_event_loop()
    try:
        loop.run_until_complete(OmniGames.setup())  # Starts the bot
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
