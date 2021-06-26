# iabot.py

### Imports of modules
import asyncio
import os
import discord
import csv
import schedule
from datetime import datetime, timedelta
from discord.ext import commands
from dotenv import load_dotenv


### Defines bot environment and client environment
bot = commands.Bot(command_prefix='!')
client = discord.Client()
bot.remove_command('help')


### Loads variables from .ENV
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


### Checks if warnings file exists. If not, it creates a blank file
warnings_exist = os.path.isfile('./warnings.csv')
if warnings_exist:
    print (f'warnings.csv already exists, reusing file. ')
    pass
else:
    print(f'warnings.csv does not exist. Creating blank .csv file. ')
    open("warnings.csv", "w")


### Allowed variablesthat the bot accepts commands from
iaval_channels = ('internal-affairs','ia')
val_roles = ('IA Officer','Sub Director','Director','CEO')
iamessage = f"Ascendance Internal affairs has sent you a message on the Goonswarm forums. \nPlease reply within 48 hours to prevent being kicked from corp. Click the link below to directly view your messages. \n\nhttps://goonfleet.com/index.php?app=members&module=messaging"


### When bot is ready, has all data, will report ready in console
@bot.event
async def on_ready():
    #await bot.change_presence(game=discord.Game(name='ASCEE.NET'))
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name='ASCEE.NET'))
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nDiscord version: {discord.__version__}\n ')
    print(f'Successfully logged in and booted...! ')


#################################################
############## RESTRICTED COMMANDS ##############
#################################################


### Warn command, allowing you to ping someone directly // WIP
@bot.command(name='warn', help='(RESTRICTED)(WIP) Warns a user to contact IA through forum PM. ')
@commands.has_any_role(*val_roles)
async def dm(ctx, *d_user: discord.User):
    time=48
    if ctx.channel.name in iaval_channels:
            for user in d_user:
                with open('warnings.csv',"r") as readfile:
                    for row in readfile:
                        if user in row:
                            await ctx.send (f"Already exists.")
                            continue
                await user.send(iamessage)
                try:
                    now = datetime.now()
                    with open('warnings.csv', "a", newline = '') as csvfile:
                        writer = csv.writer(csvfile, delimiter = ',')
                        fieldnames = user,now
                        writer.writerow(fieldnames)
                        await ctx.send(f'Warning {user.name} for {time} hours.')
                except: 
                    await ctx.send(f'Unable to write to warnings file. Warning only sent once. Please contact developer.')
    else:
        return

async def sendwarn(): ### TEST // WIP
    with open("warnings.csv","r") as warningsfile:
        towarn = list(csv.reader(warningsfile))
    for row in towarn:
        if datetime.now-row[1]:
            await row[0].send(iamessage)
schedule.every(12).hours.do(sendwarn)

### Test command // WIP
@bot.command(name='test', help='test')
async def test(ctx):
    await sendwarn()


### Cancel command // WIP1
@bot.command(name='cancel', help='(RESTRICTED)(WIP) Removes a user from the active warnings.')
@commands.has_any_role(*val_roles)
async def status(ctx, c_user):
    if ctx.channel.name in iaval_channels:
        with open("warnings.csv", "r") as f:
            data = list(csv.reader(f))
            with open("warnings.csv", "w") as f:
                writer = csv.writer(f)
                for row in data:
                    if row[0] != c_user:
                        writer.writerow(row)
    else:
        return


### activewarnings command
@bot.command(name='activewarnings', help='')
@commands.has_any_role(*val_roles)
async def activewarnings(ctx):
    if ctx.channel.name in iaval_channels:
        with open("warnings.csv", "r") as warnings:
            activewarnings = list(csv.reader(warnings))
            await ctx.send(f'Active warnings:')
            for awarn in activewarnings:
                await ctx.send(f'{awarn[0]} - set on: {awarn[1]}\n')
    else:
        return


#################################################
################ PUBLIC COMMANDS ################
#################################################


### Reminder command
@bot.command(name='remind', help='Reminds you about a message. Supports "s", "m", "h", and "d".')
async def remind(ctx, time, *, msg):
    time_conversion = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    remindertime = int(time[0]) * time_conversion[time[-1]]
    await ctx.send(f"Reminder added.")
    await asyncio.sleep(remindertime)
    await ctx.send(f"Reminder from: {ctx.author.mention}: {msg}")


### Help command
@bot.command(name='help', help='This command')
@commands.has_any_role(*val_roles)
async def help(ctx):
    if ctx.channel.name in iaval_channels:
        await ctx.send(f'```Explanation of commands:\n\n**Status**: Will show you the username of the bot, and what server it is connected to. \n\**Warn**: Will warn a user via PM that they have received a message from IA.\n\n```')
    else:
        return


bot.run(TOKEN)