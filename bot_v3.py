import discord
from discord.ext import commands
import random
import json
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

client.run(os.environ["TOKEN"])

DATA = {}
TEAM_DATA = {}
BOSS_DATA = {}

if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        DATA = json.load(f)

if os.path.exists("teams.json"):
    with open("teams.json", "r") as f:
        TEAM_DATA = json.load(f)

TEAM_NAMES = [
    "EH Team",
    "Vietnamese Team",
    "TheKing Team",
    "Suzurain Team",
    "Hava Team"
]

UPGRADE_COSTS = {
    "member_slots": [2000, 4000, 8000, 15000, 25000],
    "xp_boost": [5000, 10000, 15000, 20000, 30000],
    "double_xp": [10000, 20000, 30000, 40000, 50000],
    "boss_rate": [5000, 10000, 15000, 20000, 30000],
    "damage_boost": [10000, 20000, 30000, 40000, 50000]
}

UPGRADE_IDS = {
    "member_slots": "slots",
    "xp_boost": "xp",
    "double_xp": "double",
    "boss_rate": "bossrate",
    "damage_boost": "damage"
}

LEVEL_REQUIREMENTS = {
    1: 2000,
    2: 4000,
    3: 8000,
    4: 16000,
    5: 30000
}

BOSS_LIST = {
    "Common": [("Stone Golem", 500), ("Wild Boar", 600)],
    "Uncommon": [("Forest Spirit", 1000), ("Shadow Wolf", 1100)],
    "Rare": [("Lava Beast", 2000), ("Ice Wyrm", 2200)],
    "Legendary": [("Thunder Dragon", 4000), ("Frost Giant", 4500)],
    "Mythical": [("Chaos Phoenix", 8000), ("Eternal Demon", 8500)]
}

BOSS_XP_REWARD = {
    "Common": 300,
    "Uncommon": 500,
    "Rare": 800,
    "Legendary": 1200,
    "Mythical": 2000
}

@bot.command()
async def jointeam(ctx, *, team_name):
    uid = ctx.author.id
    if uid in DATA and "team" in DATA[uid]:
        await ctx.send("❌ Bạn đã tham gia một team rồi.")
        return

    if team_name not in TEAM_NAMES:
        await ctx.send("❌ Tên team không hợp lệ.")
        return

    if team_name not in TEAM_DATA:
        TEAM_DATA[team_name] = {
            "gem": 0,
            "xp": 0,
            "level": 0,
            "upgrade": {
                "member_slots": 0,
                "xp_boost": 0,
                "double_xp": 0,
                "boss_rate": 0,
                "damage_boost": 0
            },
            "members": []
        }

    role = discord.utils.get(ctx.guild.roles, name=team_name)
    if role:
        await ctx.author.add_roles(role)

    TEAM_DATA[team_name]["members"].append(uid)
    DATA[uid] = {
        "team": team_name,
        "inventory": {"common": 0, "rare": 0, "mythical": 0},
        "daily": False
    }

    await ctx.send(f"✅ Bạn đã tham gia `{team_name}` thành công!")

@bot.command()
async def upgrade(ctx, *, arg=None):
    uid = ctx.author.id
    if uid not in DATA or "team" not in DATA[uid]:
        await ctx.send("❌ Bạn chưa tham gia team.")
        return
    team = DATA[uid]["team"]

    if arg == "shop":
        embed = discord.Embed(title="📈 Shop Nâng Cấp Team", color=discord.Color.gold())
        for key, costs in UPGRADE_COSTS.items():
            cur = TEAM_DATA[team]["upgrade"][key]
            if cur < len(costs):
                embed.add_field(
                    name=f"{UPGRADE_IDS[key]} (lv {cur+1}) - {costs[cur]} Gem",
                    value=f"Tăng {key.replace('_', ' ')}", inline=False
                )
            else:
                embed.add_field(name=f"{UPGRADE_IDS[key]}", value="Đã max cấp", inline=False)
        await ctx.send(embed=embed)

    elif arg in UPGRADE_IDS.values():
        real_key = [k for k, v in UPGRADE_IDS.items() if v == arg][0]
        current = TEAM_DATA[team]["upgrade"][real_key]
        if current >= 5:
            await ctx.send("🚫 Mục này đã đạt cấp tối đa.")
            return

        cost = UPGRADE_COSTS[real_key][current]
        if TEAM_DATA[team]["gem"] >= cost:
            TEAM_DATA[team]["gem"] -= cost
            TEAM_DATA[team]["upgrade"][real_key] += 1
            await ctx.send(f"✅ Đã nâng cấp `{real_key}` lên lv {current + 1}")
        else:
            await ctx.send(f"❌ Không đủ Gem ({cost}) để nâng cấp `{real_key}`.")

@bot.command()
@commands.has_permissions(administrator=True)
async def teamreset(ctx, *, team_name):
    if team_name not in TEAM_DATA:
        await ctx.send(f"❌ Team `{team_name}` không tồn tại.")
        return
    for uid in list(DATA.keys()):
        if DATA[uid].get("team") == team_name:
            del DATA[uid]
    TEAM_DATA[team_name] = {
        "gem": 0,
        "xp": 0,
        "level": 0,
        "upgrade": {
            "member_slots": 0,
            "xp_boost": 0,
            "double_xp": 0,
            "boss_rate": 0,
            "damage_boost": 0
        },
        "members": []
    }
    await ctx.send(f"✅ Team `{team_name}` đã được reset.")

@bot.command()
@commands.has_permissions(administrator=True)
async def teamleave(ctx, member: discord.Member):
    uid = member.id
    if uid not in DATA or "team" not in DATA[uid]:
        await ctx.send("❌ Người này chưa tham gia team.")
        return
    team = DATA[uid]["team"]
    TEAM_DATA[team]["members"].remove(uid)
    del DATA[uid]
    await ctx.send(f"✅ `{member.display_name}` đã bị xóa khỏi `{team}`.")

@bot.command()
async def daily(ctx):
    uid = ctx.author.id
    if uid not in DATA or "team" not in DATA[uid]:
        await ctx.send("❌ Bạn chưa tham gia team.")
        return

    if DATA[uid].get("daily", False):
        await ctx.send("📅 Bạn đã điểm danh hôm nay rồi.")
        return

    team = DATA[uid]["team"]
    xp_gain = random.randint(50, 200)
    TEAM_DATA[team]["xp"] += xp_gain
    DATA[uid]["daily"] = True

    await ctx.send(f"📅 Điểm danh thành công! Team nhận được `{xp_gain}` XP.")

@bot.command()
async def inventory(ctx):
    uid = ctx.author.id
    if uid not in DATA:
        await ctx.send("❌ Bạn chưa tham gia team.")
        return

    inv = DATA[uid]["inventory"]
    embed = discord.Embed(title=f"🎒 Túi đồ của {ctx.author.display_name}", color=discord.Color.blurple())
    for k, v in inv.items():
        embed.add_field(name=k.capitalize(), value=str(v), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def cmopen(ctx):
    await open_chest(ctx, "common")

@bot.command()
async def rropen(ctx):
    await open_chest(ctx, "rare")

@bot.command()
async def mtopen(ctx):
    await open_chest(ctx, "mythical")

async def open_chest(ctx, chest_type):
    uid = ctx.author.id
    if uid not in DATA or DATA[uid]["inventory"].get(chest_type, 0) <= 0:
        await ctx.send("❌ Bạn không có rương này.")
        return

    DATA[uid]["inventory"][chest_type] -= 1
    reward = {
        "common": random.randint(100, 400),
        "rare": random.randint(1000, 1500),
        "mythical": random.randint(5000, 6000)
    }[chest_type]

    team = DATA[uid]["team"]
    TEAM_DATA[team]["gem"] += reward
    await ctx.send(f"🎁 Bạn mở rương `{chest_type}` và nhận `{reward} Gem`!")

@bot.command()
async def teaminfo(ctx):
    uid = ctx.author.id
    if uid not in DATA or "team" not in DATA[uid]:
        await ctx.send("❌ Bạn chưa tham gia team.")
        return
    team = DATA[uid]["team"]
    data = TEAM_DATA[team]

    embed = discord.Embed(title=f"📊 Thông tin team: {team}", color=discord.Color.green())
    embed.add_field(name="Cấp độ", value=data["level"])
    embed.add_field(name="XP", value=data["xp"])
    embed.add_field(name="Gem", value=data["gem"])
    embed.add_field(name="Thành viên", value=len(data["members"]))
    embed.add_field(name="Cấp nâng cấp", value=str(data["upgrade"]))
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

    uid = message.author.id
    if uid not in DATA or "team" not in DATA[uid]:
        return
    team = DATA[uid]["team"]
    data = TEAM_DATA[team]
    upgrade = data["upgrade"]

    # XP
    base_xp = 10
    bonus = base_xp * (upgrade["xp_boost"] * 0.02)
    total_xp = int(base_xp + bonus)

    # Double XP
    if random.random() < 0.05 + (upgrade["double_xp"] * 0.01):
        total_xp *= 2
        await message.channel.send("✨ Tin nhắn này được DOUBLE XP!")

    TEAM_DATA[team]["xp"] += total_xp

    # Drop chest
    roll = random.random()
    inv = DATA[uid]["inventory"]
    if roll < 0.005:
        inv["mythical"] += 1
        await message.channel.send(f"🎉 {message.author.mention} nhận được RƯƠNG MYTHICAL!")
    elif roll < 0.025:
        inv["rare"] += 1
        await message.channel.send(f"🎉 {message.author.mention} nhận được RƯƠNG RARE!")
    elif roll < 0.075:
        inv["common"] += 1
        await message.channel.send(f"🎉 {message.author.mention} nhận được RƯƠNG COMMON!")

    # Level up
    current = data["level"]
    if current + 1 in LEVEL_REQUIREMENTS and data["xp"] >= LEVEL_REQUIREMENTS[current + 1]:
        data["level"] += 1
        await message.channel.send(f"📈 Team `{team}` đã lên level {data['level']}!")

    # Team Boss (có thể thêm sau nếu cần)


async def autosave():
    while True:
        with open("data.json", "w") as f:
            json.dump(DATA, f, indent=2)
        with open("teams.json", "w") as f:
            json.dump(TEAM_DATA, f, indent=2)
        await asyncio.sleep(60)

@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")
    bot.loop.create_task(autosave())

@bot.command()
async def cm(ctx):
    await open_chest(ctx, "common")

@bot.command()
async def rr(ctx):
    await open_chest(ctx, "rare")

@bot.command()
async def mt(ctx):
    await open_chest(ctx, "mythical")

async def open_chest(ctx, chest_type):
    uid = str(ctx.author.id)
    user_data = DATA.setdefault(uid, {})
    items = user_data.setdefault("items", {})
    count = items.get(chest_type, 0)
    if count <= 0:
        await ctx.send(f"❌ Bạn không có rương {chest_type}.")
        return

    reward_range = {
        "common": (100, 400),
        "rare": (1000, 1500),
        "mythical": (5000, 6000)
    }

    amount = random.randint(*reward_range[chest_type])
    team = user_data.get("team")
    if team:
        TEAM_DATA[team]["gem"] += amount
        items[chest_type] -= 1
        await ctx.send(f"🎁 Bạn đã mở rương {chest_type} và nhận {amount} gem cho team {team}!")
    else:
        await ctx.send("❌ Bạn chưa tham gia team nào.")

bot.run("MTI1MzY3ODg0NjIzOTMwOTg3Ng.GlIp8z.RTRrSzxGeGYacV9z8CaoSIB_Sa58sulK2Tqnhs")
