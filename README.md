# Connect Four Game

This is a simple Connect Four game implemented using Python and sockets.

## Setup
- <ins>**Requires minimum python 3.10**</ins> (due to the use of the match control structures)
- On the CSU CS machines, run `source ./use-venv.sh` to load the appropriate python module and create/load the virtual environment.
- Currently, the server can only handle a single 2-player game at a time and will reject additional connections.

**How to play:**
1. **Start the server:** Run the `server.py` script.
   - Arguments:
       - `-i` to print the IPv4 address of the server
       - `-p` to specify the port number the server is listening on. If ommited, a default port is  used
       - `-h` will print a help dialog
       - `-d` will print the DNS name of the server
       - Exmaple: `python3 server.py -i -p`
3. **Connect clients:** Run the `client.py` script on two different machines or terminals.
   - Arguments:
       - `-i` to specify the IP address or hostname of the server
       - `-p` to specify the port number the server is listening on
       - `-h` will print general rules of the game and a help dialog
       - Exmaple: `python3 client.py -i 129.82.44.166 -p 55667` or `python3 client.py -i richmond.cs.colostate.edu -p 55667`
5. **Play the game:** Players take turns entering their moves. The first player to get four in an row in any direction wins! 
   - The clients will get the players' names and connect to the server. Once the server has two connections, it will begin the game, randomly selecting a player to begin.
   - The players will alternate selecting which column to place their tile. The server communicates the move to the other client so they can take their turn.
   - At every turn, the server will check if the win state is satisfied and communicate who won to both clients. 
      - After a player wins, the server closes the connections to the clients.
      - When the connection is closed, the client program will terminate
      - The server remains running and 2 more client players can connect and play. Use `ctrl-C` to stop the server.
    
## Encryption
Asymetrical RSA encryption with SHA256 hash digests are used for communicating between the client and server. A simulated certificate authority (CA) is implemented. 

The first time the server is started, it instigates the creation of the CA's "certificate", which is only to say it creates public and private keys for the CA. All "certificates" are just the public key. Normally the certificate would include other information beyond the key, like who owns it and duration. This key creation depends on NFS, or some other shared file system, being in use; the clients will use these same keys and will wait for the server to get them created before continuing. These keys are saved to files that are reused for subsequent runs. 

Every time the server and client are started, they create new keys for themselves, which they get signed by the simulated CA's private key. Normally, one would undergo rigorous authentication with the CA to have their full certificate signed and would save and reuse it. During their initial communication, the server and client exchange their public keys and the CA's signature. Both verfify the signature is from the CA for that key.

If the signature is found to be invalid, the server will send an error and terminate the connection, then continue waiting for new connections. The client will print a message to the user and terminate the program. 

## Message Protocol
Before every message are 11 bytes containting the following information: 

`{
   str: "length",
   int: <length of json, in bytes>, 
   boolean: <True when message is encrypted>
}`

This is followed by the message json contents in bytes. Every message contains a protocol number that defines what type of message is being sent and what information is associated with it. These protocols are defined as follows:

**REGISTER_CLIENT:**

Sent by the client to the server upon initiating the connection. Contains the client's public key and a name for the player. 

**REGISTER_CONFIRM:**

Sent by the server to the client to confirm a clients successful registration. Contains the client's player ID and the servers public key.

**OTHER_PLAYER:**

Sent by the server to the client to convey the other connected players' information. Contains the other players name and ID.

**YOUR_TURN:**

Sent by the server to specify that it is a client's turn. Contains the last move made by the other player. When it is the first move of the game, it sends -1.

**MAKE_MOVE:**

Sent by the client to the server to specify the move that they have made. Contains the client's move.

**GAME_OVER:**

Sent by the server to indicate that the game has ended. It contains the winning players ID and the last move resulting in the win.

**ERROR:** 

Sent by the indicating that an error has occured. Contains the error code of the type of error that has occured and the message associated with the error.


## State Management
The server maintains state for both the connections to it and the currently running game.

**Server State:**
* The connections that are not currently involved in a game
* The number of connections that have completed registration and are ready to be added to a game. When this is 2, the game starts.

**Game State:**
* The connections of the players playing the game
* Whose turn it currently is
* The state of the board.
 
The server makes the player’s moves on the board, updating the board state and checking if the moving is a winning one. If it is, the players are notified, their connections are closed, and the server returns to a waiting-for-players state. If not, the server communicates the move to the other player so they can make their move.


## Gameplay, Game State, and UI

**Game State Management (continued):**
* The server updates state (player info, tile placements, game termination state) and communicates it to the clients so they can display the state of the board during gameplay.

**Input Handling:**
* Clients allow users to select a column on the board to ‘drop’ their tile. Clients enforce the selection is valid (within the board boundaries and in a column that is not full) before communicating the move to the server.

**Winning Conditions:**
* Server checks at every move whether a game-over state has been reached. Game over states include: a player has won, the game is a draw, or a player has forfeited (when they disconnect prematurely)

**Game Over Handling:**
* When the game is determined to be over, the server communicates the winner (or indicates the game is a draw) to the clients. To play again, the clients reconnect to the server.

**User Interface (UI):**
* The board is displayed to the players with a simple terminal board representation. The players have their name and tiles displayed in their assigned colors. The players are clearly asked for their name at the beginning of the game and the number that corresponds to the column they want to ‘drop’ their tile into

## Known Issues
- Combinations of user disconnect states before the game has started, either before or after the player has been registered, interrupt the assignment of player ids, which affects the downstream action of assigning colors and play order. This is an intermitant issue that is difficult to replicate and isolate. Even now, the bug is believed to be fixed, but may not be. Gameplay proceeds normally, but tile colors are the same (which makes the game impossible for the user to play).

## Technologies used:
* Python
* Sockets
* RSA Encryption

## Additional resources
* [Connect Four Rules](https://en.wikipedia.org/wiki/Connect_Four)
* [Encryption tutorial](https://www.geeksforgeeks.org/how-to-encrypt-and-decrypt-strings-in-python/)
* [Converting rsa object for json serialization](https://stuvel.eu/python-rsa-doc/reference.html#functions)

## Sprint 1 Behavior:
Two clients can connect to the server and specify their name once their connection is accepted. The server sends back each client their player id.

