from typing import Union

port = 5555

class Player:
    def __init__(self):
        ...

class Lobby:
    # Should Game be a child of lobby? Or a completely different class that communicates with lobby?
    DEFAULT_MAX_PLAYERS = 4

    def __init__(self):
        # Should the settings be part of a separate class or something?
        self.max_players = self.DEFAULT_MAX_PLAYERS

        self.players = []
        # Should spectators be completely separate from players? (probably not) (maybe just make it a list of pointers)
        self.spectators = []
        self.host = None

    @property
    def player_count(self):
        return len(self.players)

    def add_player(self, player):
        self.players += [player]

class Message:
    ...

class MessageTypes:
    multiplayer_menu_lobby = "multiplayer_menu_lobby"

class LobbyData:
    def __init__(self, lobby_id: int,
                 lobby_title: Union[str, None] = None,
                 owner: Union[str, None] = None,
                 players: Union[list[str], None] = None,
                 game_title=None,
                 max_players: Union[int, None] = None):
        self.lobby_id = lobby_id
        self.lobby_title = lobby_title
        self.owner = owner
        self.game_title = game_title
        self.players = players
        self.max_players = max_players
