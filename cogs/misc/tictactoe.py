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
from disnake.ui import Button, View

from bot import OmniGames


class TicTacToe(Cog, name="misc.tictactoe"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

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
        if not await self.bot.utils_class.check_games_category(inter):
            return

        channel_name = f"tictactoe-{self.bot.utils_class.normalize_name(inter.author.name)}-{self.bot.utils_class.normalize_name(member.name)}"
        channel = await self.bot.utils_class.check_game_creation(
            inter, member, ["tic", "tac", "toe"]
        )

        if channel:
            await channel.send(f"❌ - Creating a new game... - ⭕")
        else:
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
                            "use_slash_commands": False,
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
                category=self.bot.configs[inter.guild.id]["games_category"],
                reason=f"Creation of the {inter.author} vs {member} tic tac toe game channel",
            )

            await inter.channel.send(
                f"❌ - The tic tac toe game {channel.mention} opposing `{inter.author.name}` and `{member.name}` has been created - ⭕"
            )

        view = View(timeout=None)

        for x in range(3):
            for y in range(3):
                view.add_item(
                    Button(label="\u200b", custom_id=f"{channel.id}.{x}.{y}", row=x)
                )

        await inter.response.send_message("The game has been created!", ephemeral=True)

        msg = await channel.send(
            f"❌ - {inter.author.mention} **VS** {member.mention} - ⭕\n\n**It's `{choice([inter.author, member]).name}`'s turn**",
            view=view,
        )

        if "games" not in self.bot.configs[inter.guild.id]:
            self.bot.configs[inter.guild.id]["games"] = {
                str(channel.id): {
                    "game_id": msg.id,
                    "players": {"p1": inter.author, "p2": member},
                    "game_type": "tictactoe",
                }
            }
        else:
            self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
                "game_id": msg.id,
                "players": {"p1": inter.author, "p2": member},
                "game_type": "tictactoe",
            }

        self.bot.games_repo.create_game(
            inter.guild.id,
            channel.id,
            msg.id,
            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
            "tictactoe",
        )

        await sleep(1)

        await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(TicTacToe(bot))
