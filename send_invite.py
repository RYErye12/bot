import discord
from discord.ext import commands
from discord import app_commands

class Laro(commands.Cog, name="send_invite"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="laro",
        description="Create a game lobby with customizable options.",
    )
    async def laro(self, interaction: discord.Interaction) -> None:
        """
        Start the process of creating a game lobby by opening a modal to collect details.
        """
        # Open the modal to collect game lobby information
        game_lobby_form = GameLobbyForm()
        await interaction.response.send_modal(game_lobby_form)

        await game_lobby_form.wait()
        interaction = game_lobby_form.interaction
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Successfully Sent the Invite Link to <#1321770764839686176>",
                color=0xBEBEFE,
            )
        )

        # Send the game lobby details to a specific channel (replace with your desired channel ID)
        channel_id = 1321770764839686176
        channel = self.bot.get_channel(channel_id)

        if channel:
            # Fetch user data from the database (including UUID)
            user_data = await self.get_user_data(interaction.user.id)

            # Handle case where user data is not found
            user_uuid = user_data.get("uuid", "UUID not found") if user_data else "UUID not found"

            # Construct the embed message
            embed = discord.Embed(
                title="New Game Lobby Created",
                description=f"**Invite Link:** {game_lobby_form.link}\n"
                            f"**Required Members:** {game_lobby_form.required_members}\n"
                            f"**Game Mode:** {game_lobby_form.game_mode}\n"
                            f"**Required Rank:** {game_lobby_form.rank}\n"
                            f"**Requested By:** {interaction.user.mention} (**UUID:** {user_uuid})",  # Mention user and display UUID
                color=0x3498db,
            )

            # Mention the role
            role = interaction.guild.get_role(1313488099426308156)
            if role:
                embed.description += f"\n{role.mention}"

            await channel.send(embed=embed)

    async def get_user_data(self, discord_id: int) -> dict:
        """Fetch user data from the database using Discord ID."""
        try:
            # Query the database for user data associated with the given discord_id
            async with self.bot.database.execute(
                "SELECT uuid, real_name, in_game_name, birthday, gender, current_rank FROM user_registration WHERE discord_id = ?",
                (str(discord_id),)  # Ensure discord_id is passed as a string
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                # Return user data as a dictionary
                return {
                    "uuid": row[0],  # UUID
                    "real_name": row[1],  # Real name
                    "in_game_name": row[2],  # In-game name
                    "birthday": row[3],  # Birthday
                    "gender": row[4],  # Gender
                    "current_rank": row[5]  # Current rank
                }
            else:
                return None  # No data found for this Discord ID
        except Exception as e:
            print(f"Error fetching user data: {e}")
            return None  # Return None in case of an error

class GameLobbyForm(discord.ui.Modal, title="Game Lobby Setup"):
    link = discord.ui.TextInput(
        label="Game Link",
        style=discord.TextStyle.short,
        placeholder="Enter the game link to join",
        required=True,
        max_length=200,
    )
    required_members = discord.ui.TextInput(
        label="Required Members",
        style=discord.TextStyle.short,
        placeholder="Enter the required members",
        required=True,
        max_length=50,
    )
    game_mode = discord.ui.TextInput(
        label="Game Mode (BR or MP)",
        style=discord.TextStyle.short,
        placeholder="Enter the game mode (BR or MP)",
        required=True,
        max_length=2,
    )
    rank = discord.ui.TextInput(
        label="Required Rank (Optional)",
        style=discord.TextStyle.short,
        placeholder="Enter the required rank (Optional)",
        required=False,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """
        Handle the submitted modal data, validate the game mode, and create an embed to send to the channel.
        """
        self.interaction = interaction
        
        # Validate Game Mode
        if self.game_mode.value not in ["BR", "MP"]:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Invalid Game Mode! Please enter either 'BR' or 'MP'.",
                    color=0xFF0000,
                )
            )
            return
        
        # Stop the modal after submission
        self.stop()

        
async def setup(bot) -> None:
    await bot.add_cog(Laro(bot))
