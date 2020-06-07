from anime_downloader.sites import ALL_ANIME_SITES
from anime_downloader.sites import get_anime_class

from discord.ext import commands
import discord
import time
import json
import os
import subprocess

try:
    import testkeys 
    testkey = testkeys.token() 
    token = testkey.anime 
except:
    token = ''

"""discord id for the bot owner, change this!!!"""
owner = 200993688527175681 

bot = commands.Bot(command_prefix='')
users = os.path.expanduser('~/keep/anime.json')
config = os.path.expanduser('~/keep/config.json')
default_provider = 'animepahe'

def Int(number): #Can it be converted to int
    try:
        number = int(number)
        return(True)
    except:
        return(False)


def Write(f, path = users):
    if os.path.exists(path):
        f = str(f).replace("'",'"')
        _file = open(path, "w")
        _file.write(f)
        _file.close()
        return True
    else:
        print(f'file: "{path}" not found, not writing')
        return False


def Load(path = users,default=False): #All user info in anime.json
    if os.path.exists(path):
        try:
            f = json.loads(open(path).read())
            return f
        except:
            print(f'Json decode error')
            return default
    else:
        print(f'file: "{path}" not found, can not load')
        return default


def load_guild(guild_id, path = config, change={}):
    blank_guild = {
        "prefix":"!"
    }
    guild_id = str(guild_id)
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

        return guilds[guild_id]
    else:
        print(f'file: "{path}" not found, can not load')
        return blank_guild


#send a pm with a discord ID
async def sendPM(ID,message):
    if ID != bot:
        await (bot.get_user(ID)).send(message)


#get the name with a discord ID
async def GetUserName(ID):
    if ID != bot:
        name = bot.get_user(ID)
        return(str(name.name))


def Message(message, prefix, user_input = True): #0 is True/False, 1 is the string after
    return [message.content[:len(prefix)] == prefix and (len(message.content) > len(prefix) or not user_input),message.content[len(prefix):]]


@bot.event
async def on_message(message):
    if message.author.id != bot.user.id:
        str_id = str(message.author.id)
        guild_id = message.guild.id if message.guild else message.channel.id
        guild_config = load_guild(guild_id)
        prefix = guild_config['prefix']

        """
        variable abuse, but I see no better way
        a for loop + dict would be nice
        """
        search = Message(message,f'{prefix}a ')
        select = Message(message,f'{prefix}s ')
        episode = Message(message,f'{prefix}e ')
        select_provider = Message(message,f'{prefix}p ')
        read_prefix = Message(message,f'!read prefix',False)
        set_prefix = Message(message,f'!set prefix ')
        list_search = Message(message,f'{prefix}l',False)

        if read_prefix[0]:
            async with message.channel.typing():
                await message.channel.send(f'The current prefix is "{prefix}"\nSet the prefix with: "!set prefix *prefix*"')

        if set_prefix[0]:
            async with message.channel.typing():
                load_guild(guild_id, config, {'prefix':set_prefix[1]})
                await  message.channel.send(f'Changed prefix to "{set_prefix[1]}"')

        #search
        if search[0]:
            async with message.channel.typing():
                print(search[1])
                f = Load()
                provider = f[str_id].get('provider',default_provider) if str_id in f else default_provider
                results, results_list = Search(search[1],provider)
                
                f[str_id] = {
                    "provider":provider,
                    "select":{"url":"","title":""},
                    "episode":0,
                    "data":[{"url":a.url,"title":a.title.replace("'",'').replace('"','')} for a in results_list]
                    }

                Write(f)
                if not len(results):
                     await message.channel.send('No results found')
                await message.channel.send(results)
                """
                except:
                    await message.channel.send('Errors when searching')
                """
        if select_provider[0]:
            f = Load()
            if str_id in f:
                if get_anime_class(select_provider[1]):
                    f[str_id]['provider'] = select_provider[1]
                    Write(f)
                    await message.channel.send(f'Selected provider "{select_provider[1]}"')
                else:
                    await message.channel.send(f'Invalid provider, choose from: {[a[0] for a in ALL_ANIME_SITES]}')
            else:
                f[str_id] = {
                    "provider":select_provider[1]
                }

        #select
        if select[0]:
            async with message.channel.typing():
                f = Load()
                if str_id in f and Int(select[1]):
                    Provider = get_anime_class(f[str_id].get("provider",default_provider))
                    user = f[str_id]
                    select[1] = int(select[1]) - 1 #Starts from 1
                    await message.channel.send('Selected: ' + user["data"][select[1]]["title"] + f' - **Episode: {user["episode"]+1}**')
                    user["select"]["url"],user["select"]["title"] = user["data"][select[1]]["url"],user["data"][select[1]]["title"]
                    Write(f)
                    try:
                        anime = Provider(user["data"][select[1]]["url"])
                        embed = discord.Embed(
                            title = user["data"][select[1]]["title"]+f' - Episode {user["episode"]+1}/{len(anime)}',
                            url = anime[user["episode"]].source().stream_url
                        )
                    except:
                        await message.channel.send('Error selecting episode')
                    
                    try: #Fix embed here
                        await message.channel.send(embed=embed)
                    except:
                        await message.channel.send(anime[user["episode"]].source().stream_url)

        #list
        if list_search[0]:
            async with message.channel.typing():
                f = Load()
                if str_id in f:
                    results = '```'
                    for b in range(len(f[str_id]["data"])):
                        results = f'{results}\n{str(f[str_id]["data"][b]["title"])}'
                    results += '```'
                    await message.channel.send(results)
        

        #change episode 
        if episode[0]:
            async with message.channel.typing():
                f = Load()
                if Int(episode[1]):
                    if str_id in f:
                        user = f[str_id]
                        user["episode"] = int(episode[1])-1
                        Write(f)

                        await message.channel.send(f'Selected episode {episode[1]}')
                        try:
                            print(user["select"]["url"])
                            anime = Provider(user["select"]["url"])
                            embed = discord.Embed(
                            title = user["select"]["title"]+f' - Episode {user["episode"]+1}/{len(anime)}',
                            url = anime[user["episode"]].source().stream_url
                            )
                        except:
                            await message.channel.send('Error selecting episode')
                        try:
                            await message.channel.send(embed=embed)
                        except:
                            await message.channel.send(anime[user["episode"]].source().stream_url)

        if message.content == f'{prefix}ping':
            await message.channel.send(f'Pong! {round(bot.latency * 1000)}ms')

        if message.content == '!help':
            await message.channel.send(f'**Current prefix:** "{prefix}"\n`!set prefix`*`prefix`* to set prefix\n`!read prefix` to get current prefix\n\n`{prefix}a` *`anime`* to search\n`{prefix}s` *`number`* to select anime\n`{prefix}e` *`number`* to select episode\n`{prefix}l` to list search')

        if message.author.id == owner:
            if message.content == ('!anime update git'):
                os.system('pip install --upgrade --force-reinstall git+https://github.com/vn-ki/anime-downloader')
                await message.channel.send('GIT: '+os.popen('anime --version').read())
            if message.content == ('!anime update pip'):
                os.system('pip install --upgrade --force-reinstall anime-downloader')
                await message.channel.send('PIP: '+os.popen('anime --version').read())

        #To allow shell commands from discord, security risk
        if message.content.startswith('?') and message.author.id == owner:
            command = message.content[1:] if not ('anime' in message.content and '-c' not in message.content) else 'yes "1" | '  + message.content[1:]
            print(command)
            #command = command.split()
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            output, error = process.communicate()
            output = output.decode('UTF-8')
            print(output,error)
            if len(output) != 0:
                for a in range(0,int(round((len(output)/2000),0)+1)):
                    await message.channel.send(output[a*1999:(a+1)*1999])

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


@bot.event
async def on_ready():
    #game = discord.Game("with ur mom")
    #await bot.change_presence(status=discord.Status.idle, activity=game)
    print(str(bot.user.name) + ' has connected to Discord!')

bot.run(token)
