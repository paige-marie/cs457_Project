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
       - `-g` use a GUI for gameplay
       - Exmaple: `python3 server.py -i -p 55567`

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

The first time the server is started, it instigates the creation of the CA's "certificate", which is only to say it creates public and private keys for the CA. All "certificates" are just the public key. Normally the certificate would include other information beyond the key, like who owns it and validity duration. This key creation depends on NFS, or some other shared file system, being in use; the clients will use these same CA key and will wait for the server to get them created before continuing. These keys are saved to files that are reused for subsequent runs. 

(Note: there is a small chance of a race condition with the CA key creation. The server should be started and allowed to create the keys before the clients are started)

Every time the server and client are started, they create new keys for themselves, which they get signed by the simulated CA's private key. Normally, one would undergo rigorous authentication with the CA to have their full certificate signed and would save and reuse it. During their initial communication, the server and client exchange their public keys and the CA's signature. Both verfify the signature is from the CA for that key using the CA's public key.

If the signature is found to be invalid, the server will send an error and terminate the connection, then continue waiting for new connections. The client will print a message to the user and terminate the program. 

## Security Evaluation
With the simulated CA and installed certificates, a vulnerability is that only the public key is used to create the signature. There is no identifying information that links that key to the user sending it. This means it is trivial authentication, but it does still offer integrity of the key. The server expects to decrypt every message after the first using the client's public key, so a man in the middle could not pose as that client. However, since the public keys are sent in clear text, all traffic could be decrypted by an observer if they intercepted those initial messages.

## Optional GUI
The clients support an optional GUI board interface. To enable, the client needs to be passed the `-g` flag when started. The GUI interface uses Pygame. The use of the GUI is completely transparent to the server and the other player. The payer clicks anywhere in the column they'd like to drop their tile. The GUI updates the player about whether it is their turn and who won.

Pygame also has an odd behavior regarding the game loop. Because the clients are completely serial, the sequence must leave the game loop to listen to the socket. When out of the gameloop, Pygame somehow gobbles (and does nothing with) all mouseclicks. This has the effect of the player being unable to click elsewhere (outside of the Pygame window) until it's their turn. This is fixable, but would add complexity (multiple threads) and require a major refactor of the client. We chose not to drastically change the client without sufficient time to test. 

Pygame is incompatable with X11 forwarding to MacOS because of Mac's default openGL version. Using Linux or Windows, if you try to X11 forward two GUIs at once, they will open right on top of each other, causing the one to open first to be blank because it's not in the rendering loop.

The best way to use try the GUI is to use RDP. Either with two RDP sessions or the other player can use SSH to play with the terminal UI. This way, when Pygame gobbles the mouseclicks, it doesn't matter because nothing else besides making that player's move needs to be done in that session. Note that keystrokes are still accepted, so you can always ALT-TAB to the terminal running the client and use CTRL-C to end it. Because this is a tricky setup, screenshots are provided in the folder `/gui-screenshots`.

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
- **FIXED** When entering a negative number for the selected column to place a tile, move was allowed due to python's negative indexing. Input is now restricted to positive numbers. 
- When using the GUI, pygame gobbles all mouseclicks when if it not the user's turn. This make it impossible to play both players on the same machine. 
- In terminal mode, if a client inputs a number when it isn't their turn, that input is used on their next turn.

## Technologies used:
* Python
* Sockets
* RSA Encryption
* Pygame

## Additional resources
* [Connect Four Rules](https://en.wikipedia.org/wiki/Connect_Four)
* [Encryption tutorial](https://www.geeksforgeeks.org/how-to-encrypt-and-decrypt-strings-in-python/)
* [Converting rsa object for json serialization](https://stuvel.eu/python-rsa-doc/reference.html#functions)
* [Pygame docs](https://www.pygame.org/docs/)

## Future Plans
There are two main thrusts for future work on this game. A user defined dynamic board and multiple games running at once in the server.

### Multiple games
The server was designed with supporting multiple games in mind. It is why the game state is separate from the server state. As soon as the server detects that there are 2 players waiting, it starts a game. Currently, if additional clients try to connect, the server notifies them that the game is full and terminates that connection. To support multiple simultaneous games, the server would not do this but instead start yet another game. This would require a method of looking up, by the player’s information stored with the socket, which game they are associated with. It would also need a way to store each game state separately, such as a game class. 

### Dynamic Board
Connect four is traditionally a 6x7 board where 4 in a row wins. Theses game parameters are easily changed, and the board class is written is such a way that they could be changed at instantiation time. This would require some rule about which player gets to select the board state, as well as some restrictions on the relationship between numbers chosen. For example, if you need 4 in a row to win, choosing a 3x3 board does not make sense and should be denied. Additionally, more than 2 players could be allowed to play on the same board, and they could pick their own color. 


## Retrospective
### What went right
- Using the TCP sockets asynchronously in the server using the select mechanism was an interesting and new perspective for asynchronous Python. 
- Updating and using server state in a way that produced predictable behavior in the face of different possible client actions was also an interesting challenge which we enjoyed.

### What could be improved on
- The biggest difficulty was introducing Pygame. The GUI has some undesirable behavior, but because of breadth of changes required to make it behave how we wanted, we chose not to potentially introduce bugs without enough time to test. The easiest way this could have been addressed is by making the client multithreaded when the GUI option was used. 
- Another difficulty was encryption. The key objects were an uncommon format that could not be serialized using the json library. Working with these, both serializing and deserializing them, was a unique challenge.

