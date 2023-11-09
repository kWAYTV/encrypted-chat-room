import sys, socket, threading
from threading import Lock
from kwslogger import Logger

# Initialize the logger
logger = Logger()

logger.create_logo("EC Server")

# An IPv4 address for the server with port.
SERVER, PORT = '127.0.0.1', 8000

# Address is stored as a tuple
ADDRESS = (SERVER, PORT)

# the format in which encoding and decoding will occur
FORMAT = "utf-8"

# Lists that will contains all the clients/rooms connected to the server.
rooms = {'CHAT': {}, 'PLUTO': {}}

# Create a new socket for the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind the address of the server to the socket
server.bind(ADDRESS)

# lock for handling multiple clients
lock = Lock()

# function to start the connection
def start_chat():
    logger.info(f"Server started on {SERVER}:{PORT}")

    # listening for connections
    server.listen()

    while True:
        # accept connections and returns a new connection to the client and the address bound to it
        conn, addr = server.accept()

        # receive room name
        room = conn.recv(64).decode()
        if room in rooms:  # if room exists send acknowledgment
            conn.send(b'ok')

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

        else:
            logger.warning('Room does not exist.')
            conn.close()

# incoming messages
def handle(conn, addr, room, name, joined, left):
    with lock:
        logger.info(f"Active connections {threading.active_count() - 1}.")
        logger.info(f"New connection {addr} = {name} to {room}.")
        broadcast_message(joined, room)
        while True:
            try:
                # receive message
                message = conn.recv(4096)
                # broadcast message
                broadcast_message(message, room)
            except:
                break

        # close the connection
        conn.close()

        # remove the client from the clients list
        del rooms[room][addr[0] + str(addr[1])]
        logger.info(f"The user {name} has disconnected.")
        broadcast_message(left, room)

# method for broadcasting messages to the each clients
def broadcast_message(message, room):
    for addr in rooms[room]:
        rooms[room].get(addr).send(message)

# begin the communication
try:
    start_chat()
except KeyboardInterrupt:
    server.close()
    sys.exit(0)
except:
    server.close()
    sys.exit(0)