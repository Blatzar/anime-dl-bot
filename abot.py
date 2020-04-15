import discord
from discord.ext import commands
import time
import json
from anime_downloader.sites import get_anime_class

try:
	import testkeys 
	testkey = testkeys.token() 
	token = testkey.anime 
except:
	token = ''

Provider = get_anime_class('animeflix')
bot = commands.Bot(command_prefix='')
path = '/home/ec2-user/keep/anime.json' #stores all user search

def Int(number): #Can it be converted to int
	try:
		number = int(number)
		return(True)
	except:
		return(False)

def Write(f, path = path):
	f = str(f).replace("'",'"')
	#print(f)
	_file = open(path, "w")
	_file.write(f)
	_file.close()

def Load(path = path): #All user info in anime.json
	f = json.loads(open(path).read())
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

def Message(message,prefix): #0 is True/False, 1 is the string after
	return [message.content[:len(prefix)] == prefix and len(message.content) > len(prefix),message.content[len(prefix):]]

@bot.event
async def on_message(message):
	
	search = Message(message,'a ')
	select = Message(message,'s ')
	episode = Message(message,'e ')
	
	#search
	if search[0]:
		print(search[1])
		results,results_list = Search(search[1])
		f = Load()
		[f.remove(a) for a in f if a['user'] == message.author.id]
		f.append({
			"user":message.author.id,
			"select":{"url":"","title":""},
			"episode":0,
			"data":[{"url":a.url,"title":a.title} for a in results_list]
			})
		Write(f)
		await message.channel.send(results)
	
	#select
	if select[0]:
		f = Load()
		for a in f:
			if a["user"] == message.author.id and Int(select[1]):
				select[1] = int(select[1]) - 1 #Starts from 1
				await message.channel.send('Selected: ' + a["data"][select[1]]["title"] + f' - **Episode: {a["episode"]+1}**')
				a["select"]["url"],a["select"]["title"] = a["data"][select[1]]["url"],a["data"][select[1]]["title"]
				Write(f)
				try:
					anime = Provider(a["data"][select[1]]["url"])
					embed = discord.Embed(
						title = a["data"][select[1]]["title"]+f' - Episode {a["episode"]+1}/{len(anime)}',
						url = anime[a["episode"]].source().stream_url
					)
				except:
					await message.channel.send('Error selecting episode')
				try:await message.channel.send(embed=embed)
				except:await message.channel.send(anime[a["episode"]].source().stream_url)
	#list
	if message.content == 'l':
		f = Load()
		for a in f:
			if a["user"] == message.author.id:
				results = '```'
				for b in range(len(a["data"])):
					results = f'{results}\n{str(a["data"][b]["title"])}'
				results += '```'
				await message.channel.send(results)
	#change episode	
	if episode[0]:
		f = Load()
		if Int(episode[1]):
			for a in f:
				if a['user'] == message.author.id: 
					a["episode"] = int(episode[1])-1
					Write(f)
					await message.channel.send(f'Selected episode {episode[1]}')
					try:
						anime = Provider(a["select"]["url"])
						embed = discord.Embed(
						title = a["select"]["title"]+f' - Episode {a["episode"]+1}/{len(anime)}',
						url = anime[a["episode"]].source().stream_url
						)
					except:
						await message.channel.send('Error selecting episode')
					try:await message.channel.send(embed=embed)
					except:await message.channel.send(anime[a["episode"]].source().stream_url)

	if message.content == 'help':
		await message.channel.send('a *anime* to search\ns *number* to select anime\ne *number* to select episode\nl to list search')
def Search(query):
	results = '```'
	print(f'Query: {query}')
	search = Provider.search(query)
	for a in range(len(search)):
		results = f'{results}\n{str(search[a])}'
	results += '```'
	print(results)
	return(results,search)


@bot.event
async def on_ready():
	#game = discord.Game("with ur mom")
	#await bot.change_presence(status=discord.Status.idle, activity=game)
	print(str(bot.user.name) + ' has connected to Discord!')

bot.run(token)
