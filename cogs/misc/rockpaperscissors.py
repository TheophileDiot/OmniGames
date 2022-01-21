from asyncio import sleep

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
from disnake.ui import View, Button

from bot import OmniGames


class RockPaperScissors(Cog, name="misc.rockpaperscissors"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    @slash_command(
        name="rockpaperscissors",
        description="Starts a rock paper scissors game against another guild member",
    )
    @max_concurrency(1, BucketType.member)
    async def game_rockpaperscissors_slash_command(
        self, inter: ApplicationCommandInteraction, member: Member
    ):
        """
        This slash command starts a rock paper scissors game against another guild member

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        member: :class:`disnake.Member`
            The member to play against
        """
        if not await self.bot.utils_class.check_games_category(inter):
            return

        channel_name = f"rockpaperscissors-{self.bot.utils_class.normalize_name(inter.author.name)}-{self.bot.utils_class.normalize_name(member.name)}"
        channel = await self.bot.utils_class.check_game_creation(
            inter, member, ["rock", "paper", "scissors"]
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
                reason=f"Creation of the {inter.author} vs {member} rock paper scissors game channel",
            )

            await inter.channel.send(
                f"🪨📄✂️ - The four in a row game {channel.mention} opposing `{inter.author.name}` and `{member.name}` has been created - 🪨📄✂️"
            )

        view = View(timeout=None)
        view.add_item(Button(emoji="🪨", custom_id=f"{channel.id}.rock"))
        view.add_item(Button(emoji="📄", custom_id=f"{channel.id}.paper"))
        view.add_item(Button(emoji="✂️", custom_id=f"{channel.id}.scissors"))

        msg = await channel.send(
            content=f"🪨📄✂️ - {inter.author.mention} **VS** {member.mention} - ✂️📄🪨\n\n**Choose one:**\n\n`{inter.author.name}` 🪹 🆚 🪹 `{member.name}`",
            view=view,
        )

        await inter.response.send_message("The game has been created!", ephemeral=True)

        if "games" not in self.bot.configs[inter.guild.id]:
            self.bot.configs[inter.guild.id]["games"] = {}

        self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
            "game_id": msg.id,
            "players": {"p1": inter.author, "p2": member},
            "game_type": "rockpaperscissors",
            "signs": {"p1": None, "p2": None},
        }

        self.bot.games_repo.create_game(
            inter.guild.id,
            channel.id,
            msg.id,
            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
            "rockpaperscissors",
            dict(self.bot.configs[inter.guild.id]["games"][str(channel.id)]),
        )

        await sleep(1)

        await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(RockPaperScissors(bot))
