import socket
# import _thread
# import pickle
import shared_assets

class Server:
    # Should the player join the server when they start the game, or when they join the lobby?
    DEFAULT_PORT = shared_assets.port

    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port_to_try = self.DEFAULT_PORT
        while True:
            try:
                self.socket.bind(("", port_to_try))
                break
            except socket.error as e:
                print("Unable to bind socket: ", e)
                port_to_try = int(input("Input new port: "))

        self.socket.listen()
        print("Server started, waiting for user(s) to connect")

    def send(self):
        ...

    def recv(self):
        ...

def listen_for_players():
    while True:
        conn, address = server.socket.accept()

        print("Connected to", address)

        # _thread.start_new_thread(..., (conn,))


if __name__ == "__main__":
    server = Server(shared_assets.port)
    listen_for_players()
