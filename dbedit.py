"""
Copyright © Krypton 2019-Present - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A comprehensive cog to manage user registration data in a database for a Discord bot in Python.

Version: 6.2.0
"""

from discord.ext import commands
from discord.ext.commands import Context
import discord


class DatabaseEdit(commands.Cog, name="Database Edit"):
    """
    A cog for managing user registration data in the database, such as gender, UUID, rank, and more.
    """

    def __init__(self, bot) -> None:
        self.bot = bot

    # Base hybrid command: /dbedit
    @commands.hybrid_command(
        name="dbedit",
        description="Provides information about available fields to edit.",
    )
    async def dbedit(self, context: Context) -> None:
        """
        Display the available fields that can be edited in the database.

        :param context: The command or application command context.
        """
        await context.send(
            "Available fields: `gender`, `games_played`, `uuid`, `current_rank`, `in_game_name`.",
            ephemeral=True if isinstance(context, discord.Interaction) else False,
        )

    # Reusable helper for updating database fields
    async def update_database_field(
        self,
        context: Context,
        field_name: str,
        field_value: str,
        user: discord.Member = None,
    ) -> None:
        """
        Update a specific field in the database for a given user.

        :param context: The command or application command context.
        :param field_name: The name of the field to update.
        :param field_value: The new value for the field.
        :param user: The user whose field is being updated.
        """
        user = user or (context.author if isinstance(context, Context) else context.user)
        discord_id = user.id

        try:
            query = f"UPDATE user_registration SET {field_name} = ? WHERE discord_id = ?"
            async with context.bot.database.execute(query, (field_value, discord_id)):
                await context.bot.database.commit()

            await context.send(
                f"{user.mention}'s `{field_name}` has been updated to: {field_value}.",
                ephemeral=True if isinstance(context, discord.Interaction) else False,
            )

        except Exception as e:
            await context.send(
                f"An error occurred while updating `{field_name}` for {user.mention}: {e}",
                ephemeral=True if isinstance(context, discord.Interaction) else False,
            )

    # Hybrid commands for editing each specific field
    @commands.hybrid_command(
        name="dbedit-gender",
        description="Edit a user's gender.",
    )
    @commands.has_permissions(manage_messages=True)
    async def edit_gender(self, context: Context, gender: str, user: discord.Member = None):
        await self.update_database_field(context, "gender", gender, user)

    @commands.hybrid_command(
        name="dbedit-games_played",
        description="Edit the games played by a user.",
    )
    
    async def edit_games_played(self, context: Context, games: str, user: discord.Member = None):
        await self.update_database_field(context, "games_played", games, user)
        
    @commands.has_permissions(manage_messages=True)
    @commands.hybrid_command(
        name="dbedit-uuid",
        description="Edit a user's UUID.",
    )
    @commands.has_permissions(manage_messages=True)
    async def edit_uuid(self, context: Context, uuid: str, user: discord.Member = None):
        await self.update_database_field(context, "uuid", uuid, user)

    @commands.hybrid_command(
        name="dbedit-current_rank",
        description="Edit a user's current rank.",
    )
    
    async def edit_current_rank(self, context: Context, rank: str, user: discord.Member = None):
        await self.update_database_field(context, "current_rank", rank, user)
    
    @commands.has_permissions(manage_messages=True)
    @commands.hybrid_command(
        name="dbedit-in_game_name",
        description="Edit a user's in-game name.",
    )
    
    async def edit_in_game_name(self, context: Context, in_game_name: str, user: discord.Member = None):
        await self.update_database_field(context, "in_game_name", in_game_name, user)

    # Hybrid command for deleting user data
    @commands.hybrid_command(
        name="dbdelete",
        description="Delete a user's registration data.",
    )
    @commands.has_permissions(manage_messages=True)
    async def delete_user_data(self, context: Context, user: discord.Member) -> None:
        """
        Delete a user's registration data from the database.

        :param context: The command or application command context.
        :param user: The user whose data will be deleted.
        """
        discord_id = user.id
        try:
            async with context.bot.database.execute(
                "DELETE FROM user_registration WHERE discord_id = ?", (discord_id,)
            ):
                await context.bot.database.commit()

            await context.send(
                f"All registration data for {user.mention} has been deleted.",
                ephemeral=True if isinstance(context, discord.Interaction) else False,
            )

        except Exception as e:
            await context.send(
                f"An error occurred while deleting data for {user.mention}: {e}",
                ephemeral=True if isinstance(context, discord.Interaction) else False,
            )


# Adding the cog to the bot
async def setup(bot) -> None:
    await bot.add_cog(DatabaseEdit(bot))
