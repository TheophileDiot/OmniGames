from disnake import (
    Embed,
    GuildCommandInteraction,
    HTTPException,
    PartyType,
    VoiceChannel,
)
from disnake.ext.commands import (
    Cog,
    guild_only,
    slash_command,
)
from disnake.http import Route

from bot import OmniGames
from data import Utils


class Miscellaneous(Cog, name="misc.activity"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @slash_command(
        name="activity",
        description="Manages the server's activities",
    )
    @guild_only()
    @Utils.check_bot_starting()
    async def activity_slash_command(
        self,
        inter: GuildCommandInteraction,
        channel: VoiceChannel,
        activity: PartyType = None,
        custom_activity: int = None,
    ):
        """
        This slash command manages the server's activities

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.GuildCommandInteraction`
            The application command interaction
        channel: :class:`disnake.VoiceChannel`
            The voice channel where the activity will take place
        activity: :class:`PartyType` optional
            Choose one of the default activities available
        custom_activity: :class:`int` optional
            If you know an activity that is not shown in the activity section then enter it's ID here!
        """
        if not isinstance(channel, VoiceChannel):
            return await inter.response.send_message(
                "The channel precised must be a valid VoiceChannel!", ephemeral=True
            )
        elif not activity and custom_activity:
            activity = custom_activity
        elif not activity:
            return await inter.response.send_message(
                "Select at least an activity or enter a custom one!", ephemeral=True
            )

        data = {
            "max_age": 0,
            "max_uses": 0,
            "target_application_id": activity,
            "target_type": 2,
            "temporary": False,
        }

        try:
            resp = await self.bot.http.request(
                Route("POST", f"/channels/{channel.id}/invites"), json=data
            )
        except HTTPException as e:
            if e.code == 50035:
                return await inter.response.send_message(
                    f"⚠️ - {inter.author.mention} - The application ID you gave is not an available one!",
                    ephemeral=True,
                )
            else:
                return await inter.response.send_message(
                    f"⚠️ - {inter.author.mention} - An error happened, please try again in a few seconds!",
                    ephemeral=True,
                )

        em = Embed(
            colour=self.bot.color,
            title="The channel is ready!",
            description=f"Added **{resp['target_application']['name']}** to {channel.mention}\n> Click on the hyperlink to join.",
            url=f"https://discord.gg/{resp['code']}",
        )
        em.set_thumbnail(
            url=f"https://cdn.discordapp.com/app-icons/{resp['target_application']['id']}/{resp['target_application']['icon']}.png"
        )
        em.set_author(
            name=f"{inter.author}",
            icon_url=inter.author.avatar.url if inter.author.avatar else None,
        )

        if self.bot.user.avatar:
            em.set_footer(
                text=f"Requested by {inter.author}", icon_url=self.bot.user.avatar.url
            )
        else:
            em.set_footer(text=f"Requested by {inter.author}")

        await inter.response.send_message(embed=em)


def setup(bot: OmniGames):
    bot.add_cog(Miscellaneous(bot))
