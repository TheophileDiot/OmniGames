from asyncio import sleep
from random import choice

from disnake import NotFound, RawMessageDeleteEvent
from disnake.ext.commands import Cog
from disnake.ui import Button, View

from bot import OmniGames
from data import NUM2EMOJI


class Events(Cog, name="events.on_raw_message_delete"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        await sleep(1.5)

        if (
            "games" in self.bot.configs[payload.guild_id]
            and str(payload.channel_id) in self.bot.configs[payload.guild_id]["games"]
        ):
            try:
                channel = self.bot.get_channel(
                    payload.channel_id
                ) or await self.bot.fetch_channel(payload.channel_id)
            except NotFound:
                channel = None

            if not channel:
                return

            if payload.cached_message:
                split_message = payload.cached_message.clean_content.split(" ")
                if (
                    "**VS**" not in split_message
                    and "**Score:**" not in split_message
                    and "GUESS:**" not in split_message
                    and "GUESSED:**" not in split_message
                ):
                    return
            else:
                try:
                    message = await channel.fetch_message(
                        self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]["game_id"]
                    )
                    if message:
                        return
                except NotFound:
                    pass

            try:
                guild = self.bot.get_guild(
                    payload.guild_id
                ) or await self.bot.fetch_guild(payload.guild_id)
            except NotFound:
                return

            for x in range(
                1,
                len(
                    self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["players"]
                )
                + 1,
            ):
                try:
                    if self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["players"][f"p{x}"]:
                        player = guild.get_member(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["players"][f"p{x}"].id
                        ) or await guild.fetch_member(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["players"][f"p{x}"].id
                        )
                    else:
                        player = None
                except NotFound:
                    player = None

                if not player:
                    await channel.send(
                        "**One of the players has left the guild so I can't reboot the game**\n\n⚠️ - **Deletion of the channel in **`5`** seconds** - ⚠️"
                    )
                    await sleep(5)
                    del self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]
                    self.bot.games_repo.remove_game(
                        payload.guild_id, payload.channel_id
                    )
                    await channel.delete()
                    return

            game_type = self.bot.configs[payload.guild_id]["games"][
                str(payload.channel_id)
            ]["game_type"]
            content = None
            view = None

            temp_message = await channel.send(
                "**The game message was deleted, the game will "
                + (
                    "reboot in **`5`** seconds**"
                    if game_type != "hangman"
                    else "be destroyed in **`5`** seconds**"
                )
            )
            await sleep(5)

            if game_type == "4inarow":
                board = [
                    ["⬛" if x == 0 or x == 8 or y == 7 else "⚪" for x in range(9)]
                    for y in range(8)
                ]
                nl = "\n"

                content = (
                    payload.cached_message.content
                    if payload.cached_message
                    else f"🔴🔴🔴🔴 - {self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p1'].mention} **VS** {self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p2'].mention} - 🔵🔵🔵🔵\n\n**This is `{choice([self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p1'], self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p2']]).name}`'s turn**\n\n{nl.join([''.join(row) for row in board])}"
                )
            elif game_type == "tictactoe":
                view = View(timeout=None)

                for x in range(3):
                    for y in range(3):
                        view.add_item(
                            Button(
                                label="\u200b",
                                custom_id=f"{channel.id}.{x}.{y}",
                                row=x,
                            )
                        )

                content = (
                    payload.cached_message.content
                    if payload.cached_message
                    else f"❌ - {self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p1'].mention} **VS** {self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p2'].mention} - ⭕\n\n**It's `{choice([self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p1'], self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']['p2']]).name}`'s turn**"
                )
            elif game_type == "hangman":
                del self.bot.configs[payload.guild_id]["games"][str(payload.channel_id)]
                self.bot.games_repo.remove_game(payload.guild_id, payload.channel_id)
                await channel.delete()
                return

            if content:
                msg = await channel.send(content, view=view)
                self.bot.configs[payload.guild_id]["games"][str(payload.channel_id)][
                    "game_id"
                ] = msg.id
                self.bot.games_repo.set_game(
                    payload.guild_id, payload.channel_id, msg.id
                )
                await temp_message.delete()

                if game_type == "4inarow":
                    for x in range(1, 8):
                        await msg.add_reaction(NUM2EMOJI[x])

                if game_type in {"4inarow", "tictactoe"}:
                    await msg.add_reaction("🔄")


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
