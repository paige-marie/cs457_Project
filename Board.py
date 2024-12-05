import auxillary as aux

import numpy as np
import pygame

NUM_COLS, NUM_ROWS = 7, 6
# NUM_COLS, NUM_ROWS = 3, 3     # change to test draw state (really hard not to accidentally win)
WINNING_NUMBER = 4
CIRCLE = '\u25CF'

class Board:
    FILL_VALUE = -1
    SLOT_SIZE = 50  # Size of each slot
    PADDING = 5     # Padding between slots
    BG_COLOR = (0, 0, 0)  # Black background
    EMPTY_COLOR = (255, 255, 0)  # Yellow for empty slots
    PLAYER_COLORS = [(255, 0, 0), (0, 0, 255)]  # Red, Blue

    def __init__(self, players, in_terminal=True):
        self.board_arr = np.full((NUM_ROWS, NUM_COLS), self.FILL_VALUE, dtype=int)
        self.players = players
        for i, ply in enumerate(players):
            if ply.is_me:
                self.me = ply
                self.color = self.PLAYER_COLORS[i]

        self.winner = -1
        self.in_terminal = in_terminal 

        if not self.in_terminal:
            self.init_pygame()

    def init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (NUM_COLS * self.SLOT_SIZE, NUM_ROWS * self.SLOT_SIZE + 50 + 60)
        )
        pygame.display.set_caption(f"{self.me.name}'s Connect 4")
        self.font = pygame.font.SysFont("arial", 24)
        self.draw_in_pygame()
        print('borad init')

    def draw_in_pygame(self, status=""):
        human_board = np.flip(self.board_arr, 0)
        self.screen.fill(self.BG_COLOR)

        player_info_text_surface = self.font.render(self.me.name, True, self.color)  # White text
        self.screen.blit(player_info_text_surface, (10, 10))  # Position at top-left with padding

        text_surface = self.font.render(status, True, (255, 255, 255))  # White text
        self.screen.blit(text_surface, (10, 60))  # Position at top-left with padding
        for r in range(NUM_ROWS):
            for c in range(NUM_COLS):
                color = (
                    self.PLAYER_COLORS[0]
                    if human_board[r][c] == self.players[0].id
                    else self.PLAYER_COLORS[1]
                    if human_board[r][c] == self.players[1].id
                    else self.EMPTY_COLOR
                )
                pygame.draw.circle(
                    self.screen,
                    color,
                    (
                        c * self.SLOT_SIZE + self.SLOT_SIZE // 2,
                        r * self.SLOT_SIZE + self.SLOT_SIZE // 2 + 50 + 60,
                    ),
                    self.SLOT_SIZE // 2 - self.PADDING,
                )
        pygame.display.flip()
        print('updating borad')

    def update_board(self, current_player=None):

        self.draw_in_pygame("It's your turn!")

        while True:  # until a valid event is processed
            # pygame.event.clear()
            # event = pygame.event.wait()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None 
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, _ = event.pos
                    selected_column = x // self.SLOT_SIZE + 1
                    if self.place_tile(selected_column, current_player):
                        self.draw_in_pygame("waiting for other player...")
                        # pygame.event.clear()
                        return selected_column
                    else:
                        print(f"Invalid move: {selected_column}")
            pygame.time.delay(10)
        

    def place_tile(self, selected_column: int, playr_num):
        selected_column -= 1
        placed = False
        playr = self.players[playr_num]
        if selected_column < len(self.board_arr[0]) and selected_column >= 0:
            for row in self.board_arr:
                if row[selected_column] == self.FILL_VALUE:
                    row[selected_column] = playr.id
                    placed = True
                    break
        return placed

    def game_over(self):
        """
        Game over check, will only be called by the server
        """
        horozontal = self.check_straight(self.board_arr)
        vertical = self.check_straight(self.board_arr.T)
        positive = self.check_diagonal(self.board_arr)
        negative = self.check_diagonal(np.flip(self.board_arr, 0))
        board_is_full = not np.any(self.board_arr == self.FILL_VALUE)
        return horozontal or vertical or positive or negative or board_is_full
    
    def check_straight(self, b):
        for row in b:
            for i in range(len(row) - WINNING_NUMBER + 1):
                if row[i] != self.FILL_VALUE and np.all(row[i:i+WINNING_NUMBER] == row[i]):
                    self.winner = row[i]
                    return True
        return False
    
    def check_diagonal(self, b):
        for r in range(len(b) + 1 - WINNING_NUMBER):
            for c in range(len(b[0]) + 1 - WINNING_NUMBER):
                if b[r][c] != self.FILL_VALUE and all(b[r][c] == b[r+k][c+k] for k in range(WINNING_NUMBER)):
                    self.winner = b[r][c]
                    return True
        return False

    def __str__(self):
        human_board = np.flip(self.board_arr, 0)
        return self.draw_board_in_terminal(human_board)
        # if self.in_terminal:
        #     return self.draw_board_in_terminal(human_board)
        # else:
        #     return self.draw_in_pygame(human_board)
    
    def draw_board_in_terminal(self, human_board):
        board_str = "\n"
        board_str += '  ' + "   ".join(str(n+1) for n in range(NUM_COLS)) + ' \n\n'
        for row in human_board:
            board_str += '| ' + " | ".join(
                aux.color_text(self.players[0], CIRCLE) if c == self.players[0].id else
                aux.color_text(self.players[1], CIRCLE) if c == self.players[1].id else
                ' ' if c == -1 else str(c) 
                for c in row
            ) + ' |\n'
        return board_str
    
    def draw_board_for_log(self):
        human_board = np.flip(self.board_arr, 0)
        board_str = "\n"
        board_str += '  ' + "   ".join(str(n+1) for n in range(NUM_COLS)) + ' \n\n'
        for row in human_board:
            board_str += '| ' + " | ".join(
                str(self.players[0].id) if c == self.players[0].id else
                str(self.players[1].id) if c == self.players[1].id else
                ' ' if c == -1 else str(c) 
                for c in row
            ) + ' |\n'
        return board_str
    
    # def draw_in_pygame(self, human_board):
    #     pass

    
if __name__ == '__main__':
    from Player import Player
    players = [Player('a', 0), Player('b', 1)]
    # b = Board(players)
    # print(b)
    b = Board(players, in_terminal=False)

    cur = 0
    while not b.game_over():
        b.update_board(current_player=cur)
        cur = (cur + 1) % 2
    