import discord
import mysql.connector as mariadb
import random
from datetime import datetime
import os
import threading


def lookForUser():

    cursor.execute(look % author)
    if cursor.fetchone()[0]:
        return 1
    else:
        return 0


def getMsges():
    cursor.execute(getAmountOfMsg % author)
    return cursor.fetchone()[0]


def updateMsges():
    if lookForUser():
        cursor.execute(updateMsg % (getMsges()+1, author))
        if(username != getUsername()):
            cursor.execute(updateUserTag % (username, author))
        if(pic_url != getPicUrl()):
            cursor.execute(updateAvatarUrl % (pic_url, author))
    else:
        cursor.execute(insert % (author, 1, 0, 100, 0, username, 0, pic_url))  # Starting values for the database

    mariadb_connection.commit()
    addRanks()


def updateXP(msgLen):
    random.seed(datetime.now())
    try:
        cursor.execute(updateExp % (getXp()+random.randint(1, deteriorateXp(msgLen)), author))
    except ValueError:
        cursor.execute(updateExp % (getXp()+random.randint(1, 15), author))

    mariadb_connection.commit()

    if checkForLvlUp():
        cursor.execute(updateExp % (getXp()-getMaxXp(), author))
        cursor.execute(updateLevel % (getLvl()+1, author))
        maxXp = getMaxXp()
        cursor.execute(updateMaxExp % (maxXp+25, author))

        mariadb_connection.commit()


def getXp():
    cursor.execute(getAmountOfXP % author)
    return cursor.fetchone()[0]


def deteriorateXp(msgLen):
    if msgLen <= 5:
        return msgLen
    elif msgLen <= 30:
        return int(msgLen/2)
    elif msgLen <= 100:
        return int(msgLen/3)
    elif msgLen <= 500:
        return int(msgLen/5)
    else:
        return int(msgLen/10)


def checkForLvlUp():
    if getXp() >= getMaxXp():
        return 1
    else:
        return 0


def getLvl():
    cursor.execute(getLevel % author)
    return cursor.fetchone()[0]


def getMaxXp():
    cursor.execute(getMaxExp % author)
    return cursor.fetchone()[0]


def getUsername():
    cursor.execute(getUserTag % author)
    return cursor.fetchone()[0]


def addRanks():
    cursor.execute("SELECT user_id FROM levels_table ORDER BY level DESC, exp DESC, msges_sent DESC")
    result = cursor.fetchall()
    for b, x in enumerate(result):
        for t in x:
            cursor.execute("UPDATE levels_table SET rank = %s WHERE user_id = '%s'" % (b+1, t))
    mariadb_connection.commit()


def getPicUrl():
    cursor.execute(getAvatarUrl % author)
    return cursor.fetchone()[0]


def backupDatabase():
    os.system('mysqldump -u %s -p%s %s > backup.sql' % (user, password, database))
    print("Backup done")
    timer = threading.Timer(120.0, backupDatabase)
    timer.start()



look = "SELECT COUNT(1) user_id FROM levels_table WHERE user_id = '%s'"
insert = "INSERT INTO levels_table (user_id, msges_sent, exp, maxXp, level, username, rank, user_avatar_url) VALUES ('%s', %s, %s, %s, %s, '%s', %s, '%s')"
getAmountOfMsg = "SELECT msges_sent FROM levels_table WHERE user_id = '%s'"
updateMsg = "UPDATE levels_table SET  msges_sent = %s WHERE user_id = '%s'"
printLevel = "SELECT * FROM levels_table WHERE user_id = '%s'"
getAmountOfXP = "SELECT exp FROM levels_table WHERE user_id = '%s'"
updateExp = "UPDATE levels_table SET exp = %s WHERE user_id = '%s'"
getLevel = "SELECT level FROM levels_table WHERE user_id = '%s'"
updateLevel = "UPDATE levels_table SET level = %s WHERE user_id = '%s'"
getMaxExp = "SELECT maxXp FROM levels_table WHERE user_id = '%s'"
updateMaxExp = "UPDATE levels_table SET maxXp = %s WHERE user_id = '%s'"
getUserTag = "SELECT username FROM levels_table WHERE user_id = '%s'"
updateUserTag = "UPDATE levels_table SET username = '%s' WHERE user_id = '%s'"
getAvatarUrl = "SELECT user_avatar_url FROM levels_table WHERE user_id = '%s'"
updateAvatarUrl = "UPDATE levels_table SET user_avatar_url = '%s' WHERE user_id = '%s'"
user = 'root'
password = 'root'
database = 'test'

try:
    mariadb_connection = mariadb.connect(
        host='localhost',
        user=user,
        password=password,
        database=database
    )

except mariadb.errors.ProgrammingError:
    mariadb_connection = mariadb.connect(
        host='localhost',
        user=user,
        password=password
    )
    cursor = mariadb_connection.cursor()
    cursor.execute("CREATE DATABASE %s" % database)

    mariadb_connection = mariadb.connect(
        host='localhost',
        user=user,
        password=password,
        database=database
    )
    os.system('mysql -u %s -p%s %s < backup.sql' % (user, password, database))


cursor = mariadb_connection.cursor()
cursor = mariadb_connection.cursor(buffered=True)
token = "NzAzMzM1Mjg0MjEzMDIyODEy.XqNyJg.mIJcZ0Hf1upT3QJfQQe4CF9jl7w"

client = discord.Client()
id = client.get_guild(548520910764769280)

timer = threading.Timer(69.0, backupDatabase)
timer.start()


@client.event
async def on_message(message):
    global author
    global username
    global pic_url
    author = message.author.id
    try:
        pic_url = str(message.author.avatar_url)
    except TypeError:
        print("errors")
        pic_url = "error lol"

    username = str(message.author)
    try:
        old_level = getLvl()
    except TypeError:
        old_level = 0
    updateMsges()
    updateXP(len(message.content))
    new_lvl = getLvl()
    if old_level != new_lvl:
        await message.channel.send("%s leveld up to %s" % ("<@"+str(author)+">", new_lvl))


    if message.author != client.user:
#
#
#
        if message.content.startswith('!scoreboard'):
            cursor.execute("SELECT * FROM levels_table ORDER BY level DESC, exp DESC, msges_sent DESC")
            embed = discord.Embed(title="!scoreboard", description="shows the top 5 users", color=random.randint(0, 0xFFFFFF))
            result = cursor.fetchall()
            for b, x in enumerate(result):
                if b == 5:
                    break
                list_result = []
                for t in x:
                    list_result.append(t)
                embed.add_field(name=list_result[5], value="rank - %s l‎evel - %s xp - %s/%s" % ("#"+str(list_result[6]), str(list_result[4]), str(list_result[2]), str(list_result[3])), inline=False)
            await message.channel.send(embed=embed)
#
#
#
        if message.content.startswith('!level'):

            if message.content == '!level':
                cursor.execute(printLevel % message.author.id)

            else:
                cursor.execute("SELECT username FROM levels_table")
                result = cursor.fetchall()
                try:
                    for b in result:
                        for t in b:
                            if t in str(message.mentions[0]):
                                cursor.execute("SELECT * FROM levels_table WHERE username = '%s'" % t)
                except IndexError:
                    error = discord.Embed(title="IndexError", description="Invalid username", color=0xda000f)
                    error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.)")
                    await message.channel.send(embed=error)
                    return 0

            result = cursor.fetchall()
            list_result = []
            try:
                for i in result:
                    for t in i:
                        list_result.append(t)
                list_result[0] = "<@" + list_result[0] + ">"
                embed = discord.Embed(title="!level", description="Shows level info‏‏‎‎", color=random.randint(0, 0xFFFFFF))
                embed.set_author(name=list_result[5])
                embed.set_thumbnail(url=list_result[7])
                embed.add_field(name="rank‏‏‎ ‎‏‏‎ ‎", value="#"+str(list_result[6]), inline=True)
                embed.add_field(name="lvl", value=list_result[4], inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="msgs‏‏‎ ‎‏‏‎ ‎", value=list_result[1], inline=True)
                embed.add_field(name="exp", value=str(list_result[2])+"/"+str(list_result[3]), inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.set_footer(text=list_result[0])
            except IndexError:
                error = discord.Embed(title="IndexError", description="User doesn't exist in levels_table", color=0xda000f)
                error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.")
                await message.channel.send(embed=error)
                return 0

            try:
                await message.channel.send(embed=embed)
            except discord.errors.HTTPException or IndexError or UnboundLocalError:
                error = discord.Embed(title="discord.errors.HTTPException: 400 Bad Request (error code: 50035)", description="Unsupported url type ", color=0xda000f)
                error.set_footer(text="Invalid Form Body In embed.thumbnail.url: Not a well formed URL.")
                await message.channel.send(embed=error)

                embed = discord.Embed(title="!level", description="Shows level info‏‏‎‎", color=random.randint(0, 0xFFFFFF))
                embed.set_author(name=list_result[5])
                embed.add_field(name="rank‏‏‎ ‎‏‏‎ ‎", value="#"+str(list_result[6]), inline=True)
                embed.add_field(name="lvl", value=list_result[4], inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="msgs‏‏‎ ‎‏‏‎ ‎", value=list_result[1], inline=True)
                embed.add_field(name="exp", value=str(list_result[2])+"/"+str(list_result[3]), inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.set_footer(text=list_result[0])
                try:
                    await message.channel.send(embed=embed)
                except IndexError:
                    error = discord.Embed(title="IndexError", description="User doesn't exist in the databe", color=0xda000f)
                    error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.)")
                    await message.channel.send(embed=error)
#
#
#
#
#
        if message.content.startswith('!add'):
            if getattr(message.author.guild_permissions, "administrator"):
                list_result = message.content.split()
                if len(list_result) == 4:
                    try:
                        int(list_result[1])
                    except ValueError:
                        error = discord.Embed(title="Invalid parameter %s" % list_result[1], description="Must be a whole positive integer", color=0xda000f)
                        error.set_footer(text="!add <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return 0

                    valid_categories = ('exp', 'level')

                    if list_result[2] not in valid_categories:
                        error = discord.Embed(title="Invalid parameter %s" % list_result[2], description="Must be 'level' or 'exp'", color=0xda000f)
                        error.set_footer(text="!add <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return 0
                    try:
                        message.mentions[0]
                    except IndexError:
                        error = discord.Embed(title="Invalid parameter %s" % list_result[3], description="Must be a mention. \n ps: you can't copy mentions", color=0xda000f)
                        error.set_footer(text="!add <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return 0


                    cursor.execute("SELECT username from levels_table")
                    result = cursor.fetchall()
                    try:
                        for b in result:
                            for t in b:
                                if t in str(message.mentions[0]):
                                    cursor.execute("SELECT user_id FROM levels_table WHERE username = '%s'" % str(t))
                                    res = cursor.fetchone()
                                    for a in res:
                                        list_result[3] = a
                    except IndexError:
                        error = discord.Embed(title="IndexError", description="Invalid username", color=0xda000f)
                        error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.)")
                        await message.channel.send(embed=error)
                        return 0

                    cursor.execute("SELECT %s FROM levels_table WHERE user_id = '%s'" % (list_result[2], list_result[3]))
                    res = cursor.fetchone()
                    for a in res:
                        list_result[0] = int(list_result[1])+a # From command name list_result switches to updated amount
                    if list_result[2] == 'level':
                        cursor.execute("UPDATE levels_table SET %s = %s WHERE user_id = '%s'" % (list_result[2], list_result[0], list_result[3]))
                        mariadb_connection.commit()
                        cursor.execute(getMaxExp % list_result[3])

                        b = cursor.fetchone()[0]
                        for i in range(0, int(list_result[1])):
                            b += 25
                        cursor.execute("UPDATE levels_table SET maxXp = %s WHERE user_id = '%s'" % (b, list_result[3]))

                    elif list_result[2] == 'exp':
                        cursor.execute(getMaxExp % list_result[3])
                        b = cursor.fetchone()[0]
                        added_lvls = 0
                        while list_result[0] >= b:
                            list_result[0] -= b
                            b+=25
                            added_lvls += 1
                        cursor.execute("UPDATE levels_table SET maxXp = %s WHERE user_id = '%s'" % (b, list_result[3]))
                        cursor.execute("UPDATE levels_table SET exp = %s WHERE user_id = '%s'" % (list_result[0], list_result[3]))
                        cursor.execute("SELECT level FROM levels_table WHERE user_id = '%s'" % list_result[3])
                        current_level = cursor.fetchone()[0]
                        cursor.execute("UPDATE levels_table SET level = %s WHERE user_id = '%s'" % (current_level+added_lvls, list_result[3]))

                    mariadb_connection.commit()

                    await message.channel.send("added %s %s to <@%s>" % (list_result[2], list_result[1], list_result[3]))
                else:
                    if len(list_result) < 4:
                        error = discord.Embed(title="Not enough parameters", description="'!add' command needs 3 parameters", color=0xda000f)
                    else:
                        error = discord.Embed(title="Too many parameters", description="'!add' command needs 3 parameters", color=0xda000f)
                    error.set_footer(text="!add <number> <category> <@person>")
                    await message.channel.send(embed=error)
                    return 0
            else:
                error = discord.Embed(title="Invalid permissions", description="Only administrators have access to this command", color=0xda000f)
                error.set_footer(text="!add <number> <category> <@person>")
                await message.channel.send(embed=error)
                return 0
#
#
#
        if message.content.startswith('!remove'):
            if getattr(message.author.guild_permissions, "administrator"):
                list_result = message.content.split()
                if len(list_result) == 4:
                    try:
                        int(list_result[1])
                    except ValueError:
                        error = discord.Embed(title="Invalid parameter %s" % list_result[1], description="Must be a whole positive integer", color=0xda000f)
                        error.set_footer(text="!remove <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return 0

                    valid_categories = ('exp', 'level')

                    if list_result[2] not in valid_categories:
                        error = discord.Embed(title="Invalid parameter %s" % list_result[2], description="Must be 'level' or 'exp'", color=0xda000f)
                        error.set_footer(text="!remove <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return 0
                    try:
                        message.mentions[0]
                    except IndexError:
                        error = discord.Embed(title="Invalid parameter %s" % list_result[3], description="Must be a mention. \n ps: you can't copy mentions", color=0xda000f)
                        error.set_footer(text="!remove <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return 0

                    cursor.execute("SELECT username from levels_table")
                    result = cursor.fetchall()
                    try:
                        for b in result:
                            for t in b:
                                if t in str(message.mentions[0]):
                                    cursor.execute("SELECT user_id FROM levels_table WHERE username = '%s'" % str(t))
                                    res = cursor.fetchone()
                                    for a in res:
                                        list_result[3] = a
                    except IndexError:
                        error = discord.Embed(title="IndexError", description="Invalid username", color=0xda000f)
                        error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.)")
                        await message.channel.send(embed=error)
                        return 0

                    cursor.execute("SELECT %s FROM levels_table WHERE user_id = '%s'" % (list_result[2], list_result[3]))
                    res = cursor.fetchone()
                    for a in res:
                        list_result[0] = a - int(list_result[1]) # From command name list_result switches to updated amount
                        if list_result[0] < 0:
                            list_result[0] = 0

                    if list_result[2] == 'level':
                        cursor.execute("UPDATE levels_table SET %s = %s WHERE user_id = '%s'" % (list_result[2], list_result[0], list_result[3]))
                        mariadb_connection.commit()
                        cursor.execute(getMaxExp % list_result[3])

                        b = cursor.fetchone()[0]
                        for i in range(0, int(list_result[1])):
                            if b<100:
                                b = 100
                                break
                            b -= 25
                        cursor.execute("UPDATE levels_table SET maxXp = %s WHERE user_id = '%s'" % (b, list_result[3]))

                        cursor.execute("SELECT exp FROM levels_table WHERE user_id = '%s'" % list_result[3])
                        result = cursor.fetchone()[0]
                        if result > b:
                            cursor.execute("UPDATE levels_table SET exp = 0 WHERE user_id = '%s'" % list_result[3])

                    elif list_result[2] == 'exp':
                        cursor.execute("UPDATE levels_table SET exp = %s WHERE user_id = '%s'" % (list_result[0], list_result[3]))

                    mariadb_connection.commit()

                    await message.channel.send("removed %s %s from <@%s>" % (list_result[1], list_result[2], list_result[3]))
                else:
                    if len(list_result) < 4:
                        error = discord.Embed(title="Not enough parameters", description="'!add' command needs 3 parameters", color=0xda000f)
                    else:
                        error = discord.Embed(title="Too many parameters", description="'!add' command needs 3 parameters", color=0xda000f)
                    error.set_footer(text="!remove <number> <category> <@person>")
                    await message.channel.send(embed=error)
                    return 0
            else:
                error = discord.Embed(title="Invalid permissions", description="Only administrators have access to this command", color=0xda000f)
                error.set_footer(text="!add <number> <category> <@person>")
                await message.channel.send(embed=error)
                return 0
#
#
#
        if message.content.startswith("!clear"):
            if getattr(message.author.guild_permissions, "administrator"):
                list_result = message.content.split()
                if len(list_result) == 3:
                    valid_categories = ['exp', 'level', 'msges', 'all']
                    if list_result[1] in valid_categories:
                        try:
                            message.mentions[0]
                        except IndexError:
                            error = discord.Embed(title="Invalid parameter %s" % list_result[2], description="Must be a mention. \n ps: you can't copy mentions", color=0xda000f)
                            error.set_footer(text="!clear <category> <@mention>")
                            await message.channel.send(embed=error)
                            return 0

                        cursor.execute("SELECT username from levels_table")
                        result = cursor.fetchall()

                        try:
                            for b in result:
                                for t in b:
                                    if t in str(message.mentions[0]):
                                        cursor.execute("SELECT user_id FROM levels_table WHERE username = '%s'" % str(t))
                                        res = cursor.fetchone()
                                        for a in res:
                                            list_result[2] = int(a)
                        except IndexError:
                            error = discord.Embed(title="IndexError", description="Invalid username", color=0xda000f)
                            error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.)")
                            await message.channel.send(embed=error)
                            return 0
                        print(list_result)
                        if list_result[1] == 'level':
                            cursor.execute("UPDATE levels_table SET %s = 0 WHERE user_id = '%s'" % (list_result[1], list_result[2]))
                            cursor.execute("UPDATE levels_table SET exp = 0 WHERE user_id = '%s'" % (list_result[2]))
                            cursor.execute("UPDATE levels_table SET maxXp = 100 WHERE user_id = '%s'" % (list_result[2]))
                        elif list_result[1] == 'exp':
                            cursor.execute("UPDATE levels_table SET %s = 0 WHERE user_id = '%s'" % (list_result[1], list_result[2]))
                        elif list_result[1] == 'msges':
                            cursor.execute("UPDATE levels_table SET %s = 0 WHERE user_id = '%s'" % (list_result[1], list_result[2]))
                        elif list_result[1] == 'all':
                            cursor.execute("UPDATE levels_table SET level = 0 WHERE user_id = '%s'" % (list_result[2]))
                            cursor.execute("UPDATE levels_table SET exp = 0 WHERE user_id = '%s'" % (list_result[2]))
                            cursor.execute("UPDATE levels_table SET maxXp = 100 WHERE user_id = '%s'" % (list_result[2]))
                            cursor.execute("UPDATE levels_table SET msges_sent = 0 WHERE user_id = '%s'" % (list_result[2]))
                        mariadb_connection.commit()
                        await message.channel.send("Cleared %s" % list_result[1])
                    else:
                        error = discord.Embed(title="Invalid parameter %s" % list_result[1], description="Must be 'level', 'exp' or 'msges'", color=0xda000f)
                        error.set_footer(text="!clear <category> <@mention>")
                        await message.channel.send(embed=error)
                        return 0
                else:
                    if len(list_result) < 3:
                        error = discord.Embed(title="Not enough parameters", description="'!add' command needs 3 parameters", color=0xda000f)
                    else:
                        error = discord.Embed(title="Too many parameters", description="'!add' command needs 3 parameters", color=0xda000f)
                        error.set_footer(text="!clear <category> <@mention>")
                        await message.channel.send(embed=error)
                        return 0



            else:
                error = discord.Embed(title="Invalid permissions", description="Only administrators have access to this command", color=0xda000f)
                error.set_footer(text="!clear <category> <@mention>")
                await message.channel.send(embed=error)
                return 0




client.run(token)
