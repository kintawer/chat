import asyncio
import logging
from typing import Optional

import websockets
from websockets import WebSocketServerProtocol


def configure_logging():
    logger = logging.getLogger()
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')

    console_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)


class Client:
    def __init__(self, websocket, name):
        self.ws = websocket
        self.name = name

    @property
    def ip(self):
        return ':'.join(str(part) for part in self.ws.remote_address)


class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._ws_server: Optional[websockets.WebSocketServer] = None
        self._client_pool = {}

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.init())
            loop.run_forever()
        except KeyboardInterrupt:
            logging.info("Server stopping...")
            loop.run_until_complete(self.stop())
        except Exception as e:
            logging.exception("Woops", exc_info=e)
            loop.run_until_complete(self.stop())
            self.run()

    async def init(self):
        serve = websockets.serve(self.on_client_connect, self.host, self.port,
                                 ping_timeout=None)
        server = await serve
        logging.info("Server running...")
        self._ws_server = server

    async def stop(self):
        self._ws_server.close()
        await self._ws_server.wait_closed()

    async def on_client_connect(self, websocket: WebSocketServerProtocol, path):
            client = await self.first_conn(websocket)
            while True:
                try:
                    message = await client.ws.recv()
                    await self.chatting(message, client)
                except websockets.exceptions.ConnectionClosedOK:
                    logging.info(f'Client {client.name} was leave from chat.')
                    self._client_pool.pop(client.ip, None)
                    await self.send_all(f'Client {client.name} leave from chat')
                    logging.info(f'Current clients: '
                                 f'{list(self._client_pool.keys())}')
                    break

    async def first_conn(self, websocket):
        await websocket.send("Say your name")
        name = await websocket.recv()
        logging.info(f"New client - {name}!")
        client = Client(websocket, name)

        self._client_pool[client.ip] = client
        await websocket.send(f"Hello {name}! Enjoy chatting!")
        return client

    async def chatting(self, message, client):
        logging.info(f"< [{client.name}] {message}")

        answer = f"> [{client.name}] {message}"
        await self.send_all(answer)

    async def send_all(self, msg):
        for ip, client in self._client_pool.items():
            logging.info(f"> [{ip}]: {msg}")
            await client.ws.send(msg)


if __name__ == '__main__':
    configure_logging()
    srv = ChatServer("0.0.0.0", 8765)
    srv.run()
