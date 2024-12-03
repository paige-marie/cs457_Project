import auxillary as aux

class Player:
    player_count = 0

    def __init__(self, name, player_id, me=False) -> None:
        self.is_me = me
        self.name = name
        self.id = player_id % 2
        self.color, self.color_code = ('white', aux.WHITE) # temporary
        Player.player_count += 1

    @staticmethod
    def set_player_colors(players):
        players[0].color, players[0].color_code = ('red', aux.RED)
        players[0].id = 0
        players[1].color, players[1].color_code = ('blue', aux.BLUE)
        players[1].id = 1

    @staticmethod
    def get_color(playr):
        return playr.color, playr.color_code
    
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