import os
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the bot token and application ID from environment variables
TOKEN = os.getenv("TOKEN")
APPLICATION_ID = os.getenv("BOT_CLIENT_ID")

if not TOKEN or not APPLICATION_ID:
    print("Error: TOKEN or APPLICATION_ID is not set in the .env file.")
    exit(1)

# Discord API URL for listing commands
url = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/commands"

# Headers for the API request
headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

# Fetch existing commands
response = requests.get(url, headers=headers)
if response.status_code == 200:
    commands = response.json()
    if not commands:
        print("No commands found.")
        exit(0)

    # Display the commands with numbers
    print("List of registered commands:")
    for idx, command in enumerate(commands):
        print(f"{idx + 1}. {command['name']} - {command['description']}")

    # Ask the user to select a command to delete
    try:
        choice = int(input("\nEnter the number of the command you want to delete: "))
        if 1 <= choice <= len(commands):
            command_to_delete = commands[choice - 1]
            command_id = command_to_delete["id"]
            delete_url = f"{url}/{command_id}"
            
            # Send DELETE request to remove the selected command
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code == 204:
                print(f"Successfully deleted command: {command_to_delete['name']}")
            else:
                print(f"Failed to delete command {command_to_delete['name']}: {delete_response.status_code} - {delete_response.text}")
        else:
            print("Invalid choice. Please enter a valid number.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")

else:
    print(f"Failed to fetch commands: {response.status_code} - {response.text}")
