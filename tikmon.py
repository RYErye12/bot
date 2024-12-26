import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
import aiosqlite
from discord.ui import Button, View
import os
import datetime
import asyncio
import undetected_chromedriver as uc
from tiktok_captcha_solver import SeleniumSolver

ms_token = os.environ.get("ms_token")  # Fetch ms_token from environment variables
DATABASE = "database/database.db"  # Database path

class TikTokMonitor(commands.Cog, name="TikTokMonitor"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.monitor.start()  # Start monitoring task
        self.driver = uc.Chrome(headless=False)
        self.api_key = os.environ.get("CAPTCHA_API_KEY")  # Get CAPTCHA API key from env
        self.sadcaptcha = SeleniumSolver(self.driver, self.api_key)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tiktok_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id INTEGER,
                    tiktok_username TEXT,
                    role_id INTEGER
                )
            """)
            await db.commit()
        print("Database initialized and ready.")

    @commands.hybrid_command(name="addcontent", description="Add TikTok user for monitoring.")
    async def add_content(self, ctx: Context, user: discord.Member, tiktok_username: str, role: discord.Role) -> None:
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute("SELECT * FROM tiktok_users WHERE discord_user_id = ?", (user.id,)) as cursor:
                existing_user = await cursor.fetchone()

            if existing_user:
                await ctx.send(f"{user.name} is already being monitored.")
                return

            await db.execute("INSERT INTO tiktok_users (discord_user_id, tiktok_username, role_id) VALUES (?, ?, ?)",
                             (user.id, tiktok_username, role.id))
            await db.commit()

        await ctx.send(f"Added TikTok user `{tiktok_username}` for monitoring.")

    @commands.hybrid_command(name="removecontent", description="Remove TikTok user from monitoring.")
    async def remove_content(self, ctx: Context, user: discord.Member) -> None:
        async with aiosqlite.connect(DATABASE) as db:
            result = await db.execute("DELETE FROM tiktok_users WHERE discord_user_id = ?", (user.id,))
            await db.commit()

            if result.rowcount > 0:
                await ctx.send(f"Removed {user.name} from monitoring.")
            else:
                await ctx.send(f"{user.name} is not being monitored.")

    @tasks.loop(minutes=2)
    async def monitor(self) -> None:
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute("SELECT discord_user_id, tiktok_username, role_id FROM tiktok_users") as cursor:
                async for row in cursor:
                    discord_user_id, tiktok_username, role_id = row
                    try:
                        latest_video_url = await self.fetch_latest_tiktok_video(tiktok_username)

                        if latest_video_url:
                            video_timestamp = datetime.datetime.utcnow()
                            today = datetime.datetime.utcnow().date()

                            if video_timestamp.date() == today:
                                guild = self.bot.get_guild(1311571732405948476)
                                discord_user = guild.get_member(discord_user_id)
                                role = guild.get_role(role_id)
                                channel = guild.get_channel(1311571732405948476)

                                if channel:
                                    await channel.send(f"New TikTok post from `{tiktok_username}`: {latest_video_url}")
                    except Exception as e:
                        print(f"Error monitoring {tiktok_username}: {e}")

    async def fetch_latest_tiktok_video(self, username: str, retries: int = 10) -> str:
        attempt = 0
        while attempt < retries:
            try:
                self.driver.get(f"https://www.tiktok.com/@{username}")
                self.sadcaptcha.solve_captcha_if_present()

                video_elements = self.driver.find_elements("css selector", 'div[data-e2e="user-post-item"]')
                for video_element in video_elements:
                    try:
                        pinned_badge = video_element.find_elements("css selector", 'div[data-e2e="video-card-badge"]')
                        if pinned_badge:
                            continue  # Skip pinned videos

                        video_link = video_element.find_element("css selector", 'a')
                        video_url = video_link.get_attribute("href")
                        return video_url
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"Error fetching video: {e}. Retrying...")
                attempt += 1
                await asyncio.sleep(5)
        print("Failed to fetch video after retries.")
        return None

    def cog_unload(self):
        self.driver.quit()

async def setup(bot) -> None:
    await bot.add_cog(TikTokMonitor(bot))
