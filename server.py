from client import ChatClient
from threading import Thread
import socket
import sys

PORT = 9877


class ChatServer(Thread):
    def __init__(self, port, host='localhost'):
        super().__init__(daemon=True)
        self.port = port
        self.host = host
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP
        )
        self.client_pool = []
        try:
            self.server.bind((self.host, self.port))
        except:
            print('Bind failed')
            sys.exit()
        self.server.listen(10)

    def parser(self, id, nick, conn, message):
        """ Parse user input """
        if message.decode().startswith('@'):
            data = message.decode().split(maxsplit=2)
            if data[0] == '@quit':
                conn.sendall(b'You have left the chat.\n')
                reply = nick.encode() + b' has left the channel.\n'
                [c.conn.sendall(reply) for c in self.client_pool if len(self.client_pool)]
                self.client_pool = [c for c in self.client_pool if c.id != id]
                conn.close()
            elif data[0] == '@list':
                [conn.sendall((c.nick + '\n').encode()) for c in self.client_pool]
            elif data[0] == '@nickname':
                for i in range(len(self.client_pool)):
                    if self.client_pool[i].nick == nick:
                        old = self.client_pool[i].nick
                        self.client_pool[i].nick = data[1].replace('\n', '')
                reply = 'Your nickname has been changed from {} to {}'.format(old, data[1])
                conn.sendall(reply.encode())
            elif data[0] == '@dm':
                sender = [c.nick for c in self.client_pool if c.id == id][0]
                recipient = data[1]
                message = data[2]
                reply = 'DM: ' + sender + ': ' + message
                for c in self.client_pool:
                    if c.nick == recipient:
                        c.conn.sendall(reply.encode())
            else:
                conn.sendall(b'Invalid command')
        else:
            for c in self.client_pool:
                if c.id == id:
                    reply = c.nick.encode() + b': ' + message
            [c.conn.sendall(reply) for c in self.client_pool if len(self.client_pool)]

    def run_thread(self, id, nick, conn, addr):
        """ Manage connection, accept user input """
        print('{} connected with {}:{}'.format(nick, addr[0], str(addr[1])))
        try:
            while True:
                data = conn.recv(4096)
                self.parser(id, nick, conn, data)
        except (ConnectionResetError, BrokenPipeError, OSError):
            conn.close()

    def run(self):
        """ Accept connections, add to client_pool, start thread """
        print('Server running on {} : {}'.format(self.host, PORT))
        while True:
            conn, addr = self.server.accept()
            client = ChatClient(conn, addr)
            self.client_pool.append(client)
            Thread(
                target=self.run_thread,
                args=(client.id, client.nick, client.conn, client.addr),
                daemon=True
            ).start()

    def exit(self):
        self.server.close()


if __name__ == '__main__':
    server = ChatServer(PORT)
    try:
        server.run()
    except KeyboardInterrupt:
        [c.conn.close() for c in server.client_pool if len(server.client_pool)]
        server.exit()
