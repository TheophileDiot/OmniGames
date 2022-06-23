from disnake import (
    ButtonStyle,
    MessageInteraction,
)
from disnake.ext.commands import Cog
from disnake.ui import Button, View

from bot import OmniGames
from data import check_for_win_tictactoe, check_for_win_rockpaperscissors


class Events(Cog, name="events.on_button_click"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        await self.bot.wait_until_ready()

        if (
            "games" in self.bot.configs[interaction.guild.id]
            and self.bot.configs[interaction.guild.id]["games"]
            and str(interaction.channel.id)
            in self.bot.configs[interaction.guild.id]["games"]
        ):
            if interaction.channel.name.startswith("tictactoe-"):
                if interaction.author not in interaction.message.mentions:
                    return await interaction.response.send_message(
                        f"⛔ - {interaction.author.mention} - Only tic tac toe participants can play",
                        ephemeral=True,
                    )

                player_turn = interaction.message.clean_content[
                    interaction.message.clean_content.rfind(
                        "`", 0, interaction.message.clean_content.rfind("`")
                    )
                    + 1 : interaction.message.clean_content.rfind("`")
                ]

                if interaction.author.name != player_turn:
                    return await interaction.response.send_message(
                        f"⛔ - {interaction.author.mention} - It's not your turn",
                        ephemeral=True,
                    )

                view = View(timeout=None)
                components = [[], [], []]
                x = 0

                for action_row in interaction.message.components:
                    y = 0

                    for button in action_row.children:
                        if button.custom_id == interaction.component.custom_id:
                            button = Button(
                                emoji="❌"
                                if interaction.message.mentions[0].name == player_turn
                                else "⭕",
                                style=ButtonStyle.danger
                                if interaction.message.mentions[0].name == player_turn
                                else ButtonStyle.success,
                                custom_id=interaction.component.custom_id,
                                disabled=True,
                                row=x,
                            )
                        else:
                            button = Button(
                                label=button.label,
                                emoji=button.emoji,
                                style=button.style,
                                custom_id=button.custom_id,
                                disabled=button.disabled,
                                row=x,
                            )

                        components[x].append(button)
                        y += 1
                    x += 1

                win = check_for_win_tictactoe(
                    [
                        [
                            button.emoji if button.emoji else button.custom_id
                            for button in action_row
                        ]
                        for action_row in components
                    ]
                )
                equ = False

                x = 0
                for action_row in components:
                    for button in action_row:
                        if button.disabled:
                            x += 1

                if x == 9:
                    equ = True

                for x in range(3):
                    for y in range(3):
                        view.add_item(
                            Button(
                                label=components[x][y].label,
                                emoji=components[x][y].emoji,
                                style=components[x][y].style,
                                custom_id=components[x][y].custom_id,
                                disabled=True
                                if win and not equ
                                else components[x][y].disabled,
                                row=x,
                            )
                        )

                if win and not equ:
                    await interaction.message.add_reaction("💥")

                await interaction.response.edit_message(
                    content=f"❌ - {interaction.message.mentions[0].mention} **VS** {interaction.message.mentions[1].mention} - ⭕\n\n"
                    + (
                        f"**It's `{interaction.message.mentions[0 if interaction.message.mentions[0].name != player_turn else 1].name}`'s turn**"
                        if not win and not equ
                        else (
                            f"🎉 - **The winner is:** `{player_turn}` - 🎉"
                            if not equ
                            else f"** It's a tie **"
                        )
                    ),
                    view=view,
                )


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
