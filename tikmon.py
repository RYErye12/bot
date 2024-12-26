import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
import aiosqlite
from discord.ui import Button, View
import os
import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_sync  # Import stealth
import asyncio

ms_token = os.environ.get("ms_token")  # Fetches the ms_token from your environment variable

# Path to the database file
DATABASE = "database/database.db"  # Update the path to your database

class TikTokMonitor(commands.Cog, name="TikTokMonitor"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.monitor.start()  # Start monitoring task

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Ensures the database and table exist when the bot is ready.
        """
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

    @commands.hybrid_command(
        name="addcontent",
        description="Adds a TikTok user for monitoring.",
    )
    async def add_content(self, ctx: Context, user: discord.Member, tiktok_username: str, role: discord.Role) -> None:
        """
        Command to add a TikTok user for monitoring.

        :param ctx: The context of the command
        :param user: The Discord user to associate
        :param tiktok_username: TikTok username to monitor
        :param role: Role to assign to the Discord user
        """
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute(""" 
                SELECT * FROM tiktok_users WHERE discord_user_id = ? 
            """, (user.id,)) as cursor:
                existing_user = await cursor.fetchone()

            if existing_user:
                await ctx.send(f"{user.name} is already being monitored.")
                return

            await db.execute(""" 
                INSERT INTO tiktok_users (discord_user_id, tiktok_username, role_id)
                VALUES (?, ?, ?)
            """, (user.id, tiktok_username, role.id))
            await db.commit()

        await ctx.send(f"Added TikTok user `{tiktok_username}` for monitoring. Associated role: `{role.name}`.")

    @commands.hybrid_command(
        name="removecontent",
        description="Removes a TikTok user from the monitoring list.",
    )
    async def remove_content(self, ctx: Context, user: discord.Member) -> None:
        """
        Command to remove a TikTok user from monitoring.

        :param ctx: The context of the command
        :param user: The Discord user to remove
        """
        async with aiosqlite.connect(DATABASE) as db:
            result = await db.execute(""" 
                DELETE FROM tiktok_users WHERE discord_user_id = ? 
            """, (user.id,))
            await db.commit()

            if result.rowcount > 0:
                await ctx.send(f"Removed {user.name} from monitoring.")
            else:
                await ctx.send(f"{user.name} is not being monitored.")

    @commands.hybrid_command(
        name="listcon",
        description="Lists all TikTok users being monitored.",
    )
    async def list_content(self, ctx: Context) -> None:
        """
        Lists all TikTok users in the database with interactive buttons.

        :param ctx: The context of the command
        """
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute(""" 
                SELECT discord_user_id, tiktok_username, role_id FROM tiktok_users
            """) as cursor:
                users = await cursor.fetchall()

        if not users:
            await ctx.send("No TikTok users are being monitored currently.")
            return

        user_list = "\n".join([f"{tiktok_username} (ID: {discord_user_id})" for discord_user_id, tiktok_username, _ in users])

        view = View()
        for discord_user_id, tiktok_username, _ in users:
            user_button = Button(label=f"Remove {tiktok_username}", custom_id=f"remove_{discord_user_id}")
            user_button.callback = self.create_remove_button_callback(discord_user_id, tiktok_username)
            view.add_item(user_button)

        await ctx.send(f"List of monitored TikTok users:\n{user_list}", view=view)

    def create_remove_button_callback(self, discord_user_id: int, tiktok_username: str):
        async def remove_user_button_callback(interaction: discord.Interaction):
            async with aiosqlite.connect(DATABASE) as db:
                await db.execute(""" 
                    DELETE FROM tiktok_users WHERE discord_user_id = ? 
                """, (discord_user_id,))
                await db.commit()

            await interaction.response.send_message(f"Removed {tiktok_username} from monitoring.", ephemeral=True)

        return remove_user_button_callback

    @tasks.loop(minutes=2)
    async def monitor(self) -> None:
        """
        Periodically checks for new TikTok posts and updates the Discord channel.
        """
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute("SELECT discord_user_id, tiktok_username, role_id FROM tiktok_users") as cursor:
                async for row in cursor:
                    discord_user_id, tiktok_username, role_id = row
                    try:
                        # Fetch TikTok user feed using Playwright with Stealth
                        latest_video_url = await self.fetch_latest_tiktok_video(tiktok_username)

                        if latest_video_url:
                            # Check if the video was posted today
                            video_timestamp = datetime.datetime.utcnow()
                            today = datetime.datetime.utcnow().date()

                            if video_timestamp.date() == today:
                                # Video was posted today, send it to Discord channel
                                guild = self.bot.get_guild(1311571732405948476)  # Replace with your guild ID
                                discord_user = guild.get_member(discord_user_id)
                                role = guild.get_role(role_id)

                                channel = guild.get_channel(1321368906027237376)  # Replace with your channel ID
                                if channel:
                                    await channel.send(
                                        f"New TikTok post from `{tiktok_username}`: {latest_video_url}\n"
                                        f"Role `{role.name}` has been notified!"
                                    )
                    except Exception as e:
                        print(f"Error monitoring {tiktok_username}: {e}")

    async def fetch_latest_tiktok_video(self, username: str, retries: int = 10) -> str:
        """
        Fetch the latest TikTok video from a given username using Playwright with Stealth mode.
        Implements retry logic in case of a timeout or CAPTCHA.
        
        :param username: The TikTok username to fetch the video from.
        :param retries: The number of retry attempts in case of failure.
        :return: The URL of the latest TikTok video or None if not found.
        """
        async with async_playwright() as p:
            # Retry logic for timeout and CAPTCHA-related issues
            attempt = 0
            while attempt < retries:
                browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
                page = await browser.new_page()

                # Apply stealth mode to avoid detection
                stealth_sync(page)  # Awaiting the stealth_sync function if it's a coroutine

                try:
                    # Navigate to the TikTok user profile
                    await page.goto(f"https://www.tiktok.com/@{username}", wait_until="domcontentloaded")
                    # Wait for the user-post-item section to be loaded (increased timeout to 60 seconds)
                    await page.wait_for_selector('div[data-e2e="user-post-item"]', timeout=800)
                    # Try extracting the first video URL
                    video_url = await page.eval_on_selector('div[data-e2e="user-post-item"] a', 
                                                            'el => el.href')
                    await browser.close()
                    return video_url
                except Exception as e:
                    # Check if it's a timeout or CAPTCHA error
                    if 'Timeout' in str(e):
                        print(f"Error waiting for selector: {e}. Retrying...")
                        attempt += 1
                        await asyncio.sleep(5)  # Wait before retrying
                    else:
                        print(f"Unexpected error: {e}")
                        await browser.close()
                        return None

            # If retries are exhausted, return None
            print(f"Failed to fetch video after {retries} attempts.")
            return None

# And then we finally add the cog to the bot so that it can load, unload, reload and use its content.
async def setup(bot) -> None:
    await bot.add_cog(TikTokMonitor(bot))
