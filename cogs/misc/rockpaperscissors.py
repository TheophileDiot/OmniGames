from asyncio import sleep

from disnake import (
    ButtonStyle,
    GuildCommandInteraction,
    Member,
    MessageInteraction,
    PermissionOverwrite,
)
from disnake.ext.commands import (
    BucketType,
    Cog,
    max_concurrency,
    slash_command,
)
from disnake.ui import button, Button, View

from bot import OmniGames


class RockPaperScissorsGame(View):
    def __init__(self, player_1: Member, player_2: Member):
        super().__init__(timeout=None)
        self.player_1 = player_1
        self.player_2 = player_2
        self.player_1_choice = None
        self.player_1_asks = 0
        self.player_2_choice = None
        self.player_2_asks = 0

    async def handle_sign(self, interaction: MessageInteraction):
        if interaction.author == self.player_1:
            if self.player_1_choice is None:
                self.player_1_choice = interaction.component.emoji.name
            else:
                return await interaction.response.send_message(
                    content=f"You already chose the sign {self.player_1_choice}",
                    ephemeral=True,
                )
        elif interaction.author == self.player_2:
            if self.player_2_choice is None:
                self.player_2_choice = interaction.component.emoji.name
            else:
                return await interaction.response.send_message(
                    content=f"You already chose the sign {self.player_2_choice}",
                    ephemeral=True,
                )
        else:
            return await interaction.response.send_message(
                f"⛔ - {interaction.author.mention} - Only rock paper scissors participants can play",
                ephemeral=True,
            )

        await interaction.response.send_message(
            content=f"You chose the sign {interaction.component.emoji.name}",
            ephemeral=True,
        )

        if self.player_1_choice is not None and self.player_2_choice is not None:
            if self.player_1_choice == self.player_2_choice:
                winner = None
            else:
                if self.player_1_choice == "🪨" and self.player_2_choice == "📄":
                    winner = 1
                elif self.player_1_choice == "🪨" and self.player_2_choice == "✂️":
                    winner = 0
                elif self.player_1_choice == "📄" and self.player_2_choice == "🪨":
                    winner = 0
                elif self.player_1_choice == "📄" and self.player_2_choice == "✂️":
                    winner = 1
                elif self.player_1_choice == "✂️" and self.player_2_choice == "🪨":
                    winner = 1
                elif self.player_1_choice == "✂️" and self.player_2_choice == "📄":
                    winner = 0

            nl = "\n"
            apostroph = "'"

            for child in self.children:
                if child.style == ButtonStyle.secondary:
                    child.disabled = True
                else:
                    child.disabled = False

            await interaction.followup.edit_message(
                interaction.message.id,
                content=f"🪨📄✂️ - {self.player_1.mention} **VS** {self.player_2.mention} - ✂️📄🪨{nl}{nl}{f'🎉 - **The winner is:** `{self.player_2.name if winner else self.player_1.name}`! - 🎉' if winner is not None else f'**It{apostroph}s a tie**'}{nl}{nl}`{self.player_1.name}` {self.player_1_choice} 🆚 {self.player_2_choice} `{self.player_2.name}`",
                view=self,
            )

    @button(emoji="🪨", custom_id="rock", style=ButtonStyle.secondary)
    async def rock(self, _: Button, interaction: MessageInteraction):
        await self.handle_sign(interaction)

    @button(emoji="📄", custom_id="paper", style=ButtonStyle.secondary)
    async def paper(self, _: Button, interaction: MessageInteraction):
        await self.handle_sign(interaction)

    @button(emoji="✂️", custom_id="scissors", style=ButtonStyle.secondary)
    async def scissors(self, _: Button, interaction: MessageInteraction):
        await self.handle_sign(interaction)

    @button(emoji="🔄", style=ButtonStyle.primary, row=1)
    async def reset(self, _: Button, interaction: MessageInteraction):
        if interaction.author == self.player_1:
            if self.player_1_asks != 2:
                self.player_1_asks = 2
            else:
                self.player_1_asks = 0
                await interaction.channel.send(
                    f"{interaction.author} canceled his reset request",
                )
                return await interaction.response.send_message(
                    content=f"You canceled your reset request",
                    ephemeral=True,
                )
        elif interaction.author == self.player_2:
            if self.player_2_asks != 2:
                self.player_2_asks = 2
            else:
                self.player_2_asks = 0
                await interaction.channel.send(
                    f"{interaction.author} canceled his reset request",
                )
                return await interaction.response.send_message(
                    content=f"You canceled your reset request",
                    ephemeral=True,
                )
        else:
            return await interaction.response.send_message(
                f"⛔ - {interaction.author.mention} - Only rock paper scissors participants can interact with the game",
                ephemeral=True,
            )

        await interaction.response.send_message(
            content=f"You asked to reset the game",
            ephemeral=True,
        )
        await interaction.channel.send(
            f"`{interaction.author}` asked to reset the game", delete_after=20
        )

        if self.player_1_asks == 2 and self.player_2_asks == 2:
            self.player_1_asks = 0
            self.player_2_asks = 0
            self.player_1_choice = None
            self.player_2_choice = None

            await interaction.channel.send("The game has been reset", delete_after=20)

    @button(emoji="💥", style=ButtonStyle.danger, row=1, disabled=True)
    async def delete(self, _: Button, interaction: MessageInteraction):
        if interaction.author == self.player_1:
            if self.player_1_asks != 2:
                self.player_1_asks = 2
            else:
                self.player_1_asks = 0
                await interaction.channel.send(
                    f"{interaction.author} canceled his deletion request",
                )
                return await interaction.response.send_message(
                    content=f"You canceled your deletion request",
                    ephemeral=True,
                )
        elif interaction.author == self.player_2:
            if self.player_2_asks != 2:
                self.player_2_asks = 2
            else:
                self.player_2_asks = 0
                await interaction.channel.send(
                    f"{interaction.author} canceled his deletion request",
                )
                return await interaction.response.send_message(
                    content=f"You canceled your deletion request",
                    ephemeral=True,
                )
        else:
            return await interaction.response.send_message(
                f"⛔ - {interaction.author.mention} - Only rock paper scissors participants can interact with the game",
                ephemeral=True,
            )

        await interaction.response.send_message(
            content=f"You asked to delete the game",
            ephemeral=True,
        )
        await interaction.channel.send(
            f"`{interaction.author}` asked to delete the game"
        )

        if self.player_1_asks == 2 and self.player_2_asks == 2:
            self.stop()
            await interaction.channel.send(
                "⚠️ - **Deletion of the channel in **`5`** seconds** - ⚠️"
            )
            await sleep(5)
            await interaction.channel.delete()


class RockPaperScissors(Cog, name="misc.rockpaperscissors"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    @slash_command(
        name="rockpaperscissors",
        description="Starts a rock paper scissors game against another guild member",
    )
    @max_concurrency(1, BucketType.member)
    async def game_rockpaperscissors_slash_command(
        self, inter: GuildCommandInteraction, member: Member
    ):
        """
        This slash command starts a rock paper scissors game against another guild member

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
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

        msg = await channel.send(
            content=f"🪨📄✂️ - {inter.author.mention} **VS** {member.mention} - ✂️📄🪨\n\n**Choose one:**\n\n`{inter.author.name}` ❔ 🆚 ❔ `{member.name}`",
            view=RockPaperScissorsGame(inter.author, member),
        )

        await inter.response.send_message("The game has been created!", ephemeral=True)

        # if "games" not in self.bot.configs[inter.guild.id]:
        #     self.bot.configs[inter.guild.id]["games"] = {}

        # self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
        #     "game_id": msg.id,
        #     "players": {"p1": inter.author, "p2": member},
        #     "game_type": "rockpaperscissors",
        #     "signs": {"p1": None, "p2": None},
        # }

        # self.bot.games_repo.create_game(
        #     inter.guild.id,
        #     channel.id,
        #     msg.id,
        #     self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
        #     "rockpaperscissors",
        #     dict(self.bot.configs[inter.guild.id]["games"][str(channel.id)]),
        # )

        await sleep(1)

        # await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(RockPaperScissors(bot))
