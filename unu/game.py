import asyncio
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio.tasks import Task

from hydrogram.types import Chat, Message, User

from config import bot, games, timeout
from unu.db import GameModel
from unu.deck import Deck


class Game:
    def __init__(self, chat: Chat, theme) -> None:
        self.theme = theme
        self.chat: Chat = chat
        self.creator_id: int = None
        self.last_card: tuple = None
        self.last_card_2: dict = None
        self.next_player: User = None
        self.deck = Deck(theme)
        self.players: dict[int, User] = {}
        self.is_started: bool = False
        self.draw: int = 0
        self.drawed: bool = False
        self.chosen: str = None
        self.closed: bool = False
        self.winner: bool = True
        self.timer_task: Task = None
        self.timer_duration: int = 45
        self.message: Message = None
        self.is_dev = False
        self.bluff = False

    def next(self):
        self.drawed = False
        indice = list(self.players.keys()).index(self.next_player.id)
        next_ind = (indice + 1) % len(self.players)
        next_key = list(self.players.keys())[next_ind]
        self.next_player = self.players[next_key]

        if not ((self.last_card[1] == "draw_four" and self.draw == 4) or
                (self.last_card[1] == "draw_six" and self.draw == 6) or
                (self.last_card[1] == "draw_ten" and self.draw == 10)):
            print("draw reset")
            self.bluff = False

        if self.timer_task and self.timer_task != asyncio.current_task():
            self.timer_task.cancel()

        self.timer_task = asyncio.create_task(self.start_timer())

    def start(self):
        self.is_started = True
        self.timer_task = asyncio.create_task(self.start_timer())

    def stop(self):
        if self.timer_task:
            self.timer_task.cancel()

    async def unpin_message(self):
        if self.message:
            try:
                await self.message.unpin()
            except Exception:
                pass


    async def start_timer(self):
        await asyncio.sleep(self.timer_duration)
        if self.chat.id in games and games[self.chat.id] == self and self.is_started:
            from functools import partial
            from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
            from config import minimum_players, player_game
            from unu.db import Chat
            from unu.locales import get_locale_string

            skipped_player = self.next_player
            cards_to_draw = 1 + self.draw
            self.draw = 0

            drawn = self.deck.draw(cards_to_draw)
            skipped_player.cards.extend(drawn)

            chat_obj = (await Chat.get_or_create(id=self.chat.id))[0]
            clang = chat_obj.lang
            gt = partial(get_locale_string, clang)

            if chat_obj.theme == "nomercy" and len(skipped_player.cards) >= 25:
                await bot.send_message(
                    self.chat.id,
                    gt("too_many_cards").format(name=skipped_player.mention),
                )
                self.next()
                self.players.pop(skipped_player.id, None)
                player_game.pop(skipped_player.id, None)
                if len(self.players) < minimum_players:
                    for p in list(self.players.keys()):
                        player_game.pop(p, None)
                    games.pop(self.chat.id, None)
                    await bot.send_message(self.chat.id, gt("game_over"))
                    self.stop()
                    if self.message:
                        await self.message.edit_text(gt("game_over"))
                    await self.unpin_message()
                    return
            else:
                self.next()

            inline_keyb = InlineKeyboardMarkup([
                [InlineKeyboardButton(gt("play"), switch_inline_query_current_chat="")]
            ])

            msg_text = (
                gt("timeout_skipped").format(name=skipped_player.mention, count=cards_to_draw)
                + "\n\n"
                + gt("next").format(name=self.next_player.mention)
            )

            await bot.send_message(
                self.chat.id,
                msg_text,
                reply_markup=inline_keyb,
            )


    async def save(self):
        print("Saving game")
        players_dict = {
            player_id: {"cards": getattr(player, "cards", None), "tcards": getattr(player, "total_cards", None)} for player_id, player in self.players.items()
        }

        game = GameModel(
            id=id(self),
            theme=self.theme,
            chat_id=self.chat.id,
            last_card=self.last_card,
            last_card_2=self.last_card_2,
            next_player_id=self.next_player.id if self.next_player else None,
            deck=json.dumps(self.deck.cards),
            players=players_dict,
            is_started=self.is_started,
            draw=self.draw,
            drawed=self.drawed,
            chosen=self.chosen,
            closed=self.closed,
            winner=self.winner,
            is_dev=self.is_dev,
            bluff=self.bluff,
            timer_duration=self.timer_duration,
            message_id=self.message.id,
        )
        if self.timer_task:
            self.timer_task.cancel()
        await game.save()
        print("Game saved")

    @classmethod
    async def load(cls, game: GameModel):
        chat = await bot.get_chat(game.chat_id)
        self = cls(chat, game.theme)
        self.theme = game.theme
        self.chat = await bot.get_chat(game.chat_id)
        self.last_card = game.last_card
        self.last_card_2 = game.last_card_2
        self.deck.cards = game.deck
        self.players = {}
        self.is_started = game.is_started
        self.draw = game.draw
        self.drawed = game.drawed
        self.chosen = game.chosen
        self.closed = game.closed
        self.winner = game.winner
        self.is_dev = game.is_dev
        self.bluff = game.bluff
        self.timer_duration = game.timer_duration
        self.message = await bot.get_messages(game.chat_id, game.message_id)
        for player_id, cards in game.players.items():
            self.players[int(player_id)] = await bot.get_users(player_id)
            self.players[int(player_id)].cards = []
            for card in cards["cards"]:
                self.players[int(player_id)].cards.append(tuple(card))
            self.players[int(player_id)].total_cards = cards["tcards"]
        self.next_player = self.players[int(game.next_player_id)] if game.next_player_id else None
        return self
