import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import os
import asyncio
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)

covens = {}
active_coven_owners = set()

VAMPIRE_NAMES = [
    "Malachar", "Seraphine", "Voss", "Isolde", "Daemon", "Lucretia", "Mordecai",
    "Thessaly", "Cain", "Vesper", "Dracul", "Noctis", "Selene", "Valdris",
    "Morvaine", "Calyx", "Sable", "Renwick", "Elspeth", "Corvus",
    "Theron", "Lyris", "Azrael", "Circe", "Balthazar", "Nyx", "Silas",
    "Araminta", "Voryn", "Caelia", "Rook", "Zephyrine", "Vanthos",
    "Morrigan", "Aldric", "Syrenne", "Dusk", "Kael", "Ivara", "Bruthen",
    "Solenne", "Wraith", "Casimir", "Lilith", "Fenris", "Atrox", "Nyxara",
    "Gideon", "Ravenna", "Cullen", "Shade", "Eryndor", "Celeste", "Damon",
    "Ashcroft", "Lestat", "Mirela", "Dravon", "Sorcha", "Kiran", "Evaine",
    "Rhydian", "Cressida", "Draeven", "Lucius", "Zara", "Caspian", "Varek",
    "Sirene", "Draven", "Moira", "Aldren", "Virel", "Saoirse", "Corvain",
    "Tessaly", "Noctara", "Vira", "Alucard", "Seraph", "Malvyn", "Orynn",
    "Caedmon", "Vesra", "Darkmore", "Isolara", "Maren", "Vortan", "Sylvara",
    "Drex", "Cassia", "Helion", "Nara", "Volthar", "Serevyn", "Ombra",
    "Revan", "Xeryn", "Cyrus", "Valdra", "Neron", "Elara", "Sorin",
    "Amara", "Bastian", "Rowan", "Alara", "Corvyn", "Mireille", "Aldara",
    "Sylvix", "Erebus", "Calix", "Thessian", "Vorn", "Sariel", "Drevan",
    "Orion", "Caera", "Malthus", "Revna", "Daxon", "Solara", "Coren",
    "Vayne", "Elyra", "Phaedra", "Obsidian", "Grimoire", "Sever", "Ixon",
    "Bellatrix", "Craven", "Morven", "Thessiane", "Dorian",
    "Evander", "Lysander", "Callyx", "Severin", "Malachy",
]

COVEN_NAMES = [
    {"name": "Order of the Crimson Veil", "domain": "the Haunted Moors"},
    {"name": "House Noctis", "domain": "the Obsidian Citadel"},
    {"name": "The Dusk Covenant", "domain": "Ashenvale Forest"},
    {"name": "Bloodline of Mordrath", "domain": "the Sunken Cathedral"},
    {"name": "The Pale Court", "domain": "Castle Vethara"},
    {"name": "Coven of the Black Rose", "domain": "the Shattered Peaks"},
    {"name": "The Eternal Conclave", "domain": "Ravenmoor City"},
    {"name": "Sanctum of the Hollow Moon", "domain": "the Blighted Marshes"},
    {"name": "House Valdris", "domain": "the Iron Crypt"},
    {"name": "The Sable Throne", "domain": "Nightfall Keep"},
    {"name": "Circle of the Red Dawn", "domain": "the Ember Wastes"},
    {"name": "The Veil Sworn", "domain": "Duskwall Manor"},
    {"name": "House of Ashen Blood", "domain": "the Forgotten Tombs"},
    {"name": "The Night Conclave", "domain": "Mirewood"},
    {"name": "Order of the Undying Flame", "domain": "the Charred Spire"},
    {"name": "The Wraith Court", "domain": "Coldfen Hollow"},
    {"name": "Bloodpact of Serath", "domain": "the Ancient Ruins"},
    {"name": "House Corvain", "domain": "Blackwater Isle"},
    {"name": "The Thornbound", "domain": "Grimhallow Village"},
    {"name": "Covenant of Eternal Night", "domain": "the Shadow Reaches"},
]

POWER_TIERS = [
    (1, 25, "Fledgling"),
    (26, 50, "Turned"),
    (51, 75, "Ancient"),
    (76, 100, "Elder"),
]

def get_power_tier(power):
    for low, high, label in POWER_TIERS:
        if low <= power <= high:
            return label
    return "Unknown"

def is_admin(message):
    return isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator

def user_has_active_coven(user_id):
    return any(c['owner_id'] == user_id and c['alive'] for c in covens.values())

def generate_code():
    while True:
        code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
        if code not in covens:
            return code

def make_member(name):
    power = random.randint(1, 100)
    return {
        "name": name,
        "alive": True,
        "power": power,
        "kills": 0,
        "deaths": 0,
        "times_imprisoned": 0,
        "missions_survived": 0,
        "imprisoned_until": None,
        "imprisonment_sentence": None,
    }

def generate_vampires(count=5):
    names = random.sample(VAMPIRE_NAMES, min(count, len(VAMPIRE_NAMES)))
    return [make_member(n) for n in names]

def get_alive_members(coven):
    return [m for m in coven['members'] if m['alive']]

def get_elder(coven):
    alive = get_alive_members(coven)
    if not alive:
        return None
    return max(alive, key=lambda m: m['power'])

def update_elder(coven):
    top = get_elder(coven)
    if top:
        coven['elder'] = top['name']

async def safe_send(channel, embed=None, content=None):
    try:
        if embed:
            await channel.send(embed=embed)
        elif content:
            if len(content) > 2000:
                chunks = [content[i:i+1990] for i in range(0, len(content), 1990)]
                for chunk in chunks:
                    await channel.send(chunk)
                    await asyncio.sleep(0.5)
            else:
                await channel.send(content)
    except discord.HTTPException as e:
        print(f"safe_send error: {e}")

async def handle_coven(message, args):
    user_id = message.author.id
    if not is_admin(message) and user_has_active_coven(user_id):
        await safe_send(message.channel, content="You already lead a coven. Type `show` to see it.")
        return

    chosen = random.choice(COVEN_NAMES)
    code = generate_code()
    members = generate_vampires(random.randint(4, 7))
    elder = max(members, key=lambda m: m['power'])

    covens[code] = {
        "name": chosen["name"],
        "domain": chosen["domain"],
        "elder": elder['name'],
        "owner_id": user_id,
        "owner_name": message.author.name,
        "code": code,
        "alive": True,
        "raids_won": 0,
        "raids_lost": 0,
        "members": members,
        "blood_debts": [],
    }

    if not is_admin(message):
        active_coven_owners.add(user_id)

    member_lines = "\n".join(
        f"`{m['name']}` — Power: {m['power']} ({get_power_tier(m['power'])})"
        for m in members
    )

    embed = discord.Embed(
        title="You Have Been Bound",
        description=(
            f"You now lead **{chosen['name']}**.\n\n"
            f"Domain: {chosen['domain']}\n"
            f"Elder: `{elder['name']}` — Power: {elder['power']} ({get_power_tier(elder['power'])})\n"
            f"Members: {len(members)}\n"
            f"Code: `{code}`\n\n"
            f"{member_lines}"
        ),
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="More commands coming.")
    await safe_send(message.channel, embed=embed)

COMMANDS = {
    "coven": handle_coven,
}

@bot.event
async def on_ready():
    print(f'{bot.user} is online and ready.')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild is None:
        await message.channel.send("Commands only work in servers, not DMs.")
        return

    parts = message.content.strip().split()
    if not parts:
        return

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in COMMANDS:
        try:
            await COMMANDS[cmd](message, args)
        except discord.HTTPException as e:
            print(f"HTTP error in {cmd}: {e}")
            try:
                await message.channel.send("Something went wrong. Try again.")
            except:
                pass
        except Exception as e:
            import traceback
            print(f"Error in {cmd}: {e}")
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
