from disnake import (
    ButtonStyle,
    Embed,
    MessageInteraction,
)
from disnake.ext.commands import Cog
from disnake.ui import Button, View

from bot import OmniGames
<<<<<<< HEAD
from cogs.misc.yams import yams_scoreboard
from data import check_for_win_tictactoe, check_for_win_rockpaperscissors, NUM2EMOJI
=======
>>>>>>> 83867a8a0c181f0e3df4616b7ba685bdfc379dc0


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
            pass
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
