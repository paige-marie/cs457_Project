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
