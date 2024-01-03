import os
import uuid
import asyncio 
import json

from datetime import datetime
try:
    from colorama import Fore, Style , init
    import aiohttp
except ModuleNotFoundError:
    os.system("pip install colorama aiohttp")
    os.system("cls")
    from colorama import Fore, Style , init

f = open("promos.txt",'r+')
genned = len(f.read().splitlines())
f.close()
f = open("proxies.txt", 'r+')
f.close()
logfile = open("log.txt", 'a+')
class Logger:
    @staticmethod
    def Sprint(tag: str, content: str, color):
        ts = f"{Fore.RESET}{Fore.LIGHTBLACK_EX}{datetime.now().strftime('%H:%M:%S')}{Fore.RESET}"
        print(Style.BRIGHT + ts + color + f" [{tag}] " + Fore.RESET + content + Fore.RESET)
        logfile.write(f"[{tag}] {content}\n")

class Stop():
    def __init__(self):
        self._stop = False

    def stop(self):
        self._stop = True

    def should_stop(self):
        return self._stop

async def gen(idx, proxy=None):
    global genned
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post('https://api.discord.gx.games/v1/direct-fulfillment', json={
                'partnerUserId': str(uuid.uuid4()),
            }, proxy=proxy) as response:
                if response.status == 429:
                    await asyncio.sleep(5)
                    return
                response = await response.text()
                ptoken = json.loads(response)['token']
                link = f"https://discord.com/billing/partner-promotions/1180231712274387115/{ptoken}"
                genned += 1
                if genned % 1000 == 0:
                    
                    Logger.Sprint(f"PROMO", f"Thread ({idx}) Promo No. {genned}", Fore.LIGHTGREEN_EX)
                f = open("promos.txt", 'a')
                f.write(f"{link}\n")
                f.close()
        except asyncio.CancelledError:
            # Handle cancellation appropriately, e.g., by cleaning up resources.
            # Logger.Sprint(f"GEN", f"Coroutine canceled (Thread {idx})", Fore.LIGHTRED_EX)
            raise  # Re-raise the exception to ensure it's propagated


async def load_proxies(filename):
    links = open(filename, "r").read().splitlines()
    with open("proxies.txt", 'a+') as f:
        async with aiohttp.ClientSession() as session:
            for link in links:
                async with session.get(link) as resp:
                    proxies = [x.strip() for x in (await resp.text()).split("\n")]
                    f.write("\n" + "\n".join(proxies))
                    
async def run(stop: Stop, idx, proxy = None):
    global proxies
    escape = False
    if proxy:
        proxy = f"http://{proxy}"
    failures = 0
    errors = ['reset by peer', 'Proxy Authentication Required', '503', '403', '502', '500', 'timed out', 'WinError 64', 'refused', 'semaphore']
    while not stop.should_stop():
        try: 
            await gen(idx, proxy)
            failures -= 1
        except Exception as e:
            e = str(e)
            if (
                any(x in e for x in errors) or 
                ("Cannot connect to host" in e and "failed" in e)
                ):
                failures += 1
            elif (
                ('Server disconnected' in e) or 
                ('400' in e) or 
                ('transport' in e)
                  ):
                failures += 1
            elif ("api.discord.gx.games" in e):
                failures += 0.5
            elif ("GeneratorExit" in e):
                break
            elif ("Coroutine" in e):
                failures += 10000
            else:
                failures += 1
                failures = round(failures, 4)
                Logger.Sprint("ERROR",f"Thread ({idx}) ({failures}) {e}",Fore.LIGHTRED_EX)
            if failures >= 5:
                Logger.Sprint("ERROR",f"Thread ({idx}) Proxy ({proxy.split('//')[1]}) is dead!",Fore.RED)
                proxies.remove(proxy.split("//")[1] if proxy.strip() != "" else proxy)
                to_write = "\n".join(proxies)
                with open("proxies.txt", 'w+') as f:
                    f.write(to_write)
                return


async def setup(): 
    init()
    await load_proxies("proxy_sources.txt")

def main():
    global proxies
    f = open("proxies.txt", 'r+')
    proxies = f.read().splitlines()
    loop = asyncio.new_event_loop()
    stop = Stop()
    tasks = []

    for i, p in enumerate(proxies):
        task = loop.create_task(run(stop, i, p))
        tasks.append(task)

    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except KeyboardInterrupt:
        Logger.Sprint("GEN", "Received KeyboardInterrupt. Cleaning up...", Fore.LIGHTRED_EX)
    finally:
        # Cancel remaining tasks
        for task in tasks:
            task.cancel()

        try:
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except asyncio.CancelledError:
            pass

        # Clean up resources and stop the loop
        with open("proxies.txt", 'w+') as f:
            f.write("\n".join(proxies))
        stop.stop()
        loop.close()


if __name__ == "__main__":
    asyncio.run(setup())
    main()