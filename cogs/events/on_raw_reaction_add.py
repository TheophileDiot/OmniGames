from asyncio import sleep
from random import choice

from disnake import NotFound, RawReactionActionEvent
from disnake.ext.commands import Cog
from disnake.ui import Button, View

from bot import OmniGames
from data import check_for_win_fourinarow, NUM2EMOJI, Utils


class Events(Cog, name="events.on_raw_reaction_add"):
    def __init__(self, bot: OmniGames):
        self.bot = bot

    @Cog.listener()
    @Utils.check_bot_starting()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        """When a reaction is added, if the channels is a game channel then handle it else if the user have a prestige pending then handle it according to the reaction added"""
        if payload.member.bot:
            return

        if (
            "games" in self.bot.configs[payload.guild_id]
            and self.bot.configs[payload.guild_id]["games"]
            and str(payload.channel_id) in self.bot.configs[payload.guild_id]["games"]
        ):
            reaction = payload.emoji

            try:
                channel = self.bot.get_channel(
                    payload.channel_id
                ) or await self.bot.fetch_channel(payload.channel_id)
            except NotFound:
                return

            try:
                message = await channel.fetch_message(payload.message_id)
            except NotFound:
                return

            if reaction.name == "💥" and all(
                [r.me for r in message.reactions if r.emoji == "💥"]
            ):
                await channel.send(
                    "⚠️ - **Deletion of the channel in **`5`** seconds** - ⚠️"
                )
                await sleep(5)
                del self.bot.configs[payload.guild_id]["games"][str(payload.channel_id)]
                self.bot.games_repo.remove_game(payload.guild_id, payload.channel_id)
                await channel.delete()

            if channel.name.startswith("4inarow-"):
                if payload.member not in message.mentions:
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Only four in a row participants can play",
                        delete_after=10,
                    )

                if reaction.name == "🔄":
                    board = [
                        ["⬛" if x == 0 or x == 8 or y == 7 else "⚪" for x in range(9)]
                        for y in range(8)
                    ]
                    nl = "\n"
                    await message.edit(
                        content=f"🔴🔴🔴🔴 - {message.mentions[0].mention} **VS** {message.mentions[1].mention} - 🔵🔵🔵🔵\n\n**This is `{choice([message.mentions[0], message.mentions[1]]).name}`'s turn**\n\n{nl.join([''.join(row) for row in board])}"
                    )

                    if len(message.reactions) < 8:
                        await message.clear_reactions()
                        for x in range(1, 8):
                            await message.add_reaction(NUM2EMOJI[x])
                        await message.add_reaction("🔄")
                    else:
                        await message.remove_reaction(reaction, payload.member)

                    return

                content = message.clean_content
                player_turn = content[content.find("`") + 1 : content.rfind("`")]

                if payload.member.name != player_turn:
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - It's not your turn",
                        delete_after=5,
                    )
                elif reaction.name not in NUM2EMOJI.values():
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Please react with only the given reactions",
                        delete_after=5,
                    )

                board = [[emoji for emoji in row] for row in content.split("\n")[4:]]
                row = int(
                    list(NUM2EMOJI.keys())[
                        list(NUM2EMOJI.values()).index(reaction.name)
                    ]
                )

                x = 6
                while board[x][row] != "⚪":
                    x -= 1

                if x == 0:
                    await message.clear_reaction(reaction)
                else:
                    await message.remove_reaction(reaction, payload.member)

                board[x][row] = (
                    "🔴" if payload.member.name == message.mentions[0].name else "🔵"
                )
                nl = "\n"

                if check_for_win_fourinarow(board):
                    await message.clear_reactions()
                    await message.edit(
                        content=f"🔴🔴🔴🔴 - {message.mentions[0].mention} **VS** {message.mentions[1].mention} - 🔵🔵🔵🔵\n\n**THE WINNER IS:** `{player_turn}`!\n\n{nl.join([''.join(row) for row in board])}"
                    )
                    await message.add_reaction("💥")
                    return await message.add_reaction("🔄")

                await message.edit(
                    content=f"🔴🔴🔴🔴 - {message.mentions[0].mention} **VS** {message.mentions[1].mention} - 🔵🔵🔵🔵\n\n**It's `{message.mentions[0 if player_turn == message.mentions[1].name else 1].name}`'s turn**\n\n{nl.join([''.join(row) for row in board])}"
                )
            elif channel.name.startswith("tictactoe-"):
                if reaction.name == "🔄":
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

                    await message.edit(
                        content=f"❌ - {message.mentions[0].mention} **VS** {message.mentions[1].mention} - ⭕\n\n**It's `{choice([message.mentions[0], message.mentions[1]]).name}`'s turn**",
                        view=view,
                    )

                    if len(message.reactions) < 2:
                        await message.clear_reactions()
                        await message.add_reaction("🔄")
                    else:
                        await message.remove_reaction(reaction, payload.member)
                else:
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Please react with only the given reactions",
                        delete_after=5,
                    )

            return


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
