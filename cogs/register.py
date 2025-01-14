import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
from datetime import datetime, date
from discord import Embed
from fuzzywuzzy import process
import tempfile

def calculate_age(birthday: str) -> int:
    """Calculate the age based on the given birthday."""
    birth_date = datetime.strptime(birthday, "%Y-%m-%d").date()
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

class UserListView(View):
    def __init__(self, bot, rows, page=0, query=None):
        super().__init__(timeout=60)  # The view will time out after 60 seconds.
        self.bot = bot
        self.rows = rows
        self.page = page
        self.query = query
        self.message = None

    async def on_timeout(self):
        """Disable the buttons when the view times out."""
        for button in self.children:
            button.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def update_embed(self, interaction: Interaction):
        """Paginate the user list."""
        start = self.page * 5
        end = start + 5
        page_rows = self.rows[start:end]

        user_list = [
            f"{i + 1}. **{row[2]}** (IGN: {row[3]})\n"
            f"   - Mention: <@{row[1]}>\n"
            f"   - Gender: {row[9]}\n"
            f"   - Games: {row[7]}\n"
            f"   - UUID: {row[5]}\n"
            f"   - Rank: {row[6]}\n"
            f"   - Age: {row[8]}"
            for i, row in enumerate(page_rows)
        ]
        user_list_str = "\n\n".join(user_list)

        embed = discord.Embed(
            title="Registered Users",
            description=user_list_str if user_list else "No users found.",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Page {self.page + 1} of {len(self.rows) // 5 + (1 if len(self.rows) % 5 != 0 else 0)}")

        # Update the message with the new embed and view
        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, button: Button, interaction: Interaction):
        """Go to the previous page."""
        if self.page > 0:
            self.page -= 1
            await self.update_embed(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, button: Button, interaction: Interaction):
        """Go to the next page."""
        if (self.page + 1) * 5 < len(self.rows):
            self.page += 1
            await self.update_embed(interaction)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, button: Button, interaction: Interaction):
        """Close the view."""
        self.stop()
        if self.message:
            await self.message.delete()  # Delete the embedded message when closing
            
class FirstRegistrationModal(discord.ui.Modal, title="Step 1: Basic Information"):
    real_name = TextInput(
        label="Real Name",
        style=discord.TextStyle.short,
        placeholder="Enter your real name",
        required=True,
        max_length=100,
    )
    in_game_name = TextInput(
        label="In-Game Name",
        style=discord.TextStyle.short,
        placeholder="Enter your in-game name",
        required=True,
        max_length=100,
    )
    birthday = TextInput(
        label="Birthday (YYYY-MM-DD)",
        style=discord.TextStyle.short,
        placeholder="Enter your birthday (YYYY-MM-DD)",
        required=True,
        max_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Store the first step's data temporarily
        interaction.client.registration_data[interaction.user.id] = {
            "real_name": self.real_name.value,
            "in_game_name": self.in_game_name.value,
            "birthday": self.birthday.value,
        }

        await interaction.response.send_message(
            "Step 1 completed. Please use `/continue_register` to proceed to Step 2.",
            ephemeral=True,
        )

class SecondRegistrationModal(discord.ui.Modal, title="Step 2: Additional Information"):
    gender = TextInput(
        label="Gender",
        style=discord.TextStyle.short,
        placeholder="Enter your gender (Male, Female, Other)",
        required=True,
        max_length=50,
    )
    games_played = TextInput(
        label="Games Played",
        style=discord.TextStyle.long,
        placeholder="Enter the games you play, separated by commas",
        required=True,
        max_length=200,
    )
    uuid = TextInput(
        label="UUID",
        style=discord.TextStyle.short,
        placeholder="Enter your unique identifier (UUID)",
        required=True,
        max_length=100,
    )
    current_rank = TextInput(
        label="Rank",
        style=discord.TextStyle.short,
        placeholder="Enter your current rank (e.g., Bronze, Silver, Gold, etc.)",
        required=True,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Acknowledge the interaction to avoid timeouts
        await interaction.response.defer(ephemeral=True)

        try:
            # Retrieve stored data from step 1
            data = interaction.client.registration_data.pop(interaction.user.id, {})

            if not data:
                await interaction.followup.send("You must complete Step 1 first!", ephemeral=True)
                return

            # Add data from step 2
            data.update({
                "gender": self.gender.value,
                "games_played": self.games_played.value,
                "uuid": self.uuid.value,
                "current_rank": self.current_rank.value,
            })

            # Calculate the user's age
            data["age"] = calculate_age(data["birthday"])

            # Insert data into the database
            discord_id = interaction.user.id
            async with interaction.client.database.execute(
                """
                INSERT INTO user_registration (discord_id, real_name, in_game_name, birthday, gender, games_played, uuid, current_rank, age)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    discord_id,
                    data["real_name"],
                    data["in_game_name"],
                    datetime.strptime(data["birthday"], "%Y-%m-%d"),
                    data["gender"],
                    data["games_played"],
                    data["uuid"],
                    data["current_rank"],
                    data["age"],
                ),
            ) as cursor:
                await interaction.client.database.commit()

            # Update user's Discord nickname
            try:
                await interaction.user.edit(nick=data["in_game_name"])
            except discord.Forbidden:
                await interaction.followup.send("I don't have permission to change your nickname.", ephemeral=True)

            # Assign and remove roles
            role_to_add = interaction.guild.get_role(1313488099426308156)
            role_to_remove = interaction.guild.get_role(1314245202990596187)
            role_to_remove2 = interaction.guild.get_role(1315700246524723292)

            if role_to_add:
                await interaction.user.add_roles(role_to_add)
            if role_to_remove:
                await interaction.user.remove_roles(role_to_remove, role_to_remove2)

            # Send registration details to the log channel
            channel = interaction.guild.get_channel(1324582941883502634)
            if channel:
                embed = Embed(
                    title="New Registration Completed",
                    description=f"Registration details for {interaction.user.name}",
                    color=0x00FF00
                )
                embed.add_field(name="Discord ID", value=discord_id, inline=False)
                embed.add_field(name="Real Name", value=data["real_name"], inline=False)
                embed.add_field(name="In-Game Name", value=data["in_game_name"], inline=False)
                embed.add_field(name="Birthday", value=data["birthday"], inline=False)
                embed.add_field(name="Gender", value=data["gender"], inline=False)
                embed.add_field(name="Games Played", value=data["games_played"], inline=False)
                embed.add_field(name="UUID", value=data["uuid"], inline=False)
                embed.add_field(name="Current Rank", value=data["current_rank"], inline=False)
                embed.add_field(name="Age", value=data["age"], inline=False)

                await channel.send(embed=embed)

            # Notify the user of success
            await interaction.followup.send("Your details have been successfully updated, and your nickname has been updated to your in-game name.", ephemeral=True)

        except Exception as e:
            # Log the error and notify the user
            print(f"Error during registration: {e}")
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


class RegistrationCog(commands.Cog, name="registration"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.registration_data = {}

    # The function that gets called when a member joins the server
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Assign a role when a member joins."""
        role_to_add = member.guild.get_role(1314245202990596187)  # Role ID to add

        if role_to_add:
            if member.guild.me.guild_permissions.manage_roles:
                try:
                    await member.add_roles(role_to_add)
                    print(f"Assigned role {role_to_add.name} to {member.name}")
                except discord.DiscordException as e:
                    print(f"Failed to assign role to {member.name}: {e}")
            else:
                print(f"Bot does not have the 'Manage Roles' permission to assign roles in {member.guild.name}.")
        else:
            print(f"Role with ID 1314245202990596187 not found in {member.guild.name}.")

    @app_commands.command(name="register", description="Register your details (Step 1).")
    async def register(self, interaction: discord.Interaction):
        """Starts the first step of the registration process."""
        modal = FirstRegistrationModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="continue_register", description="Continue your registration (Step 2).")
    async def continue_register(self, interaction: discord.Interaction):
        """Starts the second step of the registration process."""
        if interaction.user.id not in self.bot.registration_data:
            await interaction.response.send_message(
                "You must complete Step 1 first using `/register`.", ephemeral=True
            )
            return

        modal = SecondRegistrationModal()
        await interaction.response.send_modal(modal)
    

    @commands.has_permissions(manage_messages=True)
    @app_commands.command(name="list_users", description="List all registered users or export all data.")
    @app_commands.describe(option="Use 'all' to export the entire database as a text file.")
    async def list_users(self, interaction: discord.Interaction, option: str = None):
        """List all registered users or export all data."""
        try:
            if option and option.lower() == "all":
                await interaction.response.send_message("Exporting all user data...", ephemeral=False)

                async with self.bot.database.execute("SELECT * FROM user_registration") as cursor:
                    rows = await cursor.fetchall()

                if not rows:
                    await interaction.followup.send("No users are registered yet.", ephemeral=True)
                    return

                # Create user data text
                user_data = []
                for row in rows:
                    discord_id = row[1]
                    user = interaction.guild.get_member(int(discord_id))
                    in_server = "Yes" if user else "No"
                    user_data.append(f"Name: {row[2]}, IGN: {row[3]}, In Server: {in_server}")

                # Use tempfile to create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as temp_file:
                    temp_file.write("\n".join(user_data))
                    temp_file_path = temp_file.name

                # Send the text file
                await interaction.followup.send(
                    content="Here is the exported list of all registered users:",
                    file=discord.File(temp_file_path, filename="user_list.txt"),
                )

            else:
                # Default behavior: List users in an embed with pagination
                await interaction.response.send_message("Loading user list...", ephemeral=False)

                async with self.bot.database.execute("SELECT * FROM user_registration") as cursor:
                    rows = await cursor.fetchall()

                if not rows:
                    await interaction.followup.send("No users are registered yet.", ephemeral=True)
                    return

                view = UserListView(bot=self.bot, rows=rows)
                view.message = await interaction.followup.send(
                    "Here is the list of registered users:", view=view
                )

                await view.update_embed(interaction)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
    
    @commands.has_permissions(manage_messages=True)
    @app_commands.command(name="indb", description="Get information about a user from the database.")
    async def indb(self, interaction: discord.Interaction, user: discord.User = None, real_name: str = None):
        """Fetch user information from the database using their Discord ID or a real name."""
        user = user or interaction.user  # Default to the interaction's user if no user is specified
        
        try:
            if real_name:
                # Search for similar names
                async with self.bot.database.execute(
                    "SELECT * FROM user_registration WHERE real_name LIKE ?",
                    (f"%{real_name}%",)
                ) as cursor:
                    rows = await cursor.fetchall()

                if not rows:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            title="No Matches Found",
                            description=f"No users found with a name similar to '{real_name}'.",
                            color=discord.Color.red(),
                        ),
                        ephemeral=True,
                    )
                    return

                # Fuzzy matching for similarity scoring
                all_real_names = [row[2] for row in rows]  # Extract real names
                matches = process.extract(real_name, all_real_names, limit=5)  # Top 5 matches

                # Create embed for matched results
                embed = discord.Embed(
                    title="Search Results",
                    description=f"Users with names similar to '{real_name}':",
                    color=discord.Color.green(),
                )

                # List similar names with age and Discord ID, mention users
                for match_name, score in matches:
                    match_row = next(row for row in rows if row[2] == match_name)
                    discord_id = match_row[1]
                    embed.add_field(
                        name=f"Match ({score}% similarity):",
                        value=(
                            f"**Name**: {match_row[2]} | **Age**: {match_row[8]} | "
                            f"**Mention**: <@{discord_id}>"
                        ),
                        inline=False,
                    )

                await interaction.response.send_message(embed=embed)
                return

            # Default to searching by Discord ID if no real name is provided
            async with self.bot.database.execute(
                "SELECT * FROM user_registration WHERE discord_id = ?",
                (user.id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="No Data Found",
                        description=f"No data found for **{user.name}#{user.discriminator}**.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
                return

            # Create embed for exact match
            embed = discord.Embed(
                title="User Information from Database",
                description=f"Information for **{user.name}#{user.discriminator}**",
                color=discord.Color.blue(),
            )
            embed.add_field(name="User ID", value=row[1])  # Discord ID
            embed.add_field(name="Real Name", value=row[2])
            embed.add_field(name="In-Game Name", value=row[3])
            embed.add_field(name="Birthday", value=row[4])
            embed.add_field(name="Gender", value=row[9])
            embed.add_field(name="Games Played", value=row[7])
            embed.add_field(name="UUID", value=row[5])
            embed.add_field(name="Rank", value=row[6])
            embed.add_field(name="Age", value=row[8])

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred: {e}",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Assign the visitor role when a user reacts to a specific message."""
        # ID of the message to monitor
        target_message_id = 1321824651357327411  # The ID of the target message

        # ID of the 'visitor' role
        visitor_role_id = 1315700246524723292  # Role ID for visitor

        # Check if the reaction is on the specific message and if it's not a bot reacting
        if payload.message_id == target_message_id and not payload.user_id == self.bot.user.id:
            # Fetch the guild (server) where the reaction occurred
            guild = self.bot.get_guild(payload.guild_id)
            if guild is None:
                return  # Skip if the bot can't find the guild

            # Get the 'visitor' role
            visitor_role = guild.get_role(visitor_role_id)

            if not visitor_role:
                print("The 'visitor' role could not be found.")
                return

            try:
                # Get the user who reacted using their user ID
                user = guild.get_member(payload.user_id)

                if user:
                    # Add the visitor role to the user who reacted
                    await user.add_roles(visitor_role)
                    print(f"Assigned the 'visitor' role to {user.name}.")
            except discord.DiscordException as e:
                print(f"An error occurred while assigning the role: {e}")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Channel to monitor
        target_channel_id = 1314245176411033620
        exempt_message_id = 1316606878880632962

        # Ensure the bot doesn't delete its own messages or system messages
        if message.author == self.bot.user or message.type != discord.MessageType.default:
            return

        # Check if the message is in the target channel
        if message.channel.id == target_channel_id:
            # Skip if the message is the exempt one
            if message.id == exempt_message_id:
                return
            
            # Allow messages starting with '/' (commands), delete the rest
            if not message.content.startswith("1111"):
                try:
                    await message.delete()
                except discord.Forbidden:
                    print("Missing permissions to delete messages.")
                except discord.HTTPException as e:
                    print(f"Failed to delete message: {e}")

async def setup(bot):
    """Setup the cog."""
    if not hasattr(bot, "database") or bot.database is None:
        print("Database connection is not initialized in the bot.")
        return
    await bot.add_cog(RegistrationCog(bot))
