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

class Logger:
    @staticmethod
    def Sprint(tag: str, content: str, color):
        ts = f"{Fore.RESET}{Fore.LIGHTBLACK_EX}{datetime.now().strftime('%H:%M:%S')}{Fore.RESET}"
        print(Style.BRIGHT + ts + color + f" [{tag}] " + Fore.RESET + content + Fore.RESET)
    
async def gen(idx, proxy = None):
    global genned
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.discord.gx.games/v1/direct-fulfillment', json={
            'partnerUserId': str(uuid.uuid4()),
        },proxy=proxy) as response:
            if response.status == 429:
                # Logger.Sprint("RATELIMIT",f"Thread ({idx}): You are being rate limited!",Fore.LIGHTYELLOW_EX)
                await asyncio.sleep(5)
                return
            response = await response.text()
            ptoken = json.loads(response)['token']
            link = f"https://discord.com/billing/partner-promotions/1180231712274387115/{ptoken}"
            genned += 1
            if genned % 100 == 0:
                Logger.Sprint(f"PROMO",f"Thread ({idx}) Promo No. {genned}",Fore.LIGHTGREEN_EX)
            f = open("promos.txt",'a')
            f.write(f"{link}\n")
            f.close()
async def load_proxies(filename):
    links = open(filename, "r").read().splitlines()
    with open("proxies.txt", 'a+') as f:
        async with aiohttp.ClientSession() as session:
            for link in links:
                async with session.get(link) as resp:
                    proxies = [x.strip() for x in (await resp.text()).split("\n")]
                    f.write("\n")
                    f.write("\n".join(proxies))
                    
async def run(idx, proxy = None):
    if proxy:
        proxy = f"http://{proxy}"
    failures = 0
    errors = ['reset by peer', 'Proxy Authentication Required', '503', '403', '502', '500', 'timed out']
    while True:
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
                failures += 0.5
            elif ("api.discord.gx.games" in e):
                failures += 0.25
            else:
                failures += 0.5
                failures = round(failures, 4)
                Logger.Sprint("ERROR",f"Thread ({idx}) ({failures}) {e}",Fore.RED)
            if failures >= 5:
                Logger.Sprint("ERROR",f"Thread ({idx}) Proxy ({proxy.split('//')[1]}) is dead!",Fore.RED)
                with open("proxies.txt", "r") as f:
                    proxies = f.read().splitlines()
                proxies.remove(proxy.split("//")[1])
                f = open("proxies.txt",'w')
                f.write("\n".join(proxies))
                f.close()
                return


async def setup(): 
    init()
    await load_proxies("proxy_sources.txt")

def main():
    with open("proxies.txt") as f:
        proxy = f.read().splitlines()
    loop = asyncio.new_event_loop()
    for i, p in enumerate(proxy):
        loop.create_task(run(i, p))
    try: 
        loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop)))
    except KeyboardInterrupt:
        Logger.Sprint("GEN","Keyboard Interrupt",Fore.LIGHTRED_EX)
        loop.close()


if __name__ == "__main__":
    asyncio.run(setup())
    main()