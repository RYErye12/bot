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
        self.deleted_message_channel_id = 1324399249668046940  # Channel for deleted messages
        self.log_channel_id = 1324582941883502634  # Log channel ID
        self.excluded_channels = [
            1311571732405948478,
            1314246090308063293,
            1311571732405948479,
            1314244464184791070,
            1321672767124541562,
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

    async def get_audit_log_entry(self, guild, action_type):
        """Fetch the most recent audit log for a specific action type."""
        async for entry in guild.audit_logs(limit=1, action=action_type):
            return entry
        return None

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id in self.excluded_channels:
            return

        content = message.clean_content if message.clean_content else "No text"
        if not content and not message.attachments:
            content = "No content or attachments"

        deleted_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        embed = discord.Embed(
            title="Message Deleted",
            description=f"**Author:** {message.author} (`{message.author.id}`)\n"
                        f"**Channel:** {message.channel.name}\n"
                        f"**Content:** {content}\n"
                        f"**Message ID:** {message.id}\n"
                        f"**Deleted At:** {deleted_at}",
            color=discord.Color.red(),
        )

        if message.attachments:
            attachments = "\n".join([a.url for a in message.attachments])
            embed.add_field(name="Attachments", value=attachments, inline=False)

        log_channel = self.bot.get_channel(self.deleted_message_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.channel.id in self.excluded_channels:
            return

        if before.clean_content == after.clean_content:
            return

        edited_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        embed = discord.Embed(
            title="Message Edited",
            description=f"**Author:** {before.author} (`{before.author.id}`)\n"
                        f"**Channel:** {before.channel.name}\n"
                        f"**Before:** {before.clean_content if before.clean_content else 'No text'}\n"
                        f"**After:** {after.clean_content if after.clean_content else 'No text'}\n"
                        f"**Message ID:** {before.id}\n"
                        f"**Edited At:** {edited_at}",
            color=discord.Color.orange(),
        )

        log_channel = self.bot.get_channel(self.deleted_message_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

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

    # New event for role changes
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            removed_roles = [role for role in before.roles if role not in after.roles]
            added_roles = [role for role in after.roles if role not in before.roles]
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            audit_entry = await self.get_audit_log_entry(after.guild, discord.AuditLogAction.member_role_update)

            embed = discord.Embed(
                title="Role Updated",
                description=f"**User:** {after} (`{after.id}`)\n"
                            f"**Removed Roles:** {', '.join([role.name for role in removed_roles]) if removed_roles else 'None'}\n"
                            f"**Added Roles:** {', '.join([role.name for role in added_roles]) if added_roles else 'None'}\n"
                            f"**Updated At:** {timestamp}\n"
                            f"**Performed By:** {audit_entry.user if audit_entry else 'Unknown'}",
                color=discord.Color.green()
            )

            await self.log_message(embed)

    # New event for server settings changes
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.name != after.name:
            embed = discord.Embed(
                title="Server Name Changed",
                description=f"**Old Name:** {before.name}\n"
                            f"**New Name:** {after.name}\n"
                            f"**Updated At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                color=discord.Color.blue()
            )
            await self.log_message(embed)

        if before.region != after.region:
            embed = discord.Embed(
                title="Server Region Changed",
                description=f"**Old Region:** {before.region}\n"
                            f"**New Region:** {after.region}\n"
                            f"**Updated At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                color=discord.Color.purple()
            )
            await self.log_message(embed)

        if before.icon != after.icon:
            embed = discord.Embed(
                title="Server Icon Changed",
                description=f"**Old Icon:** {before.icon}\n"
                            f"**New Icon:** {after.icon}\n"
                            f"**Updated At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                color=discord.Color.orange()
            )
            await self.log_message(embed)

        if before.verification_level != after.verification_level:
            embed = discord.Embed(
                title="Server Verification Level Changed",
                description=f"**Old Verification Level:** {before.verification_level}\n"
                            f"**New Verification Level:** {after.verification_level}\n"
                            f"**Updated At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                color=discord.Color.teal()
            )
            await self.log_message(embed)

        if before.default_notifications != after.default_notifications:
            embed = discord.Embed(
                title="Server Default Notifications Changed",
                description=f"**Old Notifications Level:** {before.default_notifications}\n"
                            f"**New Notifications Level:** {after.default_notifications}\n"
                            f"**Updated At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                color=discord.Color.orange()
            )
            await self.log_message(embed)

    # New event for channel updates (like permissions, name, etc.)
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        # Log channel name changes
        if before.name != after.name:
            audit_entry = await self.get_audit_log_entry(after.guild, discord.AuditLogAction.channel_update)

            embed = discord.Embed(
                title="Channel Name Changed",
                description=f"**Old Name:** {before.name}\n"
                            f"**New Name:** {after.name}\n"
                            f"**Channel ID:** {before.id}\n"
                            f"**Updated At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                            f"**Performed By:** {audit_entry.user if audit_entry else 'Unknown'}",
                color=discord.Color.green()
            )
            await self.log_message(embed)

        # Log channel permission changes
        if before.overwrites != after.overwrites:
            audit_entry = await self.get_audit_log_entry(after.guild, discord.AuditLogAction.channel_update)

            embed = discord.Embed(
                title="Channel Permissions Changed",
                description=f"**Channel:** {after.name}\n"
                            f"**Channel ID:** {after.id}\n"
                            f"**Updated At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                            f"**Performed By:** {audit_entry.user if audit_entry else 'Unknown'}",
                color=discord.Color.yellow()
            )
            await self.log_message(embed)

    # Event for channel creation
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        audit_entry = await self.get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_create)

        embed = discord.Embed(
            title="Channel Created",
            description=f"**Channel Name:** {channel.name}\n"
                        f"**Channel ID:** {channel.id}\n"
                        f"**Type:** {channel.type}\n"
                        f"**Created At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                        f"**Performed By:** {audit_entry.user if audit_entry else 'Unknown'}",
            color=discord.Color.green()
        )
        await self.log_message(embed)

    # Event for channel deletion
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        audit_entry = await self.get_audit_log_entry(channel.guild, discord.AuditLogAction.channel_delete)

        embed = discord.Embed(
            title="Channel Deleted",
            description=f"**Channel Name:** {channel.name}\n"
                        f"**Channel ID:** {channel.id}\n"
                        f"**Type:** {channel.type}\n"
                        f"**Deleted At:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                        f"**Performed By:** {audit_entry.user if audit_entry else 'Unknown'}",
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