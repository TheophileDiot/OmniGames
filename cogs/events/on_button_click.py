from disnake import (
    ButtonStyle,
    Embed,
    MessageInteraction,
)
from disnake.ext.commands import Cog
from disnake.ui import Button, View

from bot import OmniGames
from cogs.misc.yams import yams_scoreboard
from data import check_for_win_tictactoe, check_for_win_rockpaperscissors, NUM2EMOJI


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

                if not equ:
                    await interaction.message.add_reaction("🔄")
                    return await interaction.message.add_reaction("💥")

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
            elif interaction.channel.name.startswith("rockpaperscissors-"):
                if interaction.author not in interaction.message.mentions:
                    return await interaction.response.send_message(
                        f"⛔ - {interaction.author.mention} - Only rock paper scissors participants can play",
                        ephemeral=True,
                    )

                if not self.bot.configs[interaction.guild.id]["games"][
                    str(interaction.channel.id)
                ]["signs"][
                    "p1"
                    if interaction.message.mentions[0].id == interaction.author.id
                    else "p2"
                ]:
                    self.bot.configs[interaction.guild.id]["games"][
                        str(interaction.channel.id)
                    ]["signs"][
                        "p1"
                        if interaction.message.mentions[0].id == interaction.author.id
                        else "p2"
                    ] = interaction.component.emoji.name

                    await interaction.response.send_message(
                        content=f"You chose the sign {interaction.component.emoji.name}",
                        ephemeral=True,
                    )

                    self.bot.games_repo.update_game(
                        interaction.guild.id,
                        interaction.channel.id,
                        dict(
                            self.bot.configs[interaction.guild.id]["games"][
                                str(interaction.channel.id)
                            ]
                        ),
                    )
                else:
                    return await interaction.response.send_message(
                        content=f"You already chose the sign {self.bot.configs[interaction.guild.id]['games'][str(interaction.channel.id)]['signs']['p1' if interaction.message.mentions[0].id == interaction.author.id else 'p2']}",
                        ephemeral=True,
                    )

                if (
                    self.bot.configs[interaction.guild.id]["games"][
                        str(interaction.channel.id)
                    ]["signs"]["p1"]
                    and self.bot.configs[interaction.guild.id]["games"][
                        str(interaction.channel.id)
                    ]["signs"]["p2"]
                ):
                    winner = check_for_win_rockpaperscissors(
                        self.bot.configs[interaction.guild.id]["games"][
                            str(interaction.channel.id)
                        ]["signs"]["p1"],
                        self.bot.configs[interaction.guild.id]["games"][
                            str(interaction.channel.id)
                        ]["signs"]["p2"],
                    )
                    nl = "\n"
                    view = View(timeout=None)
                    view.add_item(
                        Button(
                            emoji="🪨",
                            custom_id=f"{interaction.channel.id}.rock",
                            disabled=True,
                        )
                    )
                    view.add_item(
                        Button(
                            emoji="📄",
                            custom_id=f"{interaction.channel.id}.paper",
                            disabled=True,
                        )
                    )
                    view.add_item(
                        Button(
                            emoji="✂️",
                            custom_id=f"{interaction.channel.id}.scissors",
                            disabled=True,
                        )
                    )

                    await interaction.message.edit(
                        content=f"🪨📄✂️ - {interaction.message.mentions[0].mention} **VS** {interaction.message.mentions[1].mention} - ✂️📄🪨{nl}{nl}{f'🎉 - **The winner is:** `{interaction.message.mentions[winner].name}`! - 🎉' if winner is not None else f'**It{apostroph}s a tie**'}{nl}{nl}`{interaction.message.mentions[0].name}` {self.bot.configs[interaction.guild.id]['games'][str(interaction.channel.id)]['signs']['p1']} 🆚 {self.bot.configs[interaction.guild.id]['games'][str(interaction.channel.id)]['signs']['p2']} `{interaction.message.mentions[1].name}`",
                        view=view,
                    )

                    await interaction.message.add_reaction("💥")
            # elif interaction.channel.name.startswith("yahtzee-"):
            #     if (
            #         interaction.author
            #         not in self.bot.configs[interaction.guild.id]["games"][
            #             str(interaction.channel.id)
            #         ]["players"].values()
            #     ):
            #         return await interaction.response.send_message(
            #             f"⛔ - {interaction.author.mention} - Seul les participants du yams peuvent jouer",
            #             ephemeral=True,
            #         )
            #
            #     if (
            #         interaction.author
            #         != self.bot.configs[interaction.guild.id]["games"][
            #             str(interaction.channel.id)
            #         ]["current_player"]
            #     ):
            #         return await interaction.response.send_message(
            #             f"⛔ - {interaction.author.mention} - Ce n'est pas ton tour",
            #             ephemeral=True,
            #         )
            #
            #     await interaction.response.defer()
            #     em: Embed = interaction.message.embeds[0]
            #     view: View = View(timeout=None)
            #
            #     if (
            #         interaction.component.custom_id == "yams_dice"
            #         or interaction.component.custom_id.startswith("yams_reroll")
            #     ):
            #         if (
            #             "to_reroll"
            #             not in self.bot.configs[interaction.guild.id]["games"][
            #                 str(interaction.channel.id)
            #             ]
            #             or not self.bot.configs[interaction.guild.id]["games"][
            #                 str(interaction.channel.id)
            #             ]["to_reroll"]
            #             or interaction.component.custom_id
            #             in ("yams_reroll_again", "yams_reroll_cancel")
            #         ):
            #             self.bot.configs[interaction.guild.id]["games"][
            #                 str(interaction.channel.id)
            #             ]["to_reroll"] = []
            #
            #         if interaction.component.custom_id[-1].isdigit():
            #             self.bot.configs[interaction.guild.id]["games"][
            #                 str(interaction.channel.id)
            #             ]["to_reroll"].append(int(interaction.component.custom_id[-1]))
            #         elif interaction.component.custom_id == "yams_reroll":
            #             self.bot.configs[interaction.guild.id]["games"][
            #                 str(interaction.channel.id)
            #             ]["game"].c_player.roll(
            #                 [
            #                     x
            #                     not in self.bot.configs[interaction.guild.id]["games"][
            #                         str(interaction.channel.id)
            #                     ]["to_reroll"]
            #                     for x in range(1, 6)
            #                 ]
            #             )
            #
            #             self.bot.configs[interaction.guild.id]["games"][
            #                 str(interaction.channel.id)
            #             ]["to_reroll"] = []
            #
            #             em.description = (
            #                 "Vous avez relancé les dés et obtenu les suivants:\n\n"
            #                 + ", ".join(
            #                     f"`{d}`"
            #                     for d in self.bot.configs[interaction.guild.id][
            #                         "games"
            #                     ][str(interaction.channel.id)]["game"].c_player.dice
            #                 )
            #                 + f"\n\n**Selectionnez les dés que vous ne souhaitez pas relancer**\n\n#️⃣ - Recommencer la sélection - #️⃣\n\n🎲 - Relancer les dés non sélectionnés - 🎲\n\n✅ - Valider les dés - ✅\n\n🌐 - Lire les règles du Yams - 🌐\n\n*Il vous reste {self.bot.configs[interaction.guild.id]['games'][str(interaction.channel.id)]['game'].c_player.rolls_left} lancé{'s' if self.bot.configs[interaction.guild.id]['games'][str(interaction.channel.id)]['game'].c_player.rolls_left > 1 else ''} restants*"
            #             )
            #         elif interaction.component.custom_id == "yams_dice":
            #             self.bot.configs[interaction.guild.id]["games"][
            #                 str(interaction.channel.id)
            #             ]["game"].c_player.roll([0, 0, 0, 0, 0])
            #
            #             em.description = (
            #                 "Vous avez lancé les dés et obtenu les suivants:\n\n"
            #                 + ", ".join(
            #                     f"`{d}`"
            #                     for d in self.bot.configs[interaction.guild.id][
            #                         "games"
            #                     ][str(interaction.channel.id)]["game"].c_player.dice
            #                 )
            #                 + f"\n\n**Selectionnez les dés que vous ne souhaitez pas relancer**\n\n#️⃣ - Recommencer la sélection - #️⃣\n\n🎲 - Relancer les dés non sélectionnés - 🎲\n\n✅ - Valider les dés - ✅\n\n🌐 - Lire les règles du Yams - 🌐\n\n*Il vous reste {self.bot.configs[interaction.guild.id]['games'][str(interaction.channel.id)]['game'].c_player.rolls_left} lancé{'s' if self.bot.configs[interaction.guild.id]['games'][str(interaction.channel.id)]['game'].c_player.rolls_left > 1 else ''} restants*"
            #             )
            #
            #         for x in range(1, 6):
            #             view.add_item(
            #                 Button(
            #                     emoji=NUM2EMOJI[x],
            #                     custom_id=f"yams_reroll_{x}",
            #                     disabled=not self.bot.configs[interaction.guild.id][
            #                         "games"
            #                     ][str(interaction.channel.id)][
            #                         "game"
            #                     ].c_player.rolls_left
            #                     or (
            #                         x
            #                         in self.bot.configs[interaction.guild.id]["games"][
            #                             str(interaction.channel.id)
            #                         ]["to_reroll"]
            #                     ),
            #                 )
            #             )
            #
            #         view.add_item(
            #             Button(
            #                 emoji="#️⃣",
            #                 custom_id="yams_reroll_cancel",
            #                 style=ButtonStyle.danger,
            #             )
            #         )
            #         view.add_item(
            #             Button(
            #                 emoji="🎲",
            #                 custom_id="yams_reroll",
            #                 disabled=not self.bot.configs[interaction.guild.id][
            #                     "games"
            #                 ][str(interaction.channel.id)]["game"].c_player.rolls_left,
            #                 style=ButtonStyle.primary,
            #             )
            #         )
            #         view.add_item(
            #             Button(
            #                 emoji="✅",
            #                 custom_id="yams_validate_dice",
            #                 disabled=self.bot.configs[interaction.guild.id]["games"][
            #                     str(interaction.channel.id)
            #                 ]["to_reroll"]
            #                 != [],
            #                 style=ButtonStyle.success,
            #             )
            #         )
            #     elif interaction.component.custom_id == "yams_validate_dice":
            #         em.description = (
            #             "Vous avez validé vos dés et obtenu les suivants:\n\n"
            #             + ", ".join(
            #                 f"`{d}`"
            #                 for d in self.bot.configs[interaction.guild.id]["games"][
            #                     str(interaction.channel.id)
            #                 ]["game"].c_player.dice
            #             )
            #             + f"\n\n**Selectionnez la case dans laquelle vous voulez entrer votre score**\n\n"
            #         )
            #
            #         for x in range(1, 13):
            #             em.description += f"{NUM2EMOJI[x]} - {yams_scoreboard[x - 1]} - {NUM2EMOJI[x]}\n"
            #
            #             print(
            #                 self.bot.configs[interaction.guild.id]["games"][
            #                     str(interaction.channel.id)
            #                 ]["game"].c_player.t_scorecard[x - 1]
            #             )
            #
            #             if x < 10:
            #                 view.add_item(
            #                     Button(
            #                         emoji=NUM2EMOJI[x],
            #                         custom_id=f"yams_choose_{x}",
            #                         disabled=bool(
            #                             self.bot.configs[interaction.guild.id]["games"][
            #                                 str(interaction.channel.id)
            #                             ]["game"].c_player.t_scorecard[x - 1][1]
            #                         ),
            #                     )
            #                 )
            #             else:
            #                 view.add_item(
            #                     Button(
            #                         label=NUM2EMOJI[x],
            #                         custom_id=f"yams_choose_{x}",
            #                         disabled=bool(
            #                             self.bot.configs[interaction.guild.id]["games"][
            #                                 str(interaction.channel.id)
            #                             ]["game"].c_player.t_scorecard[x - 1][1]
            #                         ),
            #                     )
            #                 )
            #
            #     view.add_item(
            #         Button(
            #             emoji="🌐",
            #             url="https://www.joueclub.fr/contenu/yams-ou-yahtzee-les-regles-officielles.html",
            #         )
            #     )
            #     await interaction.edit_original_message(embed=em, view=view)


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
