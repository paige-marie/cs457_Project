# Statement of Work (SOW) Template for Socket Programming Project
## Project Title:
Connect Four - 2 player

## Team:
Marlowe Lankford, Caleb Chou, Paige Hansen

## Project Objective:
Develop a functioning Connect 4 game in which a centralized server accepts two client connections and handles game state and functionality. 
## Scope:
### Inclusions:
- Write python code to create a TCP server, listening for two connections.
- Write python code to create TCP clients, able to sustain a connection with the server.
- Prompt users to select a column to drop their piece into. 
- Server must handle user input.
- Tutorial that teaches player how to play / set up
### Exclusions:
* No single player version
* No web interface
* Not more than 2 players
## Deliverables:
- A working Python server
- A working client
Documentation
## Timeline:
### Key Milestones:
- Milestone 1 (Complete by Sept. 22) Est time: 3-4 days
  - Team formation and role assignment
  - Install tools (Python, Git, IDE)
  - Submit Statement of Work (SOW) with chosen game design
- Milestone 2 (Complete by Oct 6) Est time: 1.5 weeks
  - Implement basic client-server connection using sockets
  - Test two clients connecting to the server
  - Add CLI options for client (-i, -p, -h) and server (-i, -p, -h)
- Milestone 3 (Complete by Oct 20) Est time: 3 days
  - Design a game message protocol (e.g., for turn updates, game state synchronization)
  - Handle multiple client connections
- Milestone 4 (Complete by Nov 3) Est time: 1 week
  - Develop multiplayer features, save game state across clients
  - Milestone 5: (Complete by Nov 17) Est time: 2 weeks
  - Implement full game functionality
- Milestone 6: (Complete by Dec 6) Est time: 2 days
  - Error handling + final polishing of application
### Task Breakdown:
* Implement basic server functionality to connect clients
* Implement basic client functionality to connect to the server
* Implement basic game functionality (2 players playing on the same terminal)
* Define protocols for 
  * Establishing player connections
  * Communicating who’s turn it is
  * Making a move
  * Communicating other players move
  * Communicating winner
  * Graceful disconnect
* Combine previous parts into a single system
* Implement error checking at various stages (invalid moves, player unexpectedly disconnects, etc.) 

## Technical Requirements:
### Hardware:
Players will need a computer with a network card, either WiFi or ethernet. 
### Software:
Programming languages: Python 3
- Required libraries: socket, some sort of json library
- Python compatible environment
- Should be cross platform with players on any OS able to connect
## Assumptions:
Both players and all group members can connect to the internet
## Roles and Responsibilities:
- Developers: All team members.
  - Everyone will contribute equally to complete their assigned tasks. Team members will check in and help others if they are struggling
- Testers: All team members
  - All team members will contribute to the testing, however, team members should be sure to not test their own features.
- Project Manager: Marlowe Lankford
  - Schedule meeting times for group
  - Maintain GitHub repository organization
  - Ensure timely milestone completion and accuracy
  - Assist in application development and testing
## Communication Plan:
- Communicate online through Microsoft Teams. 
- Meetings will be decided on a week-by-week basis, depending on project progress state and load of work to be done. Decision making will require all group members to agree on decisions. This means if any group member wants to make a change or new implementation, it will have to be agreed upon.
- All code changes must be reviewed as a GitHub pull request, and approved by both other group members before merging. 
