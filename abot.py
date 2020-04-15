import discord
from discord.ext import commands
import os
import time
import json
from anime_downloader.sites import get_anime_class
import testkeys #my personal token
Provider = get_anime_class('animeout')
testkey = testkeys.token() #Secret token
token = testkey.anime
bot = commands.Bot(command_prefix='')

def Int(number):
    try:
        number = int(number)
        return(True)
    except:
        return(False)

def Write(f, path='$HOME/keep/anime.json'): #I couldn't be bothered to learn proper file opening, please fix this in a PR
    f = str(f).replace("'",'"')
    print(f)
    os.system(f"echo '{f}' > {path}")

def Load(path = '$HOME/keep/anime.json'): #All user info in anime.json
    f = json.loads(os.popen(f'cat {path}').read())
    return(f)

#send a pm with a discord ID
async def sendPM(ID,message):
	if ID != bot:
		await (bot.get_user(ID)).send(message)
#get the name with a discord ID
async def GetUserName(ID):
	if ID != bot:
		name = bot.get_user(ID)
		return(str(name.name))

def Message(message,prefix):
	return [message.content[:len(prefix)] == prefix and len(message.content) > len(prefix),message.content[len(prefix):]]

@bot.event
async def on_message(message):

	#search
	search = Message(message,'a ')
	select = Message(message,'s ')
	episode = Message(message,'e ')
	if search[0]:
		print(search[1])
		results,results_list = Search(search[1])
		f = Load()
		[f.remove(a) for a in f if a['user'] == message.author.id]
		f.append({"user":message.author.id,"episode":0,"data":[{"url":a.url,"title":a.title} for a in results_list]})
		Write(f)
		await message.channel.send(results)
	
	#select
	if select[0]:
		f = Load()
		for a in f:
			if a["user"] == message.author.id and Int(select[1]):
				select[1] = int(select[1]) - 1 #Starts from 1
				await message.channel.send('Selected: ' + a["data"][select[1]]["title"] + f' **Episode: {a["episode"]+1}**')
				anime = Provider(a["data"][select[1]]["url"])
				#print(anime)
				embed = discord.Embed(
					title = a["data"][select[1]]["url"],
					url = anime[0].source().stream_url
				)
				try:await message.channel.send(embed=embed)
				except:await message.channel.send(anime[0].source().stream_url)
				Write(f)

	if message.content == 'l':
		f = Load()
		for a in f:
			if a["user"] == message.author.id:
				results = ''
				for b in range(len(a["data"])):
					results = f'{results}\n**{str(b+1)}** {str(a["data"][b]["title"])}'
				await message.channel.send(results)
			
	if episode[0]:
		f = Load()
		if Int(episode[1]):
			for a in f:
				if a['user'] == message.author.id: 
					a["episode"] = int(episode[1])+1
					Write(f)
	if message.content == 'help':
		await message.channel.send('a *anime* to search\ns *number* to select anime\ne *number* to select episode')
def Search(query):
	results = ''
	print(f'Query: {query}')
	search = Provider.search(query)
	for a in range(len(search)):
		results = f'{results}\n**{str(a+1)}** {str(search[a])}'
	print(results)
	return(results,search)


@bot.event
async def on_ready():
	#game = discord.Game("with ur mom")
	#await bot.change_presence(status=discord.Status.idle, activity=game)
	print(str(bot.user.name) + ' has connected to Discord!')

bot.run(token)
