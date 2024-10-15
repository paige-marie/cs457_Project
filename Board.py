import auxillary as aux

import numpy as np

NUM_COLS, NUM_ROWS = 7, 6
FILL_VALUE = -1
WINNING_NUMBER = 4
CIRCLE = '\u25CF'

class Board:

    def __init__(self, players, in_terminal=True):
        self.board_arr = np.full((NUM_ROWS, NUM_COLS), FILL_VALUE, dtype=int)
        self.players = players
        self.winner = -1
        self.in_terminal = in_terminal 

    def place_tile(self, selected_column: int, playr_num):
        placed = False
        playr = self.players[playr_num]
        if selected_column < len(self.board_arr[0]):
            for row in self.board_arr:
                if row[selected_column] == FILL_VALUE:
                    row[selected_column] = playr.id
                    placed = True
                    break
        return placed

    def game_over(self):
        """
        Game over check, will only be called by the server
        """
        #TODO return early if any of these checks are true instead of checking them all
        horozontal = self.check_straight(self.board_arr)
        vertical = self.check_straight(self.board_arr.T)
        positive = self.check_diagonal(self.board_arr)
        negative = self.check_diagonal(np.flip(self.board_arr, 0))
        print(f'horozontal win = {horozontal}')
        print(f'vertical win = {vertical}')
        print(f'positive win = {positive}')
        print(f'negative win = {negative}')
        return horozontal or vertical or positive or negative
    
    def check_straight(self, b):
        for row in b:
            for i in range(len(row) - WINNING_NUMBER + 1):
                if row[i] != FILL_VALUE and np.all(row[i:i+WINNING_NUMBER] == row[i]):
                    self.winner = row[i]
                    return True
        return False
    
    def check_diagonal(self, b):
        for r in range(len(b) + 1 - WINNING_NUMBER):
            for c in range(len(b[0]) + 1 - WINNING_NUMBER):
                if b[r][c] != FILL_VALUE and all(b[r][c] == b[r+k][c+k] for k in range(WINNING_NUMBER)):
                    self.winner = b[r][c]
                    return True
        return False

    def __str__(self):
        human_board = np.flip(self.board_arr, 0)
        if self.in_terminal:
            return self.draw_board_in_terminal(human_board)
        else:
            return self.draw_in_pygame(human_board)
    
    def draw_board_in_terminal(self, human_board):
        board_str = "\n"
        board_str += '  ' + "   ".join(str(n) for n in range(NUM_COLS)) + ' \n\n'
        for row in human_board:
            board_str += '| ' + " | ".join(
                aux.color_text(self.players[0], CIRCLE) if c == self.players[0].id else
                aux.color_text(self.players[1], CIRCLE) if c == self.players[1].id else
                ' ' if c == -1 else str(c) 
                for c in row
            ) + ' |\n'
        return board_str
    
    def draw_in_pygame(self, human_board):
        pass

    
if __name__ == '__main__':
    from Player import Player
    players = [Player('a', 0), Player('b', 1)]
    b = Board(players)
    print(b)