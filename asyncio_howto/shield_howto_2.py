import asyncio


async def x():
    for i in range(5):
        await asyncio.sleep(1)
        print(i)


async def y():
    for i in range(5):
        await asyncio.sleep(1)
        print("Y")


async def cancel_all(tasks):
    await asyncio.sleep(2)
    for i in tasks:
        i.cancel()
    print("Everything was canceled")


async def m():
    t1 = asyncio.create_task(x())
    t2 = asyncio.create_task(y())
    t3 = asyncio.create_task(x())
    t4 = asyncio.create_task(x())
    sh1 = asyncio.shield(t1)
    sh2 = asyncio.shield(t2)  # declared but not used !
    sh3 = asyncio.shield(t3)
    sh4 = asyncio.shield(t4)

    # pay attention that we cancel not original t1, t3, t4
    # only t2 will be canceled in the case
    can = asyncio.create_task(cancel_all([sh1, t2, sh3, sh4]))  # t2 is not sh2 !
    # return_exceptions = True, otherwise you'll have to handle CancelError explicitly
    await asyncio.gather(t1, t2, t3, t4, can, return_exceptions=True)
    print("All Done")

if __name__ == '__main__':
    asyncio.run(m())
