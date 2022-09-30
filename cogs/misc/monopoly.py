from asyncio import sleep
from typing import List

from disnake import (
    File,
    GuildCommandInteraction,
    Member,
    PermissionOverwrite,
)
from disnake.ext.commands import (
    BucketType,
    Cog,
    max_concurrency,
    Param,
    slash_command,
)

from bot import OmniGames
from data import Utils
from data.monopoly import MonopolyGame


class Monopoly(Cog, name="misc.monopoly"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    """ GROUP """

    @slash_command(
        name="monopoly",
        description="Manages the monopoly game",
    )
    async def monopoly_slash_command_group(
        self,
        inter: GuildCommandInteraction,
    ):
        """
        This command group manages the monopoly game

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        """
        if not await self.bot.utils_class.check_games_category(inter):
            return

    """ GROUP'S COMMAND(S) """

    @monopoly_slash_command_group.sub_command(
        name="info",
        description="Displays the information of a Monopoly player (or yourself)",
    )
    @max_concurrency(1, BucketType.member)
    async def monopoly_infos_slash_command(
        self,
        inter: GuildCommandInteraction,
        member: Member = None,
    ):
        """
        This command displays the information of a Monopoly player (or yourself)

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        members: :class:`disnake.Member`
            The member corresponding to the Monopoly player (if not specified then display your information)
        """
        if (
            "games" not in self.bot.configs[inter.guild.id]
            or str(inter.channel.id) not in self.bot.configs[inter.guild.id]["games"]
            or not inter.channel.name.startswith("monopoly-")
        ):
            return await inter.response.send_message(
                f"ℹ️ - {inter.author.mention} - You must be in a Monopoly game room to use this command",
                ephemeral=True,
            )

        if not member:
            member = inter.author

        player = self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
            "game"
        ].get_player(member=member)

        if not player:
            return await inter.response.send_message(
                f"ℹ️ - {inter.author.mention} - The member you have selected is not part of this Monopoly game",
                ephemeral=True,
            )

        await inter.response.send_message(
            embed=self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                "game"
            ].get_player_embed(player.id),
            ephemeral=True,
        )

    @monopoly_slash_command_group.sub_command(
        name="create",
        description="Start a Monopoly game against other server members",
    )
    @max_concurrency(1, BucketType.member)
    async def monopoly_create_slash_command(
        self,
        inter: GuildCommandInteraction,
        members: List[Member] = Param(None, converter=Utils.members_converter),
    ):
        """
        This command start a Monopoly game against other server members

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        members: :class:`typing.List[disnake.Member]`
            Monopoly members with you (maximum 7 participants)
        """
        if len(members) > 7:
            return await inter.response.send_message(
                f"ℹ️ - {inter.author.mention} - The maximum number of participants in a Monopoly game is 8 (including you)",
                ephemeral=True,
            )
        elif inter.author in members:
            return await inter.response.send_message(
                f"ℹ️ - {inter.author.mention} - When you create a Monopoly game, you are already part of it. You therefore don't need to add yourself",
                ephemeral=True,
            )

        overwrites = {
            inter.author: PermissionOverwrite(
                **{
                    "view_channel": True,
                    "send_messages": True,
                    "use_slash_commands": True,
                    "add_reactions": False,
                }
            ),
            self.bot.user: PermissionOverwrite(
                **{
                    "view_channel": True,
                    "send_messages": True,
                    "add_reactions": True,
                    "attach_files": True,
                }
            ),
            inter.guild.default_role: PermissionOverwrite(
                **{
                    "view_channel": True,
                    "send_messages": False,
                    "use_slash_commands": False,
                    "add_reactions": False,
                }
            ),
        } | {
            member: PermissionOverwrite(
                **{
                    "view_channel": True,
                    "send_messages": True,
                    "use_slash_commands": True,
                    "add_reactions": False,
                }
            )
            for member in members
        }

        channel = await inter.guild.create_text_channel(
            name=f"monopoly-{self.bot.utils_class.normalize_name(inter.author.name)}",
            overwrites=overwrites,
            category=self.bot.configs[inter.guild.id]["games_category"],
            reason=f"Creation of the Monopoly game of {inter.author}",
        )

        await inter.response.send_message(
            f"💰 - The Monopoly game {channel.mention} with {', '.join([f'`{m.name}`' for m in members])} has just been created - 💰"
        )

        if "games" not in self.bot.configs[inter.guild.id]:
            self.bot.configs[inter.guild.id]["games"] = {}

        members.append(inter.author)

        msg = await channel.send("💰 - Creating the game... - 💰")
        monopoly_game = MonopolyGame(self.bot, members, msg)
        self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
            "game_id": msg.id,
            "players": {f"p{x}": members[x - 1] for x in range(1, len(members) + 1)},
            "game_type": "monopoly",
            "game": monopoly_game,
        }

        players = self.bot.configs[inter.guild.id]["games"][str(channel.id)][
            "game"
        ].get_players()

        await msg.edit(
            content=f"💰 - **Order of play (decided randomly):** {' → '.join([f'`{p.name}` (die 1: `' + str(p.last_dice['d1']) + '`, die 2: `' + str(p.last_dice['d2']) + '`)' for p in players])} - 💰",
            file=File(monopoly_game.get_board(), filename=f"monopoly_{channel.id}.jpg"),
        )

        self.bot.games_repo.create_game(
            inter.guild.id,
            channel.id,
            msg.id,
            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
            "monopoly",
        )

        await sleep(1)

        self.bot.configs[inter.guild.id]["games"][str(channel.id)]["game"].save()

        self.bot.utils_class.task_launcher(
            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["game"].turn,
            (),
            count=1,
        )


def setup(bot: OmniGames):
    bot.add_cog(Monopoly(bot))
