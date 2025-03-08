# Unclaimed Hills
A multiplayer game website hosted on vercel with a backend API for handling game actions
## Tools
* Next.js
  * *Typescript
* Flask
  * *Python
  * RESTful API
  * SocketIO
## API
### Post
* `/game/create`: No parameters
  * Returns: 'gameCode': String, 'hostId': String, 'playerId': String, 'board': Array, 'nextUpdateTime': Float
* `/game/join`: 'gameCode': String
  * Returns: 'playerId': String, 'board': Array, 'nextUpdateTime': Float
* `/game/move`: 'gameCode': String, 'playerId': String, 'index': Integer, 'moveType': String
  * Returns: 'nextGameUpdate': Integer
### Get
* `/game/active`: No parameters
* `/game/sync`: 'gameCode': String
  * Returns: 'board': String, 'nextUpdateTime': String, 'pendingMoves': Map, 'gameOver': boolean, 'winner': String
### Socket IO
* TO SERVER (Input) `join_game`: 'gameCode': String
  * Adds player to game room, returns same info as `/game/sync`
* FROM SERVER (Output) `game_update`
  * Five second interval, returns same info as `/game/sync`
* FROM SERVER (Output) `game_timeout`
  * Removes session when host has not responded or game has lasted too long
