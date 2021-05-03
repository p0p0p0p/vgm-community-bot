import discord
from fuzzywuzzy import fuzz
import requests
import csv

discord.opus.load_opus
TOKEN = 'INSERT TOKEN HERE'
SID = 1 # "Game" station
STATION = requests.get('http://rainwave.cc/api4/stations').json()['stations'][SID-1]['stream']
NUMWORDS = (('0','Zero'),('I','One'),('II','Two'),('III','Three'),('IV','Four'),('V','Five'),
            ('VI','Six'),('VII','Seven'),('VIII','Eight'),('IX','Nine'),('X','Ten'),
            ('XI','Eleven'),('XII','Twelve'),('XIII','Thirteen'),('XIV','Fourteen'),('XV','Fifteen'),
            ('XVI','Sixteen'),('XVII','Seventeen'),('XVIII','Eighteen'),('XIX','Nineteen'),('XX','Twenty'))
METADATA = 'meta.csv'

def strip(s):
    result = ""
    for c in s:
        if c.isalnum() or c.isspace(): # 0-9, a-z, spaces
            result += c.lower()
        elif c in '/\\|-~_:;,.&+':
            result += ' '
    return result

def fuzzy_match(query, target):
    if query == "": # Can match anything
        return True
    if target == "": # Error in data source
        return False
    for n in range(len(NUMWORDS)): # Series must match numeric entry exactly
        if query.endswith(' {0}'.format(n)) or query.endswith(' {0}'.format(NUMWORDS[n][0].lower())) or query.endswith(' {0}'.format(NUMWORDS[n][1].lower())):
            if not (target.endswith(' {0}'.format(n)) or target.endswith(' {0}'.format(NUMWORDS[n][0].lower())) or target.endswith(' {0}'.format(NUMWORDS[n][1].lower()))):
                if not (' {0} '.format(n) in target or ' {0} '.format(NUMWORDS[n][0].lower()) in target or ' {0} '.format(NUMWORDS[n][1].lower()) in target):
                    return False
    if fuzz.ratio(query, target) > 80: # Approximate full match
        return True

    query_tokens = query.split()
    target_tokens = target.split()
    m = len(query_tokens)
    M = len(target_tokens)
    if m > M: # Query phrase can't fit
        return False
    for offset in range(M-m+1):
        sub_match = True
        for i in range(m):
            if fuzz.ratio(query_tokens[i], target_tokens[offset+i]) < 90:
                sub_match = False
                break
        if sub_match:
            return True

    return False

def get_track_info():
    info = ""

    basic_stations = requests.post('http://rainwave.cc/api4/info_all', data={'sid': SID}).json()
    game = basic_stations['all_stations_info'][str(SID)]['album']
    song = basic_stations['all_stations_info'][str(SID)]['title']
    info += game + ' \u2014 ' + song
    
    current_songs = requests.post('http://rainwave.cc/api4/info', data={'sid': SID}).json()['sched_current']
    info += '\n' + ', '.join(artist['name'] for artist in current_songs['songs'][0]['artists'])
    info += '\nStation: <https://rainwave.cc/game>'

    game_strip = strip(game) # 0-9, a-z, spaces   
    info += query_summary('vgmgg.csv', 'B8 VGMGG', game_strip)
    info += query_summary('siiva.csv', 'Siiva VGMGG', game_strip)
    info += query_summary('vgmc.csv', 'VGMC', game_strip)
    info += query_summary('rtvgm.csv', 'RtVGM', game_strip)

    return info

def query_summary(source, label, game):
    count = 0
    game_match = ""
    with open(source, newline='') as csvref:
        csvdata = csv.reader(csvref)
        for row in csvdata:
            row0_strip = strip(row[0])
            if fuzzy_match(game, row0_strip):
                if game_match == "":
                    game_match = row[0]
                count += 1

    return '\n{1} appearance{2} in {3}{0}'.format(' (' + game_match + ')' if count > 0 else "", count, "" if count == 1 else 's', label)

def query_channel(source, label, generator, joint, game, song, max_results):
    info = ""
    count = 0
    with open(source, newline='') as csvref:
        csvdata = csv.reader(csvref)
        for row in csvdata:
            row0_strip = strip(row[0])
            row1_strip = strip(row[1])
            if joint:
                if fuzzy_match(game, row0_strip) and fuzzy_match(song, row1_strip):
                    count += 1
                    if count <= max_results:
                        info += generator(row)
            elif fuzzy_match(game, row0_strip) or fuzzy_match(game, row1_strip):
                count += 1
                if count <= max_results:
                    info += generator(row)

    if count > max_results:
        info += '\n{0} more entr{1} hidden... (PM for full results)'.format(count - max_results, 'y' if count-max_results == 1 else 'ies')
    elif count == 0:
        info = 'No {0} entries found.'.format(label)
    return info

def query_private(source, label, generator, joint, game, song):
    MAX_LENGTH = 1980 # 20-character buffer just in case
    blocks = []
    info = ""
    count = 0
    with open(source, newline='') as csvref:
        csvdata = csv.reader(csvref)
        for row in csvdata:
            row0_strip = strip(row[0])
            row1_strip = strip(row[1])
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

    update_tag = ""
    if (label == 'B8 VGMGG'):
        with open(METADATA, newline='') as csvref:
            csvdata = csv.reader(csvref)
            update_tag = " (current as of {0})".format(next(csvdata)[0])
            
    if count > 0:
        footer = '\nTOTAL RESULTS: {0}{1}'.format(count, update_tag)
        if len(info+footer) > MAX_LENGTH:
            blocks.append(info)
            info = footer
        else:
            info += footer
        blocks.append(info)
    else:
        blocks.append('No {0} entries found.{1}'.format(label, update_tag))

    return blocks

class RadioBot(discord.Client):
    async def on_ready(self):
        print('Logged in as {0} on {1}'.format(self.user, ', '.join(g.name for g in self.guilds)))

    async def on_message(self, message):
        if message.author == self.user:
            return

        command = message.content.split()
        if len(command) == 0:
            return
        command = command[0].lower()
        if not command.startswith('r.'):
            return

        if isinstance(message.channel, discord.TextChannel):
            vclient = message.guild.voice_client
            if command == 'r.join':
                vstate = message.author.voice
                if vstate and vstate.channel:
                    if vclient:
                        await vclient.move_to(vstate.channel)
                    else:
                        await vstate.channel.connect()
                        vclient = message.guild.voice_client
                        source = discord.FFmpegPCMAudio(STATION)
                        vclient.play(source)
                else:
                    await message.channel.send("You must be in a voice channel first.")
            elif command == 'r.leave':
                if vclient:
                    await vclient.disconnect()
            elif command == 'r.refresh':
                if vclient:
                    source = discord.FFmpegPCMAudio(STATION)
                    vclient.stop()
                    vclient.play(source)
                else:
                    await message.channel.send("I'm not playing anything right now, but you can use this command to restart the live connection.")
            elif command in ('r.all', 'r.b8', 'r.sv', 'r.rt'):
                tokens = message.content[len(command):].lstrip() # Discord automatically rstrips
                if tokens == "":
                    await message.channel.send("Please provide an argument in the form of Keyword, Game--Song, Game--, or --Song")
                    return

                to_split = '--' in tokens
                game = ""
                song = ""
                if to_split:
                    tokens = tokens.split('--')
                    game = strip(tokens[0])
                    song = strip(tokens[1])
                else:
                    game = strip(tokens)

                if command == 'r.all':
                    await message.channel.send(query_channel('vgmgg.csv', 'B8 VGMGG', lambda r: '\n{0} \u2014 {1} (B8 list by {2})'.format(r[0], r[1], r[2]), to_split, game, song, 4))
                    await message.channel.send(query_channel('siiva.csv', 'Siiva VGMGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), to_split, game, song, 4))
                    await message.channel.send(query_channel('vgmc.csv', 'VGMC', lambda r: '\n{0} \u2014 {1} (Best: Round {2}, Most recent: VGMC {3})'.format(r[0], r[1], r[2], r[3]), to_split, game, song, 4))
                    await message.channel.send(query_channel('rtvgm.csv', 'RtVGM', lambda r: '\n{0} \u2014 {1} (Average rating {2})'.format(r[0], r[1], r[2]), to_split, game, song, 4))
                elif command == 'r.b8':
                    await message.channel.send(query_channel('vgmgg.csv', 'B8 VGMGG', lambda r: '\n{0} \u2014 {1} (B8 list by {2})'.format(r[0], r[1], r[2]), to_split, game, song, 6))
                    await message.channel.send(query_channel('vgmc.csv', 'VGMC', lambda r: '\n{0} \u2014 {1} (Best: Round {2}, Most recent: VGMC {3})'.format(r[0], r[1], r[2], r[3]), to_split, game, song, 6))
                elif command == 'r.sv':
                    await message.channel.send(query_channel('siiva.csv', 'Siiva VGMGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), to_split, game, song, 8))
                elif command == 'r.rt':
                    await message.channel.send(query_channel('rtvgm.csv', 'RtVGM', lambda r: '\n{0} \u2014 {1} (Average rating {2})'.format(r[0], r[1], r[2]), to_split, game, song, 8))
            elif command == 'r.help':
                await message.channel.send("Commands: r.help, r.join, r.np, r.refresh, r.leave, r.b8, r.sv, r.rt, r.all")
            elif command == 'r.np':
                await message.channel.send(get_track_info())
            elif command == 'r.echo':
                await message.channel.send(message.content[len(command):].lstrip())
        else: # Private or group channel
            if command in ('r.all', 'r.b8', 'r.sv', 'r.rt'):
                tokens = message.content[len(command):].lstrip() # Discord automatically rstrips
                if tokens == "":
                    await message.channel.send("Please provide an argument in the form of Keyword, Game--Song, Game--, or --Song")
                    return

                to_split = '--' in tokens
                game = ""
                song = ""
                if to_split:
                    tokens = tokens.split('--')
                    game = strip(tokens[0])
                    song = strip(tokens[1])
                else:
                    game = strip(tokens)

                if command in ('r.all', 'r.b8'):
                    for b in query_private('vgmgg.csv', 'B8 VGMGG', lambda r: '\n{0} \u2014 {1} (B8 list by {2})'.format(r[0], r[1], r[2]), to_split, game, song):
                        await message.channel.send(b)
                if command in ('r.all', 'r.sv'):
                    for b in query_private('siiva.csv', 'Siiva VGMGG', lambda r: '\n{0} \u2014 {1} (Siiva list by {2})'.format(r[0], r[1], r[2]), to_split, game, song):
                        await message.channel.send(b)
                if command in ('r.all', 'r.b8'):
                    for b in query_private('vgmc.csv', 'VGMC', lambda r: '\n{0} \u2014 {1} (Best: Round {2}, Most recent: VGMC {3})'.format(r[0], r[1], r[2], r[3]), to_split, game, song):
                        await message.channel.send(b)
                if command in ('r.all', 'r.rt'):
                    for b in query_private('rtvgm.csv', 'RtVGM', lambda r: '\n{0} \u2014 {1} (Average rating {2})'.format(r[0], r[1], r[2]), to_split, game, song):
                        await message.channel.send(b)
            elif command == 'r.help':
                await message.channel.send("Commands: r.help, r.join, r.np, r.refresh, r.leave, r.b8, r.sv, r.rt, r.all (r.join, r.refresh, r.leave not available in private messages)")
            elif command == 'r.np':
                await message.channel.send(get_track_info())
            elif command == 'r.echo':
                await message.channel.send(message.content[len(command):].lstrip())

client = RadioBot(activity=discord.Activity(name='r.help', type=discord.ActivityType.listening))
client.run(TOKEN)
