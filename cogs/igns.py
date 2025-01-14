import sqlite3
from discord.ext import commands
from discord import app_commands, Interaction, Member, Embed

class IGNs(commands.Cog, name="igns"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="update_nicknames",
        description="Updates nicknames for all users or a mentioned user based on the database.",
    )
    async def update_nicknames(self, interaction: Interaction, member: Member = None) -> None:
        """
        Updates nicknames for all users or a mentioned user based on the database.

        :param interaction: The application command interaction.
        :param member: The mentioned Discord member to update (optional).
        """
        try:
            # Acknowledge the interaction immediately to prevent timeouts
            await interaction.response.defer()

            # Connect to the SQLite database
            conn = sqlite3.connect("database/database.db")
            cursor = conn.cursor()
        except sqlite3.Error as e:
            embed = Embed(
                description=f"❌ Failed to connect to the database: {e}",
                color=0xFF0000,
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            if member:
                # Query for the mentioned user's IGN
                cursor.execute("SELECT in_game_name FROM user_registration WHERE discord_id = ?", (str(member.id),))
                row = cursor.fetchone()

                if row:
                    in_game_name = row[0]
                    try:
                        await member.edit(nick=in_game_name)
                        embed = Embed(
                            description=f"✅ Updated nickname for {member.mention} to `{in_game_name}`.",
                            color=0x00FF00,
                        )
                        await interaction.followup.send(embed=embed)
                    except Exception as e:
                        embed = Embed(
                            description=f"❌ Failed to update nickname for {member.mention}: {e}",
                            color=0xFF0000,
                        )
                        await interaction.followup.send(embed=embed)
                else:
                    embed = Embed(
                        description=f"❌ No record found for {member.mention} in the database.",
                        color=0xFF0000,
                    )
                    await interaction.followup.send(embed=embed)
            else:
                # Query for all users with an IGN
                cursor.execute("SELECT discord_id, in_game_name FROM user_registration WHERE in_game_name IS NOT NULL")
                rows = cursor.fetchall()

                if not rows:
                    embed = Embed(
                        description="❌ No users with IGN found in the database.",
                        color=0xFF0000,
                    )
                    await interaction.followup.send(embed=embed)
                    return

                successes, failures = 0, 0
                failed_updates = []

                for discord_id, in_game_name in rows:
                    member = interaction.guild.get_member(int(discord_id))
                    if member:
                        try:
                            await member.edit(nick=in_game_name)
                            successes += 1
                        except Exception as e:
                            failures += 1
                            failed_updates.append(f"{member.mention} ({e})")
                    else:
                        failures += 1
                        failed_updates.append(f"User ID {discord_id} (not found in the guild)")

                # Create an embed with a summary of the updates
                embed = Embed(
                    title="Nickname Update Summary",
                    description=f"✅ Successfully updated {successes} nickname(s).\n❌ Failed to update {failures} nickname(s).",
                    color=0x3498db,
                )
                if failed_updates:
                    embed.add_field(
                        name="Failed Updates",
                        value="\n".join(failed_updates),
                        inline=False,
                    )
                await interaction.followup.send(embed=embed)
        except sqlite3.Error as e:
            embed = Embed(
                description=f"❌ Database query error: {e}",
                color=0xFF0000,
            )
            await interaction.followup.send(embed=embed)
        finally:
            conn.close()

async def setup(bot) -> None:
    await bot.add_cog(IGNs(bot))
