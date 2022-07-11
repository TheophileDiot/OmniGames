from asyncio import sleep
from random import choice, shuffle
from typing import List

from disnake import (
    ApplicationCommandInteraction,
    ButtonStyle,
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


class TicTacToeButton(Button["TicTacToeGame"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: MessageInteraction):
        assert self.view is not None
        view: TicTacToe = self.view

        if interaction.author not in [view.player_1, view.player_2]:
            return await interaction.response.send_message(
                f"⛔ - {interaction.author.mention} - Only Tic Tac Toe participants can play",
                ephemeral=True,
            )
        elif (
            interaction.author == view.player_1
            and view.current_player == view.O
            or interaction.author == view.player_2
            and view.current_player == view.X
        ):
            return await interaction.response.send_message(
                f"⛔ - {interaction.author.mention} - It's not your turn",
                ephemeral=True,
            )

        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        content = f"❌ - {view.player_1.mention} **VS** {view.player_2.mention} - ⭕\n\n"

        if view.current_player == view.X:
            self.style = ButtonStyle.danger
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            additional_content = f"**It's `{view.player_2.name}`'s turn**"
        else:
            self.style = ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            additional_content = f"**It's `{view.player_1.name}`'s turn**"

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                additional_content = (
                    f"🎉 - **The winner is:** `{view.player_1.name}` - 🎉"
                )
            elif winner == view.O:
                additional_content = (
                    f"🎉 - **The winner is:** `{view.player_2.name}` - 🎉"
                )
            else:
                additional_content = f"** It's a tie **"

            for child in view.children:
                if child.label in ("X", "O"):
                    child.disabled = True
                else:
                    child.disabled = False

        await interaction.response.edit_message(
            content=f"{content}{additional_content}", view=view
        )


class TicTacToeGame(View):
    children: List[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player_1: Member, player_2: Member):
        super().__init__(timeout=None)
        self.player_1 = player_1
        self.player_2 = player_2
        self.player_1_asks = 0
        self.player_2_asks = 0
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None

    @button(emoji="🔄", style=ButtonStyle.primary, row=3)
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
            await interaction.channel.send("The game has been reset", delete_after=20)

            players = [self.player_1, self.player_2]
            shuffle(players)
            view = TicTacToeGame(players[0], players[1])
            await interaction.followup.edit_message(
                interaction.message.id,
                content=f"❌ - {players[0].mention} **VS** {players[1].mention} - ⭕\n\n**It's `{players[0].name}`'s turn**",
                view=view,
            )

    @button(emoji="💥", style=ButtonStyle.danger, row=3, disabled=True)
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

        # view = View(timeout=None)

        # for x in range(3):
        #     for y in range(3):
        #         view.add_item(
        #             Button(label="\u200b", custom_id=f"{channel.id}.{x}.{y}", row=x)
        #         )

        await inter.response.send_message("The game has been created!", ephemeral=True)

        members = [inter.author, member]
        shuffle(members)

        msg = await channel.send(
            f"❌ - {inter.author.mention} **VS** {member.mention} - ⭕\n\n**It's `{members[0].name}`'s turn**",
            view=TicTacToeGame(members[0], members[1]),
        )

        # if "games" not in self.bot.configs[inter.guild.id]:
        #     self.bot.configs[inter.guild.id]["games"] = {}

        # self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
        #     "game_id": msg.id,
        #     "players": {"p1": inter.author, "p2": member},
        #     "game_type": "tictactoe",
        # }

        # self.bot.games_repo.create_game(
        #     inter.guild.id,
        #     channel.id,
        #     msg.id,
        #     self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
        #     "tictactoe",
        # )

        # await sleep(1)

        # await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(TicTacToe(bot))
