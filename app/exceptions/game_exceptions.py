class GameError(Exception):
    pass


class InvalidAction(GameError):
    pass


class NotPlayersTurn(GameError):
    pass


class GameNotStarted(GameError):
    pass


