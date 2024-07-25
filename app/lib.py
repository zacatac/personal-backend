import asyncio
from typing import AsyncGenerator, Tuple


async def async_tee(
    generator: AsyncGenerator, n: int = 2
) -> Tuple[AsyncGenerator, ...]:
    queues = [asyncio.Queue() for _ in range(n)]

    async def distribute():
        async for item in generator:
            for queue in queues:
                await queue.put(item)
        for queue in queues:
            await queue.put(None)

    asyncio.create_task(distribute())
    return tuple(_queue_to_async_gen(queue) for queue in queues)


async def _queue_to_async_gen(queue: asyncio.Queue) -> AsyncGenerator:
    while True:
        item = await queue.get()
        if item is None:
            break
        yield item
