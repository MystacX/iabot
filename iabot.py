# iabot.py

### All the imports
import discord
import asyncio
import os
import csv
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandNotFound
from dotenv import load_dotenv

### load the .env file
load_dotenv()

### Set bot and client environments
bot = commands.Bot(command_prefix='!')
client = discord.Client()

### Removes default help command
bot.remove_command('help')

### Project variables
TOKEN = os.getenv('DISCORD_TOKEN')
runtime = datetime.now()
time_in_hours = 48
remindertime = 4
timeformat = '%Y-%m-%d %H:%M'
iaval_channels = ('internal-affairs','ia')
val_roles = ('IA Officer','Sub Director','Director','CEO')
iamessage = f'Ascendance Internal affairs has sent you a message on the Goonswarm forums. \nPlease reply within 48 hours to prevent being kicked from corp. Click the link below to directly view your messages. \n\nhttps://goonfleet.com/index.php?app=members&module=messaging'

### Intro stuff
print (f"""                                              
 _______   _____      _____    _____  _______ 
(_______) (_____)    (_____)  (_____)(__ _ __)
   (_)   (_)___(_)   (_)__(_)(_)   (_)  (_)   
   (_)   (_______)   (_____) (_)   (_)  (_)   
 __(_)__ (_)   (_)   (_)__(_)(_)___(_)  (_)   
(_______)(_)   (_)   (_____)  (_____)   (_)   
                                              """)
warnings_exist = os.path.isfile('./warnings.csv')
if warnings_exist:
    print (f'INFO: warnings.csv already exists, reusing file.')
else:
    print(f'WARNING: warnings.csv does not exist. Creating blank .csv file.')
    open("warnings.csv", "w")

### Bot ready
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="your ESI data"))
    print(f'INFO: Logged in as: {bot.user.name} - {bot.user.id}')
    print(f'INFO: Discord version: {discord.__version__}')
    print(f'INFO: Successfully logged in and booted at {runtime}')

### Mute command
@bot.command(name='mute', help="Mutes the specified user.")
@commands.has_permissions(manage_messages=True)
@commands.has_any_role(*val_roles)
async def mute(ctx, member: discord.Member, *, reason=None):
    guild = ctx.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")
    if not mutedRole:
        mutedRole = await guild.create_role(name="Muted")
        for channel in guild.channels:
            await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    embed = discord.Embed(title="Muted", description=f"{member.mention} was muted ", colour=discord.Colour.light_gray())
    embed.add_field(name="Reason:", value=reason, inline=False)
    await ctx.send(embed=embed)
    await member.add_roles(mutedRole, reason=reason)
    await member.send(f" you have been muted from: {guild.name} reason: {reason}")

### Unmute command
@bot.command(name='unmute', help="Unmutes a specified user.")
@commands.has_permissions(manage_messages=True)
@commands.has_any_role(*val_roles)
async def unmute(ctx, member: discord.Member):
   mutedRole = discord.utils.get(ctx.guild.roles, name="Muted")
   await member.remove_roles(mutedRole)
   await member.send(f"You have been unmuted from: {ctx.guild.name}")
   embed = discord.Embed(title="Unmute", description=f"Unmuted: {member.mention}",colour=discord.Colour.light_gray())
   await ctx.send(embed=embed)

### Warning command, will DM a target, and write to file
@bot.command(name='warn', help='(RESTRICTED) Warns a user to contact IA through forum PM.')
@commands.has_any_role(*val_roles)
async def dm(ctx, d_user: discord.User):
    if ctx.channel.name in iaval_channels:
        with open("warnings.csv", "r") as r:
            now = datetime.now()
            nowstr = now.strftime(timeformat)
            if str(d_user).lower() in r.read().lower():
                await ctx.send(f'{d_user} already exists in file.')
            else:
                #try:
                await d_user.send(iamessage)
                #except: 
                    #await ctx.send(f'Error: Bot shit the bed.')
                    #return
                await ctx.send(f'Warning {d_user} for {time_in_hours} hours, every {remindertime} hours.')
                try:
                    with open("warnings.csv", "a", newline='') as a:
                        aa = csv.writer(a, delimiter=',') 
                        aa.writerow([f'{d_user}',f'{d_user.id}',f'{nowstr}'])
                except:
                    await ctx.send(f'Unable to write to file. Warning only sent once.')
                    return
    else:
        return

### Loop task, will send another warning every X hours until Y hours have passed.
@tasks.loop(hours=remindertime)
async def sendwarns():
    with open("warnings.csv","r") as warningsfile:
        towarn = list(csv.reader(warningsfile))
    for row in towarn:
        user_to_warn = await bot.fetch_user(row[1])
        dm_channel = user_to_warn.dm_channel
        now = datetime.now()
        rowtime = datetime.strptime(row[2], timeformat)
        if now-timedelta(hours=48) <= rowtime <= now:
            if dm_channel is None:
                await user_to_warn.create_dm()
                dm_channel = user_to_warn.dm_channel
                await dm_channel.send(iamessage)
            else:
                await dm_channel.send(iamessage)

### Test command. Test is next.
@bot.command(name='test', help='test')
async def test(ctx):
    await ctx.send(f'Test is dead! FUCK YOU TEST')

### Evetime command
@bot.command(name='evetime', help='Current evetime')
async def evetime(ctx):
    current_time = datetime.utcnow()
    evetime = current_time.strftime("%H:%M")
    await ctx.send(evetime)

### Cancel command. Will remove a previously warned user from the warnings file.
@bot.command(name='cancel', help='(RESTRICTED) Removes a user from the active warnings.')
@commands.has_any_role(*val_roles)
async def cancel(ctx, c_user: discord.User):
    if ctx.channel.name in iaval_channels:
        with open('warnings.csv') as warnfile:
            newlines = []
            for line in warnfile:
                if (str(c_user) in line):
                    continue
                else:
                    newlines.append(line)
            with open('warnings.csv', 'w') as wwarnfile:
                try: 
                    wwarnfile.writelines(newlines)
                    await ctx.send(f'{c_user} removed from file.')
                except:
                    await ctx.send(f'Error occurred during writing. Unable to remove {c_user}')
    else:
        return

### Active warnings command. Will list all the entries in the warnings file and output to channel.
@bot.command(name='activewarnings', help='')
@commands.has_any_role(*val_roles)
async def activewarnings(ctx):
    if ctx.channel.name in iaval_channels:
        with open("warnings.csv", "r") as warnings:
            activewarnings = list(csv.reader(warnings))
            await ctx.send(f'**Active warnings:**')
            for awarn in activewarnings:
                now = datetime.now()
                rowtime = datetime.strptime(awarn[2], timeformat)
                if now-timedelta(hours=48) <= rowtime <= now:
                    try:
                        await ctx.send(f'User: {awarn[0]} - set on: {awarn[2]}')
                    except IndexError:
                        continue
                else:
                    try:
                        await ctx.send(f'User: {awarn[0]} - EXPIRED')
                    except IndexError:
                        continue
    else:
        return

### Reminder command. Will remind the author in the specified amount of time. No persistence.
@bot.command(name='remind', help='Reminds you about a message. Supports "s", "m", "h", and "d".')
async def remind(ctx, time, *, msg):
    time_conversion = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    remindertime = int(time[0]) * time_conversion[time[-1]]
    await ctx.send(f"Reminder added.")
    await asyncio.sleep(remindertime)
    await ctx.send(f"Reminder from: {ctx.author.mention}: {msg}")

### Custom help command.
@bot.command(name='help', help='This command')
@commands.has_any_role(*val_roles)
async def help(ctx):
    if ctx.channel.name in iaval_channels:
        await ctx.send(f'```Explanation of commands:\n\n**Status**: Will show you the username of the bot, and what server it is connected to. \n\**Warn**: Will warn a user via PM that they have received a message from IA.\n\n```')
    else:
        return

### Run loops
sendwarns.start()

### Run bot, run!
bot.run(TOKEN)
