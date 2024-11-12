import auxillary as aux

class Player:
    player_count = 0

    def __init__(self, name, player_id, me=False) -> None:
        # if Player.player_count >= 2:
        #     raise aux.CustomError("Cannot have more than 2 players")

        self.is_me = me
        self.name = name
        # self.id = Player.player_count
        self.id = player_id % 2
        self.color, self.color_code = self.get_color(self)
        Player.player_count += 1

    @staticmethod
    def get_color(playr):
        # TODO decouple from the player id, maybe move this function into the board class and determine it by position in list?
        return ('red', aux.RED) if playr.id % 2 == 1 else ('blue', aux.BLUE)
    
    @staticmethod
    def get_player_by_id(players, id):
        for player in players:
            if player.id == id:
                return player
        raise aux.CustomError("Somehow you're searching for a player that doesn't exist in game")
    
    def __str__(self):
        return f"{self.name=} {self.id=} {self.color=} {self.is_me=}"
    
    def __lt__(self, other):
        return self.id < other.id

if __name__ == '__main__':
    player = Player('paige', 1)