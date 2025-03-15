from enum import IntEnum


class MessageType(IntEnum):
    PING = 0
    ID_ASSIGN = 1
    PLAYER_INFO = 2
    DISCONNECT = 3

    NEW_GAME = 10
    NEW_ROUND = 11
    GAME_OVER = 12
    PLAYER_DISQUALIFIED = 13 

    # Round announcements
    NEW_CARD = 20
    STAND = 21
    BUST = 22
    FREEZE = 23
    FLIP_THREE = 24
    SECOND_CHANCE = 25
    SECOND_CHANCE_USED = 26

    # Requests to player
    REQUEST_HIT_OR_STAND = 30
    REQUEST_ASSIGN_FREEZE = 31
    REQUEST_ASSIGN_FLIP_THREE = 32 
    REQUEST_ASSIGN_SECOND_CHANCE = 33

    # Player Choices
    HIT_OR_STAND = 34
    ASSIGN_FREEZE = 35
    ASSIGN_FLIP_THREE = 36
    ASSIGN_SECOND_CHANCE = 37


