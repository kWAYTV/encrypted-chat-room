import sys, socket, threading
from kwslogger import Logger

logger = Logger()
logger.create_logo("EC Server")

# Choose a port that is free
PORT = 8000

# An IPv4 address for the server.
SERVER = '0.0.0.0'

# Address is stored as a tuple
ADDRESS = (SERVER, PORT)

# the format in which encoding
# and decoding will occur
FORMAT = "utf-8"

# Lists that will contains all the clients/rooms connected to the server.
rooms = {'CHAT': {}, 'PLUTO': {}}

# Create a new socket for the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind the address of the server to the socket
server.bind(ADDRESS)


# function to start the connection
def startChat():
    logger.info("server is working on " + SERVER)

    # listening for connections
    server.listen()

    while True:
        # accept connections and returns a new connection to the client and the address bound to it
        conn, addr = server.accept()

        # receive room name
        room = conn.recv(64).decode()
        if room in rooms:  # if room exists
            conn.send(b'ok')  # send acknowledgment

            # append the client to the respective list
            rooms[room][addr[0] + str(addr[1])] = conn

            name = conn.recv(64).decode()
            conn.send(b'ok')  # send acknowledgment
            joined = conn.recv(4096)
            conn.send(b'ok')  # send acknowledgment
            left = conn.recv(4096)
            conn.send(b'ok')  # send acknowledgment

            # Start the handling thread
            thread = threading.Thread(target=handle, args=(conn, addr, room, name, joined, left))
            thread.start()

            # no. of clients connected to the server
            logger.info(f"active connections {threading.activeCount() - 1}")

        else:
            logger.warning('Room does not exist.')
            conn.close()


# incoming messages
def handle(conn, addr, room, name, joined, left):
    broadcastMessage(joined, room)
    logger.info(f"new connection {addr} = {name} to {room}.\n")
    while True:
        try:
            # receive message
            message = conn.recv(4096)
            # broadcast message
            broadcastMessage(message, room)
        except:
            break

    # close the connection
    conn.close()

    # remove the client from the clients list
    del rooms[room][addr[0] + str(addr[1])]
    logger.info(f"{name} has disconnected")
    broadcastMessage(left, room)


# method for broadcasting
# messages to the each clients
def broadcastMessage(message, room):
    for addr in rooms[room]:
        rooms[room].get(addr).send(message)


# begin the communication
try:
    startChat()
except KeyboardInterrupt:
    server.close()
    server.close()
except:
    server.close()
    sys.exit(0)