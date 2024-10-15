from colorama import Fore, Style
import os, platform

RED = Fore.RED
BLUE = Fore.BLUE

def clear_terminal():
    os.system('cls') if platform.system() == "Windows" else os.system('clear')

def color_text(player, text): 
    return player.color_code + text + Style.RESET_ALL

class CustomError(Exception):
    """Custom exception for specific error conditions."""
    def __init__(self, message):
        super().__init__(message)
