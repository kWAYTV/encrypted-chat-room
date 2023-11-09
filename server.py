import socket, sys, threading
from threading import Lock
from kwslogger import Logger

class Client:
    def __init__(self, server: str, port: int, rooms: dict = {'CHAT': {}}, encoding_format: str ="utf-8"):
        self.logger = Logger()
        # lock for handling multiple clients
        self.lock = Lock()
        # An IPv4 address for the server with port.
        self.server, self.port = server, port
        # Address is stored as a tuple
        self.address = (self.server, self.port)
        # the format in which encoding and decoding will occur
        self.encoding_format = encoding_format
        # Lists that will contains all the clients/rooms connected to the server.
        self.rooms = rooms
        # Create a new socket for the server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the address to the server
        self.client.bind(self.address)
        # Create a logo for the server
        self.logger.create_logo("EC Server")

    def start_chat(self):
        self.logger.info(f"Server started on {self.server}:{self.port}")

        # listening for connections
        self.client.listen()

        while True:
            # accept connections and returns a new connection to the client and the address bound to it
            conn, addr = self.client.accept()

            # receive room name
            room = conn.recv(64).decode()
            if room in self.rooms:  # if room exists send acknowledgment
                conn.send(b'ok')

                # append the client to the respective list
                self.rooms[room][addr[0] + str(addr[1])] = conn

                name = conn.recv(64).decode()
                conn.send(b'ok')  # send acknowledgment
                joined = conn.recv(4096)
                conn.send(b'ok')  # send acknowledgment
                left = conn.recv(4096)
                conn.send(b'ok')  # send acknowledgment

                # Start the handling thread
                thread = threading.Thread(target=self.handle, args=(conn, addr, room, name, joined, left))
                thread.start()
            
            else:
                self.logger.warning("Room does not exist")
                conn.close()

    def handle(self, conn, addr, room, name, joined, left):
        with self.lock:
            self.logger.info(f"Active connections {threading.active_count() - 1}.")
            self.logger.info(f"New connection {addr} = {name} to {room}.")
            self.broadcast_message(joined, room)

            while True:
                try:
                    # receive message
                    message = conn.recv(4096)
                    # broadcast message
                    self.broadcast_message(message, room)
                except:
                    break

            # close the connection
            conn.close()

            # remove the client from the clients list
            del self.rooms[room][addr[0] + str(addr[1])]
            self.logger.info(f"The user {name} has disconnected.")
            self.broadcast_message(left, room)

    def broadcast_message(self, message, room):
        for addr in self.rooms[room]:
            self.rooms[room].get(addr).send(message)

if __name__ == '__main__':
    client = Client(server="127.0.01", port="8000", rooms={'CHAT': {}, 'PLUTO': {}})
    try:
        client.start_chat()
    except KeyboardInterrupt:
        client.logger.info("Goodbye!")
        client.client.close()
        sys.exit(1)
    except Exception as e:
        client.logger.error(f"An error occured {e}.")
        client.client.close()
        sys.exit(1)