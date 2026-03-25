import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib
import random

@dataclass
class RateLimitBucket:
    tokens: float
    last_update: datetime
    max_tokens: float
    refill_rate: float  # tokens per second

class ScraperNode:
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.rate_limits: Dict[str, RateLimitBucket] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.load = 0.0  # Current load metric (0-1)

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        await self.announce_to_peers()

    async def shutdown(self):
        if self.session:
            await self.session.close()

    def get_domain_bucket(self, url: str) -> str:
        domain = url.split('/')[2]
        return hashlib.md5(domain.encode()).hexdigest()

    async def acquire_token(self, bucket: str) -> bool:
        now = datetime.now()
        if bucket not in self.rate_limits:
            self.rate_limits[bucket] = RateLimitBucket(
                tokens=1.0,
                last_update=now,
                max_tokens=1.0,
                refill_rate=0.1
            )

        rl = self.rate_limits[bucket]
        elapsed = (now - rl.last_update).total_seconds()
        rl.tokens = min(rl.max_tokens, rl.tokens + elapsed * rl.refill_rate)
        rl.last_update = now

        if rl.tokens >= 1.0:
            rl.tokens -= 1.0
            return True
        return False

    async def scrape_url(self, url: str) -> dict:
        bucket = self.get_domain_bucket(url)
        
        while not await self.acquire_token(bucket):
            await asyncio.sleep(0.1)

        try:
            if not self.session:
                raise RuntimeError("Session not initialized")

            async with self.session.get(url) as response:
                self.load = min(1.0, self.load + 0.1)
                content = await response.text()
                return {
                    "url": url,
                    "status": response.status,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {"url": url, "error": str(e)}
        finally:
            self.load = max(0.0, self.load - 0.1)

    async def announce_to_peers(self):
        if not self.session:
            return
            
        status = {
            "node_id": self.node_id,
            "load": self.load,
            "rate_limits": {
                k: {"tokens": v.tokens, "max": v.max_tokens}
                for k, v in self.rate_limits.items()
            }
        }

        for peer in self.peers:
            try:
                async with self.session.post(
                    f"{peer}/announce\