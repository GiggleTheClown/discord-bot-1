import discord
import mysql.connector as mariadb
import random
from datetime import datetime
import os
import threading


def BackupDatabase():
    os.system('mysqldump -u %s -p%s %s > backup.sql' % (user, password, database))
    print("Backup done")
    timer = threading.Timer(1000.0, BackupDatabase)
    timer.start()


def ConvertToDict(keys, values):
    return dict(zip(keys, values))


def UpdateLevelingTableRow(levelingListRow):
    for level in levelingList:
        if levelingListRow["user_id"] == level["user_id"]:
            for i in keys:
                cursor.execute("UPDATE levels_table SET %s = '%s' WHERE user_id = %s " % (i, level[i], level["user_id"]))
            mariadb_connection.commit()
            return


def UpdateLevelingTable():
    for level in levelingList:
        for i in keys:
            cursor.execute("UPDATE levels_table SET %s = '%s' WHERE user_id = %s" % (i, level[i], level["user_id"]))
    mariadb_connection.commit()


def ExpGain(msgLen, prestigeLevel):
    random.seed(datetime.now())
    try:
        expAmount = random.randint(1, DeteriorateXp(msgLen))
        return round(expAmount + (expAmount/20)*prestigeLevel, 3)
    except ValueError:
        return random.randint(1, 15)


def DeteriorateXp(msgLen):
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


def IncreaseMaxExp(previousMaxExp):  # WIP - more comlex system
    return 25


def SortListOfDict(): # Bubble sort used because assuming everyhing is sorted, its the fastest
    n = len(levelingList)
    returnval = 0

    for i in range(n-1):

        for j in range(0, n-i-1):

            if levelingList[j]["prestige"] < levelingList[j+1]["prestige"]:
                levelingList[j], levelingList[j+1] = levelingList[j+1], levelingList[j]
                returnval = 1
            elif levelingList[j]["prestige"] == levelingList[j+1]["prestige"]:
                if levelingList[j]["level"] < levelingList[j+1]["level"]:
                    levelingList[j], levelingList[j+1] = levelingList[j+1], levelingList[j]
                    returnval = 1
                elif levelingList[j]["level"] == levelingList[j+1]["level"]:
                    if levelingList[j]["exp"] < levelingList[j+1]["exp"]:
                        levelingList[j], levelingList[j+1] = levelingList[j+1], levelingList[j]
                        returnval = 1
                    elif levelingList[j]["exp"] == levelingList[j+1]["exp"]:
                        if levelingList[j]["msges_sent"] < levelingList[j]["msges_sent"]:
                            levelingList[j], levelingList[j+1] = levelingList[j+1], levelingList[j]
                            returnval = 1
    return returnval


def AddRanks():
    for i, level in enumerate(levelingList, 1):
        levelingList[i-1]["rank"] = i



user = 'root'
password = 'root'
database = 'test'


# Check if database exists - if it doesn't create new and sync with backup

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

insert = "INSERT INTO levels_table (user_id, msges_sent, exp, maxXp, level, username, rank, user_avatar_url) VALUES ('%s', %s, %s, %s, %s, '%s', %s, '%s')"

# Create a dictonary with all the info from levels_table

cursor.execute("SELECT * FROM levels_table ORDER BY rank ASC")
rows = cursor.fetchall()
global keys
keys = ['user_id', 'msges_sent', 'exp', 'maxXp', 'level', 'username', 'rank', 'user_avatar_url', 'prestige']
global levelingList
levelingList = []
for i in rows:
    levelingList.append(ConvertToDict(keys, i))


token = "Im a fake token"

client = discord.Client()
id = client.get_guild(548520910764769280)

timer = threading.Timer(300.0, BackupDatabase)
timer.start()


@client.event
async def on_message(message):
    # Update msges_sent, exp, maxXp. level, rank, user_avatar_url in levels_table for user_id
    for i, level in enumerate(levelingList):
        if level["user_id"] == str(message.author.id):
            try:
                level["user_avatar_url"] = str(message.author.avatar_url)
            except TypeError:
                level["user_avatar_url"] = "-1"
            level["msges_sent"] += 1
            level["exp"] += ExpGain(len(message.content), level["prestige"])

            if level["exp"] >= level["maxXp"]:
                level["level"] += 1
                await message.channel.send("%s is now level %s" % ("<@"+level["user_id"]+">", level["level"]))
                level["exp"] -= level["maxXp"]
                level["maxXp"] += IncreaseMaxExp(level["maxXp"])
            level["exp"] = round(level["exp"], 3)
            levelingList[i] = level
            if SortListOfDict():
                AddRanks()
                UpdateLevelingTable()
            else:
                UpdateLevelingTableRow(levelingList[i])  # so that it doesnt update the whole table every msg
            break

        # Create user if doesnt exist

        if i == len(levelingList):
            cursor.execute(insert % (message.author.id, 1, 0, 100, 0, str(message.author), 0, '-1', 0))
            mariadb.commit()
            mem = {keys[0]: message.author.id, keys[1]: 1, keys[2]: 0, keys[3]: 100, keys[4]: 0, keys[5]: str(message.author), keys[6]: len(levelingList)+1, keys[7]: -1, keys[8]: 0}
            levelingList.append(mem)

    # diffrent commands

    if message.author != client.user:  # so that bot cant use own commands

        if message.content == "!scoreboard":
            embed = discord.Embed(title="!scoreboard", description="shows the top 5 users", color=random.randint(0, 0xFFFFFF))
            for i, level in enumerate(levelingList):
                if i == 5:
                    break
                embed.add_field(name=level["username"], value="rank - %s \u200b \u200b prestige - %s level - %s" % ("#"+str(level["rank"]), level["prestige"], level["level"]), inline=False)
            await message.channel.send(embed=embed)
#
#
#
        if message.content.startswith("!level") or message.content.startswith("!rank"):
            level = {}
            if message.content == "!level" or message.content == "!rank":
                for level in levelingList:
                    if level["user_id"] == str(message.author.id):
                        break
            else:
                try:
                    for level in levelingList:
                        if level["username"] == str(message.mentions[0]):
                            break

                except IndexError:
                    error = discord.Embed(title="IndexError", description="Invalid username", color=0xda000f)
                    error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.)")
                    await message.channel.send(embed=error)
                    return

            try:
                embed = discord.Embed(title="!level", description="Shows level info‏‏‎‎", color=random.randint(0, 0xFFFFFF))
                embed.set_author(name=level["username"])
                embed.set_thumbnail(url=level["user_avatar_url"])
                embed.add_field(name="rank‏‏‎ ‎‏‏‎ ‎", value="#"+str(level["rank"]), inline=True)
                embed.add_field(name="prestige ", value=level["prestige"], inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="lvl", value=level["level"], inline=True)
                embed.add_field(name="exp", value=str(level["exp"])+"/"+str(level["maxXp"]), inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="msgs‏‏‎ ‎‏‏‎ ‎", value=level["msges_sent"], inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.set_footer(text="<@%s>" % (level["user_id"]))
            except IndexError:
                error = discord.Embed(title="IndexError", description="User doesn't exist in levels_table", color=0xda000f)
                error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.")
                await message.channel.send(embed=error)
                return 0

            try:
                await message.channel.send(embed=embed)
            except discord.errors.HTTPException or IndexError or UnboundLocalError:  # bad avatar url
                error = discord.Embed(title="discord.errors.HTTPException: 400 Bad Request (error code: 50035)", description="Unsupported url type ", color=0xda000f)
                error.set_footer(text="Invalid Form Body In embed.thumbnail.url: Not a well formed URL.")
                await message.channel.send(embed=error)

                embed.set_thumbnail(url="")
                try:
                    await message.channel.send(embed=embed)
                except IndexError:
                    error = discord.Embed(title="IndexError", description="User doesn't exist in the databe", color=0xda000f)
                    error.set_footer(text="Raised when a sequence subscript is out of range. (Slice indices are silently truncated to fall in the allowed range; if an index is not a plain integer, TypeError is raised.)")
                    await message.channel.send(embed=error)

        if message.content.startswith("!add") or message.content.startswith("!remove"):
            if getattr(message.author.guild_permissions, "administrator"):
                # [0] = !add, [1] = amount, [2] = category, [3] mention
                userMsgList = message.content.split()

                if len(userMsgList) == 4:
                    # check [1]
                    try:
                        int(userMsgList[1])
                    except TypeError or ValueError:
                        error = discord.Embed(title="Invalid parameter %s" % userMsgList[1], description="Must be a whole positive integer", color=0xda000f)
                        error.set_footer(text="<command name> <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return

                    if int(userMsgList[1]) <= 0:
                        error = discord.Embed(title="Invalid parameter %s" % userMsgList[1], description="Must be a whole positive integer", color=0xda000f)
                        error.set_footer(text="<command name> <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return
                    # check [2]
                    validCategories = ["exp", "level", "msges_sent", "prestige"]
                    if userMsgList[2] not in validCategories:
                        error = discord.Embed(title="Invalid parameter %s" % userMsgList[2], description="Must be 'prestige', 'level', 'exp' or 'msges_sent'", color=0xda000f)
                        error.set_footer(text="<command name> <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return
                    # check [3]
                    try:
                        message.mentions[0]
                    except IndexError:
                        error = discord.Embed(title="Invalid parameter %s" % userMsgList[3], description="Must be a mention. \n ps: you can't copy mentions", color=0xda000f)
                        error.set_footer(text="<command name> <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return 0

                    level = {}
                    check3 = 0
                    for i, level in enumerate(levelingList):
                        if str(message.mentions[0]) == level["username"]:
                            check3 = 1
                            break
                    if check3 == 0:
                        error = discord.Embed(title="Invalid parameter %s" % userMsgList[3], description="User doesn't exist in database \n ps: you can't copy mentions", color=0xda000f)
                        error.set_footer(text="<command name> <number> <category> <@person>")
                        await message.channel.send(embed=error)
                        return

                    del check3

                    # add/remove to levelingList and databases and polish diffrent scenarios
                    userMsgList[1] = int(userMsgList[1])
                    if "add" in message.content:
                        level[userMsgList[2]] += userMsgList[1]

                    # increase maxXp if added levels

                        if userMsgList[2] == "level":
                            for b in range(userMsgList[1]):
                                level["maxXp"] += IncreaseMaxExp(level["maxXp"])

                    # see if new exp causes leveling up

                        if userMsgList[2] == "exp":
                            while level["exp"] >= level["maxXp"]:
                                level["level"] += 1
                                level["exp"] -= level["maxXp"]
                                level["maxXp"] += IncreaseMaxExp(level["maxXp"])

                    if "remove" in message.content:
                        level[userMsgList[2]] -= userMsgList[1]

                        if level[userMsgList[2]] < 0:
                            level[userMsgList[2]] = 0
                        # when removing levels decrease maxXp and negate exp
                        if userMsgList[2] == "level":
                            for b in range(userMsgList[1]):
                                level["maxXp"] -= IncreaseMaxExp(level["maxXp"]-1)
                                if level["maxXp"] < 0:
                                    level["maxXp"] = 0
                                    break

                            level["exp"] = 0
                        # when removing exp, lower levels and maxXp
                        if userMsgList[2] == "exp":
                            if userMsgList[1] > 0:
                                level["maxXp"] -= IncreaseMaxExp(level["maxXp"]-1)
                                level["level"] -= 1

                            while userMsgList[1] > level["maxXp"]:
                                userMsgList[1] -= level["maxXp"]
                                level["maxXp"] -= IncreaseMaxExp(level["maxXp"]-1)
                                level["level"] -= 1
                                if level["maxXp"] < 0:
                                    level["maxXp"] = 25
                                    userMsgList[1] = 25
                                    break
                            level["exp"] = level["maxXp"] - userMsgList[1]
                            if level["exp"] < 0:
                                level["exp"] = 0

                    # save changes
                    levelingList[i] = level

                    if SortListOfDict():
                        AddRanks()
                        UpdateLevelingTable()
                    else:
                        UpdateLevelingTableRow(levelingList[i])

                    await message.channel.send("success")


                else:
                    if len(userMsgList) < 4:
                        error = discord.Embed(title="Not enough parameters", description="'!add' command uses 3 parameters", color=0xda000f)
                    else:
                        error = discord.Embed(title="Too many parameters", description="'!add' command uses 3 parameters", color=0xda000f)
                    error.set_footer(text="!add <number> <category> <@person>")
                    await message.channel.send(embed=error)
                    return 0
            else:
                error = discord.Embed(title="Invalid permissions", description="Only administrators have access to this command", color=0xda000f)
                error.set_footer(text="!add <number> <category> <@person>")
                await message.channel.send(embed=error)
                return 0

        if message.content.startswith("!clear"):
            # [1] = category, [2] = @mention

            if getattr(message.author.guild_permissions, "administrator"):
                userMsgList = message.content.split()
                if len(userMsgList) == 3:
                    # [1] check
                    validCategories = ["msges_sent", "exp", "level", "prestige", "all"]
                    if userMsgList[1] not in validCategories:
                        error = discord.Embed(title="Invalid parameter %s" % userMsgList[1], description="Must be 'level', 'exp' or 'msges_sent'", color=0xda000f)
                        error.set_footer(text="<command name> <category> <@person>")
                        await message.channel.send(embed=error)
                        return

                    # [2] check
                    if userMsgList[2] != "all":
                        try:
                            message.mentions[0]
                        except IndexError:
                            error = discord.Embed(title="Invalid parameter %s" % userMsgList[2], description="Must be a mention. \n ps: you can't copy mentions", color=0xda000f)
                            error.set_footer(text="<command name> <category> <@person>")
                            await message.channel.send(embed=error)
                            return

                        level = {}
                        i = -1
                        check3 = 0
                        for i, level in enumerate(levelingList):
                            if str(message.mentions[0]) == level["username"]:
                                check3 = 1
                                break
                        if check3 == 0:
                            error = discord.Embed(title="Invalid parameter %s" % userMsgList[2], description="User doesn't exist in database \n ps: you can't copy mentions", color=0xda000f)
                            error.set_footer(text="<command name>  <category> <@person>")
                            await message.channel.send(embed=error)
                            return

                        del check3

                        # clear category
                        try:
                            level[userMsgList[1]] = 0
                        except error:  # if userMsgList[1] is "all", then its not in level, but for some reason it doesnt give an error
                            if userMsgList[1] == "all":
                                level["level"] = 0
                                level["exp"] = 0
                                level["maxXp"] = 25
                                level["msges_sent"] = 0
                                level["prestige"] = 0

                        if userMsgList[1] == "all":
                            level["level"] = 0
                            level["exp"] = 0
                            level["maxXp"] = 25
                            level["msges_sent"] = 0
                            level["prestige"] = 0

                        if userMsgList[1] == "level":
                            level["maxXp"] = 25
                            level["exp"] = 1
                        levelingList[i] = level
                    else:
                        for b, level in enumerate(levelingList):
                            try:
                                level[userMsgList[1]] = 0
                            except error:  # if userMsgList[1] is "all", then its not in level, but for some reason it doesnt give an error
                                if userMsgList[1] == "all":
                                    level["level"] = 0
                                    level["exp"] = 0
                                    level["maxXp"] = 25
                                    level["msges_sent"] = 0
                                    level["prestige"] = 0

                            if userMsgList[1] == "all":
                                level["level"] = 0
                                level["exp"] = 0
                                level["maxXp"] = 25
                                level["msges_sent"] = 0
                                level["prestige"] = 0

                            if userMsgList[1] == "level":
                                level["maxXp"] = 25
                                level["exp"] = 1

                            levelingList[b] = level
                    await message.channel.send("success")
                    SortListOfDict()
                    AddRanks()
                    UpdateLevelingTable()
                else:
                    if len(userMsgList) < 3:
                        error = discord.Embed(title="Not enough parameters", description="'!clear' command uses 2 parameters", color=0xda000f)
                    else:
                        error = discord.Embed(title="Too many parameters", description="'!clear' command uses 2 parameters", color=0xda000f)
                    error.set_footer(text="!clear <number> <category> <@person>")
                    await message.channel.send(embed=error)
                    return
            else:
                error = discord.Embed(title="Invalid permissions", description="Only administrators have access to this command", color=0xda000f)
                error.set_footer(text="!add <number> <category> <@person>")
                await message.channel.send(embed=error)
                return

        if message.content == "!prestige":
            # each prestige increases ur exp gain by 5%
            level = {}
            for i, level in enumerate(levelingList):
                if level["user_id"] == str(message.author.id):
                    # check if u have required levels to prestige
                    if level["level"] >= 100 + 20*level["prestige"]:  # you can prestige every 20 levels after 100
                        # erase all other stats except msges sent but increase prestige
                        level["level"] = 0
                        level["exp"] = 0
                        level["maxXp"] = 0
                        level["prestige"] += 1
                        levelingList[i] = level
                        SortListOfDict()
                        AddRanks()
                        UpdateLevelingTable()
                        await message.channel.send("<@%s> prestiged to %s" % (level["user_id"], level["prestige"]))
                    else:
                        await message.channel.send("You need %s more levels untill you can prestige" % ((100 + 20*level["prestige"]) - level["level"]))

                    break

                if i == len(levelingList):
                    await message.channel.send("error")


client.run(token)
