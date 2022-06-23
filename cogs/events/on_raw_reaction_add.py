from asyncio import sleep
from random import choice

from disnake import NotFound, RawReactionActionEvent
from disnake.ext.commands import Cog
from disnake.ui import Button, View

from bot import OmniGames
from cogs.misc.hangman import hm_images
from data import check_for_win_fourinarow, LETTER_EMOJIS, NUM2EMOJI, Utils


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

            if reaction.name == "💥":
                mentions = set(message.mentions)

                if not all([r.me for r in message.reactions if r.emoji == "💥"]):
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Please react with only the given reactions",
                        delete_after=5,
                    )

                if channel.name.startswith("hangman-") or len(
                    [
                        mentions & set(await r.users().flatten())
                        for r in message.reactions
                        if r.emoji == "💥"
                    ][0]
                ) == len(mentions):
                    if (
                        channel.name.startswith("hangman-")
                        and self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]["author"].id
                        != payload.member.id
                    ):
                        await message.remove_reaction(reaction, payload.member)
                        return await channel.send(
                            f"⛔ - {payload.member.mention} - Only the author of the hangman game can delete it",
                            delete_after=10,
                        )

                    await channel.send(
                        "⚠️ - **Deletion of the channel in **`5`** seconds** - ⚠️"
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

            if reaction.name == "🔄":
                mentions = set(message.mentions)

                if len(
                    [
                        mentions & set(await r.users().flatten())
                        for r in message.reactions
                        if r.emoji == "🔄"
                    ][0]
                ) == len(mentions):
                    await message.clear_reactions()

                    if channel.name.startswith("4inarow-"):
                        board = [
                            [
                                "⬛" if x == 0 or x == 8 or y == 7 else "⚪"
                                for x in range(9)
                            ]
                            for y in range(8)
                        ]
                        nl = "\n"
                        await message.edit(
                            content=f"🔴🔴🔴🔴 - {message.mentions[0].mention} **VS** {message.mentions[1].mention} - 🔵🔵🔵🔵\n\n**This is `{choice([message.mentions[0], message.mentions[1]]).name}`'s turn**\n\n{nl.join([''.join(row) for row in board])}"
                        )

                        for x in range(1, 8):
                            await message.add_reaction(NUM2EMOJI[x])
                        await message.add_reaction("🔄")
                    elif channel.name.startswith("tictactoe-"):
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

                        await message.add_reaction("🔄")
                    elif channel.name.startswith("rockpaperscissors-"):
                        view = View(timeout=None)
                        view.add_item(Button(emoji="🪨", custom_id=f"{channel.id}.rock"))
                        view.add_item(
                            Button(emoji="📄", custom_id=f"{channel.id}.paper")
                        )
                        view.add_item(
                            Button(emoji="✂️", custom_id=f"{channel.id}.scissors")
                        )

                        await message.edit(
                            content=f"🪨📄✂️ - {message.mentions[0].mention} **VS** {message.mentions[1].mention} - ✂️📄🪨\n\n**Choose one:**\n\n`{message.mentions[0].name}` 🪹 🆚 🪹 `{message.mentions[1].name}`",
                            view=view,
                        )

                        await message.add_reaction("🔄")

                        self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]["signs"] = {"p1": None, "p2": None}

                return

            if channel.name.startswith("4inarow-"):
                if payload.member not in message.mentions:
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Only four in a row participants can play",
                        delete_after=10,
                    )

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
            elif channel.name.startswith("hangman-"):
                if reaction.name not in list(LETTER_EMOJIS.keys()) + ["➡️", "⬅️"]:
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Please react with only the given reactions",
                        delete_after=5,
                    )

                if (
                    not self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["includes_me"]
                    and payload.member
                    == self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["author"]
                ):
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - The user who created the hangman game cannot try to guess the word(s)",
                        delete_after=10,
                    )

                if (
                    not self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["all"]
                    and payload.member
                    not in self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["players"].values()
                ):
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Only participants in the hangman game can try to guess the word(s)",
                        delete_after=10,
                    )

                if self.bot.configs[payload.guild_id]["games"][str(payload.channel_id)][
                    "init"
                ]:
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - Please wait until the game is fully initialised before adding reactions",
                        delete_after=10,
                    )

                if "GUESSED:**" in message.clean_content.split(" "):
                    await message.remove_reaction(reaction, payload.member)
                    return await channel.send(
                        f"⛔ - {payload.member.mention} - The game is over, you can't guess more words or characters",
                        delete_after=10,
                    )

                if reaction.name == "➡️":
                    await message.clear_reactions()
                    for x in range(
                        18,
                        len(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["reactions"]
                        ),
                    ):
                        await message.add_reaction(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["reactions"][x]
                        )
                    await message.add_reaction("⬅️")
                    await message.add_reaction("💥")
                    self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["page"] = 1
                    self.bot.games_repo.update_game(
                        payload.guild_id,
                        payload.channel_id,
                        dict(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]
                        ),
                    )
                    return
                elif reaction.name == "⬅️":
                    await message.clear_reactions()
                    for x in range(
                        len(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["reactions"]
                        )
                    ):
                        if (
                            x == 18
                            and len(
                                self.bot.configs[payload.guild_id]["games"][
                                    str(payload.channel_id)
                                ]["reactions"]
                            )
                            > 19
                        ):
                            await message.add_reaction("➡️")
                            break
                        await message.add_reaction(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["reactions"][x]
                        )
                    await message.add_reaction("💥")
                    self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["page"] = 0
                    self.bot.games_repo.update_game(
                        payload.guild_id,
                        payload.channel_id,
                        dict(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]
                        ),
                    )
                    return

                index = self.bot.configs[payload.guild_id]["games"][
                    str(payload.channel_id)
                ]["reactions"].index(reaction.name)
                letter = LETTER_EMOJIS[
                    self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["reactions"].pop(index)
                ]

                if (
                    letter
                    in self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["chars"]
                ):
                    self.bot.games_repo.update_game(
                        payload.guild_id,
                        payload.channel_id,
                        dict(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]
                        ),
                    )
                    return

                if letter not in [
                    char
                    for char in self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["normal_words"]
                ]:
                    self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["level"] += 1

                self.bot.configs[payload.guild_id]["games"][str(payload.channel_id)][
                    "chars"
                ].append(letter)

                msg_guesses = message.clean_content.split("\n")[4]
                guesses = [
                    char
                    for char in msg_guesses[
                        msg_guesses.find("`") + 1 : msg_guesses.rfind("`")
                    ]
                    .replace("  ", "$")
                    .replace(" ", "")
                    .replace("$", " ")
                ]

                await message.clear_reaction(reaction)

                if (
                    self.bot.configs[payload.guild_id]["games"][
                        str(payload.channel_id)
                    ]["level"]
                    < 6
                ):
                    await message.edit(
                        content=f"💬 - **HANGMAN GAME** - 💬\n\n**PARTICIPANT{'S' if len(self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']) > 1 else ''}:** {', '.join([f'`{member.name}`' for member in self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players'].values()]) if not self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['all'] else '`All members of the server`'}\n\n**WORD TO GUESS:** `{' '.join([guesses[x] if self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['normal_words'][x] != letter else letter for x in range(len(self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['words']))])}`\n\n**Characters used:** {', '.join([f'`{letter}`' for letter in self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['chars']])}"
                        + (
                            f"\n\n**Attempted words:** {', '.join([f'`{letter}`' for letter in self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['guesses']])}"
                            if self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["guesses"]
                            else ""
                        )
                        + f"\n\n{hm_images[self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['level']]}\n\n**The word is in `{'English' if self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['language'] == 0 else 'French'}`**"
                    )
                else:
                    await channel.send(
                        f"❌ - YOU LOST! THE WORD WASN'T GUESSED, THE WORD WAS: `{self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['words']}`! - ❌"
                    )
                    await message.edit(
                        content=f"💬 - **HANGMAN GAME** - 💬\n\n**PARTICIPANT{'S' if len(self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players']) > 1 else ''}:** {', '.join([f'`{member.name}`' for member in self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['players'].values()]) if not self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['all'] else '`All members of the server`'}\n\n**THE WORD HASN'T BEEN GUESSED:** `{' '.join([guesses[x] for x in range(len(self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['words']))])}`\n\n**THE WORD WAS:** `{self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['words']}`\n\n**Characters used:** {', '.join([f'`{letter}`' for letter in self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['chars']])}"
                        + (
                            f"\n\n**Attempted words:** {', '.join([f'`{letter}`' for letter in self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['guesses']])}"
                            if self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["guesses"]
                            else ""
                        )
                        + f"\n\n{hm_images[self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['level']]}\n\n**The word is in `{'English' if self.bot.configs[payload.guild_id]['games'][str(payload.channel_id)]['language'] == 0 else 'French'}`**"
                    )
                    await message.clear_reactions()
                    await message.add_reaction("💥")

                if (
                    len(
                        self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]["reactions"]
                    )
                    > 17
                ):
                    x = 17
                    if (
                        len(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["reactions"]
                        )
                        <= 19
                        and self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]["page"]
                        == 1
                    ):
                        self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]["page"] = 0
                        await message.clear_reactions()
                        x = 0
                    elif (
                        self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]["page"]
                        == 1
                    ):
                        return self.bot.games_repo.update_game(
                            payload.guild_id,
                            payload.channel_id,
                            dict(
                                self.bot.configs[payload.guild_id]["games"][
                                    str(payload.channel_id)
                                ]
                            ),
                        )
                    else:
                        await message.clear_reaction("➡️")
                        await message.clear_reaction("💥")

                    for x in range(
                        x,
                        len(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["reactions"]
                        ),
                    ):
                        if (
                            x == 18
                            and len(
                                self.bot.configs[payload.guild_id]["games"][
                                    str(payload.channel_id)
                                ]["reactions"]
                            )
                            > 19
                        ):
                            await message.add_reaction("➡️")
                            break

                        await message.add_reaction(
                            self.bot.configs[payload.guild_id]["games"][
                                str(payload.channel_id)
                            ]["reactions"][x]
                        )

                    await message.add_reaction("💥")

                self.bot.games_repo.update_game(
                    payload.guild_id,
                    payload.channel_id,
                    dict(
                        self.bot.configs[payload.guild_id]["games"][
                            str(payload.channel_id)
                        ]
                    ),
                )

            return


def setup(bot: OmniGames):
    bot.add_cog(Events(bot))
