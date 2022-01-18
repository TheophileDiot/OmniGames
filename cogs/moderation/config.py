from inspect import Parameter
from typing import List, Union

from disnake import (
    ApplicationCommandInteraction,
    CategoryChannel,
    Forbidden,
    TextChannel,
)
from disnake.ext.commands import (
    bot_has_permissions,
    Context,
    Cog,
    group,
    guild_only,
    slash_command,
)
from disnake.ext.commands.errors import (
    MissingRequiredArgument,
)

from bot import OmniGames
from data import Utils

BOOL2VAL = {True: "ON", False: "OFF"}


class Moderation(Cog, name="moderation.config"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    """ MAIN GROUP(S) """

    @group(
        pass_context=True,
        case_insensitive=True,
        name="config",
        aliases=["cfg"],
        usage="(sub-command)",
        description="This command manages the server's configuration",
    )
    @Utils.check_bot_starting()
    @Utils.check_moderator()
    @bot_has_permissions(send_messages=True)
    async def config_group(self, ctx: Context):
        """
        This command group manages the server's configuration

        Parameters
        ----------
        ctx: :class:`disnake.ext.commands.Context`
            The command context
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                embed=self.bot.utils_class.get_embed_from_ctx(
                    ctx, title="Server's configuration"
                )
            )

    @slash_command(
        name="config",
        description="This slash command manages the server's configuration",
    )
    @Utils.check_bot_starting()
    @Utils.check_moderator()
    async def config_slash_group(self, inter: ApplicationCommandInteraction):
        """
        This slash command group manages the server's configuration

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        pass

    """ MAIN GROUP(S)'S COMMAND(S) """

    """ PREFIX """

    @config_group.command(
        pass_context=True,
        name="prefix",
        aliases=["prfx"],
        brief="❗",
        description="Manages the server's prefix",
        usage="(set|reset) (<prefix>)",
    )
    async def config_prefix_command(
        self, ctx: Context, option: Utils.to_lower = None, prefix: str = None
    ):
        """
        This command manages the server's prefix

        Parameters
        ----------
        ctx: :class:`disnake.ext.commands.Context`
            The command context
        option: :class:`Utils.to_lower` optional
            The option -> set or reset
        prefix: :class:`str` optional
            The prefix to set if the option set is chosen
        """
        await self.handle_prefix(ctx, option, prefix)

    @slash_command(
        name="prefix",
        description="Manages the server's prefix",
    )
    @guild_only()
    @Utils.check_bot_starting()
    @Utils.check_moderator()
    async def config_prefix_slash_group(self, inter: ApplicationCommandInteraction):
        """
        This slash command manages the server's prefix

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        pass

    @config_prefix_slash_group.sub_command(
        name="display",
        description="Displays the current server's prefix",
    )
    async def config_prefix_display_slash_command(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """
        This slash command display the current server's prefix

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        await self.handle_prefix(inter)

    @config_prefix_slash_group.sub_command(
        name="set",
        description="Sets the current server's prefix",
    )
    async def config_prefix_set_slash_command(
        self,
        inter: ApplicationCommandInteraction,
        prefix: str,
    ):
        """
        This slash command display the current server's prefix

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        prefix: :class:`str`
            The new prefix to set
        """
        await self.handle_prefix(inter, "set", prefix)

    @config_prefix_slash_group.sub_command(
        name="reset",
        description="Reset the current server's prefix (o!)",
    )
    async def config_prefix_reset_slash_command(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """
        This slash command reset the current server's prefix (o!)

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        await self.handle_prefix(inter, "reset")

    async def handle_prefix(
        self,
        source: Union[Context, ApplicationCommandInteraction],
        option: str = None,
        prefix: str = None,
    ):
        if option:
            try:
                if option == "set":
                    if not prefix:
                        raise MissingRequiredArgument(
                            param=Parameter(name="prefix", kind=Parameter.KEYWORD_ONLY)
                        )

                    self.bot.config_repo.set_prefix(source.guild.id, prefix)
                    self.bot.configs[source.guild.id]["prefix"] = prefix

                    if isinstance(source, Context):
                        await source.send(f"ℹ️ - Bot prefix updated to `{prefix}`.")
                    else:
                        await source.response.send_message(
                            f"ℹ️ - Bot prefix updated to `{prefix}`."
                        )
                elif option == "reset":
                    self.bot.config_repo.set_prefix(source.guild.id)
                    self.bot.configs[source.guild.id]["prefix"] = "o!"

                    if isinstance(source, Context):
                        await source.send(f"ℹ️ - Bot prefix has been reset to `o!`.")
                    else:
                        await source.response.send_message(
                            f"ℹ️ - Bot prefix has been reset to `o!`."
                        )
                else:
                    await source.reply(
                        f"ℹ️ - {source.author.mention} - This option isn't available for the command `{source.command.qualified_name}`! option: `{option}`! Use the command `{self.bot.utils_class.get_guild_pre(source.message)[0]}{source.command.parents[0]}` to get more help!",
                        delete_after=20,
                    )
            except MissingRequiredArgument as mre:
                raise MissingRequiredArgument(param=mre.param)
            except Exception as e:
                await source.channel.send(
                    f"⚠️ - {source.author.mention} - An error occurred while {'resetting the prefix' if option == 'reset' else f'setting the prefix to `{prefix}`'}! please try again in a few seconds! Error type: {type(e)}",
                    delete_after=20,
                )
        else:
            if isinstance(source, Context):
                msg = await source.send(
                    f"ℹ️ - {source.author.mention} - Here's my prefix for this guild: `{self.bot.utils_class.get_guild_pre(source.author)[0]}`!"
                )
            else:
                await source.response.send_message(
                    f"ℹ️ - {source.author.mention} - Here's my prefix for this guild: `{self.bot.utils_class.get_guild_pre(source.author)[0]}`!"
                )
                msg = await source.original_message()

            try:
                await msg.add_reaction("👀")
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to add reactions in the channel {source.channel.mention} (message: {msg.jump_url}, reaction: 👀)! Required perms: `{', '.join(['ADD_REACTIONS'])}`"
                raise

    """ GAMES CATEGORY """

    @config_group.command(
        pass_context=True,
        name="games_category",
        aliases=["game_category"],
        brief="🔱",
        description="Manages the server's games category where all the game channels are created",
        usage="(set|remove #category)",
    )
    async def config_channels_games_category_command(
        self,
        ctx: Context,
        option: Utils.to_lower = None,
        games_category: CategoryChannel = None,
    ):
        """
        This command manages the server's games category where all the game channels are created

        Parameters
        ----------
        ctx: :class:`disnake.ext.commands.Context`
            The command context
        option: :class:`Utils.to_lower` optional
            The option -> set or remove
        games_category: :class:`disnake.CategoryChannel` optional
            The category that will be the games category
        """
        await self.handle_games_category(ctx, option, games_category)

    @config_slash_group.sub_command_group(
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
        source: Union[Context, ApplicationCommandInteraction],
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
                        if isinstance(source, Context):
                            return await source.reply(
                                f"ℹ️ - The server's games category is already {games_category.mention}!",
                                delete_after=20,
                            )
                        else:
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

                    if isinstance(source, Context):
                        await source.send(
                            f"ℹ️ - The games category is now {games_category.mention} in this guild!"
                        )
                    else:
                        await source.response.send_message(
                            f"ℹ️ - The games category is now {games_category.mention} in this guild!"
                        )
                elif option == "remove":
                    if "games_category" not in self.bot.configs[source.guild.id]:
                        if isinstance(source, Context):
                            return await source.reply(
                                f"ℹ️ - The server already doesn't have a games category configured!",
                                delete_after=20,
                            )
                        else:
                            return await source.response.send_message(
                                f"ℹ️ - The server already doesn't have a games category configured!",
                                ephemeral=True,
                            )

                    self.bot.config_repo.set_games_category(source.guild.id, None)
                    del self.bot.configs[source.guild.id]["games_category"]

                    if isinstance(source, Context):
                        await source.send(
                            f"ℹ️ - This guild doesn't have a games category anymore!"
                        )
                    else:
                        await source.response.send_message(
                            f"ℹ️ - This guild doesn't have a games category anymore!"
                        )
                else:
                    await source.reply(
                        f"ℹ️ - {source.author.mention} - This option isn't available for the command `{source.command.qualified_name}`! option: `{option}`! Use the command `{self.bot.utils_class.get_guild_pre(source.message)[0]}{source.command.parents[0]}` to get more help!",
                        delete_after=20,
                    )
            else:
                if isinstance(source, Context):
                    await source.send(
                        f"ℹ️ - The current server's games category is: {self.bot.configs[source.guild.id]['games_category'].mention}"
                        if "games_category" in self.bot.configs[source.guild.id]
                        else f"ℹ️ - The server doesn't have a games category yet!"
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
