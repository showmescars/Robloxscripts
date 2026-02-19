import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import os
import asyncio
import time
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
    "Rhydian", "Cressida", "Draeven", "Lucius", "Zara", "Belmont", "Caspian",
    "Varek", "Sirene", "Draven", "Moira", "Aldren", "Virel", "Saoirse",
    "Corvain", "Tessaly", "Obsidian", "Noctara", "Vira", "Alucard", "Seraph",
    "Malvyn", "Thessane", "Orynn", "Caedmon", "Vesra", "Darkmore", "Cael",
    "Isolara", "Maren", "Vortan", "Sylvara", "Drex", "Cassia", "Helion",
    "Nara", "Volthar", "Serevyn", "Ombra", "Revan", "Xeryn", "Cyrus",
    "Valdra", "Neron", "Elara", "Sorin", "Amara", "Bastian", "Vesper",
    "Rowan", "Alara", "Corvyn", "Mireille", "Aldara", "Sylvix", "Erebus",
    "Calix", "Thessian", "Vorn", "Sariel", "Drevan", "Orion", "Caera",
    "Malthus", "Revna", "Daxon", "Solara", "Coren", "Vayne", "Elyra",
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

SENTENCE_TIERS = [
    {"label": "2 nights", "minutes": 2},
    {"label": "5 nights", "minutes": 5},
    {"label": "10 nights", "minutes": 10},
    {"label": "15 nights", "minutes": 15},
    {"label": "25 nights", "minutes": 25},
    {"label": "40 nights", "minutes": 40},
    {"label": "50 nights", "minutes": 50},
]
SENTENCE_WEIGHTS = [30, 25, 20, 12, 8, 3, 2]

MSG_DELAY = 2.1

HUNT_LOCATIONS = [
    "a masked ball in the noble quarter",
    "a fog-drenched cemetery on the hill",
    "the lamplit streets of the old city",
    "a crowded tavern near the docks",
    "a moonlit crossroads outside of town",
    "an abandoned estate on the outskirts",
    "the underground markets beneath the city",
    "a candlelit cathedral after midnight",
    "a traveling carnival camped outside the walls",
    "the rooftops overlooking the sleeping city",
]

# --- Helpers ---

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
    return {
        "name": name, "alive": True, "kills": 0, "deaths": 0,
        "times_imprisoned": 0, "missions_survived": 0,
        "imprisoned_until": None, "imprisonment_sentence": None,
    }

def generate_vampires(count=5):
    names = random.sample(VAMPIRE_NAMES, min(count, len(VAMPIRE_NAMES)))
    return [make_member(n) for n in names]

def get_alive_members(coven):
    return [m for m in coven['members'] if m['alive']]

def get_dead_members(coven):
    return [m for m in coven['members'] if not m['alive']]

def is_imprisoned(member):
    return bool(member['imprisoned_until'] and time.time() < member['imprisoned_until'])

def get_free_members(coven):
    return [m for m in coven['members'] if m['alive'] and not is_imprisoned(m)]

def get_coven_kills(coven):
    return sum(m['kills'] for m in coven['members'])

def get_coven_deaths(coven):
    return sum(m['deaths'] for m in coven['members'])

def update_elder(coven):
    alive = get_alive_members(coven)
    if not alive:
        return
    top = max(alive, key=lambda m: m['kills'])
    coven['elder'] = top['name']

def check_and_mark_dead(code):
    coven = covens.get(code)
    if not coven:
        return
    if not get_alive_members(coven):
        coven['alive'] = False
        if not user_has_active_coven(coven['owner_id']):
            active_coven_owners.discard(coven['owner_id'])

def imprison(member):
    tier = random.choices(SENTENCE_TIERS, weights=SENTENCE_WEIGHTS, k=1)[0]
    member['imprisoned_until'] = time.time() + tier['minutes'] * 60
    member['imprisonment_sentence'] = tier['label']
    member['times_imprisoned'] += 1
    return tier['label']

def get_member_status(m):
    if not m['alive']:
        return "Destroyed"
    if is_imprisoned(m):
        return f"Imprisoned ({m['imprisonment_sentence']})"
    return "Free"

def add_blood_debt(coven, slayer_name, enemy_info, enemy_power):
    debts = coven.setdefault('blood_debts', [])
    for d in debts:
        if d['coven'] == enemy_info['name']:
            d['name'] = slayer_name
            d['enemy_power'] = enemy_power
            return
    debts.append({"name": slayer_name, "coven": enemy_info['name'], "coven_info": enemy_info, "enemy_power": enemy_power})

def get_blood_debts(coven):
    return coven.get('blood_debts', [])

def remove_blood_debt(coven, coven_name):
    coven['blood_debts'] = [d for d in coven.get('blood_debts', []) if d['coven'] != coven_name]

async def safe_send(channel, content):
    try:
        if len(content) > 2000:
            chunks = [content[i:i+1990] for i in range(0, len(content), 1990)]
            for chunk in chunks:
                await channel.send(chunk)
                await asyncio.sleep(0.3)
        else:
            await channel.send(content)
    except discord.HTTPException as e:
        print(f"safe_send error: {e}")

# --- Subcommand handlers ---

async def handle_coven_new(message):
    user_id = message.author.id
    if not is_admin(message) and user_has_active_coven(user_id):
        await safe_send(message.channel, "You already lead a coven. Use `coven show` to see it.")
        return

    chosen = random.choice(COVEN_NAMES)
    code = generate_code()
    members = generate_vampires(random.randint(4, 7))
    power = random.randint(10, 100)

    covens[code] = {
        "name": chosen["name"], "domain": chosen["domain"],
        "elder": members[0]['name'], "power": power,
        "owner_id": user_id, "owner_name": message.author.name,
        "code": code, "alive": True,
        "hunts_won": 0, "hunts_lost": 0,
        "members": members, "blood_debts": [],
    }

    if not is_admin(message):
        active_coven_owners.add(user_id)

    roster = "\n".join(f"  {m['name']}" for m in members)
    lines = [
        f"You have been bound to {chosen['name']}.",
        f"",
        f"Domain   : {chosen['domain']}",
        f"Elder    : {members[0]['name']}",
        f"Power    : {power}",
        f"Members  : {len(members)}",
        f"Code     : {code}",
        f"",
        f"Coven Roster",
        f"{roster}",
        f"",
        f"Commands: coven show | coven hunt | coven raid | coven recruit | coven retaliate | coven stalk | coven purge | coven delete",
    ]
    await safe_send(message.channel, "\n".join(lines))


async def handle_coven_show(message, args):
    user_id = message.author.id

    if args:
        code = args[0].upper()
        target = covens.get(code)
        if not target:
            await safe_send(message.channel, f"No coven found with code {code}.")
            return
        if target['owner_id'] != user_id and not is_admin(message):
            await safe_send(message.channel, "That is not your coven.")
            return
        user_covens = [target]
    else:
        user_covens = [c for c in covens.values() if c['owner_id'] == user_id]

    if not user_covens:
        await safe_send(message.channel, "You lead no coven. Use `coven new` to begin.")
        return

    alive_covens = [c for c in user_covens if c['alive']]
    if not alive_covens:
        await safe_send(message.channel, "No active coven. Use `coven new` to begin again.")
        return

    for c in alive_covens:
        update_elder(c)
        hw = c.get('hunts_won', 0)
        hl = c.get('hunts_lost', 0)
        total = hw + hl
        win_rate = f"{int((hw / total) * 100)}%" if total > 0 else "N/A"
        debts = get_blood_debts(c)
        alive = get_alive_members(c)
        dead = get_dead_members(c)

        lines = [
            f"{c['name']} -- {c['code']}",
            f"",
            f"Domain   : {c.get('domain', 'Unknown')}",
            f"Elder    : {c.get('elder', 'Unknown')}",
            f"Power    : {c['power']}",
            f"Record   : {hw}W -- {hl}L   Win Rate: {win_rate}",
            f"Kills    : {get_coven_kills(c)}   Deaths: {get_coven_deaths(c)}",
            f"Standing : {len(alive)} alive   {len(get_free_members(c))} free",
        ]

        if debts:
            lines.append("")
            lines.append("Blood Debts")
            for d in debts:
                lines.append(f"  {d['name']} of {d['coven']}")

        if alive:
            lines.append("")
            lines.append("Active Members")
            for m in alive:
                lines.append(f"  {m['name']} | {m['kills']} kills | {get_member_status(m)}")

        if dead:
            lines.append("")
            lines.append("Destroyed")
            for m in dead:
                lines.append(f"  {m['name']} | {m['kills']} kills | Destroyed")

        await safe_send(message.channel, "\n".join(lines))


async def handle_coven_recruit(message, args):
    if not args:
        await safe_send(message.channel, "Usage: coven recruit <code> <number>")
        return

    code = args[0].upper()
    coven = covens.get(code)
    if not coven:
        await safe_send(message.channel, f"No coven found with code {code}.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, "That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed.")
        return

    requested = 1
    if len(args) >= 2:
        try:
            requested = int(args[1])
        except ValueError:
            await safe_send(message.channel, "The number must be a whole number. Example: coven recruit XKRV 3")
            return
        if requested < 1:
            await safe_send(message.channel, "Recruit at least 1.")
            return
        if requested > 10:
            await safe_send(message.channel, "Max 10 at once.")
            return

    existing = {m['name'] for m in coven['members']}
    available = [n for n in VAMPIRE_NAMES if n not in existing]
    if not available:
        await safe_send(message.channel, f"{coven['name']} roster is full. All names are taken.")
        return

    actual = min(requested, len(available))
    joined = []
    failed = 0

    for _ in range(actual):
        if not available:
            break
        if random.randint(1, 100) <= 60:
            new_name = random.choice(available)
            available.remove(new_name)
            existing.add(new_name)
            coven['members'].append(make_member(new_name))
            joined.append(new_name)
        else:
            failed += 1

    if joined and failed == 0:
        roster = "\n".join(f"  {n}" for n in joined)
        lines = [
            f"{len(joined)} joined the coven.",
            f"",
            roster,
            f"",
            f"Total alive: {len(get_alive_members(coven))}",
        ]
    elif joined and failed > 0:
        roster = "\n".join(f"  {n}" for n in joined)
        lines = [
            f"{len(joined)} joined. {failed} refused the turning.",
            f"",
            roster,
            f"",
            f"Total alive: {len(get_alive_members(coven))}",
        ]
    else:
        lines = [
            f"None accepted the offer. {requested} refused.",
            f"Total alive: {len(get_alive_members(coven))}",
        ]

    await safe_send(message.channel, "\n".join(lines))


async def handle_coven_hunt(message, args):
    if not args:
        await safe_send(message.channel, "Usage: coven hunt <code> <number>")
        return

    code = args[0].upper()
    coven = covens.get(code)
    if not coven:
        await safe_send(message.channel, f"No coven found with code {code}.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, "That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed.")
        return

    if len(args) < 2:
        await safe_send(message.channel, "Usage: coven hunt <code> <number>")
        return

    try:
        requested = int(args[1])
    except ValueError:
        await safe_send(message.channel, "Needs to be a number. Example: coven hunt XKRV 3")
        return

    if requested < 1:
        await safe_send(message.channel, "Send at least 1.")
        return

    free = get_free_members(coven)
    if not free:
        jailed = [m for m in coven['members'] if m['alive'] and is_imprisoned(m)]
        if jailed:
            await safe_send(message.channel, f"No free members. {len(jailed)} are imprisoned.")
        else:
            await safe_send(message.channel, "No free members available.")
        return

    actual = min(requested, len(free), 10)
    hunting = random.sample(free, actual)
    location = random.choice(HUNT_LOCATIONS)
    old_power = coven['power']

    hunting_names = ", ".join(m['name'] for m in hunting)
    await safe_send(message.channel, f"{coven['name']} moves through {location}.\nHunting: {hunting_names}")
    await asyncio.sleep(MSG_DELAY)

    power_change = 0
    fallen = []
    imprisoned_members = []
    result_lines = []

    for m in hunting:
        roll = random.randint(1, 100)
        if roll <= 50:
            gain = random.randint(10, 40)
            power_change += gain
            m['kills'] += 1
            m['missions_survived'] += 1
            result_lines.append(random.choice([
                f"  {m['name']} fed well tonight. +{gain} power.",
                f"  {m['name']} found prey in the dark. +{gain} power.",
                f"  {m['name']} returned sated. +{gain} power.",
            ]))
        elif roll <= 65:
            sentence = imprison(m)
            imprisoned_members.append((m['name'], sentence))
            loss = random.randint(10, 30)
            power_change -= loss
            result_lines.append(f"  {m['name']} was seized by hunters. Imprisoned for {sentence}. -{loss} power.")
        elif roll <= 80:
            loss = random.randint(5, 20)
            power_change -= loss
            result_lines.append(random.choice([
                f"  {m['name']} was driven off before feeding. -{loss} power.",
                f"  {m['name']} encountered resistance. -{loss} power.",
            ]))
        elif roll <= 92:
            result_lines.append(f"  {m['name']} returned with nothing. The night gave nothing.")
        else:
            if len(get_alive_members(coven)) > 1:
                m['alive'] = False
                m['deaths'] += 1
                fallen.append(m['name'])
                loss = random.randint(20, 50)
                power_change -= loss
                result_lines.append(f"  {m['name']} was destroyed. -{loss} power.")
            else:
                sentence = imprison(m)
                imprisoned_members.append((m['name'], sentence))
                result_lines.append(f"  {m['name']} was taken. Imprisoned for {sentence}.")

    coven['power'] = max(1, old_power + power_change)
    update_elder(coven)
    check_and_mark_dead(code)

    power_display = f"{old_power} -> {coven['power']} (+{power_change})" if power_change >= 0 else f"{old_power} -> {coven['power']} ({power_change})"

    lines = ["Hunt Results", ""]
    lines.extend(result_lines)
    lines.append("")
    lines.append(f"Power  : {power_display}")
    lines.append(f"Elder  : {coven['elder']}")
    lines.append(f"Alive  : {len(get_alive_members(coven))}   Free: {len(get_free_members(coven))}")
    if fallen:
        lines.append(f"Destroyed : {', '.join(fallen)}")
    if imprisoned_members:
        lines.append(f"Imprisoned : {', '.join(f'{n} ({s})' for n, s in imprisoned_members)}")

    await safe_send(message.channel, "\n".join(lines))

    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed. Use `coven new` to begin again.")


async def handle_coven_raid(message, args):
    if len(args) < 2:
        await safe_send(message.channel, "Usage: coven raid <code> <number>")
        return

    code = args[0].upper()
    coven = covens.get(code)
    if not coven:
        await safe_send(message.channel, f"No coven found with code {code}.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, "That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed.")
        return

    try:
        requested = int(args[1])
    except ValueError:
        await safe_send(message.channel, "Needs to be a number. Example: coven raid XKRV 3")
        return

    if requested < 1:
        await safe_send(message.channel, "Send at least 1.")
        return

    free = get_free_members(coven)
    if not free:
        await safe_send(message.channel, "No free members available to raid.")
        return

    actual = min(requested, len(free), 10)
    raiding = random.sample(free, actual)
    enemy_info = random.choice(COVEN_NAMES)
    enemy_power = random.randint(10, 500)

    raiding_names = ", ".join(m['name'] for m in raiding)
    await safe_send(message.channel, f"{coven['name']} moves against {enemy_info['name']}.\nRaiding: {raiding_names}\n\nYour power: {coven['power']}   Enemy power: {enemy_power}")
    await asyncio.sleep(MSG_DELAY)

    player_power = coven['power']
    power_diff = player_power - enemy_power
    win_chance = max(10, min(90, 50 + int((power_diff / 500) * 40)))
    player_won = random.randint(1, 100) <= win_chance

    fallen = []
    imprisoned_list = []
    result_lines = []

    if player_won:
        power_gain = random.randint(20, max(21, int(enemy_power * 0.4)))
        coven['power'] = player_power + power_gain
        coven['hunts_won'] = coven.get('hunts_won', 0) + 1

        for m in raiding:
            m['kills'] += 1
            m['missions_survived'] += 1
            result_lines.append(random.choice([
                f"  {m['name']} tore through them without mercy.",
                f"  {m['name']} moved through the enemy like shadow.",
                f"  {m['name']} left nothing standing in their path.",
            ]))

        free_raiders = [m for m in raiding if not is_imprisoned(m)]
        if len(get_alive_members(coven)) > 1 and random.randint(1, 100) <= 20 and free_raiders:
            c = random.choice(free_raiders)
            c['alive'] = False
            c['deaths'] += 1
            fallen.append(c['name'])
            result_lines.append(f"  {c['name']} was destroyed in the chaos.")

        if random.randint(1, 100) <= 15:
            free_raiders2 = [m for m in raiding if m['alive'] and not is_imprisoned(m)]
            if free_raiders2:
                j = random.choice(free_raiders2)
                s = imprison(j)
                imprisoned_list.append((j['name'], s))
                result_lines.append(f"  {j['name']} was seized leaving the scene. Imprisoned for {s}.")

        update_elder(coven)
        power_display = f"{player_power} -> {coven['power']} (+{power_gain})"
        outcome = "Raid Won"

    else:
        coven['hunts_lost'] = coven.get('hunts_lost', 0) + 1

        for m in raiding:
            if is_imprisoned(m):
                continue
            if len(get_alive_members(coven)) > 1 and random.randint(1, 100) <= 40:
                m['alive'] = False
                m['deaths'] += 1
                fallen.append(m['name'])
                result_lines.append(random.choice([
                    f"  {m['name']} fell to the enemy. Destroyed.",
                    f"  {m['name']} was overwhelmed. Gone.",
                ]))
            elif random.randint(1, 100) <= 30:
                s = imprison(m)
                imprisoned_list.append((m['name'], s))
                result_lines.append(f"  {m['name']} was captured. Imprisoned for {s}.")
            else:
                m['missions_survived'] += 1
                result_lines.append(random.choice([
                    f"  {m['name']} escaped into the dark.",
                    f"  {m['name']} retreated with wounds.",
                ]))

        power_loss = random.randint(20, max(21, int(player_power * 0.25)))
        coven['power'] = max(1, player_power - power_loss)
        power_display = f"{player_power} -> {coven['power']} (-{power_loss})"
        outcome = "Raid Lost"

        alive_before_names = {m['name'] for m in get_alive_members(coven)}
        if fallen:
            killer_name = random.choice(VAMPIRE_NAMES)
            add_blood_debt(coven, killer_name, enemy_info, enemy_power)

        update_elder(coven)

    check_and_mark_dead(code)

    lines = [outcome, ""]
    lines.extend(result_lines)
    lines.append("")
    lines.append(f"Power  : {power_display}")
    lines.append(f"Elder  : {coven['elder']}")
    lines.append(f"Alive  : {len(get_alive_members(coven))}   Free: {len(get_free_members(coven))}")
    if fallen:
        lines.append(f"Destroyed : {', '.join(fallen)}")
    if imprisoned_list:
        lines.append(f"Imprisoned : {', '.join(f'{n} ({s})' for n, s in imprisoned_list)}")
    if get_blood_debts(coven):
        lines.append("")
        lines.append("Blood is owed. Use `coven retaliate` to collect.")

    await safe_send(message.channel, "\n".join(lines))

    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed. Use `coven new` to begin again.")


async def handle_coven_retaliate(message, args):
    if not args:
        await safe_send(message.channel, "Usage: coven retaliate <code>")
        return

    code = args[0].upper()
    coven = covens.get(code)
    if not coven:
        await safe_send(message.channel, f"No coven found with code {code}.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, "That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed.")
        return

    debts = get_blood_debts(coven)
    if not debts:
        await safe_send(message.channel, "No blood owed. The ledger is clear.")
        return

    free = get_free_members(coven)
    if not free:
        await safe_send(message.channel, "No free members to send.")
        return

    target = random.choice(debts)
    enemy_info = target['coven_info']
    enemy_power = target.get('enemy_power', random.randint(10, 500))
    rolling = random.sample(free, random.randint(1, min(3, len(free))))

    rolling_names = ", ".join(m['name'] for m in rolling)
    await safe_send(message.channel, f"{coven['name']} moves against {enemy_info['name']} to settle the debt.\nSent: {rolling_names}")
    await asyncio.sleep(MSG_DELAY)

    player_power = coven['power']
    power_diff = player_power - enemy_power
    win_chance = max(10, min(95, 55 + int((power_diff / 500) * 40)))
    player_won = random.randint(1, 100) <= win_chance

    fallen = []
    imprisoned_list = []
    result_lines = []

    if player_won:
        power_gain = random.randint(25, max(26, int(enemy_power * 0.45)))
        coven['power'] = player_power + power_gain
        coven['hunts_won'] = coven.get('hunts_won', 0) + 1

        for m in rolling:
            m['kills'] += 1
            m['missions_survived'] += 1
            result_lines.append(f"  {m['name']} settled the debt in blood.")

        remove_blood_debt(coven, enemy_info['name'])
        update_elder(coven)
        power_display = f"{player_power} -> {coven['power']} (+{power_gain})"
        outcome = "Retaliation Successful"
    else:
        coven['hunts_lost'] = coven.get('hunts_lost', 0) + 1

        for m in rolling:
            if is_imprisoned(m):
                continue
            if len(get_alive_members(coven)) > 1 and random.randint(1, 100) <= 40:
                m['alive'] = False
                m['deaths'] += 1
                fallen.append(m['name'])
                result_lines.append(f"  {m['name']} was destroyed in the attempt.")
            elif random.randint(1, 100) <= 30:
                s = imprison(m)
                imprisoned_list.append((m['name'], s))
                result_lines.append(f"  {m['name']} was captured. Imprisoned for {s}.")
            else:
                m['missions_survived'] += 1
                result_lines.append(f"  {m['name']} fled before it was too late.")

        if fallen:
            add_blood_debt(coven, target['name'], enemy_info, enemy_power)

        power_loss = random.randint(20, max(21, int(player_power * 0.25)))
        coven['power'] = max(1, player_power - power_loss)
        power_display = f"{player_power} -> {coven['power']} (-{power_loss})"
        outcome = "Retaliation Failed"
        update_elder(coven)

    check_and_mark_dead(code)

    lines = [outcome, ""]
    lines.extend(result_lines)
    lines.append("")
    lines.append(f"Power  : {power_display}")
    lines.append(f"Elder  : {coven['elder']}")
    lines.append(f"Alive  : {len(get_alive_members(coven))}   Free: {len(get_free_members(coven))}")
    if fallen:
        lines.append(f"Destroyed : {', '.join(fallen)}")
    if imprisoned_list:
        lines.append(f"Imprisoned : {', '.join(f'{n} ({s})' for n, s in imprisoned_list)}")

    remaining = get_blood_debts(coven)
    if remaining:
        lines.append("")
        lines.append("Blood Still Owed")
        for d in remaining:
            lines.append(f"  {d['name']} of {d['coven']}")
        lines.append("")
        lines.append(f"Use `coven retaliate {code}` again.")
    elif player_won:
        lines.append("")
        lines.append("All debts are settled.")

    await safe_send(message.channel, "\n".join(lines))

    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed. Use `coven new` to begin again.")


async def handle_coven_stalk(message, args):
    if len(args) < 2:
        await safe_send(message.channel, "Usage: coven stalk <code> <name>")
        return

    code = args[0].upper()
    member_name = " ".join(args[1:])
    coven = covens.get(code)

    if not coven:
        await safe_send(message.channel, f"No coven found with code {code}.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, "That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed.")
        return

    target = next((m for m in coven['members'] if m['name'].lower() == member_name.lower()), None)
    if not target:
        roster = ", ".join(m['name'] for m in coven['members'])
        await safe_send(message.channel, f"No member named {member_name}.\nRoster: {roster}")
        return
    if not target['alive']:
        await safe_send(message.channel, f"{target['name']} has been destroyed.")
        return
    if is_imprisoned(target):
        await safe_send(message.channel, f"{target['name']} is imprisoned.")
        return

    enemy_info = random.choice(COVEN_NAMES)
    enemy_power = random.randint(10, 500)
    player_power = coven['power']
    win_chance = max(10, min(75, 40 + int(((player_power - enemy_power) / 500) * 30)))
    roll = random.randint(1, 100)

    await safe_send(message.channel, f"{target['name']} moves alone into {enemy_info['name']} territory.\nKills so far: {target['kills']}   Domain: {enemy_info['domain']}")
    await asyncio.sleep(MSG_DELAY)

    if roll <= win_chance:
        target['kills'] += 1
        target['missions_survived'] += 1
        rep_gain = random.randint(15, 60)
        coven['power'] = player_power + rep_gain
        update_elder(coven)
        lines = [
            "Stalk -- Target Taken",
            "",
            f"{target['name']} moved without sound. The target never saw it coming.",
            "",
            f"Kills  : {target['kills']}",
            f"Power  : {player_power} -> {coven['power']} (+{rep_gain})",
            f"Elder  : {coven['elder']}",
        ]
    elif roll <= win_chance + 30:
        target['missions_survived'] += 1
        power_loss = random.randint(5, 25)
        coven['power'] = max(1, player_power - power_loss)
        lines = [
            "Stalk -- Returned Wounded",
            "",
            f"{target['name']} took damage but made it back before dawn.",
            "",
            f"Kills  : {target['kills']}",
            f"Power  : {player_power} -> {coven['power']} (-{power_loss})",
        ]
    elif roll <= win_chance + 50:
        s = imprison(target)
        power_loss = random.randint(10, 35)
        coven['power'] = max(1, player_power - power_loss)
        update_elder(coven)
        lines = [
            "Stalk -- Captured",
            "",
            f"{target['name']} was seized by hunters before reaching the target. Imprisoned for {s}.",
            "",
            f"Power  : {player_power} -> {coven['power']} (-{power_loss})",
            f"Elder  : {coven['elder']}",
        ]
    else:
        power_loss = random.randint(20, 60)
        coven['power'] = max(1, player_power - power_loss)
        if len(get_alive_members(coven)) > 1:
            target['alive'] = False
            target['deaths'] += 1
            check_and_mark_dead(code)
            update_elder(coven)
            lines = [
                "Stalk -- Destroyed",
                "",
                f"{target['name']} did not return. Destroyed in enemy territory.",
                "",
                f"Kills  : {target['kills']}",
                f"Power  : {player_power} -> {coven['power']} (-{power_loss})",
                f"Alive  : {len(get_alive_members(coven))}",
                f"Elder  : {coven['elder']}",
            ]
        else:
            s = imprison(target)
            update_elder(coven)
            lines = [
                "Stalk -- Captured",
                "",
                f"{target['name']} was taken. Imprisoned for {s}.",
                "",
                f"Power  : {player_power} -> {coven['power']} (-{power_loss})",
                f"Elder  : {coven['elder']}",
            ]

    await safe_send(message.channel, "\n".join(lines))


async def handle_coven_purge(message, args):
    if len(args) < 2:
        await safe_send(message.channel, "Usage: coven purge <code> <name>")
        return

    code = args[0].upper()
    member_name = " ".join(args[1:])
    coven = covens.get(code)

    if not coven:
        await safe_send(message.channel, f"No coven found with code {code}.")
        return
    if coven['owner_id'] != message.author.id:
        await safe_send(message.channel, "That is not your coven.")
        return
    if not coven['alive']:
        await safe_send(message.channel, f"{coven['name']} has been destroyed.")
        return

    target = next((m for m in coven['members'] if m['name'].lower() == member_name.lower()), None)
    if not target:
        roster = ", ".join(m['name'] for m in get_alive_members(coven))
        await safe_send(message.channel, f"No member named {member_name}.\nAlive: {roster}")
        return
    if not target['alive']:
        await safe_send(message.channel, f"{target['name']} is already destroyed.")
        return
    if is_imprisoned(target):
        await safe_send(message.channel, f"{target['name']} is imprisoned and cannot be purged right now.")
        return

    free = get_free_members(coven)
    executors = [m for m in free if m['name'] != target['name']]
    if not executors:
        await safe_send(message.channel, "No free members available to carry out the purge.")
        return

    num_exe = min(len(executors), random.randint(2, 5))
    selected = random.sample(executors, num_exe)
    exe_names = ", ".join(m['name'] for m in selected)

    await safe_send(message.channel, f"The coven has called judgment on {target['name']}.\n{exe_names} step forward.")
    await asyncio.sleep(MSG_DELAY)

    roll = random.randint(1, 100)

    if roll <= 15:
        target['alive'] = False
        target['deaths'] += 1
        check_and_mark_dead(code)
        update_elder(coven)
        outcome = random.choice([
            f"{target['name']} did not survive the judgment. The coven does not speak of what happened.",
            f"The purge went further than intended. {target['name']} is gone.",
            f"{target['name']} was destroyed during the rite. The elder called it necessary.",
        ])
        lines = [
            "Purge -- Destroyed",
            "",
            outcome,
            "",
            f"Alive  : {len(get_alive_members(coven))}",
            f"Elder  : {coven['elder']}",
        ]

    elif roll <= 40:
        coven['members'].remove(target)
        update_elder(coven)
        outcome = random.choice([
            f"{target['name']} was cast out and stripped of all ties to the coven. They will not return.",
            f"The judgment was exile. {target['name']} walked into the night alone and is no longer of this coven.",
            f"{target['name']} was exiled before dawn. The coven does not claim them.",
        ])
        lines = [
            "Purge -- Exiled",
            "",
            outcome,
            "",
            f"Alive  : {len(get_alive_members(coven))}",
            f"Elder  : {coven['elder']}",
        ]

    else:
        power_loss = random.randint(5, 20)
        coven['power'] = max(1, coven['power'] - power_loss)
        outcome = random.choice([
            f"{target['name']} endured the punishment and remains. They know their standing now.",
            f"The coven made its displeasure known. {target['name']} survived and will not forget this.",
            f"{target['name']} took the judgment without flinching. They are still one of us. For now.",
        ])
        lines = [
            "Purge -- Survived",
            "",
            outcome,
            "",
            f"Power  : {coven['power'] + power_loss} -> {coven['power']} (-{power_loss})",
            f"Alive  : {len(get_alive_members(coven))}",
            f"Elder  : {coven['elder']}",
        ]

    await safe_send(message.channel, "\n".join(lines))


async def handle_coven_delete(message, args):
    if not args:
        await safe_send(message.channel, "Usage: coven delete <code>")
        return

    code = args[0].upper()
    coven = covens.get(code)

    if not coven:
        await safe_send(message.channel, f"No coven found with code {code}.")
        return
    if coven['owner_id'] != message.author.id and not is_admin(message):
        await safe_send(message.channel, "That is not your coven.")
        return

    coven_name = coven['name']
    owner_id = coven['owner_id']
    del covens[code]
    if not user_has_active_coven(owner_id):
        active_coven_owners.discard(owner_id)

    await safe_send(message.channel, f"{coven_name} ({code}) has been dissolved. Use `coven new` to begin again.")


# --- Command router ---

COVEN_SUBCOMMANDS = {
    "new": lambda msg, args: handle_coven_new(msg),
    "show": handle_coven_show,
    "recruit": handle_coven_recruit,
    "hunt": handle_coven_hunt,
    "raid": handle_coven_raid,
    "retaliate": handle_coven_retaliate,
    "stalk": handle_coven_stalk,
    "purge": handle_coven_purge,
    "delete": handle_coven_delete,
}

COVEN_HELP = (
    "coven new               -- form a new coven\n"
    "coven show [code]       -- show your coven\n"
    "coven hunt <code> <n>   -- send members to hunt\n"
    "coven raid <code> <n>   -- raid a rival coven\n"
    "coven recruit <code> <n>-- turn new vampires\n"
    "coven retaliate <code>  -- collect a blood debt\n"
    "coven stalk <code> <name>-- send one member alone\n"
    "coven purge <code> <name>-- pass judgment on a member\n"
    "coven delete <code>     -- dissolve your coven"
)


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
    if cmd != "coven":
        return

    if len(parts) < 2:
        await safe_send(message.channel, COVEN_HELP)
        return

    sub = parts[1].lower()
    args = parts[2:]

    handler = COVEN_SUBCOMMANDS.get(sub)
    if not handler:
        await safe_send(message.channel, f"Unknown subcommand: {sub}\n\n{COVEN_HELP}")
        return

    try:
        await handler(message, args)
    except discord.HTTPException as e:
        print(f"HTTP error in coven {sub}: {e}")
        try:
            await message.channel.send("Something went wrong. Try again.")
        except:
            pass
    except Exception as e:
        import traceback
        print(f"Error in coven {sub}: {e}")
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
