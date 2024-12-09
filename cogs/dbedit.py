from discord import app_commands
from discord.ext import commands
import discord


class DatabaseEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Base command: /dbedit
    @app_commands.command(name="dbedit", description="Edit your registration data.")
    async def dbedit(self, interaction: discord.Interaction):
        """Base command for dbedit. It provides no actions but gives information about available fields."""
        await interaction.response.send_message(
            "Choose an option to edit. Available fields: `gender`, `games_played`, `uuid`, `current_rank`, `in_game_name`. ",
            ephemeral=True
        )

    # Subcommand: Edit gender
    @app_commands.command(name="gender", description="Edit your gender.")
    async def edit_gender(self, interaction: discord.Interaction, gender: str, user: discord.Member = None):
        """Edit the user's gender. Optionally specify a user to edit their gender."""
        user = user or interaction.user  # If no user is mentioned, use the current user
        discord_id = user.id
        try:
            # Update the gender in the database
            async with interaction.client.database.execute(
                "UPDATE user_registration SET gender = ? WHERE discord_id = ?",
                (gender, discord_id),
            ):
                await interaction.client.database.commit()

            await interaction.response.send_message(
                f"{user.mention}'s gender has been updated to: {gender}", ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while updating {user.mention}'s gender: {e}", ephemeral=True
            )

    # Subcommand: Edit games_played
    @app_commands.command(name="games_played", description="Edit the games you play.")
    async def edit_games_played(self, interaction: discord.Interaction, games: str, user: discord.Member = None):
        """Edit the games the user plays. Optionally specify a user to edit their games_played."""
        user = user or interaction.user  # If no user is mentioned, use the current user
        discord_id = user.id
        try:
            # Update the games_played in the database
            async with interaction.client.database.execute(
                "UPDATE user_registration SET games_played = ? WHERE discord_id = ?",
                (games, discord_id),
            ):
                await interaction.client.database.commit()

            await interaction.response.send_message(
                f"{user.mention}'s games played have been updated to: {games}", ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while updating {user.mention}'s games played: {e}", ephemeral=True
            )

    # Subcommand: Edit UUID
    @app_commands.command(name="uuid", description="Edit your UUID.")
    async def edit_uuid(self, interaction: discord.Interaction, uuid: str, user: discord.Member = None):
        """Edit the user's UUID. Optionally specify a user to edit their UUID."""
        user = user or interaction.user  # If no user is mentioned, use the current user
        discord_id = user.id
        try:
            # Update the uuid in the database
            async with interaction.client.database.execute(
                "UPDATE user_registration SET uuid = ? WHERE discord_id = ?",
                (uuid, discord_id),
            ):
                await interaction.client.database.commit()

            await interaction.response.send_message(
                f"{user.mention}'s UUID has been updated to: {uuid}", ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while updating {user.mention}'s UUID: {e}", ephemeral=True
            )

    # Subcommand: Edit current_rank
    @app_commands.command(name="current_rank", description="Edit your current rank.")
    async def edit_current_rank(self, interaction: discord.Interaction, rank: str, user: discord.Member = None):
        """Edit the user's current rank. Optionally specify a user to edit their rank."""
        user = user or interaction.user  # If no user is mentioned, use the current user
        discord_id = user.id
        try:
            # Update the current_rank in the database
            async with interaction.client.database.execute(
                "UPDATE user_registration SET current_rank = ? WHERE discord_id = ?",
                (rank, discord_id),
            ):
                await interaction.client.database.commit()

            await interaction.response.send_message(
                f"{user.mention}'s rank has been updated to: {rank}", ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while updating {user.mention}'s rank: {e}", ephemeral=True
            )

    # Subcommand: Edit in_game_name
    @app_commands.command(name="in_game_name", description="Edit your in-game name.")
    async def edit_in_game_name(self, interaction: discord.Interaction, in_game_name: str, user: discord.Member = None):
        """Edit the user's in-game name. Optionally specify a user to edit their in-game name."""
        user = user or interaction.user  # If no user is mentioned, use the current user
        discord_id = user.id
        try:
            # Update the in_game_name in the database
            async with interaction.client.database.execute(
                "UPDATE user_registration SET in_game_name = ? WHERE discord_id = ?",
                (in_game_name, discord_id),
            ):
                await interaction.client.database.commit()

            await interaction.response.send_message(
                f"{user.mention}'s in-game name has been updated to: {in_game_name}", ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while updating {user.mention}'s in-game name: {e}", ephemeral=True
            )

    # Subcommand: Delete user data
    @app_commands.command(name="dbd", description="Delete a user's registration data.")
    async def delete_data(self, interaction: discord.Interaction, user: discord.Member):
        """Delete the user's registration data from the database."""
        discord_id = user.id
        try:
            # Delete the user's data from the database
            async with interaction.client.database.execute(
                "DELETE FROM user_registration WHERE discord_id = ?",
                (discord_id,),
            ):
                await interaction.client.database.commit()

            await interaction.response.send_message(
                f"All registration data for {user.mention} has been deleted.", ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while deleting {user.mention}'s data: {e}", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(DatabaseEdit(bot))
