import discord
from dotenv import load_dotenv
import os
import time
import random
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

keys = []
used_keys = set()
user_claims = {}
claim_log = []
allowed_channel = None

def is_admin(message):
    return isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator

def get_user_data(user_id):
    if user_id not in user_claims:
        user_claims[user_id] = {"count": 0, "cooldown_until": 0}
    return user_claims[user_id]

def format_time(ts):
    import datetime
    return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')

# --- set ---

async def handle_set(message):
    global allowed_channel
    allowed_channel = message.channel.id

    embed = discord.Embed(
        title="Channel Set",
        description="This channel is now the designated key channel.\nAll bot commands will only work here.",
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
    raw_keys = [line.strip() for line in lines if line.strip()]

    added = []
    skipped = 0
    for k in raw_keys:
        if k in used_keys:
            skipped += 1
        else:
            added.append(k)
            used_keys.add(k)

    keys.clear()
    keys.extend(added)

    embed = discord.Embed(
        title="Stock Loaded",
        color=discord.Color.green()
    )
    embed.description = (
        f"**{len(added)}** new keys loaded.\n"
        f"**{skipped}** duplicate skipped.\n"
        f"Previous stock replaced with new unique keys only."
    )
    embed.set_footer(text="Use 'refill' to add more keys on top.")
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
    raw_keys = [line.strip() for line in lines if line.strip()]

    added = []
    skipped = 0
    for k in raw_keys:
        if k in used_keys:
            skipped += 1
        else:
            added.append(k)
            used_keys.add(k)
            keys.append(k)

    embed = discord.Embed(
        title="Stock Refilled",
        color=discord.Color.blurple()
    )
    embed.description = (
        f"**{len(added)}** new keys added.\n"
        f"**{skipped}** duplicate skipped.\n"
        f"**{len(keys)}** total keys now in stock."
    )
    embed.set_footer(text="Use 'stock' to replace all stock with a new file.")
    await message.channel.send(embed=embed)

# --- key ---

async def handle_key(message):
    if message.guild is None:
        await message.channel.send("This command only works in a server.")
        return

    if is_admin(message):
        if not keys:
            await message.channel.send("No keys are in stock right now.")
            return

        key = random.choice(keys)
        keys.remove(key)

        claim_log.append({
            "display_name": message.author.display_name,
            "user_id": message.author.id,
            "key": key,
            "timestamp": time.time(),
            "admin": True,
        })

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
            keys.append(key)
            claim_log.pop()
            await message.channel.send("I couldn't DM you. Please enable DMs from server members and try again.")
        return

    user_id = message.author.id
    data = get_user_data(user_id)
    now = time.time()

    if data["cooldown_until"] > now:
        remaining = int(data["cooldown_until"] - now)
        mins = remaining // 60
        secs = remaining % 60
        await message.channel.send(
            f"You're on cooldown. Try again in **{mins}m {secs}s**."
        )
        return

    if data["cooldown_until"] != 0 and data["cooldown_until"] <= now:
        data["count"] = 0
        data["cooldown_until"] = 0

    if data["count"] >= 3:
        data["cooldown_until"] = now + 3600
        data["count"] = 0
        await message.channel.send("You've reached your limit. Try again in **60m**.")
        return

    if not keys:
        await message.channel.send("No keys are in stock right now. Check back later.")
        return

    key = random.choice(keys)
    keys.remove(key)
    data["count"] += 1

    if data["count"] >= 3:
        data["cooldown_until"] = now + 3600

    claim_log.append({
        "display_name": message.author.display_name,
        "user_id": message.author.id,
        "key": key,
        "timestamp": time.time(),
        "admin": False,
    })

    try:
        embed = discord.Embed(
            title="Your Key",
            description=f"`{key}`",
            color=discord.Color.dark_red()
        )
        claims_left = 3 - data["count"]
        if claims_left > 0:
            footer = f"You have {claims_left} claim remaining before cooldown."
        else:
            footer = "You've used all 3 claims. Come back in 1 hour."
        embed.set_footer(text=footer)
        await message.author.send(embed=embed)

        confirm = discord.Embed(
            title="Key Sent",
            description="Your key has been sent to your DMs.",
            color=discord.Color.green()
        )
        claims_left = 3 - data["count"]
        if claims_left > 0:
            confirm.set_footer(text=f"{claims_left} claim remaining before cooldown.")
        else:
            confirm.set_footer(text="You've used all 3 claims. Cooldown started — 1 hour.")
        await message.channel.send(embed=confirm)

    except discord.Forbidden:
        keys.append(key)
        claim_log.pop()
        data["count"] -= 1
        if data["count"] < 3:
            data["cooldown_until"] = 0
        await message.channel.send("I couldn't DM you. Please enable DMs from server members and try again.")

# --- log ---

async def handle_log(message):
    if not is_admin(message):
        await message.channel.send("You don't have permission to use this command.")
        return

    if not claim_log:
        await message.channel.send("No keys have been claimed yet.")
        return

    entries_per_page = 10
    pages = [claim_log[i:i+entries_per_page] for i in range(0, len(claim_log), entries_per_page)]

    for idx, page in enumerate(pages):
        lines = []
        for entry in page:
            admin_tag = " *(admin)*" if entry.get("admin") else ""
            lines.append(
                f"**{entry['display_name']}**{admin_tag}\n"
                f"ID: `{entry['user_id']}`\n"
                f"Key: `{entry['key']}`\n"
                f"Time: {format_time(entry['timestamp'])}\n"
            )

        embed = discord.Embed(
            title=f"Key Claim Log ({idx + 1}/{len(pages)})",
            description="\n".join(lines),
            color=discord.Color.dark_gold()
        )
        embed.set_footer(text=f"Total claims: {len(claim_log)} | Keys remaining: {len(keys)}")
        await message.channel.send(embed=embed)

# --- see ---

async def handle_see(message):
    if not is_admin(message):
        await message.channel.send("You don't have permission to use this command.")
        return

    if not keys:
        await message.channel.send("There are no keys in stock right now.")
        return

    try:
        entries_per_page = 20
        pages = [keys[i:i+entries_per_page] for i in range(0, len(keys), entries_per_page)]

        for idx, page in enumerate(pages):
            lines = "\n".join(f"`{k}`" for k in page)

            embed = discord.Embed(
                title=f"Keys In Stock ({idx + 1}/{len(pages)})",
                description=lines,
                color=discord.Color.dark_teal()
            )
            embed.set_footer(text=f"Total keys remaining: {len(keys)}")
            await message.author.send(embed=embed)

        confirm = discord.Embed(
            title="Stock List Sent",
            description=f"All **{len(keys)}** keys in stock have been sent to your DMs.",
            color=discord.Color.green()
        )
        await message.channel.send(embed=confirm)

    except discord.Forbidden:
        await message.channel.send("I couldn't DM you. Please enable DMs from server members and try again.")

# --- router ---

COMMANDS = {
    "set": handle_set,
    "stock": handle_stock,
    "refill": handle_refill,
    "key": handle_key,
    "log": handle_log,
    "see": handle_see,
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

    if content not in COMMANDS:
        return

    if content == "set":
        if is_admin(message):
            await handle_set(message)
        else:
            await message.channel.send("You don't have permission to use this command.")
        return

    if allowed_channel is None:
        if is_admin(message):
            await message.channel.send("No channel set yet. Type `set` in the channel you want the bot to use.")
        return

    if is_admin(message):
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
        return

    if message.channel.id != allowed_channel:
        return

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
