from inspect import Parameter
from typing import List

from disnake import (
    ApplicationCommandInteraction,
    CategoryChannel,
    TextChannel,
)
from disnake.ext.commands import (
    Cog,
    slash_command,
)
from disnake.ext.commands.errors import (
    MissingRequiredArgument,
)

from bot import OmniGames

BOOL2VAL = {True: "ON", False: "OFF"}


class Moderation(Cog, name="moderation.config"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    """ GAMES CATEGORY """

    @slash_command(
        name="games_category",
        description="Manages the server's games category where all the game channels are created",
    )
    async def config_channels_games_category_slash_group(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """
        This slash command group manages the server's games category where all the game channels are created

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        pass

    @config_channels_games_category_slash_group.sub_command(
        name="display",
        description="Displays the server's games category",
    )
    async def config_channels_games_category_display_slash_command(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """
        This slash command displays the server's games category

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        await self.handle_games_category(inter)

    @config_channels_games_category_slash_group.sub_command(
        name="set",
        description="Sets the server's games category",
    )
    async def config_channels_games_category_set_slash_command(
        self,
        inter: ApplicationCommandInteraction,
        category: CategoryChannel,
    ):
        """
        This slash command sets the server's games category

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        category: :class:`disnake.CategoryChannel` optional
            The category that will be the games category
        """
        await self.handle_games_category(inter, "set", category)

    @config_channels_games_category_slash_group.sub_command(
        name="remove",
        description="Removes the server's games category",
    )
    async def config_channels_games_category_remove_slash_command(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """
        This slash removes the server's games category

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        await self.handle_games_category(inter, "remove")

    async def handle_games_category(
        self,
        source: ApplicationCommandInteraction,
        option: str = None,
        games_category: CategoryChannel = None,
    ):
        try:
            if option:
                if option == "set":
                    if not games_category:
                        raise MissingRequiredArgument(
                            param=Parameter(
                                name="category", kind=Parameter.KEYWORD_ONLY
                            )
                        )
                    elif (
                        "games_category" in self.bot.configs[source.guild.id]
                        and self.bot.configs[source.guild.id]["games_category"]
                        == games_category
                    ):
                        return await source.response.send_message(
                            f"ℹ️ - The server's games category is already {games_category.mention}!",
                            ephemeral=True,
                        )

                    if (
                        "games_category" in self.bot.configs[source.guild.id]
                        and self.bot.configs[source.guild.id]["games_category"]
                    ):
                        if (
                            self.bot.configs[source.guild.id]["games_category"]
                            .permissions_for(source.guild.me)
                            .manage_channels
                        ):
                            if games_category.permissions_for(
                                source.guild.me
                            ).manage_channels:
                                channels: List[TextChannel] = self.bot.configs[
                                    source.guild.id
                                ]["games_category"].channels

                                for channel in channels:
                                    await channel.edit(
                                        category=games_category,
                                        reason=f"Games category set to {games_category} by {source.author}!",
                                    )
                            else:
                                await self.bot.utils_class.send_message_to_mods(
                                    f"⚠️ - I don't have the right permissions to edit channels in the category {games_category.mention}! Required perms: `{', '.join(['MANAGE_CHANNELS'])}`",
                                    source.guild.id,
                                )
                        else:
                            await self.bot.utils_class.send_message_to_mods(
                                f"⚠️ - I don't have the right permissions to edit channels in the category {self.bot.configs[source.guild.id]['games_category'].mention}! Required perms: `{', '.join(['MANAGE_CHANNELS'])}`",
                                source.guild.id,
                            )

                    self.bot.config_repo.set_games_category(
                        source.guild.id,
                        games_category.id,
                    )
                    self.bot.configs[source.guild.id]["games_category"] = games_category

                    await source.response.send_message(
                        f"ℹ️ - The games category is now {games_category.mention} in this guild!"
                    )
                elif option == "remove":
                    if "games_category" not in self.bot.configs[source.guild.id]:
                        return await source.response.send_message(
                            f"ℹ️ - The server already doesn't have a games category configured!",
                            ephemeral=True,
                        )

                    self.bot.config_repo.set_games_category(source.guild.id, None)
                    del self.bot.configs[source.guild.id]["games_category"]

                    await source.response.send_message(
                        f"ℹ️ - This guild doesn't have a games category anymore!"
                    )
            else:
                await source.response.send_message(
                    f"ℹ️ - The current server's games category is: {self.bot.configs[source.guild.id]['games_category'].mention}"
                    if "games_category" in self.bot.configs[source.guild.id]
                    else f"ℹ️ - The server doesn't have a games category yet!"
                )
        except MissingRequiredArgument as mre:
            raise MissingRequiredArgument(param=mre.param)
        except Exception as e:
            await source.channel.send(
                f"⚠️ - {source.author.mention} - An error occurred while setting the games category! please try again in a few seconds! Error type: {type(e)}",
                delete_after=20,
            )


def setup(bot: OmniGames):
    bot.add_cog(Moderation(bot))
