from asyncio import sleep
from hashlib import pbkdf2_hmac
from unicodedata import normalize
from typing import List

from disnake import (
    ApplicationCommandInteraction,
    Enum,
    Member,
    PermissionOverwrite,
)
from disnake.ext.commands import (
    BucketType,
    Cog,
    max_concurrency,
    Param,
    slash_command,
)
from random_word import RandomWords
from randomwordfr import RandomWordFr

from bot import OmniGames
from data import Utils


class AvailableLanguages(Enum):
    English = 0
    French = 1


hm_images = {
    0: "https://imgur.com/PqwE2ym",
    1: "https://imgur.com/jJcABje",
    2: "https://imgur.com/wBGNEKP",
    3: "https://imgur.com/lZLCnGR",
    4: "https://imgur.com/VfNxrej",
    5: "https://imgur.com/UGW0IDT",
    6: "https://imgur.com/tcgTNAW",
}


class Hangman(Cog, name="misc.hangman"):
    def __init__(self, bot: OmniGames) -> None:
        self.bot = bot
        self.rw_en = RandomWords()
        self.rw_fr = RandomWordFr()

    """ GROUP """

    @slash_command(
        name="hangman",
        description="Manages the hangman game",
    )
    async def hangman_slash_command_group(
        self,
        inter: ApplicationCommandInteraction,
    ):
        """
        This slash command group manages the hangman game

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        """
        if not await self.bot.utils_class.check_games_category(inter):
            return

    """ GROUP'S COMMAND(S) """

    @hangman_slash_command_group.sub_command(
        name="guess",
        description="Guesses a word for the handman game",
    )
    @max_concurrency(1, BucketType.channel)
    async def hangman_guess_slash_command(
        self,
        inter: ApplicationCommandInteraction,
        word: str,
    ):
        """
        This slash command starts a hangman game against other guild members

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        word: :class:`str`
            The word to guess
        """
        if (
            "games" not in self.bot.configs[inter.guild.id]
            or str(inter.channel.id) not in self.bot.configs[inter.guild.id]["games"]
            or not inter.channel.name.startswith("hangman-")
        ):
            return await inter.response.send_message(
                f"ℹ️ - {inter.author.mention} - You have to be in a hangman game channel to use this command",
                ephemeral=True,
            )

        if (
            not self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                "includes_me"
            ]
            and self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                "author"
            ].id
            == inter.author.id
        ):
            return await inter.response.send_message(
                f"⛔ - {inter.author.mention} - The user who created the hangman game cannot try to guess the word",
                ephemeral=True,
            )

        message = await self.bot.utils_class.get_last_game_message(inter.channel)

        if not message:
            return await inter.response.send_message(
                f"⛔ - {inter.author.mention} - I could not find the game message",
                ephemeral=True,
            )

        if "GUESSED:**" in message.clean_content.split(" "):
            return await inter.response.send_message(
                f"⛔ - {inter.author.mention} - The game is over, you can't guess more words or characters",
                ephemeral=True,
            )

        guess = normalize("NFD", word).encode("ascii", "ignore").decode("ascii")

        if (
            guess
            in self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                "guesses"
            ]
        ):
            return await inter.response.send_message(
                f"⛔ - {inter.author.mention} - This attempt has already been used",
                ephemeral=True,
            )
        elif len(guess) != len(
            self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                "normal_words"
            ]
        ):
            return await inter.response.send_message(
                f"⛔ - {inter.author.mention} - The word you tried to guess doesn't have the same amount of caracters than the word hidden",
                ephemeral=True,
            )

        self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
            "guesses"
        ].append(guess)

        if (
            guess
            == self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                "normal_words"
            ]
        ):
            await inter.response.send_message(
                f"✅ - VICTORY! THE WORD WAS GUESSED BY {inter.author}, THE WORD WAS: `{self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['words']}`! - ✅"
            )
        else:
            self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                "level"
            ] += 1

        if (
            self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)]["level"]
            >= 6
        ):
            await inter.response.send_message(
                f"❌ - YOU LOST! THE WORD WASN'T GUESSED, THE WORD WAS: `{self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['words']}`! - ❌"
            )
        else:
            await inter.response.send_message(
                f"ℹ️ - WRONG! `{inter.author.name}` tried guessing the word `{guess}` - ℹ️"
            )

        msg_guesses = message.clean_content.split("\n")[4]
        guesses = [
            char
            for char in msg_guesses[msg_guesses.find("`") + 1 : msg_guesses.rfind("`")]
            .replace("  ", "$")
            .replace(" ", "")
            .replace("$", " ")
        ]

        await message.edit(
            content=f"💬 - **HANGMAN GAME** - 💬\n\n**PARTICIPANT{'S' if len(self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['players']) > 1 else ''}:** {', '.join([f'`{member.name}`' for member in self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['players'].values()]) if not self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['all'] else '`All members of the server`'}\n\n**WORD TO GUESS:** `{' '.join([guesses[x] for x in range(len(self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['words']))])}`"
            + (
                f"\n\n**Characters used:** {', '.join([f'`{letter}`' for letter in self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['chars']])}"
                if self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)][
                    "chars"
                ]
                else ""
            )
            + f"\n\n**Attempted words:** {', '.join([f'`{letter}`' for letter in self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['guesses']])}\n\n{hm_images[self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['level']]}\n\n**The word is in `{'English' if self.bot.configs[inter.guild.id]['games'][str(inter.channel.id)]['language'] == 0 else 'French'}`**"
        )

        self.bot.games_repo.update_game(
            inter.guild.id,
            inter.channel.id,
            dict(self.bot.configs[inter.guild.id]["games"][str(inter.channel.id)]),
        )

    @hangman_slash_command_group.sub_command(
        name="create",
        description="Starts a hangman game against another guild member",
    )
    @max_concurrency(1, BucketType.member)
    async def hangman_create_slash_command(
        self,
        inter: ApplicationCommandInteraction,
        members: List[Member] = Param(None, converter=Utils.members_converter),
        all_members: bool = False,
        random: bool = False,
        word: str = None,
        language: AvailableLanguages = AvailableLanguages.English,
        includes_me: bool = False,
    ):
        """
        This slash command starts a hangman game against other guild members

        Parameters
        ----------
        inter: :class:`disnake.ext.commands.ApplicationCommandInteraction`
            The application command interaction
        members: :class:`typing.List[disnake.Member]`
            The members to play against
        all_members: :class:`bool`
            Precise if the game contains every member of the guild
        random: :class:`bool` optional
            Precise if the word is chose randomly or not
        word: :class:`str` optional
            The word to guess if random is false
        language: :class:`AvailableLanguages` optional
            The language of the hangman game
        includes_me: :class:`bool` optional
            Specify if the game will include yourself or not (only works if the word is random)
        """

        if members or all_members:
            if not random and not word:
                return await inter.response.send_message(
                    f"ℹ️ - {inter.author.mention} - You have to choose either a word or have it generated randomly",
                    ephemeral=True,
                )

            if random:
                if language == 0:
                    word = self.rw_en.get_random_word()
                elif language == 1:
                    word = self.rw_fr.get()["word"]
                else:
                    return await inter.response.send_message(
                        f"⚠️ - {inter.author.mention} - An error happened please re enter your command",
                        ephemeral=True,
                    )
            else:
                if includes_me:
                    return await inter.response.send_message(
                        f"⚠️ - {inter.author.mention} - You can't create a hangman game with a chosen word that includes yourself!",
                        ephemeral=True,
                    )

                word = word.strip()

            channel_name = f"hangman-{self.bot.utils_class.normalize_name(inter.author.name)}-{hash(word)}"
            channels = {channel.name: channel for channel in inter.guild.text_channels}
            channel = None

            if channel_name in channels.keys():
                channel = channels[channel_name]
                message = await self.bot.utils_class.get_last_game_message(channel)

                if message:
                    return await inter.response.send_message(
                        f"ℹ️ - {inter.author.mention} - You already have a hangman game against {', '.join([f'`{m.name}`' for m in members]) if members else '`All members of the server`'}! {channel}",
                        ephemeral=True,
                    )

            if not channel:
                overwrites = {
                    inter.author: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": True,
                            "use_slash_commands": True,
                            "add_reactions": False,
                        }
                    ),
                    self.bot.user: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": True,
                            "add_reactions": True,
                        }
                    ),
                    inter.guild.default_role: PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": False,
                            "use_slash_commands": False,
                            "add_reactions": False,
                        }
                    ),
                }

                if members:
                    if any([m.bot for m in members]):
                        return await inter.response.send_message(
                            f"⚠️ - {inter.author.mention} - You can't create a hangman game with a bot",
                            ephemeral=True,
                        )

                    overwrites = overwrites | {
                        member: PermissionOverwrite(
                            **{
                                "view_channel": True,
                                "send_messages": True,
                                "use_slash_commands": True,
                                "add_reactions": False,
                            }
                        )
                        for member in members
                    }
                else:
                    overwrites[inter.guild.default_role] = PermissionOverwrite(
                        **{
                            "view_channel": True,
                            "send_messages": True,
                            "use_slash_commands": True,
                            "add_reactions": False,
                        }
                    )

                channel = await inter.guild.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites,
                    category=self.bot.configs[inter.guild.id]["games_category"],
                    reason=f"Creation of the {inter.author} hangman game channel",
                )

            await inter.channel.send(
                f"💬 - The hangman game {channel.mention} in {'English' if language == 0 else 'French'} with {', '.join([f'`{m.name}`' for m in members]) if members else '`All members of the server`'} has been created - 💬"
            )

            msg = await channel.send(
                content=f"💬 - **HANGMAN GAME** - 💬\n\n**PARTICIPANT{'S' if all_members or len(members) > 1 else ''}:** {', '.join([f'`{member.name}`' for member in (members if not includes_me else members + [inter.author])]) if not all_members else '`All members of the server`'}\n\n**WORD TO GUESS:** `{' '.join(['_' if char != ' ' else ('-' if char == '-' else ' ') for char in word])}`\n\n{hm_images[0]}\n\n**The word is in `{'English' if language == 0 else 'French'}`**"
            )

            await inter.response.send_message(
                "The game has been created!", ephemeral=True
            )

            if "games" not in self.bot.configs[inter.guild.id]:
                self.bot.configs[inter.guild.id]["games"] = {}

            self.bot.configs[inter.guild.id]["games"][str(channel.id)] = {
                "game_id": msg.id,
                "players": {f"p{x}": members[x - 1] for x in range(1, len(members) + 1)}
                if not all_members
                else {},
                "game_type": "hangman",
                "author": inter.author,
                "words": word,
                "normal_words": normalize("NFD", word)
                .encode("ascii", "ignore")
                .decode("ascii"),
                "all": all_members,
                "level": 0,
                "chars": [],
                "guesses": [],
                "reactions": [
                    "🇦",
                    "🇧",
                    "🇨",
                    "🇩",
                    "🇪",
                    "🇫",
                    "🇬",
                    "🇭",
                    "🇮",
                    "🇯",
                    "🇰",
                    "🇱",
                    "🇲",
                    "🇳",
                    "🇴",
                    "🇵",
                    "🇶",
                    "🇷",
                    "🇸",
                    "🇹",
                    "🇺",
                    "🇻",
                    "🇼",
                    "🇽",
                    "🇾",
                    "🇿",
                ],
                "page": 0,
                "init": True,
                "includes_me": includes_me,
                "language": language,
            }

            if includes_me and not all_members:
                self.bot.configs[inter.guild.id]["games"][str(channel.id)][
                    "players"
                ] = self.bot.configs[inter.guild.id]["games"][str(channel.id)][
                    "players"
                ] | {
                    f"p{len(self.bot.configs[inter.guild.id]['games'][str(channel.id)]['players']) + 1}": inter.author
                }

            self.bot.games_repo.create_game(
                inter.guild.id,
                channel.id,
                msg.id,
                self.bot.configs[inter.guild.id]["games"][str(channel.id)]["players"],
                "hangman",
                dict(self.bot.configs[inter.guild.id]["games"][str(channel.id)]),
            )

            await sleep(1)

            for x in range(
                len(
                    self.bot.configs[inter.guild.id]["games"][str(channel.id)][
                        "reactions"
                    ]
                )
            ):
                if x == 18:
                    await msg.add_reaction("➡️")
                    break
                await msg.add_reaction(
                    self.bot.configs[inter.guild.id]["games"][str(channel.id)][
                        "reactions"
                    ][x]
                )

            await msg.add_reaction("💥")

            self.bot.configs[inter.guild.id]["games"][str(channel.id)]["init"] = False

            self.bot.games_repo.update_game(
                inter.guild.id,
                channel.id,
                dict(self.bot.configs[inter.guild.id]["games"][str(channel.id)]),
            )


def setup(bot: OmniGames):
    bot.add_cog(Hangman(bot))
