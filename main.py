import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

keys = []
claimed_users = set()

def is_admin(message):
    return isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator

async def handle_stock(message):
    if not is_admin(message):
        await message.channel.send("You don't have permission to use this command.")
        return

    if not message.attachments:
        await message.channel.send("Please attach a `.txt` file with one key per line.")
        return

    attachment = message.attachments[0]

    if not attachment.filename.endswith('.txt'):
        await message.channel.send("Only `.txt` files are accepted.")
        return

    content = await attachment.read()
    lines = content.decode('utf-8').splitlines()
    new_keys = [line.strip() for line in lines if line.strip()]

    if not new_keys:
        await message.channel.send("The file was empty or had no valid keys.")
        return

    keys.clear()
    keys.extend(new_keys)

    embed = discord.Embed(
        title="Stock Loaded",
        description=f"**{len(keys)}** keys loaded successfully.\nPrevious stock was replaced.",
        color=discord.Color.green()
    )
    embed.set_footer(text="Use 'refill' to add more keys on top of existing stock.")
    await message.channel.send(embed=embed)

async def handle_refill(message):
    if not is_admin(message):
        await message.channel.send("You don't have permission to use this command.")
        return

    if not message.attachments:
        await message.channel.send("Please attach a `.txt` file with one key per line.")
        return

    attachment = message.attachments[0]

    if not attachment.filename.endswith('.txt'):
        await message.channel.send("Only `.txt` files are accepted.")
        return

    content = await attachment.read()
    lines = content.decode('utf-8').splitlines()
    new_keys = [line.strip() for line in lines if line.strip()]

    if not new_keys:
        await message.channel.send("The file was empty or had no valid keys.")
        return

    keys.extend(new_keys)

    embed = discord.Embed(
        title="Stock Refilled",
        description=f"**{len(new_keys)}** keys added.\n**{len(keys)}** total keys now in stock.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Use 'stock' to replace all stock with a new file.")
    await message.channel.send(embed=embed)

async def handle_key(message):
    if message.guild is None:
        await message.channel.send("This command only works in a server.")
        return

    if message.author.id in claimed_users:
        await message.channel.send("You have already claimed a key.")
        return

    if not keys:
        await message.channel.send("No keys are in stock right now. Check back later.")
        return

    key = keys.pop(0)
    claimed_users.add(message.author.id)

    try:
        embed = discord.Embed(
            title="Your Key",
            description=f"`{key}`",
            color=discord.Color.dark_red()
        )
        embed.set_footer(text="Keep this safe. You can only claim once.")
        await message.author.send(embed=embed)

        confirm = discord.Embed(
            title="Key Sent",
            description="Your key has been sent to your DMs.",
            color=discord.Color.green()
        )
        await message.channel.send(embed=confirm)

    except discord.Forbidden:
        keys.insert(0, key)
        claimed_users.discard(message.author.id)
        await message.channel.send("I couldn't DM you. Please enable DMs from server members and try again.")

COMMANDS = {
    "stock": handle_stock,
    "refill": handle_refill,
    "key": handle_key,
}

@bot.event
async def on_ready():
    print(f'{bot.user} is online and ready.')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild is None:
        return

    content = message.content.strip().lower()

    if content in COMMANDS:
        try:
            await COMMANDS[content](message)
        except discord.HTTPException as e:
            print(f"HTTP error: {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                await message.channel.send("An error occurred. Check the logs.")
            except:
                pass

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not found in .env")
    else:
        keep_alive()
        bot.run(TOKEN)
