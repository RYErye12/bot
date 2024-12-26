import discord
from discord.ext import commands
import logging
from datetime import datetime

class DiscordLogHandler(logging.Handler):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def emit(self, record):
        try:
            log_message = self.format(record)
            # Send the log message as an embed to the Discord channel
            embed = discord.Embed(
                title="Bot Log",
                description=log_message,
                color=discord.Color.blue()
            )
            await self.channel.send(embed=embed)
        except Exception as e:
            print(f"Error while sending log to Discord: {e}")  # Debug: Catch errors in the handler

class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1314244464184791070  # Log channel ID
        self.excluded_channels = [
            1311571732405948478,
            1314246090308063293,
            1311571732405948479,
            1321672767124541562
        ]

    async def on_ready(self):
        """Wait for the bot to be fully ready before setting up logging."""
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            discord_handler = DiscordLogHandler(log_channel)
            discord_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(discord_handler)
            logging.getLogger().setLevel(logging.INFO)
            # Optionally, log that the logging setup is complete
            await self.log_message("Logging setup complete.")
        else:
            print("Log channel not found")  # Debug: Channel not found

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id in self.excluded_channels:
            return
        
        # Use clean_content to sanitize mentions and other special content
        content = message.clean_content if message.clean_content else 'No text'
        if not content and not message.attachments:
            content = 'No content or attachments'

        # Get the current timestamp for when the deletion occurred
        deleted_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        embed = discord.Embed(
            title="Message Deleted",
            description=f"**Author:** {message.author} (`{message.author.id}`)\n"
                        f"**Channel:** {message.channel.name}\n"
                        f"**Content:** {content}\n"
                        f"**Message ID:** {message.id}\n"
                        f"**Deleted At:** {deleted_at}",
            color=discord.Color.red()
        )

        # Handle attachments if present
        if message.attachments:
            attachments = "\n".join([a.url for a in message.attachments])
            embed.add_field(name="Attachments", value=attachments, inline=False)

        await self.log_message(embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.channel.id in self.excluded_channels:
            return
        
        # Skip if there is no actual change in content or attachments
        if before.clean_content == after.clean_content:
            return
        
        # Get the current timestamp for when the edit occurred
        edited_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        embed = discord.Embed(
            title="Message Edited",
            description=f"**Author:** {before.author} (`{before.author.id}`)\n"
                        f"**Channel:** {before.channel.name}\n"
                        f"**Before:** {before.clean_content if before.clean_content else 'No text'}\n"
                        f"**After:** {after.clean_content if after.clean_content else 'No text'}\n"
                        f"**Message ID:** {before.id}\n"
                        f"**Edited At:** {edited_at}",
            color=discord.Color.orange()
        )

        await self.log_message(embed)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Log the command usage
        # Get the current timestamp for when the command was executed
        command_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        embed = discord.Embed(
            title="Command Used",
            description=f"**User:** {ctx.author} (`{ctx.author.id}`)\n"
                        f"**Command:** `{ctx.command}`\n"
                        f"**Arguments:** {', '.join([str(arg) for arg in ctx.args]) if ctx.args else 'None'}\n"
                        f"**Channel:** {ctx.channel.name}\n"
                        f"**Executed At:** {command_time}",
            color=discord.Color.blue()
        )

        await self.log_message(embed)

    @commands.Cog.listener()
    async def on_error(self, error):
        # Log any uncaught errors
        error_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        embed = discord.Embed(
            title="Bot Error",
            description=f"**Error Time:** {error_time}\n"
                        f"**Error Message:** {str(error)}",
            color=discord.Color.red()
        )

        await self.log_message(embed)

    async def log_message(self, embed):
        # Send the log message embed to the log channel
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print("Failed to send log to channel")  # Debug: Handle case when channel is not found

async def setup(bot):
    await bot.add_cog(MessageLogger(bot))
