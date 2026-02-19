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

ENEMY_VAMPIRE_NAMES = [
    "Malgrath", "Syndra", "Vorlen", "Thessiva", "Carnax", "Belara", "Drevus",
    "Isoleth", "Raxon", "Calindra", "Morvex", "Selenith", "Vrakon", "Caelith",
    "Syndros", "Velthar", "Noxara", "Drevian", "Sylveth", "Corveth",
    "Maldris", "Vaelith", "Thessorn", "Noxian", "Caeldris", "Marveth",
    "Isolorn", "Drexan", "Corvian", "Sylvorn",
]

POWER_TIERS = [
    (1, 25, "Fledgling"),
    (26, 50, "Turned"),
    (51, 75, "Ancient"),
    (76, 100, "Elder"),
]

MSG_DELAY = 2.1
EMBED_DESC_LIMIT = 4000
EMBED_FIELD_LIMIT = 1024

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

def make_member(name, is_new_turn=False):
    power = random.randint(1, 15) if is_new_turn else random.randint(1, 100)
    return {
        "name": name,
        "alive": True,
        "power": power,
        "kills": 0,
        "deaths": 0,
        "missions_survived": 0,
    }

def generate_vampires(count=5):
    names = random.sample(VAMPIRE_NAMES, min(count, len(VAMPIRE_NAMES)))
    return [make_member(n) for n in names]

def get_alive_members(coven):
    return [m for m in coven['members'] if m['alive']]

def get_dead_members(coven):
    return [m for m in coven['members'] if not m['alive']]

def update_elder(coven):
    alive = get_alive_members(coven)
    if not alive:
        coven['elder'] = "None"
        return
    top = max(alive, key=lambda m: m['power'])
    coven['elder'] = top['name']

def check_and_mark_dead(code):
    coven = covens.get(code)
    if not coven:
        return
    if not get_alive_members(coven):
        coven['alive'] = False
        active_coven_owners.discard(coven['owner_id'])

def get_coven_kills(coven):
    return sum(m['kills'] for m in coven['members'])

def get_coven_deaths(coven):
    return sum(m['deaths'] for m in coven['members'])

async def safe_send(channel, embed=None, content=None):
    try:
        if embed:
            if embed.description and len(embed.description) > EMBED_DESC_LIMIT:
                embed.description = embed.description[:EMBED_DESC_LIMIT - 3] + "..."
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

# --- coven command ---

async def handle_coven(message, args):
    user_id = message.author.id
    if not is_admin(message) and user_has_active_coven(user_id):
        await safe_send(message.channel, content="You already lead a coven. Type `view` to see it.")
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
        "hunts_won": 0,
        "hunts_lost": 0,
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
    embed.set_footer(text="coven | hunt <code> <number> | new <code> <number> | view")
    await safe_send(message.channel, embed=embed)

# --- new command ---

async def handle_new(message, args):
    if not args:
        await safe_send(message.channel, content="Usage: `new <code> <number>`")
        return

    code = args[0].upper()
    coven = covens.get(code)

    if not coven:
        await safe_send(message.channel, content=f"No coven found with code `{code}`.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, content="That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, content=f"**{coven['name']}** has been destroyed. Type `coven` to begin again.")
        return

    requested = 1
    if len(args) >= 2:
        try:
            requested = int(args[1])
        except ValueError:
            await safe_send(message.channel, content="The number must be a whole number. Example: `new XKRV 3`")
            return
        if requested < 1:
            await safe_send(message.channel, content="Turn at least 1.")
            return
        if requested > 10:
            await safe_send(message.channel, content="Max 10 at once.")
            return

    existing = {m['name'] for m in coven['members']}
    available = [n for n in VAMPIRE_NAMES if n not in existing]

    if not available:
        await safe_send(message.channel, content=f"**{coven['name']}** has no more names to give. The roster is full.")
        return

    actual = min(requested, len(available))
    turned = []
    refused = 0

    for _ in range(actual):
        if not available:
            break
        if random.randint(1, 100) <= 60:
            new_name = random.choice(available)
            available.remove(new_name)
            existing.add(new_name)
            new_member = make_member(new_name, is_new_turn=True)
            coven['members'].append(new_member)
            turned.append(new_member)
        else:
            refused += 1

    update_elder(coven)

    if turned and refused == 0:
        turned_lines = "\n".join(
            f"`{m['name']}` — Power: {m['power']} ({get_power_tier(m['power'])})"
            for m in turned
        )
        embed = discord.Embed(
            title=f"{len(turned)} Turned",
            description=(
                f"{turned_lines}\n\n"
                f"All {len(turned)} accepted the blood.\n"
                f"Total alive: {len(get_alive_members(coven))}"
            ),
            color=discord.Color.dark_red()
        )
        embed.set_footer(text="They are Fledglings. Hunt to grow their power.")

    elif turned and refused > 0:
        turned_lines = "\n".join(
            f"`{m['name']}` — Power: {m['power']} ({get_power_tier(m['power'])})"
            for m in turned
        )
        embed = discord.Embed(
            title=f"{len(turned)} Turned — {refused} Refused",
            description=(
                f"{turned_lines}\n\n"
                f"{refused} rejected the offering.\n"
                f"Total alive: {len(get_alive_members(coven))}"
            ),
            color=discord.Color.dark_gold()
        )
        embed.set_footer(text="They are Fledglings. Hunt to grow their power.")

    else:
        embed = discord.Embed(
            title="None Accepted",
            description=(
                f"Offered the blood to {requested} but none accepted.\n"
                f"Total alive: {len(get_alive_members(coven))}"
            ),
            color=discord.Color.dark_grey()
        )
        embed.set_footer(text=f"Try again with `new {code} <number>`.")

    await safe_send(message.channel, embed=embed)

# --- hunt command ---

async def handle_hunt(message, args):
    if len(args) < 2:
        await safe_send(message.channel, content="Usage: `hunt <code> <number>`")
        return

    code = args[0].upper()
    coven = covens.get(code)

    if not coven:
        await safe_send(message.channel, content=f"No coven found with code `{code}`.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, content="That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, content=f"**{coven['name']}** has been destroyed. Type `coven` to begin again.")
        return

    try:
        requested = int(args[1])
    except ValueError:
        await safe_send(message.channel, content="Needs to be a number. Example: `hunt XKRV 3`")
        return

    if requested < 1:
        await safe_send(message.channel, content="Send at least 1.")
        return

    alive = get_alive_members(coven)
    if not alive:
        await safe_send(message.channel, content="No members left. Type `coven` to begin again.")
        return

    actual = min(requested, len(alive), 10)
    hunting = random.sample(alive, actual)

    enemy_name = random.choice(ENEMY_VAMPIRE_NAMES)
    enemy_power = random.randint(1, 100)
    enemy_tier = get_power_tier(enemy_power)

    hunting_names = ", ".join(f"`{m['name']}`" for m in hunting)

    intro = discord.Embed(title="The Hunt Begins", color=discord.Color.dark_red())
    intro.description = (
        f"**{coven['name']}** moves into the dark.\n\n"
        f"Hunting: {hunting_names}\n\n"
        f"Target: `{enemy_name}` — Power: {enemy_power} ({enemy_tier})"
    )
    intro.set_footer(text="The night belongs to them.")
    await safe_send(message.channel, embed=intro)
    await asyncio.sleep(MSG_DELAY)

    result_lines = []
    fallen = []
    total_kills = 0

    for m in hunting:
        power_diff = m['power'] - enemy_power
        win_chance = max(15, min(85, 50 + int((power_diff / 100) * 35)))
        roll = random.randint(1, 100)

        if roll <= win_chance:
            m['kills'] += 1
            m['missions_survived'] += 1
            total_kills += 1
            power_gain = random.randint(1, 10)
            old_power = m['power']
            m['power'] = min(100, m['power'] + power_gain)
            result_lines.append(random.choice([
                f"`{m['name']}` — hunted `{enemy_name}` down. Power: {old_power} -> {m['power']} (+{power_gain})",
                f"`{m['name']}` — the target never stood a chance. Power: {old_power} -> {m['power']} (+{power_gain})",
                f"`{m['name']}` — moved through the dark and did not miss. Power: {old_power} -> {m['power']} (+{power_gain})",
            ]))
        elif roll <= win_chance + 25:
            m['missions_survived'] += 1
            power_loss = random.randint(1, 8)
            old_power = m['power']
            m['power'] = max(1, m['power'] - power_loss)
            result_lines.append(random.choice([
                f"`{m['name']}` — took damage but returned. Power: {old_power} -> {m['power']} (-{power_loss})",
                f"`{m['name']}` — escaped with wounds. Power: {old_power} -> {m['power']} (-{power_loss})",
            ]))
        else:
            m['alive'] = False
            m['deaths'] += 1
            fallen.append(m['name'])
            result_lines.append(random.choice([
                f"`{m['name']}` — was destroyed by `{enemy_name}`. They do not return.",
                f"`{m['name']}` — fell. The enemy was stronger.",
                f"`{m['name']}` — met their end in the dark.",
            ]))

    update_elder(coven)
    check_and_mark_dead(code)

    crew_text = "\n".join(result_lines) if result_lines else "Nothing to report."
    alive_after = get_alive_members(coven)
    coven_wiped = not coven['alive']

    result_embed = discord.Embed(
        title="Coven Destroyed" if coven_wiped else ("Hunt Over — Blood Spilled" if fallen else "Hunt Over"),
        color=discord.Color.dark_grey() if coven_wiped else (discord.Color.dark_red() if fallen else discord.Color.green())
    )

    desc = f"**Kills this hunt:** {total_kills}\n"
    desc += f"**Standing:** {len(alive_after)} alive\n"
    desc += f"**Elder:** `{coven['elder']}`\n"

    if fallen:
        desc += "\n**Destroyed:** " + ", ".join(f"`{n}`" for n in fallen)

    if coven_wiped:
        desc += "\n\nThe coven has been wiped out. There is nothing left."

    result_embed.description = desc

    if len(crew_text) <= EMBED_FIELD_LIMIT:
        result_embed.add_field(name="Results", value=crew_text, inline=False)
    else:
        chunks = [result_lines[i:i+10] for i in range(0, len(result_lines), 10)]
        for idx, chunk in enumerate(chunks):
            result_embed.add_field(
                name="Results" if idx == 0 else "Results (cont.)",
                value="\n".join(chunk),
                inline=False
            )

    if not coven_wiped:
        kills_field = "\n".join(
            f"`{m['name']}` — {m['kills']} kill{'s' if m['kills'] != 1 else ''} | Power: {m['power']} ({get_power_tier(m['power'])})"
            for m in coven['members']
        )
        if len(kills_field) <= EMBED_FIELD_LIMIT:
            result_embed.add_field(name="Coven Stats", value=kills_field, inline=False)

    result_embed.set_footer(
        text="The coven is gone. Type `coven` to begin again." if coven_wiped else
        ("Some did not return." if fallen else "The coven endures.")
    )
    await safe_send(message.channel, embed=result_embed)

# --- view command ---

async def handle_view(message, args):
    user_id = message.author.id

    if args:
        code = args[0].upper()
        target = covens.get(code)
        if not target:
            await safe_send(message.channel, content=f"No coven found with code `{code}`.")
            return
        if target['owner_id'] != user_id and not is_admin(message):
            await safe_send(message.channel, content="That is not your coven.")
            return
        user_covens = [target]
    else:
        user_covens = [c for c in covens.values() if c['owner_id'] == user_id]

    if not user_covens:
        await safe_send(message.channel, content="You lead no coven. Type `coven` to start one.")
        return

    alive_covens = [c for c in user_covens if c['alive']]
    if not alive_covens:
        await safe_send(message.channel, content="No active coven. Type `coven` to start again.")
        return

    for c in alive_covens:
        update_elder(c)
        alive = get_alive_members(c)
        dead = get_dead_members(c)

        desc = (
            f"Domain: {c.get('domain', 'Unknown')}\n"
            f"Elder: `{c.get('elder', 'Unknown')}`\n"
            f"Total Kills: {get_coven_kills(c)}   Total Deaths: {get_coven_deaths(c)}\n"
            f"Standing: {len(alive)} alive\n"
        )

        if alive:
            roster = "\n".join(
                f"`{m['name']}` | Power: {m['power']} ({get_power_tier(m['power'])}) | {m['kills']} kills"
                for m in alive
            )
            desc += f"\nActive Members\n{roster}"

        embed = discord.Embed(
            title=f"{c['name']} — `{c['code']}`",
            description=desc,
            color=discord.Color.dark_red()
        )
        embed.set_footer(text="coven | hunt <code> <number> | new <code> <number> | view")
        await safe_send(message.channel, embed=embed)

        if dead:
            dead_lines = "\n".join(
                f"`{m['name']}` | Power: {m['power']} ({get_power_tier(m['power'])}) | {m['kills']} kills | Destroyed"
                for m in dead
            )
            fallen_embed = discord.Embed(
                title=f"{c['name']} — Destroyed",
                description=dead_lines,
                color=discord.Color.dark_grey()
            )
            fallen_embed.set_footer(text="They do not return.")
            await safe_send(message.channel, embed=fallen_embed)

# --- Router ---

COMMANDS = {
    "coven": handle_coven,
    "hunt": handle_hunt,
    "new": handle_new,
    "view": handle_view,
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
