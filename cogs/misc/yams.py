from random import sample
from typing import List

from disnake import (
    ApplicationCommandInteraction,
    ButtonStyle,
    Embed,
    Member,
    Message,
    PermissionOverwrite,
)
from disnake.ext.commands import (
    BucketType,
    Cog,
    max_concurrency,
    Param,
    slash_command,
)
from disnake.ui import Button, View
from yahtzee_api.game import Game as Yahtzee_Game

from bot import OmniGames
from data import Utils

yams_scoreboard = {
    0: "1",
    1: "2",
    2: "3",
    3: "4",
    4: "5",
    5: "6",
    6: "Brelan",
    7: "Carré",
    8: "Full house",
    9: "Suite courte",
    10: "Suite longue",
    11: "Yams",
    12: "Chance",
}


class Yams(Cog, name="misc.yams"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    """ GROUP """

    @slash_command(
        name="yams",
        description="Gère le jeux du yams",
    )
    async def yams_slash_command_group(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """
        Ce groupe de commande gère le jeux du yams

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            L'intéraction de commande
        """
        if not await self.bot.utils_class.check_games_category(inter):
            return

    """ GROUP'S COMMAND(S) """

    @yams_slash_command_group.sub_command(
        name="créer",
        description="Démarre une partie de yams contre d'autres membres du serveur",
    )
    @max_concurrency(1, BucketType.member)
    async def yahtzee_create_slash_command(
        self,
        inter: ApplicationCommandInteraction,
        membres: List[Member] = Param([], converter=Utils.members_converter),
    ):
        """
        Cette commande démarre une partie de yams contre d'autres membres du serveur

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            L'intéraction de commande
        membres: :class:`typing.List[disnake.Member]`
            Les membres participants au yams (5 max)
        """
        if not await self.bot.utils_class.check_game_members(inter, membres, "yams"):
            return

        overwrites = (
            {
                inter.author: PermissionOverwrite(
                    **{
                        "view_channel": True,
                        "send_messages": True,
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
                inter.guild.default_role: PermissionOverwrite(
                    **{
                        "view_channel": True,
                        "send_messages": False,
                        "use_slash_commands": False,
                        "add_reactions": False,
                    }
                ),
            }
            | {
                member: PermissionOverwrite(
                    **{
                        "view_channel": True,
                        "send_messages": True,
                        "use_slash_commands": False,
                        "add_reactions": False,
                    }
                )
                for member in membres
            }
            if membres
            else {}
        )

        channel = await inter.guild.create_text_channel(
            name=f"yams-{self.bot.utils_class.normalize_name(inter.author.name)}",
            overwrites=overwrites,
            category=self.bot.configs[inter.guild.id]["games_category"],
            reason=f"Création de la partie de Yams de {inter.author}",
        )

        membres.extend([inter.author])

        await inter.response.send_message(
            f"🎲🎲🎲🎲🎲 - La partie de Yams {channel.mention} avec {', '.join([f'`{m.name}`' for m in membres])} vient d'être créée - 🎲🎲🎲🎲🎲"
        )

        if "games" not in self.bot.configs[inter.guild.id]:
            self.bot.configs[inter.guild.id]["games"] = {}

        msg: Message = await channel.send(
            "🎲🎲🎲🎲🎲 - Création de la partie en cours... - 🎲🎲🎲🎲🎲"
        )
        self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
            "game_id": msg.id,
            "players": {f"p{x}": membres[x - 1] for x in range(1, len(membres) + 1)},
            "game_type": "yams",
            "contestants": iter(sample(membres, len(membres))),
            "game": Yahtzee_Game(len(membres)),
        }

        self.bot.configs[inter.guild.id]["games"][str(channel.id)][
            "current_player"
        ] = next(
            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["contestants"]
        )

        self.bot.games_repo.create_game(
            inter.guild.id,
            channel.id,
            msg.id,
            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
            "yams",
        )

        em = Embed(
            colour=self.bot.color,
            description=f"**Que souhaitez vous faire ?**\n\n🎲 - Lancer les dés - 🎲\n🌐 - Lire les règles du Yams - 🌐",
        )

        view = View(timeout=None)
        view.add_item(
            Button(emoji="🎲", custom_id="yams_dice", style=ButtonStyle.primary)
        )
        view.add_item(
            Button(
                emoji="🌐",
                url="https://www.joueclub.fr/contenu/yams-ou-yahtzee-les-regles-officielles.html",
            )
        )

        em.set_author(
            name=f"C'est au tour de {self.bot.configs[inter.guild.id]['games'][str(channel.id)]['current_player'].name}",
            icon_url=self.bot.configs[inter.guild.id]["games"][str(channel.id)][
                "current_player"
            ].avatar.url
            if self.bot.configs[inter.guild.id]["games"][str(channel.id)][
                "current_player"
            ].avatar
            else "https://s3.amazonaws.com/itunes-images/app-assets/967422975/115971072/967422975-115971072-circularArtwork-300.jpg",
        )

        em.set_footer(
            text=f"🎲 - {self.bot.configs[inter.guild.id]['games'][str(channel.id)]['game'].remaining_turns} tours restants - 🎲"
        )

        await msg.edit(
            content=f"🎲🎲🎲🎲🎲 - YAMS! - 🎲🎲🎲🎲🎲\n\n**PARTICIPANTS:** {', '.join([f'{member.mention}' for member in self.bot.configs[inter.guild.id]['games'][str(channel.id)]['players'].values()])}"
        )
        await msg.add_reaction("💥")

        await channel.send(embed=em, view=view)


def setup(bot: OmniGames):
    bot.add_cog(Yams(bot))
