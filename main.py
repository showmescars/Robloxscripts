import discord
from dotenv import load_dotenv
import os
import asyncio
import time
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

keys = []
user_claims = {}        # user_id: {"count": int, "cooldown_until": float}
allowed_channel = None  # channel id that bot listens to

def is_admin(message):
    return isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator

def get_user_data(user_id):
    if user_id not in user_claims:
        user_claims[user_id] = {"count": 0, "cooldown_until": 0}
    return user_claims[user_id]

# --- set ---

async def handle_set(message):
    global allowed_channel

    if not is_admin(message):
        await message.channel.send("You don't have permission to use this command.")
        return

    allowed_channel = message.channel.id

    embed = discord.Embed(
        title="Channel Set",
        description=f"This channel is now the designated key channel.\nAll bot commands will only work here.",
        color=discord.Color.green()
    )
    embed.set_footer(text="Use 'set' in any channel to move it.")
    await message.channel.send(embed=embed)

# --- stock ---

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

# --- refill ---

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

# --- key ---

async def handle_key(message):
    if message.guild is None:
        await message.channel.send("This command only works in a server.")
        return

    # admins bypass everything
    if is_admin(message):
        if not keys:
            await message.channel.send("No keys are in stock right now.")
            return

        key = keys.pop(0)

        try:
            embed = discord.Embed(
                title="Your Key",
                description=f"`{key}`",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Admin claim — unlimited.")
            await message.author.send(embed=embed)

            confirm = discord.Embed(
                title="Key Sent",
                description="Your key has been sent to your DMs.",
                color=discord.Color.green()
            )
            await message.channel.send(embed=confirm)

        except discord.Forbidden:
            keys.insert(0, key)
            await message.channel.send("I couldn't DM you. Please enable DMs from server members and try again.")
        return

    # normal user logic
    user_id = message.author.id
    data = get_user_data(user_id)
    now = time.time()

    # check cooldown
    if data["cooldown_until"] > now:
        remaining = int(data["cooldown_until"] - now)
        mins = remaining // 60
        secs = remaining % 60
        await message.channel.send(
            f"You're on cooldown. Try again in **{mins}m {secs}s**."
        )
        return

    # reset count if cooldown has passed and they were on one
    if data["cooldown_until"] != 0 and data["cooldown_until"] <= now:
        data["count"] = 0
        data["cooldown_until"] = 0

    if data["count"] >= 2:
        # shouldn't normally hit this but safety net
        data["cooldown_until"] = now + 3600
        data["count"] = 0
        remaining = 3600
        mins = remaining // 60
        await message.channel.send(
            f"You've reached your limit. Try again in **{mins}m**."
        )
        return

    if not keys:
        await message.channel.send("No keys are in stock right now. Check back later.")
        return

    key = keys.pop(0)
    data["count"] += 1

    # if they've now hit 2, start the cooldown
    if data["count"] >= 2:
        data["cooldown_until"] = now + 3600

    try:
        embed = discord.Embed(
            title="Your Key",
            description=f"`{key}`",
            color=discord.Color.dark_red()
        )
        claims_left = 2 - data["count"]
        if claims_left > 0:
            footer = f"You have {claims_left} claim(s) remaining before cooldown."
        else:
            footer = "You've used both claims. Come back in 1 hour."
        embed.set_footer(text=footer)
        await message.author.send(embed=embed)

        confirm = discord.Embed(
            title="Key Sent",
            description="Your key has been sent to your DMs.",
            color=discord.Color.green()
        )
        claims_left = 2 - data["count"]
        if claims_left > 0:
            confirm.set_footer(text=f"{claims_left} claim(s) remaining before cooldown.")
        else:
            confirm.set_footer(text="You've used both claims. Cooldown started — 1 hour.")
        await message.channel.send(embed=confirm)

    except discord.Forbidden:
        keys.insert(0, key)
        data["count"] -= 1
        if data["count"] < 2:
            data["cooldown_until"] = 0
        await message.channel.send("I couldn't DM you. Please enable DMs from server members and try again.")

# --- router ---

COMMANDS = {
    "set": handle_set,
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

    # set cmd works in any channel so admin can move it
    if content == "set":
        if is_admin(message):
            await handle_set(message)
        else:
            await message.channel.send("You don't have permission to use this command.")
        return

    # all other cmds only work in the set channel
    if allowed_channel is None:
        if is_admin(message) and content in COMMANDS:
            await message.channel.send("No channel set yet. Type `set` in the channel you want the bot to use.")
        return

    if message.channel.id != allowed_channel:
        return

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
