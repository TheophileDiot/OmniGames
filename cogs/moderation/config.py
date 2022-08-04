from inspect import Parameter
from typing import List, Union

from disnake import (
    CategoryChannel,
    GuildCommandInteraction,
    Member,
    NotFound,
    Role,
    TextChannel,
)
from disnake.ext.commands import (
    Cog,
    Param,
    slash_command,
)
from disnake.ext.commands.errors import BadUnionArgument, MissingRequiredArgument

from bot import OmniGames
from data.utils import Utils

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
        inter: GuildCommandInteraction,
    ):
        """
        This slash command group manages the server's games category where all the game channels are created

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        """
        pass

    @config_channels_games_category_slash_group.sub_command(
        name="display",
        description="Displays the server's games category",
    )
    async def config_channels_games_category_display_slash_command(
        self,
        inter: GuildCommandInteraction,
    ):
        """
        This slash command displays the server's games category

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        """
        await self.handle_games_category(inter)

    @config_channels_games_category_slash_group.sub_command(
        name="set",
        description="Sets the server's games category",
    )
    async def config_channels_games_category_set_slash_command(
        self,
        inter: GuildCommandInteraction,
        category: CategoryChannel,
    ):
        """
        This slash command sets the server's games category

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
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
        inter: GuildCommandInteraction,
    ):
        """
        This slash removes the server's games category

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        """
        await self.handle_games_category(inter, "remove")

    async def handle_games_category(
        self,
        source: GuildCommandInteraction,
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
                try:
                    await source.response.send_message(
                        f"ℹ️ - The current server's games category is: {self.bot.configs[source.guild.id]['games_category'].mention} ({self.bot.configs[source.guild.id]['games_category'].id})"
                        if "games_category" in self.bot.configs[source.guild.id]
                        else f"ℹ️ - The server doesn't have a games category yet!"
                    )
                except AttributeError:
                    self.bot.config_repo.set_games_category(source.guild.id, None)
                    del self.bot.configs[source.guild.id]["games_category"]

                    await source.response.send_message(
                        f"ℹ️ - The server doesn't have a games category yet!"
                    )
        except MissingRequiredArgument as mre:
            raise MissingRequiredArgument(param=mre.param)
        except Exception as e:
            await source.channel.send(
                f"⚠️ - {source.author.mention} - An error occurred while setting the games category! please try again in a few seconds! Error type: {type(e)}",
                delete_after=20,
            )

    """ DJS """

    @slash_command(
        name="djs",
        description="Manages the server's djs (role & members)",
    )
    @Utils.check_bot_starting()
    @Utils.check_moderator()
    async def config_djs_slash_group(self, inter: GuildCommandInteraction):
        """
        This slash command group manages the server's djs (role & members)

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        """
        pass

    @config_djs_slash_group.sub_command(
        name="list",
        description="Lists members/roles in the server's djs list",
    )
    async def config_djs_list_slash_command(
        self,
        inter: GuildCommandInteraction,
    ):
        """
        This slash command group lists members/roles in the server's djs list

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        """
        await self.handle_djs(inter)

    @config_djs_slash_group.sub_command(
        name="add",
        description="Adds members/roles to the server's djs list (can add multiple at a time)",
    )
    async def config_djs_add_slash_command(
        self,
        inter: GuildCommandInteraction,
        djs: List[Union[Member, Role]] = Param(converter=Utils.mentionable_converter),
    ):
        """
        This slash command adds members/roles to the server's djs list (can add multiple at a time)

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        djs: :class:`typing.List[typing.Union[disnake.Member, disnake.Role]]` optional
            The djs (that can be either roles or members) (mentions only)
        """
        if djs:
            await self.handle_djs(inter, "add", *djs)

    @config_djs_slash_group.sub_command(
        name="remove",
        description="Removes members/roles from the server's djs list (can remove multiple at a time)",
    )
    async def config_djs_remove_slash_command(
        self,
        inter: GuildCommandInteraction,
        djs: List[Union[Member, Role]] = Param(
            default=None, converter=Utils.mentionable_converter
        ),
    ):
        """
        This slash command removes members/roles from the server's djs list (can remove multiple at a time)

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        djs: :class:`typing.List[typing.Union[disnake.Member, disnake.Role]]` optional
            The djs (that can be either roles or members) (mentions only)
        """
        if djs:
            await self.handle_djs(inter, "remove", *djs)

    @config_djs_slash_group.sub_command(
        name="purge", description="Purges the server's djs list"
    )
    async def config_djs_purge_slash_command(
        self,
        inter: GuildCommandInteraction,
    ):
        """
        This slash command purges the server's djs list

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        """
        await self.handle_djs(inter, "purge")

    async def handle_djs(
        self,
        source: GuildCommandInteraction,
        option: str = None,
        *djs: Union[Member, Role],
    ):
        if option:
            try:
                if option in ("add", "remove"):
                    if not djs:
                        raise MissingRequiredArgument(
                            param=Parameter(name="djs", kind=Parameter.KEYWORD_ONLY)
                        )

                    _djs = djs
                    djs = list(djs)
                    warning_djs = []
                    dropped_djs = []
                    bot_djs = []
                    for dj in _djs:
                        if option == "add":
                            if dj.id in set(self.bot.djs[source.guild.id]):
                                del djs[djs.index(dj)]
                                dropped_djs.append(dj)
                                continue
                            elif isinstance(dj, Member) and dj.bot:
                                del djs[djs.index(dj)]
                                bot_djs.append(dj)
                                continue

                            self.bot.config_repo.add_dj(
                                source.guild.id, dj.id, f"{dj}", type(dj).__name__
                            )
                            self.bot.djs[source.guild.id].append(dj.id)
                        elif option == "remove":
                            if dj.id not in set(self.bot.djs[source.guild.id]):
                                del djs[djs.index(dj)]
                                dropped_djs.append(dj)
                                continue

                            self.bot.config_repo.remove_dj(source.guild.id, dj.id)
                            del self.bot.djs[source.guild.id][
                                self.bot.djs[source.guild.id].index(dj.id)
                            ]

                            try:
                                await source.channel.send(
                                    f"ℹ️ - Removed `@{source.guild.get_member(int(dj.id)) or await source.guild.fetch_member(int(dj.id)) if isinstance(dj, Member) else source.guild.get_role(int(dj.id))}` {'role' if isinstance(dj, Role) else 'member'} from the djs list!."
                                )
                            except NotFound:
                                pass

                    resp = ""

                    if bot_djs:
                        resp += f"ℹ️ - {source.author.mention} - {', '.join([f'`@{dj}`' for dj in bot_djs])} {'is a' if len(bot_djs) == 1 else 'are'} bot user{'s' if len(bot_djs) > 1 else ''} so you can't add {'them' if len(bot_djs) > 1 else 'him'} in the djs list!"

                    if dropped_djs:
                        resp += (
                            ("\n" if resp else f"ℹ️ - {source.author.mention} - ")
                            + f"{', '.join([f'`@{dj} ({type(dj).__name__})`' for dj in dropped_djs])} {'is' if len(dropped_djs) == 1 else 'are'} already {'not' if option == 'remove' else ''} in the djs list!"
                        )

                    if warning_djs:
                        resp += (
                            ("\n" if resp else f"ℹ️ - {source.author.mention} - ")
                            + f"{', '.join([f'`@{dj[0]} ({type(dj[0]).__name__})` is already assigned to a {dj[1]} role' for dj in warning_djs])}!"
                        )

                    if resp:
                        await source.channel.send(resp, delete_after=20)

                    if djs:
                        await source.response.send_message(
                            f"ℹ️ - {'Added' if option == 'add' else 'Removed'} {', '.join([f'`@{dj} ({type(dj).__name__})`' for dj in djs])} {'to' if option == 'add' else 'from'} the djs list!."
                        )
                elif option == "purge":
                    if not self.bot.djs[source.guild.id]:
                        return await source.response.send_message(
                            f"ℹ️ - {source.author.mention} - No djs (members & roles) have been added to the list yet!",
                            ephemeral=True,
                        )

                    self.bot.config_repo.purge_djs(source.guild.id)
                    self.bot.djs[source.guild.id] = {}

                    await source.response.send_message(
                        f"ℹ️ - Removed all the djs from the djs list!."
                    )
                else:
                    await source.reply(
                        f"ℹ️ - {source.author.mention} - This option isn't available for the command `{source.command.qualified_name}`! option: `{option}`! Use the command `{self.bot.utils_class.get_guild_pre(source.message)[0]}{source.command.parents[0]}` to get more help!",
                        delete_after=20,
                    )
            except MissingRequiredArgument as mre:
                raise MissingRequiredArgument(param=mre.param)
            except BadUnionArgument as bua:
                raise BadUnionArgument(
                    param=bua.param, converters=bua.converters, errors=bua.errors
                )
            except Exception as e:
                await source.channel.send(
                    f"⚠️ - {source.author.mention} - An error occurred while {'adding' if option == 'add' else 'removing'} `@{dj}` {'role' if isinstance(dj, Role) else 'member'} to the djs list! please try again in a few seconds! Error type: {type(e)}",
                    delete_after=20,
                )
        else:
            server_djs = self.bot.config_repo.get_djs(source.guild.id).values()

            if not server_djs:
                return await source.response.send_message(
                    f"ℹ️ - {source.author.mention} - No djs (members & roles) have been added to the list yet!",
                    ephemeral=True,
                )

            server_djs_roles = []
            server_djs_members = []

            for m in server_djs:
                if m["type"] == "Role":
                    server_djs_roles.append(m["name"])
                else:
                    server_djs_members.append(m["name"])

            await source.response.send_message(
                f"**ℹ️ - Here's the list of the server's djs:**\n\n"
                + (
                    f"Members: {', '.join(f'`{m}`' for m in server_djs_members)}\n"
                    if server_djs_members
                    else ""
                )
                + (
                    f"Roles: {', '.join(f'`{r}`' for r in server_djs_roles)}\n"
                    if server_djs_roles
                    else ""
                )
            )


def setup(bot: OmniGames):
    bot.add_cog(Moderation(bot))
