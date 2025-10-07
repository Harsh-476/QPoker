class LobbyError(Exception):
    pass


class LobbyNotFound(LobbyError):
    pass


class LobbyFull(LobbyError):
    pass


class LobbyInGame(LobbyError):
    pass


