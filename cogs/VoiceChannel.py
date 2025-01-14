"""
Description:
🐍 A cog that monitors a voice channel, creates a new VC, assigns a role to manage it, moves the user to the new VC, and cleans up when the user leaves.

Version: 6.2.1
"""

from discord.ext import commands
import discord

class VoiceChannelManager(commands.Cog, name="voice_channel_manager"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.watched_channel_id = 1321363056537763880  # Replace with the ID of the channel to monitor
        self.category_id = 1311571732405948485  # Replace with the ID of the category for new channels
        self.active_channels = {}  # Track active voice channels and their associated roles
        self.additional_roles = [1313488099426308156, 1315700246524723292]  # Roles allowed to view and connect

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """
        Listens for voice state updates to create a new VC, assign a role, move the user, and clean up when the user leaves.

        :param member: The member whose voice state has updated.
        :param before: The member's previous voice state.
        :param after: The member's new voice state.
        """
        guild = member.guild

        # Check if the member joined the monitored voice channel
        if after.channel and after.channel.id == self.watched_channel_id:
            category = discord.utils.get(guild.categories, id=self.category_id)

            if not category:
                print(f"Category with ID {self.category_id} not found.")
                return

            # Create a new voice channel named after the member
            channel_name = f"{member.display_name}'s VC"
            new_vc = await category.create_voice_channel(channel_name)

            # Create a role for the member with manage permissions
            role_name = f"{member.display_name}'s VC Manager"
            vc_role = await guild.create_role(
                name=role_name,
                color=discord.Color.blue(),
                permissions=discord.Permissions(permissions=0)
            )

            # Assign the role to the member
            await member.add_roles(vc_role)

            # Set permissions for the voice channel
            overwrite = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),  # Deny everyone by default
                vc_role: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    manage_channels=True,
                    manage_permissions=True
                )
            }

            # Add permissions for the additional roles
            for role_id in self.additional_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrite[role] = discord.PermissionOverwrite(view_channel=True, connect=True)

            await new_vc.edit(overwrites=overwrite)

            # Track the new VC and role in the active channels
            self.active_channels[new_vc.id] = {"role": vc_role, "creator": member}

            # Move the member to the new voice channel
            await member.move_to(new_vc)

            print(f"Created VC '{channel_name}', assigned role '{role_name}', and moved {member.display_name} to the channel.")

        # Check if the member left any voice channel
        if before.channel and before.channel.id in self.active_channels:
            vc_data = self.active_channels[before.channel.id]

            # Cleanup: Only delete if the VC is empty and the user is the creator
            if len(before.channel.members) == 0:
                await before.channel.delete()
                await vc_data["role"].delete()
                del self.active_channels[before.channel.id]
                print(f"Deleted VC '{before.channel.name}' and role '{vc_data['role'].name}'.")

async def setup(bot) -> None:
    await bot.add_cog(VoiceChannelManager(bot))
