# Connect Four Game

This is a simple Connect Four game implemented using Python and sockets.

## Setup
- Requires minimum python 3.10 (due to the use of match control structures)
- On the CSU CS machines, run `source ./use-venv.sh` to load the appropriate module and create/load the virtual environment.

**How to play:**
1. **Start the server:** Run the `server.py` script.
2. **Connect clients:** Run the `client.py` script on two different machines or terminals.
3. **Play the game:** Players take turns entering their moves. The first player to get four in an row in any direction wins!

**Technologies used:**
* Python
* Sockets

**Additional resources:**
* [Connect Four Rules](https://en.wikipedia.org/wiki/Connect_Four)

**Spring 1 Behavior:**
Two clients can connect to the server and specify their name once their connection is accepted. The server send back each client their player id.
