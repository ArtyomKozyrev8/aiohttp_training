import asyncio


async def real_task():
    print("Task started")
    await asyncio.sleep(5)
    print("Task finished")


async def cancel_task(t: asyncio.Task):
    await asyncio.sleep(1)
    t.cancel()
    print("Cancellation done!")


async def main():
    t = asyncio.create_task(real_task())
    sh = asyncio.shield(t)
    can = asyncio.create_task(cancel_task(sh))  # pay attention that we cancel sh, not original t
    await t
    if sh.done():
        print("Yes")
    if sh.cancelled():
        print("Yeap")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
