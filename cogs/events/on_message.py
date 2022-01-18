from disnake import Forbidden, Message
from disnake.ext.commands import Cog

from bot import OmniGames
from data import Utils


class Events(Cog, name="events.on_message"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    """ EVENT """

    @Cog.listener()
    @Utils.check_bot_starting()
    async def on_message(self, message: Message):
        """When a message is sent, if the prevent_invites option is on check if there is an invitation link to another discord server in the message and is the xp is on then manage the user's xp"""
        await self.bot.wait_until_ready()
        if message.is_system() or message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message=message)

        if (
            ctx.message.mentions
            and self.bot.user in ctx.message.mentions
            and (
                len(ctx.message.content) == len(f"{self.bot.user.mention}")
                or len(ctx.message.content) == len(f"{self.bot.user.mention}") + 1
            )
        ):
            try:
                msg = await ctx.send(
                    f"ℹ️ - {ctx.author.mention} - Here's my prefix for this guild: `{self.bot.utils_class.get_guild_pre(ctx.message)[0]}`!"
                )
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to send messages in the channel {ctx.channel.mention} (message: `ℹ️ - {ctx.author.mention} - Here's my prefix for this guild: `{self.bot.utils_class.get_guild_pre(ctx.message)[0]}`!`)!"
                raise

            try:
                await msg.add_reaction("👀")
            except Forbidden as f:
                f.text = f"⚠️ - I don't have the right permissions to add reactions in the channel {ctx.channel.mention} (message: {msg.jump_url}, reaction: 👀)!"
                raise


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
