from time import time

from disnake import Member, PermissionOverwrite, VoiceState
from disnake.ext.commands import Cog

from data import Utils


class Events(Cog, name="events.on_voice_state_update"):
    def __init__(self, bot):
        self.bot = bot

    """ EVENT """

    @Cog.listener()
    @Utils.check_bot_starting()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        if member.bot:
            return

        if before.channel is not None and after.channel != before.channel:
            if not [m for m in before.channel.members if not m.bot]:
                if member.guild.voice_client:
                    await member.guild.voice_client.disconnect(force=True)

                self.bot.playlists[member.guild.id].clear()


def setup(bot):
    bot.add_cog(Events(bot))
