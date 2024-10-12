# Connect Four Game

This is a simple Connect Four game implemented using Python and sockets.

## Setup
- Requires minimum python 3.10 (due to the use of match control structures)
- On the CSU CS machines, run `source ./use-venv.sh` to load the appropriate python module and create/load the virtual environment.
- Currently, the server can only handle a single 2-player game at a time and will reject additional connections.

**How to play:**
1. **Start the server:** Run the `server.py` script.
   - Arguments:
       - `-i` to print the IPv4 address of the server
       - `-p` to print the port number the server is listening on
       - Exmaple: `python3 server.py -i -p`
       - `-h` will print a help dialog
       - `-d` will print the DNS name of the server
3. **Connect clients:** Run the `client.py` script on two different machines or terminals.
  - Arguments:
       - `-i <IP address of the server>` 
       - `-p <port number the server is listening on`
       - Exmaple: `python3 client.py -i 129.82.44.166 -p 55667` or `python3 client.py -i richmond.cs.colostate.edu -p 55667`
       - `-h` will print general rules of the game and a help dialog
5. **Play the game:** Players take turns entering their moves. The first player to get four in an row in any direction wins!

**Technologies used:**
* Python
* Sockets
* RSA Encryption

**Additional resources:**
* [Connect Four Rules](https://en.wikipedia.org/wiki/Connect_Four)
* [Encryption tutorial](https://www.geeksforgeeks.org/how-to-encrypt-and-decrypt-strings-in-python/)
* [Converting rsa object for json serialization](https://stuvel.eu/python-rsa-doc/reference.html#functions)

## Sprint 1 Behavior:
Two clients can connect to the server and specify their name once their connection is accepted. The server sends back each client their player id.
