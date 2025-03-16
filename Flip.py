from enum import IntEnum


class Cards(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2 
    THREE = 3
    FOUR = 4 
    FIVE = 5 
    SIX = 6 
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    ELEVEN = 11
    TWELVE = 12 
    FREEZE = 13
    FLIP_THREE = 14
    SECOND_CHANCE = 15 
    PLUS_TWO = 16
    PLUS_FOUR = 17
    PLUS_SIX = 18
    PLUS_EIGHT = 19
    PLUS_TEN = 20
    TIMES_TWO = 21

class AddCardResult:
    ALIVE = 0
    BUST = 1 
    SECOND_CHANCE_USED = 2 

class Player:

    id: int

    is_bust: bool = False
    is_passed: bool = False
    has_second_chance: bool = False

    total_points: int = 0

    def add_card(self, card:Cards) -> AddCardResult:
        if(int(card < 13)):
            if(card in self.cards):
                if(self.has_second_chance):
                    self.has_second_chance = False
                    return AddCardResult.SECOND_CHANCE_USED
                else:
                    self.is_bust = True
                    return AddCardResult.BUST
        if(card == Cards.SECOND_CHANCE):
            self.has_second_chance =True
                
        self.cards.append(card)
        return AddCardResult.ALIVE
        
    def get_points_cards(self):
        point_cards = [card for card in self.cards if int(card) < 13]
        return point_cards
        
    def get_points(self):
        if(self.is_bust):
            return 0

        point_cards = self.get_points_cards()
        point_card_count = len(point_cards)
        card_points = 2 * sum(point_cards) if Cards.TIMES_TWO in self.cards else sum(point_cards)
        additional_points = sum([((card - 15) * 2) for card in self.cards if card in [Cards.PLUS_TWO, Cards.PLUS_FOUR, Cards.PLUS_SIX, Cards.PLUS_EIGHT, Cards.PLUS_TEN]])
        additional_points += 15 if (point_card_count == 7) else 0

        return card_points + additional_points
    
    def new_round(self):
        self.total_points += self.get_points()
        self.cards.clear()
        self.has_second_chance = False
        self.is_bust = False
        self.is_passed = False

    def new_game(self):
        self.new_round()
        self.total_points = 0
    
    def __repr__(self):
        return f"id = {self.id}, passed = {self.is_passed}, bust = {self.is_bust}, second_chance = {self.has_second_chance} cards = [{" ".join([str(card) for card in self.cards])}], points = {self.get_points()}"

    def is_alive(self):
        return not (self.is_bust or self.is_passed or len(self.get_points_cards()) >=7)

    def __init__(self):
        self.cards: list[Cards] = []

    