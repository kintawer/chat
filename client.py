import asyncio
import websockets


async def client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        recv = asyncio.create_task(receiver(websocket))
        send = asyncio.create_task(sender(websocket))
        await asyncio.wait([send, recv], return_when=asyncio.FIRST_COMPLETED)


async def sender(ws):
    loop = asyncio.get_event_loop()
    while True:
        msg = await loop.run_in_executor(None, input)
        if msg == 'exit':
            break
        await ws.send(msg)


async def receiver(ws):
    while True:
        try:
            msg = await ws.recv()
            print(msg)
        except websockets.exceptions.WebSocketException:
            print(f"Error with websocket")
            break
        except asyncio.CancelledError:
            break


if __name__ == '__main__':
    asyncio.run(client())
