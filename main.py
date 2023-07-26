import aiohttp, asyncio
    
class GroupFinder:
    def __init__(self, start_at=10000, webhook=None, wait_time=0, threads=1, display_ownerless=False):
        self.current = start_at
        self.webhook = {"enabled": True if webhook else False, "url": webhook}
        self.wait_time = wait_time
        self.threads = threads
        self.display_ownerless = display_ownerless
    
    async def send_webhook(self, group_id, session):
        while True:
            async with session.post(self.webhook["url"], json={"content": f"group {group_id} is ownerless and not locked"}) as response:
                if response.status == 429: print("ratelimit"); continue
                return
    
    async def search(self, session):
        while True:
         try:
            generated_ids = []
            for i in range(100):
                generated_ids.append(self.current)
                self.current += 1
                
            async with session.get(f"https://groups.roblox.com/v2/groups?groupIds={','.join(map(str, generated_ids))}") as response:
                if response.status != 200: 
                    print(f"unexpected status code: {response.status}")
                    self.current -= 100
                    continue
                try:
                    groups = (await response.json())["data"]
                    for group in groups:
                        if not group.get("owner", True):
                            while True:
                                async with session.get(f"https://groups.roblox.com/v1/groups/{group.get('id')}") as response:
                                    if response.status == 429: print("ratelimit"); continue
                                    if response.status != 200: print(f"unexpected status code: {response.status}"); break
                                    group = await response.json()
                                    if not group.get("publicEntryAllowed"): 
                                        if self.display_ownerless: 
                                            print(f"group {group.get('id')} is ownerless but locked")
                                        break
                                    print(f"group {group.get('id')} is ownerless and not locked")
                                    if self.webhook["enabled"]:
                                        await self.send_webhook(group.get('id'), session)
                                    break
                except Exception as e:
                    print(f"unexpected error: {e}")
                    
         except Exception as e:
             print(e, " error")
         finally:
            await asyncio.sleep(self.wait_time)
                
  
    async def run(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.search(session) for i in range(self.threads)]
            await asyncio.gather(*tasks)

asyncio.run(GroupFinder(threads=1, display_ownerless=True).run())