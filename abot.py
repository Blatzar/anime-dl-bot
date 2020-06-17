from anime_downloader.sites import ALL_ANIME_SITES
from anime_downloader.sites import get_anime_class

from discord.ext import commands
import discord
import time
import json
import os
import sys
import subprocess

try:
    import testkeys 
    testkey = testkeys.token() 
    token = testkey.anime 
except:
    token = ''

"""discord id for the bot owner, change this!!!"""
owner = 200993688527175681 

#bot = commands.Bot(command_prefix='')

anime_config = os.path.expanduser('~/keep/anime.json')
guild_config = os.path.expanduser('~/keep/config.json')
default_provider = 'animepahe'

def get_prefix(client, message, path = guild_config, change = {}):
    prefix = 'a!'
    guild_id = str(message.guild.id) if message.guild else str(message.channel.id)
    blank_guild = {
        "prefix":"!"
    }
    if message.content.startswith('a!help'): #In case the prefix is forgotten a!help always works
        return 'a!'

    if os.path.exists(path):
        data = Load(path)
        guilds = data['guilds']
        if not guild_id in guilds:
            guilds[guild_id] = blank_guild
            data['guilds'] = guilds
            Write(data,path)
        
        if change:
            for a in change:
                guilds[guild_id][a] = change[a]
            data['guilds'] = guilds
            Write(data,path)

        prefix = guilds[guild_id].get('prefix',prefix)

    else:
        print(f'file: "{path}" not found, can not load')

    return prefix

client = commands.Bot(command_prefix = get_prefix)
#client.remove_command('help')
def run_bot(client):
    client.run(token)


def Int(number): #Can it be converted to int
    try:
        number = int(number)
        return(True)
    except:
        return(False)


async def sendPM(ID,message):
    if ID != client.user.id:
        await (client.get_user(ID)).send(message)


def Write(data, path):
    print('Write')
    if os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    else:
        print(f'file: "{path}" not found, not writing')
        return False


def Load(path,default=False): #All user info in anime.json
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            print(f'Json decode error')
            return default
    else:
        print(f'file: "{path}" not found, can not load')
        return default

def Search(query,Provider):
    Provider = get_anime_class(Provider)
    results = '```'
    print(f'Query: {query}')
    search = Provider.search(query)
    for a in range(len(search)):
        """discord limit of 2000 chars, should ideally split the messages"""
        if len(f'{results}\n{str(search[a])}')+3 < 1999: 
            results = f'{results}\n{a+1}: {str(search[a])}'
    results += '```'
    print(results)
    return(results,search)

client.remove_command('help')
@client.command(pass_context=True)
async def help(ctx):
    ctx.message.content = 'test' #To bypass all prefix exceptions
    prefix = get_prefix(client, ctx.message)
    embed = discord.Embed(color=0xafb6c5)
    embed.set_author(name=f'Prefix: "{prefix}"')
    embed.add_field(inline=False, name='ping', value='Returns the ping of the bot.')
    embed.add_field(inline=False, name='help', value='Lists all the available commands the bot offers.\na!help works regardless of prefix')
    embed.add_field(inline=False, name='set prefix', value='Set prefix to chosen string, admin permissions needed')
    embed.add_field(inline=False, name='search, a, anime', value='Search for a show')
    embed.add_field(inline=False, name='select, s', value='Select a result from search')
    embed.add_field(inline=False, name='episode, e', value='Select an episode')
    embed.add_field(inline=False, name='provider, p', value='Select provider')
    await ctx.message.channel.send(embed=embed)
    #  f'**Current prefix:** "{prefix}"\n`!set prefix`*`prefix`* to set prefix\n`!read prefix` to get current prefix\n\n`{prefix}a` *`anime`* to search\n`{prefix}s` *`number`* to select anime\n`{prefix}e` *`number`* to select episode\n`{prefix}l` to list search')


@client.command(aliases=['exit'])
async def shutdown(ctx):
    if str(ctx.message.author.id) == str(owner):
        await ctx.send('The bot is exiting.')
        time.sleep(2)
        sys.exit(0)
    else:
        await ctx.send('You are not allowed to use this command.')


@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

'''
@client.command()
async def read(ctx, query):
    if query == 'prefix':
        async with ctx.typing():
            prefix = get_prefix(client,ctx.message)
            await ctx.send(f'The current prefix is "{prefix}"\nSet the prefix with: "!set prefix *prefix*"')
'''
@client.command()
async def set(ctx, query, prefix):
    if query == 'prefix':
        async with ctx.typing():
            premission = ctx.message.author.server_permissions.administrator if ctx.message.guild else True
            if premission:
                get_prefix(client,ctx.message,guild_config,{"prefix":prefix})
                await ctx.send(f'Changed prefix to "{prefix}"')
            else:
                ctx.send('Admin permissions needed to change prefix')


@client.command(aliases=['p'])
async def provider(ctx, provider):
    async with ctx.typing():
        f = Load(anime_config)
        str_id = str(ctx.author.id)
        if get_anime_class(provider):
            f[str_id]['provider'] = provider
            Write(f, anime_config)
            await ctx.send(f'Selected provider "{provider}"')
        else:
            await ctx.send(f'Invalid provider, choose from: {[a[0] for a in ALL_ANIME_SITES]}')


@client.command(aliases=['a','anime'])
async def search(ctx, *, query):
    async with ctx.typing():
        str_id = str(ctx.author.id)
        f = Load(anime_config)
        provider = f[str_id].get('provider',default_provider) if str_id in f else default_provider
        results, results_list = Search(query,provider)
        
        f[str_id] = {
            "provider":provider,
            "select":{"url":"","title":""},
            "episode":0,
            "data":[{"url":a.url,"title":a.title.replace("'",'').replace('"','')} for a in results_list]
            }

        Write(f,anime_config)
        if not len(results):
             await ctx.send('No results found')
        await ctx.send(results)


@client.command(aliases=['s'])
async def select(ctx, number):
    async with ctx.typing():
        str_id = str(ctx.author.id)
        f = Load(anime_config)
        if str_id in f and Int(number):
            Provider = get_anime_class(f[str_id].get("provider",default_provider))
            user = f[str_id]
            number = int(number) - 1 #Starts from 1
            await ctx.send('Selected: ' + user["data"][number]["title"] + f' - **Episode: {user["episode"]+1}**')
            user["select"]["url"],user["select"]["title"] = user["data"][number]["url"],user["data"][number]["title"]
            Write(f, anime_config)
            try:
                anime = Provider(user["data"][number]["url"])
                embed = discord.Embed(
                    title = user["data"][number]["title"]+f' - Episode {user["episode"]+1}/{len(anime)}',
                    url = anime[user["episode"]].source().stream_url
                )
            except:
                await ctx.send('Error selecting episode')
            
            try: #Fix embed here
                await ctx.send(embed=embed)
            except:
                await ctx.send(anime[user["episode"]].source().stream_url)


@client.command(aliases=['e'])
async def episode(ctx, number):
    async with ctx.typing():
        str_id = str(ctx.author.id)
        f = Load(anime_config)
        if Int(number):
            if str_id in f:
                user = f[str_id]
                user["episode"] = int(number)-1
                Write(f,anime_config)
                Provider = get_anime_class(f[str_id].get("provider",default_provider))
                print(user["select"]["url"])
                await ctx.send(f'Selected episode {number}')
                try:
                    print(user["select"]["url"])
                    anime = Provider(user["select"]["url"])
                    embed = discord.Embed(
                    title = user["select"]["title"]+f' - Episode {user["episode"]+1}/{len(anime)}',
                    url = anime[user["episode"]].source().stream_url
                    )
                except:
                    await ctx.send('Error selecting episode')
                try:
                    await ctx.send(embed=embed)
                except:
                    await ctx.send(anime[user["episode"]].source().stream_url)
        else:
            await ctx.send(f'Invalid number: "{number}"')


@client.command()
async def run(ctx, *, query):
    if ctx.message.author.id == owner: #Important!
        command = query if not ('anime' in query and '-c' not in message.content) else 'yes "1" | '  + query
        print(command)
        #command = command.split()
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        output, error = process.communicate()
        output = output.decode('UTF-8')
        print(output,error)
        if len(output) != 0:
            for a in range(0,int(round((len(output)/2000),0)+1)):
                await ctx.send(output[a*1999:(a+1)*1999])


@client.event
async def on_ready():
    #game = discord.Game("with ur mom")
    #await bot.change_presence(status=discord.Status.idle, activity=game)
    print(str(client.user.name) + ' has connected to Discord!')

run_bot(client)
