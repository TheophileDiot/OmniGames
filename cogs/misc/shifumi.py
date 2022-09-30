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


class ShiFuMi(Cog, name="misc.shifumi"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot

    @slash_command(
        name="shifumi",
        description="Démarre une partie de shifumi contre un autre membre du serveur",
    )
    @max_concurrency(1, BucketType.member)
    async def game_rockpaperscissors_slash_command(
        self, inter: ApplicationCommandInteraction, membre: Member
    ):
        """
        Cette commande démarre une partie de shifumi contre un autre membre du serveur

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            L'intéraction de commande
        membre: :class:`disnake.Member`
            Le membre du serveur auquel jouer contre
        """
        if not await self.bot.utils_class.check_games_category(inter):
            return

        channel_name = f"shifumi-{self.bot.utils_class.normalize_name(inter.author.name)}-{self.bot.utils_class.normalize_name(membre.name)}"
        channel = await self.bot.utils_class.check_game_creation(
            inter, membre, ["shifumi"]
        )

        if channel:
            return

        channel = await inter.guild.create_text_channel(
            name=channel_name,
            overwrites={
                membre: PermissionOverwrite(
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
            reason=f"Création de la partie de shifumi opposant {inter.author} et {membre}",
        )

        await inter.response.send_message(
            f"🪨📄✂️ - La partie de shifumi {channel.mention} opposant `{inter.author.name}` et `{membre.name}` vient d'être créée - 🪨📄✂️"
        )

        view = View(timeout=None)
        view.add_item(Button(emoji="🪨", custom_id=f"{channel.id}.rock"))
        view.add_item(Button(emoji="📄", custom_id=f"{channel.id}.paper"))
        view.add_item(Button(emoji="✂️", custom_id=f"{channel.id}.scissors"))

        msg = await channel.send(
            content=f"🪨📄✂️ - {inter.author.mention} **VS** {membre.mention} - ✂️📄🪨\n\n**Choisis un signe:**\n\n`{inter.author.name}` 🪹 🆚 🪹 `{membre.name}`",
            view=view,
        )

        if "games" not in self.bot.configs[inter.guild.id]:
            self.bot.configs[inter.guild.id]["games"] = {}

        self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
            "game_id": msg.id,
            "players": {"p1": inter.author, "p2": membre},
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
    bot.add_cog(ShiFuMi(bot))
