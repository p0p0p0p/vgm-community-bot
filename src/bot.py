import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

import csv
import logging
import requests
from typing import List, Tuple

logger = logging.getLogger('vgmbot')
logger.setLevel(logging.INFO)
stderrHandler = logging.StreamHandler()
stderrHandler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
)
logger.addHandler(stderrHandler)

"""
TODO:

discord.opus.load_opus

Fix radio commands
Send responses as an embed?
Use command arguments instead of --?

SID = 1  # "Game" station
STATION = requests.get('http://rainwave.cc/api4/stations').json()['stations'][SID-1]['stream']

def get_track_info():
    info = ""

    basic_stations = requests.post('http://rainwave.cc/api4/info_all', data={'sid': SID}).json()
    game = basic_stations['all_stations_info'][str(SID)]['album']
    song = basic_stations['all_stations_info'][str(SID)]['title']
    info += game + ' \u2014 ' + song
    
    current_songs = requests.post('http://rainwave.cc/api4/info', data={'sid': SID}).json()['sched_current']
    info += '\n' + ', '.join(artist['name'] for artist in current_songs['songs'][0]['artists'])
    info += '\nStation: <https://rainwave.cc/game>'

    game_strip = title_strip(game, preserve_quotes=True) 
    info += query_summary('vgmgg.csv', 'B8 VGMGG', game_strip)
    info += query_summary('siiva.csv', 'Siiva VGMGG', game_strip)
    info += query_summary('vgmc.csv', 'VGMC', game_strip)
    info += query_summary('rtvgm.csv', 'RtVGM', game_strip)
    info += query_summary('supra.csv', 'Supra VGMGG', game_strip)

    return info

def query_summary(source, label, game):
    count = 0
    game_match = ""
    with open(source, newline='') as csvref:
        csvdata = csv.reader(csvref)
        for row in csvdata:
            row0_strip = title_strip(row[0])
            if fuzzy_match(game, row0_strip):
                if game_match == "":
                    game_match = row[0]
                count += 1

    return '\n{1} appearance{2} in {3}{0}'.format(' (' + game_match + ')' if count > 0 else "", count, "" if count == 1 else 's', label)
"""

'''
vclient = message.guild.voice_client
if command == 'r.join':
    vstate = message.author.voice
    if False: #vstate and vstate.channel:
        if vclient:
            await vclient.move_to(vstate.channel)
        else:
            await vstate.channel.connect()
            vclient = message.guild.voice_client
            source = discord.FFmpegPCMAudio(STATION)
            vclient.play(source)
    else:
        #await interaction.response.send_message("You must be in a voice channel first.")
        await interaction.response.send_message("Command is under construction!")
elif command == 'r.leave':
    if vclient:
        await vclient.disconnect()
elif command == 'r.refresh':
    if vclient:
        source = discord.FFmpegPCMAudio(STATION)
        vclient.stop()
        vclient.play(source)
    else:
        await interaction.response.send_message("I'm not playing anything right now, but you can use this command to restart the live connection.")
el'''

'''
elif TODO == 'r.np':
    await interaction.response.send_message(get_track_info())
elif TODO == 'r.echo':
    await interaction.response.send_message(message.content[len(TODO):].lstrip())
'''

'''
elif TODO == 'r.np':
    await interaction.response.send_message(get_track_info())
elif TODO == 'r.echo':
    await interaction.response.send_message(message.content[len(TODO):].lstrip
'''


NUMWORDS = (('0','Zero'),('I','One'),('II','Two'),('III','Three'),('IV','Four'),('V','Five'),
            ('VI','Six'),('VII','Seven'),('VIII','Eight'),('IX','Nine'),('X','Ten'),
            ('XI','Eleven'),('XII','Twelve'),('XIII','Thirteen'),('XIV','Fourteen'),('XV','Fifteen'),
            ('XVI','Sixteen'),('XVII','Seventeen'),('XVIII','Eighteen'),('XIX','Nineteen'),('XX','Twenty'))
with open('token.txt') as file:
    TOKEN = file.read().splitlines()[0]

def is_quoted(s):
    return len(s) > 1 and s[0] == '"' and s[-1] == '"'

def title_strip(s, preserve_quotes=False):
    result = ""
    for c in s:
        if c.isalnum() or c.isspace():  # 0-9, a-z, spaces
            result += c.lower()
        elif c in '/\\|-~_:;,.&+':
            result += ' '

    if preserve_quotes and is_quoted(s):
        result = '"' + result
        result += '"'
    return result

def fuzzy_match(query, target):
    if query == "":  # Match anything to support Game-- and --Song
        return True
    if target == "":  # Error in data source
        return False
    if is_quoted(query):
        return fuzz.ratio(query[1:-1], target) >= 98  # Require near-perfect match

    for n in range(len(NUMWORDS)):  # Series must match numeric entry exactly
        if query.endswith(' {0}'.format(n)) or query.endswith(' {0}'.format(NUMWORDS[n][0].lower())) or query.endswith(' {0}'.format(NUMWORDS[n][1].lower())):
            if not (target.endswith(' {0}'.format(n)) or target.endswith(' {0}'.format(NUMWORDS[n][0].lower())) or target.endswith(' {0}'.format(NUMWORDS[n][1].lower()))):
                # Probably not a match, but target might have a subtitle like Final Fantasy XIV: Heavensward
                if not (' {0} '.format(n) in target or ' {0} '.format(NUMWORDS[n][0].lower()) in target or ' {0} '.format(NUMWORDS[n][1].lower()) in target):
                    return False

    if fuzz.ratio(query, target) >= 80:  # Approximate full match
        return True

    query_tokens = query.split()
    target_tokens = target.split()
    m = len(query_tokens)
    M = len(target_tokens)
    if m > M:  # Query phrase can't fit
        return False
    for offset in range(M-m+1):  # Check that all words match with 90%
        sub_match = True
        for i in range(m):
            if fuzz.ratio(query_tokens[i], target_tokens[offset+i]) < 90:
                sub_match = False
                break
        if sub_match:
            return True

    return False

def query_channel(source, label, generator, joint, game, song, max_lines):
    info = ""
    count = 0
    final_match = ""
    with open(source, newline='') as csvref:
        csvdata = csv.reader(csvref)
        for row in csvdata:
            row0_strip = title_strip(row[0])
            row1_strip = title_strip(row[1])
            if joint:
                if fuzzy_match(game, row0_strip) and fuzzy_match(song, row1_strip):
                    count += 1
                    if count < max_lines:
                        info += generator(row)
                    elif count == max_lines:
                        final_match = generator(row)
            elif fuzzy_match(game, row0_strip) or fuzzy_match(game, row1_strip):
                count += 1
                if count < max_lines:
                    info += generator(row)
                elif count == max_lines:
                    final_match = generator(row)

    if count == 0:
        info = 'No {0} entries found.'.format(label)
    elif count == max_lines:
        # Add final match since it takes up about the same space as the More entries string
        info += final_match
    elif count > max_lines:
        info += '\n{0} more entries hidden... (DM for full results)'.format(count - max_lines + 1)
    return info

def query_private(source, label, generator, joint, game, song):
    MAX_LENGTH = 1980  # 20-character buffer just in case
    blocks = []
    info = ""
    count = 0
    with open(source, newline='') as csvref:
        csvdata = csv.reader(csvref)
        for row in csvdata:
            row0_strip = title_strip(row[0])
            row1_strip = title_strip(row[1])
            if joint:
                if fuzzy_match(game, row0_strip) and fuzzy_match(song, row1_strip):
                    count += 1
                    entry = generator(row)
                    if len(info+entry) > MAX_LENGTH:
                        blocks.append(info)
                        info = entry
                    else:
                        info += entry
            elif fuzzy_match(game, row0_strip) or fuzzy_match(game, row1_strip):
                count += 1
                entry = generator(row)
                if len(info+entry) > MAX_LENGTH:
                    blocks.append(info)
                    info = entry
                else:
                    info += entry
            
    if count > 0:
        footer = '\nTOTAL RESULTS: {}'.format(count)
        if len(info+footer) > MAX_LENGTH:
            blocks.append(info)
            info = footer
        else:
            info += footer
        blocks.append(info)
    else:
        blocks.append('No {} entries found.'.format(label))

    return blocks

# Must call interaction.response.send_message before it returns
async def tokenize_query(interaction: discord.Interaction, query: str, use_artist = False) -> Tuple[bool, str, str]:
    query = query.lstrip()  # Discord automatically rstrips
    if query == "" or all(not(c.isalnum()) for c in query):
        if use_artist:
            await interaction.response.send_message('Search using Keyword, Artist--Song, "Exact Artist"--"Exact Song", Artist--, or --Song')
        else:
            await interaction.response.send_message('Search using Keyword, Game--Song, "Exact Game"--"Exact Song", Game--, or --Song')
        return False, None, None

    do_split = '--' in query
    game = ""
    song = ""
    if do_split:
        tokens = query.split('--')
        game = title_strip(tokens[0], preserve_quotes=True)
        song = title_strip(tokens[1], preserve_quotes=True)
        await interaction.response.send_message(f"Searching for game with song: {query}")
    else:
        game = title_strip(query, preserve_quotes=True)
        await interaction.response.send_message(f"Searching for song or game: {game}")

    return do_split, game, song

def query_helper(server: str, do_split: bool, game: str, song: str, private: bool) -> List[str]:
    results = []
    if private:        
        if server in ('all', 'b8'):
            for b in query_private('vgmgg.csv', 'B8 VGMGG', lambda r: '\n{0} \u2014 {1} (B8 list by {2})'.format(r[0], r[1], r[2]), do_split, game, song):
                results.append(b)
        if server in ('all', 'b8', 'v8'):
            # Always include composers
            for b in query_private('vgmc.csv', 'VGMC', lambda r: '\n{0} \u2014 {1} [{2}] (VGMCs: {3})'.format(r[0], r[1], r[2], r[3]), do_split, game, song):
                results.append(b)
        if server in ('all', 'sv'):
            for b in query_private('siiva.csv', 'Siiva VGMGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), do_split, game, song):
                results.append(b)
        if server in ('all', 'rt'):
            for b in query_private('rtvgm.csv', 'RtVGM', lambda r: '\n{0} \u2014 {1} (Average {3}, {2} votes)'.format(r[0], r[1], r[2], r[3]), do_split, game, song):
                results.append(b)
        if server in ('all', 'sd'):
            for b in query_private('supra.csv', 'Supra VGMGG', lambda r: '\n{0} \u2014 {1} (Supra list by {2})'.format(r[0], r[1], r[2]), do_split, game, song):
                results.append(b)
        if server == 'mg':
            for b in query_private('mgg.csv', 'Siiva MGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), do_split, game, song):
                results.append(b)
    else:
        vgmc_default = lambda r: '\n{0} \u2014 {1} (VGMCs: {3})'.format(r[0], r[1], r[2], r[3])
        vgmc_composers = lambda r: '\n{0} \u2014 {1} [{2}] (VGMCs: {3})'.format(r[0], r[1], r[2], r[3])
        if server == 'all':  # Limit to 3 lines each
            results.append(query_channel('vgmgg.csv', 'B8 VGMGG', lambda r: '\n{0} \u2014 {1} (B8 list by {2})'.format(r[0], r[1], r[2]), do_split, game, song, 3))
            results.append(query_channel('vgmc.csv', 'VGMC', vgmc_default, do_split, game, song, 3))
            results.append(query_channel('siiva.csv', 'Siiva VGMGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), do_split, game, song, 3))
            results.append(query_channel('rtvgm.csv', 'RtVGM', lambda r: '\n{0} \u2014 {1} (Average {3}, {2} votes)'.format(r[0], r[1], r[2], r[3]), do_split, game, song, 3))
            results.append(query_channel('supra.csv', 'Supra VGMGG', lambda r: '\n{0} \u2014 {1} (Supra list by {2})'.format(r[0], r[1], r[2]), do_split, game, song, 3))
        elif server == 'b8':
            results.append(query_channel('vgmgg.csv', 'B8 VGMGG', lambda r: '\n{0} \u2014 {1} (B8 list by {2})'.format(r[0], r[1], r[2]), do_split, game, song, 6))
            results.append(query_channel('vgmc.csv', 'VGMC', vgmc_default, do_split, game, song, 6))
        elif server == 'v8':
            results.append(query_channel('vgmc.csv', 'VGMC', vgmc_composers, do_split, game, song, 10))
        elif server == 'sv':
            results.append(query_channel('siiva.csv', 'Siiva VGMGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), do_split, game, song, 12))
        elif server == 'rt':
            results.append(query_channel('rtvgm.csv', 'RtVGM', lambda r: '\n{0} \u2014 {1} (Average {3}, {2} votes)'.format(r[0], r[1], r[2], r[3]), do_split, game, song, 12))
        elif server == 'sd':
            results.append(query_channel('supra.csv', 'Supra VGMGG', lambda r: '\n{0} \u2014 {1} (Supra list by {2})'.format(r[0], r[1], r[2]), do_split, game, song, 12))
        elif server == 'mg':
            results.append(query_channel('mgg.csv', 'Siiva MGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), do_split, game, song, 12))
    
    return results

class VGMBot(commands.Bot):
    async def setup_hook(self) -> None:
        # Dev only #
        # self.tree.copy_global_to(guild=discord.Object(id=655102875214807050))
        # await self.tree.sync(guild=discord.Object(id=655102875214807050))
        # Dev only #
        synced_commands = await self.tree.sync()
        logger.info(f'Synced commands: {synced_commands}')

    async def on_ready(self):
        logger.info('Logged in as {0} on {1}'.format(self.user, ', '.join(g.name for g in self.guilds)))

    # Migration period only - see command_prefix #
    async def on_message(self, message):
        if message.author == self.user:
            return

        command = message.content.split()
        if len(command) == 0:
            return
        command = command[0].lower()
        if not command.startswith('r.'):
            return

        for cmd in ('r.join', 'r.leave', 'r.refresh', 'r.np', 'r.help', 'r.all', 'r.b8', 'r.v8', 'r.sv', 'r.rt', 'r.sd', 'r.mg', 'r.src', 'r.echo'):
            if command == cmd:
                await message.channel.send(
                    "This bot now uses slash commands! Try /help or /b8search\n"
                    "Help: /help, /sources\n"
                    "Data search: /b8search, /v8search, /svsearch, /rtsearch, /sdsearch, /allsearch, /mgsearch"
                )
                return
    # Migration period only - see command_prefix #

intentsWithMessageContent = discord.Intents.default()
intentsWithMessageContent.message_content = True
# Disable spammy events we don't need
intentsWithMessageContent.expressions = False
intentsWithMessageContent.reactions = False  # Could enable for reaction-based commands
intentsWithMessageContent.typing = False
bot = VGMBot(command_prefix="r.", intents=intentsWithMessageContent, activity=discord.Activity(name='j.help, /help', type=discord.ActivityType.listening))

@bot.tree.command(name="allsearch", description="All VGMGG history")
async def _allsearch(interaction: discord.Interaction, *, query: str) -> None:
    do_split, game, song = await tokenize_query(interaction, query)
    if game is None:
        return

    is_private = isinstance(interaction.channel, discord.abc.PrivateChannel)
    results = query_helper('all', do_split, game, song, is_private)
    for r in results:
        await interaction.followup.send(r)
    if is_private:
        await interaction.followup.send(":warning: Use `/sources` to check how out-of-date these results are")

@bot.tree.command(name="b8search", description="Board 8 VGMGG & VGMC history")
async def _b8search(interaction: discord.Interaction, *, query: str) -> None:
    do_split, game, song = await tokenize_query(interaction, query)
    if game is None:
        return

    is_private = isinstance(interaction.channel, discord.abc.PrivateChannel)
    results = query_helper('b8', do_split, game, song, is_private)
    for r in results:
        await interaction.followup.send(r)
    if is_private:
        await interaction.followup.send(":warning: Use `/sources` to check how out-of-date these results are")

@bot.tree.command(name="v8search", description="Board 8 VGMC history")
async def _v8search(interaction: discord.Interaction, *, query: str) -> None:
    do_split, game, song = await tokenize_query(interaction, query)
    if game is None:
        return

    is_private = isinstance(interaction.channel, discord.abc.PrivateChannel)
    results = query_helper('v8', do_split, game, song, is_private)
    for r in results:
        await interaction.followup.send(r)
    if is_private:
        await interaction.followup.send(":warning: Use `/sources` to check how out-of-date these results are")

@bot.tree.command(name="svsearch", description="Siiva VGMGG history")
async def _svsearch(interaction: discord.Interaction, *, query: str) -> None:
    do_split, game, song = await tokenize_query(interaction, query)
    if game is None:
        return

    is_private = isinstance(interaction.channel, discord.abc.PrivateChannel)
    results = query_helper('sv', do_split, game, song, is_private)
    for r in results:
        await interaction.followup.send(r)
    if is_private:
        await interaction.followup.send(":warning: Use `/sources` to check how out-of-date these results are")

@bot.tree.command(name="sdsearch", description="SupraDarky VGMGG history")
async def _sdsearch(interaction: discord.Interaction, *, query: str) -> None:
    do_split, game, song = await tokenize_query(interaction, query)
    if game is None:
        return

    is_private = isinstance(interaction.channel, discord.abc.PrivateChannel)
    results = query_helper('sd', do_split, game, song, is_private)
    for r in results:
        await interaction.followup.send(r)
    if is_private:
        await interaction.followup.send(":warning: Use `/sources` to check how out-of-date these results are")

@bot.tree.command(name="rtsearch", description="RtVGM history")
async def _rtsearch(interaction: discord.Interaction, *, query: str) -> None:
    do_split, game, song = await tokenize_query(interaction, query)
    if game is None:
        return

    is_private = isinstance(interaction.channel, discord.abc.PrivateChannel)
    results = query_helper('rt', do_split, game, song, is_private)
    for r in results:
        await interaction.followup.send(r)
    if is_private:
        await interaction.followup.send(":warning: Use `/sources` to check how out-of-date these results are")

@bot.tree.command(name="mgsearch", description="Siiva MGG history")
async def _mgsearch(interaction: discord.Interaction, *, query: str) -> None:
    do_split, game, song = await tokenize_query(interaction, query, True)
    if game is None:
        return

    is_private = isinstance(interaction.channel, discord.abc.PrivateChannel)
    results = query_helper('mg', do_split, game, song, is_private)
    for r in results:
        await interaction.followup.send(r)
    if is_private:
        await interaction.followup.send(":warning: Use `/sources` to check how out-of-date these results are")

@bot.tree.command(name="sources", description="VGMGG data sources")
async def _sources(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Check Pastebins for up-to-date data, bot's local data is current up to: (mm/dd/yyyy)")
    info = ""
    with open("sources.csv", newline='') as csvref:
        csvdata = csv.reader(csvref)
        for row in csvdata:
            pastebin = ""
            if row[2]:
                pastebin = "- <{}>".format(row[2])
            info += '{0}: {1} {2}\n'.format(row[0], row[1], pastebin)
    await interaction.followup.send(info)

@bot.tree.command(name="help", description="List of VGMGG history commands")
async def _help(interaction: discord.Interaction) -> None:
    if isinstance(interaction.channel, discord.abc.PrivateChannel):
        await interaction.response.send_message(
            "Maintained by haha_oh_no a.k.a. PIayer_0\n"
            "Help: /help, /sources\n"
            "Data search: /b8search, /v8search, /svsearch, /rtsearch, /sdsearch, /allsearch, /mgsearch (use with ? as the query for more help)\n"
            "Radio (under maintenance, not available in DMs): /join, /refresh, /leave, /np")
    else:
        await interaction.response.send_message(
            "Maintained by haha_oh_no a.k.a. PIayer_0\n"
            "You can DM me commands too, try it!\n"
            "Help: /help, /sources\n"
            "Data search: /b8search, /v8search, /svsearch, /rtsearch, /sdsearch, /allsearch, /mgsearch (use with ? as the query for more help)\n"
            "Radio (under maintenance): /join, /refresh, /leave, /np")

bot.run(TOKEN)
