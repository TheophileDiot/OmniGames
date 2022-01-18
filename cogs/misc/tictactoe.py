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
from disnake.ui import Button, View

from bot import OmniGames


class TicTacToe(Cog, name="misc.tictactoe"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    @command(
        pass_context=True,
        name="tictactoe",
        aliases=["ttt"],
        brief=None,  # TODO add an emoji
        description="Starts a tic tac toe game against another guild member",
        usage="@member",
    )
    @max_concurrency(1, BucketType.member)
    async def game_tictactoe_command(self, ctx: Context, member: Member):
        """
        This command starts a tic tac toe game against another guild member

        Parameters
        ----------
        ctx: :class:`disnake.ext.commands.Context`
            The command context
        member: :class:`disnake.Member`
            The member to play against
        """
        await self.handle_tictactoe(ctx, member)

    @slash_command(
        name="tictactoe",
        description="Starts a tic tac toe game against another guild member",
    )
    @max_concurrency(1, BucketType.member)
    async def game_tictactoe_slash_command(
        self, inter: ApplicationCommandInteraction, member: Member
    ):
        """
        This slash command starts a tic tac toe game against another guild member

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        member: :class:`disnake.Member`
            The member to play against
        """
        await self.handle_tictactoe(inter, member)

    async def handle_tictactoe(
        self, source: Union[Context, ApplicationCommandInteraction], member: Member
    ):
        channel_name = f"tictactoe-{source.author.name.lower()}-{member.name.lower()}"
        channel = await self.bot.utils_class.check_game_creation(
            source, member, ["tic", "tac", "toe"]
        )

        if channel:
            await channel.send(f"❌ - Creating a new game... - ⭕")
        else:
            channel = await source.guild.create_text_channel(
                name=channel_name,
                overwrites={
                    member: PermissionOverwrite(**{"send_messages": True}),
                    source.author: PermissionOverwrite(**{"send_messages": True}),
                    source.guild.default_role: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": False,
                        }
                    ),
                    self.bot.user: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": True,
                        }
                    ),
                },
                category=self.bot.configs[source.guild.id]["games_category"],
                reason=f"Creation of the {source.author} vs {member} tic tac toe game channel",
            )

            await source.channel.send(
                f"❌ - The tic tac toe game {channel.mention} opposing `{source.author.name}` and `{member.name}` has been created - ⭕"
            )

        view = View(timeout=None)

        for x in range(3):
            for y in range(3):
                view.add_item(
                    Button(label="\u200b", custom_id=f"{channel.id}.{x}.{y}", row=x)
                )

        if isinstance(source, ApplicationCommandInteraction):
            await source.response.send_message(
                "The game has been created!", ephemeral=True
            )

        msg = await channel.send(
            f"❌ - {source.author.mention} **VS** {member.mention} - ⭕\n\n**It's `{choice([source.author, member]).name}`'s turn**",
            view=view,
        )

        if "games" not in self.bot.configs[source.guild.id]:
            self.bot.configs[source.guild.id]["games"] = {
                str(channel.id): {
                    "game_id": msg.id,
                    "players": {"p1": source.author, "p2": member},
                    "game_type": "tictactoe",
                }
            }
        else:
            self.bot.configs[source.guild.id]["games"][str(channel.id)] = {
                "game_id": msg.id,
                "players": {"p1": source.author, "p2": member},
                "game_type": "tictactoe",
            }

        self.bot.games_repo.create_game(
            source.guild.id,
            channel.id,
            msg.id,
            self.bot.configs[source.guild.id]["games"][str(channel.id)]["players"],
            "tictactoe",
        )

        await sleep(1)

        await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(TicTacToe(bot))
