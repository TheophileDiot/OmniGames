from collections import OrderedDict
from math import floor
from re import findall
from typing import Union, List, Optional

from disnake import (
    ApplicationCommandInteraction,
    Embed,
    Forbidden,
    Guild,
    Message,
    Member,
    NotFound,
    Role,
    TextChannel,
    VoiceChannel,
)
from disnake.ext.commands import Context, check
from disnake.ext.commands.errors import BadArgument
from disnake.ext.tasks import loop

from bot import OmniGames

NUM2EMOJI = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣"}


def check_for_win_fourinarow(board) -> bool:
    board = [[col for col in row[1:-1]] for row in board[0:-1]]
    for x in range(len(board)):
        for y in range(len(board[0])):
            if x + 3 < 7:
                if (
                    board[x][y] != "⚪"
                    and board[x][y] == board[x + 1][y]
                    and board[x + 1][y] == board[x + 2][y]
                    and board[x + 2][y] == board[x + 3][y]
                ):
                    return True
            if y + 3 < 7:
                if (
                    board[x][y] != "⚪"
                    and board[x][y] == board[x][y + 1]
                    and board[x][y + 1] == board[x][y + 2]
                    and board[x][y + 2] == board[x][y + 3]
                ):
                    return True
            if x + 3 < 7 and y + 3 < 7:
                if (
                    board[x][y] != "⚪"
                    and board[x][y] == board[x + 1][y + 1]
                    and board[x + 1][y + 1] == board[x + 2][y + 2]
                    and board[x + 2][y + 2] == board[x + 3][y + 3]
                ):
                    return True
            if x - 3 > 0 and y + 3 < 7:
                if (
                    board[x][y] != "⚪"
                    and board[x][y] == board[x - 1][y + 1]
                    and board[x - 1][y + 1] == board[x - 2][y + 2]
                    and board[x - 2][y + 2] == board[x - 3][y + 3]
                ):
                    return True

    return False


def check_for_win_tictactoe(board: list) -> bool or None:
    win = (
        board[0][0] == board[0][1]
        and board[0][1] == board[0][2]
        or board[1][0] == board[0][1]
        and board[0][1] == board[0][2]
        or board[2][0] == board[2][1]
        and board[2][1] == board[2][2]
        or board[0][0] == board[1][0]
        and board[1][0] == board[2][0]
        or board[0][1] == board[1][1]
        and board[1][1] == board[2][1]
        or board[0][2] == board[1][2]
        and board[1][2] == board[2][2]
        or board[0][0] == board[1][1]
        and board[1][1] == board[2][2]
        or board[0][2] == board[1][1]
        and board[1][1] == board[2][0]
    )

    if not win:
        return None
    else:
        return True


class Utils:
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    async def send_message_to_owner(
        self, message: str, guild_id: int, em: Embed = None
    ):
        """This method send a message to the bot owner"""
        guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)

        message += f"\n\nIn the guild -> `{guild}` (ID: `{guild_id}`)"

        bot_owner = self.bot.owner

        if not bot_owner:
            bot_owner = await self.bot.fetch_user(
                int(
                    self.bot.owner_id or self.bot.owner_ids[0]
                    if self.bot.owner_ids
                    else self.bot.get_ownerid()
                )
            )

        return await bot_owner.send(
            message,
            embed=em,
        )

    def get_embed_from_ctx(self, ctx: Context, title: str) -> Embed:
        em = Embed(
            colour=self.bot.color,
            title=title,
            description=f"Use the command format `{self.get_guild_pre(ctx.message)[0]}{ctx.command.qualified_name} <option>` to view more info about an option.",
        )

        if self.bot.user.avatar:
            em.set_thumbnail(url=self.bot.user.avatar.url)
            em.set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.avatar.url,
            )
        else:
            em.set_author(
                name=self.bot.user.name,
            )

        if ctx.guild.icon:
            em.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url)
        else:
            em.set_footer(text=ctx.guild.name)

        cmds = OrderedDict(
            sorted(
                {
                    c.name: {
                        "brief": c.brief,
                        "description": c.description,
                        "aliases": c.aliases,
                        "usage": c.usage,
                        "commands": c.commands
                        if "all_commands" in vars(c).keys() and c.commands
                        else None,
                    }
                    for c in set(ctx.command.commands)
                }.items()
            )
        )
        for name, cmd in cmds.items():
            em.add_field(
                name=f"{cmd['brief']} {name}",
                value=f"{cmd['description']}"
                + (
                    f"\n**Alias"
                    + ("es" if len(cmd["aliases"]) > 1 else "")
                    + "**: "
                    + ", ".join([f"`{a}`" for a in cmd["aliases"]])
                    if cmd["aliases"]
                    else ""
                )
                + (f"\n**Usage**: `{cmd['usage']}`" if cmd["usage"] else "")
                + (
                    f"\n**Sub-commands:** {', '.join([f'`{cmd.name}`' for cmd in cmd['commands']])}"
                    if cmd["commands"]
                    else ""
                ),
                inline=True,
            )

        return em

    async def parse_duration(
        self,
        _duration: int,
        type_duration: str,
        source: Union[Context, ApplicationCommandInteraction],
    ) -> Optional[Union[bool, int]]:
        type_duration = self.to_lower(type_duration)

        if _duration <= 0:
            try:
                if isinstance(source, Context):
                    await source.reply(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater than 0! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.",
                        delete_after=15,
                    )
                else:
                    await source.response.send_message(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater than 0!",
                        ephemeral=True,
                    )
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to send messages in the channel {source.channel.mention} (message: `⚠️ - {source.author.mention} - Please provide a minimum duration greater than 0! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.`)!"
                raise

            return False
        elif (
            (
                source.command.qualified_name
                if isinstance(source, Context)
                else source.application_command.qualified_name
            )
            == "poll create"
        ) and (
            _duration < 600
            and type_duration == "s"
            or _duration < 10
            and type_duration == "m"
        ):
            try:
                if isinstance(source, Context):
                    await source.reply(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater or equal to 10 minutes to create a poll! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.",
                        delete_after=15,
                    )
                else:
                    await source.response.send_message(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater or equal to 10 minutes to create a poll!",
                        ephemeral=True,
                    )
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to send messages in the channel {source.channel.mention} (message: `⚠️ - {source.author.mention} - Please provide a minimum duration greater than 10 minutes to create a poll! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.`)!"
                raise

            return False
        elif (
            source.command.qualified_name
            if isinstance(source, Context)
            else source.application_command.qualified_name
        ) == "sanction mute add" and (
            _duration < 600
            and type_duration == "s"
            or _duration < 10
            and type_duration == "m"
        ):
            try:
                if isinstance(source, Context):
                    await source.reply(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater or equal to 10 minutes to mute a member! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.",
                        delete_after=15,
                    )
                else:
                    await source.response.send_message(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater or equal to 10 minutes to mute a member!",
                        ephemeral=True,
                    )
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to send messages in the channel {source.channel.mention} (message: `⚠️ - {source.author.mention} - Please provide a minimum duration greater than 10 minutes to create a poll! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.`)!"
                raise

            return False
        elif (
            source.command.qualified_name
            if isinstance(source, Context)
            else source.application_command.qualified_name
        ) == "sanction ban" and (
            _duration < 86400
            and type_duration == "s"
            or _duration < 1440
            and type_duration == "m"
            or _duration < 24
            and type_duration == "h"
            or _duration < 1
            and type_duration == "d"
        ):
            try:
                if isinstance(source, Context):
                    await source.reply(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater or equal to 1 day to ban a member! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.",
                        delete_after=15,
                    )
                else:
                    await source.response.send_message(
                        f"⚠️ - {source.author.mention} - Please provide a minimum duration greater or equal to 1 day to ban a member! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.",
                        ephemeral=True,
                    )
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to send messages in the channel {source.channel.mention} (message: `⚠️ - {source.author.mention} - Please provide a minimum duration greater than 10 minutes to create a poll! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.`)!"
                raise

            return False

        if type_duration == "s":
            return _duration * 1
        elif type_duration == "m":
            return _duration * 60
        elif type_duration == "h":
            return _duration * 3600
        elif type_duration == "d":
            return _duration * 86400
        else:
            try:
                await source.reply(
                    f"⚠️ - {source.author.mention} - Please provide a valid duration type! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.",
                    delete_after=15,
                )
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to send messages in the channel {source.channel.mention} (message: `⚠️ - {source.author.mention} - Please provide a valid duration type! `{self.get_guild_pre(source.message)[0]}{f'{source.command.parents[0]}' if source.command.parents else f'help {source.command.qualified_name}'}` to get more help.`)!"
                raise

            return False

    def get_guild_pre(self, arg: Union[Message, Member, int]) -> list:
        try:
            if isinstance(arg, int):
                prefix = self.configs[arg]["prefix"]
            else:
                prefix = self.configs[arg.guild.id]["prefix"]
        except AttributeError:
            if isinstance(arg, int):
                prefix = self.bot.configs[arg]["prefix"]
            else:
                prefix = self.bot.configs[arg.guild.id]["prefix"] or "o!"

        return [prefix, prefix.lower(), prefix.upper()]

    async def get_last_game_message(self, channel: TextChannel) -> Message or None:
        if (
            "games" in self.bot.configs[channel.guild.id]
            and str(channel.id) in self.bot.configs[channel.guild.id]["games"]
        ):
            try:
                message = await channel.fetch_message(
                    self.bot.configs[channel.guild.id]["games"][str(channel.id)][
                        "game_id"
                    ]
                )
                return message
            except NotFound:
                pass

        return None

    async def check_game_creation(
        self,
        source: Union[Context, ApplicationCommandInteraction],
        member: Member,
        game: list,
    ) -> TextChannel or None:
        if isinstance(source, Context):
            if member.bot:
                return await source.reply(
                    f"⚠️ - {source.author.mention} - You cannot start a {' '.join(game)} game against a bot"
                )
            elif source.author.id == member.id:
                return await source.reply(
                    f"⚠️ - {source.author.mention} - You cannot start a {' '.join(game)} game against yourself"
                )
        else:
            if member.bot:
                return await source.response.send_message(
                    f"⚠️ - {source.author.mention} - You cannot start a {' '.join(game)} game against a bot",
                    ephemeral=True,
                )
            elif source.author.id == member.id:
                return await source.response.send_message(
                    f"⚠️ - {source.author.mention} - You cannot start a {' '.join(game)} game against yourself",
                    ephemeral=True,
                )

        channel_name = (
            f"{''.join(game)}-{source.author.name.lower()}-{member.name.lower()}"
        )
        channel_name_other = (
            f"{''.join(game)}-{member.name.lower()}-{source.author.name.lower()}"
        )
        channels = {channel.name: channel for channel in source.guild.text_channels}
        channel = None

        if channel_name in channels.keys() or channel_name_other in channels.keys():
            channel = (
                channels[channel_name]
                if channel_name in channels.keys()
                else channels[channel_name_other]
            )
            message = await self.get_last_game_message(channel)

            if message:
                if isinstance(source, Context):
                    return await source.reply(
                        f"ℹ️ - You already have a {' '.join(game)} game against `{member.name}`! {channels[channel_name].mention if channel_name in channels.keys() else channels[channel_name_other].mention}"
                    )
                else:
                    return await source.response.send_message(
                        f"ℹ️ - You already have a {' '.join(game)} game against `{member.name}`! {channels[channel_name].mention if channel_name in channels.keys() else channels[channel_name_other].mention}",
                        ephemeral=True,
                    )

        return channel

    @staticmethod
    def to_lower(argument):
        if argument.isdigit():
            raise BadArgument
        if isinstance(argument, str):
            return argument.lower()
        elif isinstance(argument, list):
            return [arg.lower() for arg in argument]

    @staticmethod
    def resolve_guild_path(function):
        def check_guild_path(self, guild_id: int, *args, **kwargs):
            self.path = f"guilds/{str(guild_id)}/{self.innerpath}"
            return function(self, guild_id, *args, **kwargs)

        return check_guild_path

    @staticmethod
    def check_bot_starting():
        def predicate(source: Union[Context, ApplicationCommandInteraction]):
            return not source.bot.starting

        return check(predicate)

    @staticmethod
    def duration(s: int) -> str:
        seconds = s
        minutes = floor(seconds / 60)
        hours = 0
        days = 0

        if minutes >= 60:
            hours = floor(minutes / 60)
            minutes = minutes - hours * 60

        if hours >= 24:
            days = floor(hours / 24)
            hours = hours - days * 24

        seconds = floor(seconds % 60)
        response = ""
        separator = ""

        if days > 0:
            plural = "s" if days > 1 else ""
            response = f"{days} day{plural}"
            separator = ", "
            response += f", {hours}h" if hours > 0 else ""
        elif hours > 0:
            response = f"{hours}h"
            separator = ", "

        if (days > 0 or hours > 0) and minutes > 0:
            response += f", {minutes}m"
        elif minutes > 0:
            response = f"{minutes}m"
            separator = ", "

        if seconds > 0:
            response += f"{separator}{seconds}s"

        return response

    async def init_guild(self, guild: Guild):
        """DB USERS"""
        bot = self.bot

        db_users = bot.user_repo.get_users(guild.id)
        members = set(
            [
                m
                for m in guild.members
                if not m.bot and str(m.id) not in set(db_users.keys())
            ]
        )
        for member in members:
            bot.user_repo.create_user(guild.id, member.id, f"{member}")

        bot.configs[guild.id] = {"prefix": bot.config_repo.get_prefix(guild.id)}

        """ GAMES CATEGORY """

        games_category = bot.config_repo.get_games_category(guild.id)
        if games_category:
            bot.configs[guild.id]["games_category"] = guild.get_channel(
                int(games_category)
            )

        """ GAMES """

        game_channels = bot.games_repo.get_game_channels(guild.id)
        if game_channels:
            bot.configs[guild.id]["games"] = {}
            games_channels = {}

            if (
                "games_category" in bot.configs[guild.id]
                and bot.configs[guild.id]["games_category"]
            ):
                games_channels = {
                    c.id for c in bot.configs[guild.id]["games_category"].channels
                }

            for channel_id, value in game_channels.items():
                if int(channel_id) in games_channels:
                    bot.configs[guild.id]["games"][channel_id] = {}
                    for k, v in value.items():
                        if k != "players":
                            bot.configs[guild.id]["games"][channel_id][k] = v
                        else:
                            bot.configs[guild.id]["games"][channel_id][k] = {}
                            for p, m in v.items():
                                try:
                                    bot.configs[guild.id]["games"][channel_id][k][
                                        p
                                    ] = guild.get_member(m) or await guild.fetch_member(
                                        m
                                    )
                                except NotFound:
                                    bot.configs[guild.id]["games"][channel_id][k][
                                        p
                                    ] = None
                else:
                    bot.games_repo.remove_game(guild.id, channel_id)

    @classmethod
    def check_moderator(cls):
        def predicate(source: Union[Context, ApplicationCommandInteraction]):
            source.bot.last_check = "moderator"
            return cls.is_mod(source.author)

        return check(predicate)

    # The `args` are the arguments passed into the loop
    @staticmethod
    def task_launcher(function, param, **interval) -> loop:
        """Creates new instances of `tasks.Loop`"""
        # Creating the task
        # You can also pass a static interval and/or count
        new_task = loop(**interval)(function)
        # Starting the task
        new_task.start(*param)
        return new_task

    @staticmethod
    def is_mod(member: Member) -> bool:
        return member.guild_permissions.administrator

    @staticmethod
    async def mentionable_converter(
        inter: ApplicationCommandInteraction,
        argument: str,
    ) -> Optional[List[Union[Member, Role]]]:
        ids = findall(r"([0-9]{15,20})", argument)
        result = []
        for id in ids:
            try:
                result.append(
                    inter.guild.get_role(int(id))
                    or inter.guild.get_member(int(id))
                    or await inter.guild.fetch_member(int(id))
                )
            except NotFound:
                continue

        if not result or not all(result):
            await inter.channel.send(
                f"⚠️ - {inter.author.mention} - None of the mods you gave are valid ones!",
                delete_after=20,
            )
            return None

        return result

    @staticmethod
    async def channel_converter(
        inter: ApplicationCommandInteraction,
        argument: str,
    ) -> Optional[List[Union[TextChannel, VoiceChannel]]]:
        ids = findall(r"([0-9]{15,20})", argument)
        result = []
        for id in ids:
            try:
                result.append(
                    inter.guild.get_channel(id) or await inter.guild.fetch_channel(id)
                )
            except NotFound:
                continue

        if not result or not all(result):
            await inter.channel.send(
                f"⚠️ - {inter.author.mention} - None of the channels you gave are valid ones!",
                delete_after=20,
            )
            return None

        return result
