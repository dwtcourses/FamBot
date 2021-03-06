#!/usr/bin/python3

import os
from discordUtils import debug, fetchFile
from sqlalchemy import create_engine, update, select, MetaData, Table, Column, Integer, String 

DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))

blacklistLow = {"jap"}
blacklistStrict = {"xxx"}
	
def helper(message):
	args = message.content.split()
	operator = args[1].lower()
	return {
		'get': lambda: getFilter(message.channel.id),
		'set': lambda: insertFilter(message.channel.id, args[2]),
		'clear': lambda: insertFilter(message.channel.id, 0),
		'clearall': lambda: reset(),
		'help': lambda: get_help(),
		'add': lambda: addWord(args[2], args[3:]),
	}.get(operator, lambda: None)()

def getHelp():
	return fetchFile('help', 'filters')

def check(message):
	text = message.content.split()
	fLevel = getFilter(message.channel.id)
	lists = {'2': (blacklistStrict), '1': (blacklistLow)}
	if fLevel in lists:
		for word in text:
			if word in lists[fLevel]:
				return True #Message contains blocked word
	return False #Message is clean or no filter set for channel

def importBlacklists():
	listOfFiles_low = list()
	listOfFiles_high = list()
	for (dirpath, dirnames, filenames) in os.walk(DEFAULT_DIR+'/docs/blacklists'):
		if 'low' in dirpath:
			listOfFiles_low += [os.path.join(dirpath, file_) for file_ in filenames]
		elif 'strict' in dirpath:
			listOfFiles_high += [os.path.join(dirpath, file_) for file_ in filenames]
	
	for file_ in listOfFiles_low:
		with open(file_, 'r') as f:
			for line in f:
				blacklistLow.add(line.strip())
				blacklistStrict.add(line.strip())
	for file_ in listOfFiles_high:
		with open(file_, 'r') as f:
			for line in f:
				blacklistStrict.add(line.strip())
	blacklistStrict.remove('')
	print("[+] Imported Filter Blacklists")

def addWord(level, word):
	fileDict = {
		'1': DEFAULT_DIR+'/docs/blacklists/low/blacklist_custom.txt',
		'2': DEFAULT_DIR+'/docs/blacklists/strict/blacklist_custom.txt',
		}
	path = fileDict.get(level, None)
	word = ' '.join(word)
	if path:
		with open(path, 'a') as f:
			f.write(word)
			print("[+] Added {} to level {} custom filters".format(word, level))
			return "Success, added: `{}` to Filter level {}".format(word, level)
	return "Error"

def setup():
	global engine, meta, Filters
	engine = create_engine('sqlite:///./log/quotes.db', echo = False)
	meta = MetaData()
	Filters = Table(
		'filters', meta,
		Column('id', Integer, primary_key = True),
		Column('level', Integer),
		)
	meta.create_all(engine)
	print('[+] End filters Setup')
	
def insertFilter(id_, level):
	conn = engine.connect()
	if getFilter(id_):
		ins = Filters.update().where(Filters.c.id==id_).values(level=level)	
	else:
		ins = Filters.insert().values(id = id_, level = level,)
	conn.execute(ins)
	return "Set filter for current channel to {}".format(level)

def getFilter(id_):
	select_st = select([Filters]).where(
		Filters.c.id == id_)
	conn = engine.connect()	
	res = conn.execute(select_st)
	result = res.fetchone()
	if result:
		return result[1]
	return None

def reset():
	conn = engine.connect()
	query = Filters.drop(engine)
	setup()
	print("[!] TABLE filters RESET")

setup()
