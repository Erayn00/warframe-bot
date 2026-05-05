import discord
from discord.ext import tasks
import feedparser
import requests
from datetime import datetime

import os
TOKEN = os.getenv("MTUwMDk3OTE2MzMwNDI5NjYyMA.GW14Nr.rbdevimCMUQ5VCkfSY61hRi8E7mM7fi6SqwnK8")

# ----------------------------
# CANALI SEPARATI
# ----------------------------
CHANNEL_NEWS = 1494623085154930798
CHANNEL_EVENTS = 1494623129010438276
CHANNEL_EQUIPMENT = 1494623175399575644
CHANNEL_ALERTS = 1501273656603447388

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ----------------------------
# MEMORIA ANTI-SPAM
# ----------------------------
sent_news = set()
last_sortie = None
last_archon = None
last_fissures = set()
last_week_index = None
last_nightwave_week = -1

# ----------------------------
# INCARNON ROTATION
# ----------------------------
INCARNON_ROTATION = [
    ["Braton", "Lato", "Skana", "Paris", "Kunai"],
    ["Bo", "Latron", "Furis", "Strun", "Lex"],
    ["Magistar", "Boltor", "Torid", "Dual Toxocyst", "Dual Ichor"],
    ["Ceramic Dagger", "Ack & Brunt", "Soma", "Vasto", "Nami Solo"],
    ["Burston", "Zylok", "Sibear", "Dread", "Despair"],
    ["Hate", "Gorgon", "Boar", "Angstrum", "Gammacor"],
    ["Anku", "Ack & Brunt", "Soma", "Vasto", "Bo"]
]

# ----------------------------
# WORLDSTATE
# ----------------------------
def get_worldstate():
    try:
        r = requests.get("https://api.warframestat.us/pc", timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

# ----------------------------
# NEWS
# ----------------------------
def get_news():
    return feedparser.parse("https://www.warframe.com/rss").entries[:10]

def create_news_embed(entry):
    embed = discord.Embed(
        title=entry.title,
        url=entry.link,
        color=0x1abc9c
    )
    embed.timestamp = datetime.utcnow()
    return embed

# ----------------------------
# SORTIE
# ----------------------------
def create_sortie_embed(sortie):
    embed = discord.Embed(title="⚔️ Sortie", color=0xf1c40f)
    embed.add_field(name="Boss", value=sortie.get("boss", "N/A"), inline=False)
    embed.add_field(name="Fazioni", value=", ".join(sortie.get("factions", [])), inline=False)
    return embed

# ----------------------------
# ARCHON
# ----------------------------
def create_archon_embed(archon):
    embed = discord.Embed(title="⚔️ Archon Hunt", color=0xe74c3c)

    embed.add_field(name="Boss", value=archon.get("boss", "N/A"), inline=False)

    missions = archon.get("missions", [])
    text = ""

    for i, m in enumerate(missions[:3]):
        text += f"Fase {i+1}: {m.get('node')} - {m.get('type')}\n"

    embed.add_field(name="Missioni", value=text or "N/A", inline=False)
    embed.add_field(name="Reward", value="1 Archon Shard", inline=False)

    return embed

# ----------------------------
# FISSURE
# ----------------------------
def create_fissure_embed(fissures):
    lith, meso, neo, axi, steel = [], [], [], [], []

    for f in fissures:
        tier = (f.get("tier") or "").lower()
        is_steel = bool(f.get("isHard") or f.get("hard"))

        if is_steel:
            steel.append(f)
        elif "lith" in tier:
            lith.append(f)
        elif "meso" in tier:
            meso.append(f)
        elif "neo" in tier:
            neo.append(f)
        elif "axi" in tier:
            axi.append(f)

    def fmt(items):
        if not items:
            return "Nessuna"
        return "\n".join(
            f"• {f.get('tier')} - {f.get('node')} ({f.get('missionType')})"
            for f in items[:5]
        )

    embed = discord.Embed(title="💠 Void Fissures", color=0x9b59b6)

    embed.add_field(name="Lith", value=fmt(lith), inline=False)
    embed.add_field(name="Meso", value=fmt(meso), inline=False)
    embed.add_field(name="Neo", value=fmt(neo), inline=False)
    embed.add_field(name="Axi", value=fmt(axi), inline=False)
    embed.add_field(name="Steel Path", value=fmt(steel), inline=False)

    return embed

# ----------------------------
# INCARNON
# ----------------------------
def get_week_index():
    start = datetime(2023, 4, 26)
    return (datetime.utcnow() - start).days // 7 % len(INCARNON_ROTATION)

def create_incarnon_embed(weapons, index):
    embed = discord.Embed(
        title="🔁 Incarnon",
        description=f"Settimana {index + 1}",
        color=0x3498db
    )
    embed.add_field(name="Armi", value="\n".join(weapons), inline=False)
    return embed

# ----------------------------
# NIGHTWAVE
# ----------------------------
def get_nightwave_week():
    start = datetime(2023, 1, 1)
    return (datetime.utcnow() - start).days // 7

def create_nightwave_embed(data):
    embed = discord.Embed(title="🌌 Nightwave", color=0x9b59b6)

    text = ""
    for c in data.get("activeChallenges", [])[:5]:
        text += f"{c.get('title')} - {c.get('desc')}\n\n"

    embed.add_field(name="Sfide", value=text or "Nessuna", inline=False)
    return embed

# ----------------------------
# SEND HELPERS
# ----------------------------
async def send_news(embed):
    ch = client.get_channel(CHANNEL_NEWS)
    if ch:
        await ch.send(embed=embed)

async def send_events(embed):
    ch = client.get_channel(CHANNEL_EVENTS)
    if ch:
        await ch.send(embed=embed)

async def send_equipment(embed):
    ch = client.get_channel(CHANNEL_EQUIPMENT)
    if ch:
        await ch.send(embed=embed)

async def send_alert(embed):
    ch = client.get_channel(CHANNEL_ALERTS)
    if ch:
        await ch.send(embed=embed)

# ----------------------------
# LOOP NEWS
# ----------------------------
@tasks.loop(minutes=30)
async def check_news():
    for entry in get_news():
        if entry.id not in sent_news:
            sent_news.add(entry.id)
            await send_news(create_news_embed(entry))

# ----------------------------
# LOOP WORLD
# ----------------------------
@tasks.loop(minutes=5)
async def check_world():
    global last_sortie, last_archon, last_fissures

    data = get_worldstate()

    # EVENTS
    if data.get("sortie"):
        if data["sortie"]["id"] != last_sortie:
            last_sortie = data["sortie"]["id"]
            await send_events(create_sortie_embed(data["sortie"]))

    if data.get("archonHunt"):
        if data["archonHunt"]["id"] != last_archon:
            last_archon = data["archonHunt"]["id"]
            await send_events(create_archon_embed(data["archonHunt"]))

    # ALERTS
    fissures = data.get("fissures", [])
    ids = set(f.get("id") for f in fissures if f.get("id"))

    if ids != last_fissures:
        last_fissures = ids
        await send_alert(create_fissure_embed(fissures))

# ----------------------------
# INCARNON LOOP
# ----------------------------
@tasks.loop(minutes=60)
async def check_incarnon():
    global last_week_index

    idx = get_week_index()

    if idx != last_week_index:
        last_week_index = idx
        await send_equipment(
            create_incarnon_embed(INCARNON_ROTATION[idx], idx)
        )

# ----------------------------
# START
# ----------------------------
@client.event
async def on_ready():
    print(f"Loggato come {client.user}")

    check_news.start()
    check_world.start()
    check_incarnon.start()

client.run(TOKEN)