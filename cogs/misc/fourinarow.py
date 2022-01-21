from asyncio import sleep
from random import choice

from disnake import (
    ApplicationCommandInteraction,
    Member,
    PermissionOverwrite,
)
from disnake.ext.commands import (
    BucketType,
    Cog,
    max_concurrency,
    slash_command,
)

from bot import OmniGames
from data import NUM2EMOJI


class FourInARow(Cog, name="misc.fourinarow"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    @slash_command(
        name="fourinarow",
        description="Starts a four in a row game against another guild member",
    )
    @max_concurrency(1, BucketType.member)
    async def game_fourinarow_slash_command(
        self, inter: ApplicationCommandInteraction, member: Member
    ):
        """
        This slash command starts a four in a row game against another guild member

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        member: :class:`disnake.Member`
            The member to play against
        """
        if not await self.bot.utils_class.check_games_category(inter):
            return

        channel_name = f"4inarow-{self.bot.utils_class.normalize_name(inter.author.name)}-{self.bot.utils_class.normalize_name(member.name)}"
        channel = await self.bot.utils_class.check_game_creation(
            inter, member, ["4", "in", "a", "row"]
        )

        if not channel:
            channel = await inter.guild.create_text_channel(
                name=channel_name,
                overwrites={
                    member: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": True,
                            "add_reactions": False,
                        }
                    ),
                    inter.author: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": True,
                            "add_reactions": False,
                        }
                    ),
                    inter.guild.default_role: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": False,
                            "add_reactions": False,
                            "use_slash_commands": False,
                        }
                    ),
                    self.bot.user: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": True,
                            "add_reactions": True,
                        }
                    ),
                },
                category=self.bot.configs[inter.guild.id]["games_category"],
                reason=f"Creation of the {inter.author} vs {member} 4 in a row game channel",
            )

            await inter.channel.send(
                f"🔴🔴🔴🔴 - The four in a row game {channel.mention} opposing `{inter.author.name}` and `{member.name}` has been created - 🔵🔵🔵🔵"
            )

        board = [
            ["⬛" if x == 0 or x == 8 or y == 7 else "⚪" for x in range(9)]
            for y in range(8)
        ]
        nl = "\n"

        msg = await channel.send(
            f"🔴🔴🔴🔴 - {inter.author.mention} **VS** {member.mention} - 🔵🔵🔵🔵\n\n**This is `{choice([inter.author, member]).name}`'s turn**\n\n{nl.join([''.join(row) for row in board])}"
        )

        await inter.response.send_message("The game has been created!", ephemeral=True)

        if "games" not in self.bot.configs[inter.guild.id]:
            self.bot.configs[inter.guild.id]["games"] = {}

        self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
            "game_id": msg.id,
            "players": {"p1": inter.author, "p2": member},
            "game_type": "4inarow",
        }

        self.bot.games_repo.create_game(
            inter.guild.id,
            channel.id,
            msg.id,
            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
            "4inarow",
        )

        await sleep(1)

        for x in range(1, 8):
            await msg.add_reaction(NUM2EMOJI[x])

        await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(FourInARow(bot))
