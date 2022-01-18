from asyncio import sleep
from random import choice
from typing import Union

from disnake import (
    ApplicationCommandInteraction,
    Member,
    PermissionOverwrite,
)
from disnake.ext.commands import (
    BucketType,
    command,
    Context,
    Cog,
    max_concurrency,
    slash_command,
)

from bot import OmniGames
from data import NUM2EMOJI


class FourInARow(Cog, name="misc.fourinarow"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    @command(
        pass_context=True,
        name="fourinarow",
        aliases=["4inarow"],
        brief="4️⃣",
        description="Starts a four in a row game against another guild member",
        usage="@member",
    )
    @max_concurrency(1, BucketType.member)
    async def game_fourinarow_command(self, ctx: Context, member: Member):
        """
        This command starts a four in a row game against another guild member

        Parameters
        ----------
        ctx: :class:`disnake.ext.commands.Context`
            The command context
        member: :class:`disnake.Member`
            The member to play against
        """
        await self.handle_fourinarow(ctx, member)

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
        await self.handle_fourinarow(inter, member)

    async def handle_fourinarow(
        self, source: Union[Context, ApplicationCommandInteraction], member: Member
    ):
        channel_name = f"4inarow-{source.author.name.lower()}-{member.name.lower()}"
        channel = await self.bot.utils_class.check_game_creation(
            source, member, ["4", "in", "a", "row"]
        )

        if not channel:
            channel = await source.guild.create_text_channel(
                name=channel_name,
                overwrites={
                    member: PermissionOverwrite(
                        **{"send_messages": True, "add_reactions": False}
                    ),
                    source.author: PermissionOverwrite(
                        **{"send_messages": True, "add_reactions": False}
                    ),
                    source.guild.default_role: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": False,
                            "add_reactions": False,
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
                category=self.bot.configs[source.guild.id]["games_category"],
                reason=f"Creation of the {source.author} vs {member} 4 in a row game channel",
            )

            await source.channel.send(
                f"🔴🔴🔴🔴 - The four in a row game {channel.mention} opposing `{source.author.name}` and `{member.name}` has been created - 🔵🔵🔵🔵"
            )

        board = [
            ["⬛" if x == 0 or x == 8 or y == 7 else "⚪" for x in range(9)]
            for y in range(8)
        ]
        nl = "\n"

        msg = await channel.send(
            f"🔴🔴🔴🔴 - {source.author.mention} **VS** {member.mention} - 🔵🔵🔵🔵\n\n**This is `{choice([source.author, member]).name}`'s turn**\n\n{nl.join([''.join(row) for row in board])}"
        )

        if isinstance(source, ApplicationCommandInteraction):
            await source.response.send_message(
                "The game has been created!", ephemeral=True
            )

        if "games" not in self.bot.configs[source.guild.id]:
            self.bot.configs[source.guild.id]["games"] = {
                str(channel.id): {
                    "game_id": msg.id,
                    "players": {"p1": source.author, "p2": member},
                    "game_type": "4inarow",
                }
            }
        else:
            self.bot.configs[source.guild.id]["games"][str(channel.id)] = {
                "game_id": msg.id,
                "players": {"p1": source.author, "p2": member},
                "game_type": "4inarow",
            }

        self.bot.games_repo.create_game(
            source.guild.id,
            channel.id,
            msg.id,
            self.bot.configs[source.guild.id]["games"][str(channel.id)]["players"],
            "4inarow",
        )

        await sleep(1)

        for x in range(1, 8):
            await msg.add_reaction(NUM2EMOJI[x])

        await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(FourInARow(bot))
