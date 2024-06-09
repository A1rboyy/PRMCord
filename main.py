import discord
from discord.ext import commands
import pymysql
from random import randint
import asyncio
import settings
import math
from PIL import Image, ImageDraw, ImageFont
import os
import datetime


client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    print("We are ready")
    print("-------")

db = pymysql.connect(host = "prmcord-cluster-do-user-15766503-0.c.db.ondigitalocean.com", user = "-", password = "-", database = "prmcord", port = 25060)
cursor = db.cursor()

allowed_channel_id = [1211285687714971679,1211307699107536926,1211296263115636766,1215689387342434366,1215802619709362217]

AceChannel = [1215774155140632618,1215774179144765510,1215774203987361994,1215774294055976970,1215775381588545556,1216782260594937947]

TestServer = [1216169954613657630,1216170312744435732]

allowed_channel_id = allowed_channel_id + AceChannel + TestServer

q_channel = [1215689387342434366,1215774179144765510]

test_q = [1216170312744435732]

q_channel = q_channel + test_q

client.remove_command("help")

@client.command(name="help")
async def help(ctx):
    embed = discord.Embed(title="Alle Commands", color=discord.Color.blue())
    embed.set_image(url="https://cdn.discordapp.com/attachments/1195342755610759219/1204485581611081799/info.png?ex=65d4e79c&is=65c2729c&hm=adccc077d4082aff54a603cfc574d2291db7404fa693eb81eba79302aa99a120&")
    await ctx.send(embed=embed)

# Checks

async def is_allowed_channel(ctx):
    if ctx.channel.id not in allowed_channel_id:
        print("Command im falschen Channel")
        return False
    return True

async def is_registered(ctx):
    discord_id = ctx.author.id
    cursor.execute("SELECT COUNT(*) FROM fantasy WHERE discord_id = %s", (discord_id))
    count = cursor.fetchone()[0]
    if count >0:
        return True
    else:
        return False

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Du kannst diesen Befehl nicht ausführen, registrier dein Team zuerst mit !register oder komm auf den offiziellen Server https://discord.gg/QtEkcCQnRq und frag um Hilfe.")

# Commands

@client.command(name="odds", aliases=["wahrscheinlichkeiten"])
async def odds(ctx):
    embed = discord.Embed(title="Alle Wahrscheinlichkeiten", color=discord.Color.blue())
    embed.add_field(name="Stärke von Spielern", value=settings.explain_spieler)
    embed.add_field(name="Einfluss von Coaches", value=settings.einfluss_coaches)
    embed.add_field(name="Synergien", value=settings.synergies)
    embed.add_field(name="Pulls", value=settings.chances_pulls)
    
    await ctx.send(embed=embed)

# geiler Command
@client.command()
async def noice(ctx):
    channel = client.get_channel(1216169954613657630)
    await channel.send("lol")
    



# Infos zu einem Team bekommen
@client.command(name="info")
async def info(ctx, team: str=None,):
    if team is None:
        await ctx.send("Du musst ein Teamnamen in Anführungszeichen angeben!")
        return
    cursor.execute("SELECT toplaner, jungler, midlaner, botlaner, supporter FROM teams WHERE teamname = %s", (team,))     
    players = cursor.fetchone()
    cursor.execute("SELECT coach1 FROM teams WHERE teamname = %s", (team,))     
    coach1 = cursor.fetchone()[0]
    if coach1 is None:
        coach1 = "leer"
    cursor.execute("SELECT coach2 FROM teams WHERE teamname = %s", (team,))     
    coach2 = cursor.fetchone()[0]
    if coach2 is None:
        coach2 = "leer"

    player_list = ",".join(players)
    await ctx.send(f"Die Spieler in {team} sind: {player_list}")
    if coach1 == "leer":
        return
    if coach2 == "leer":
        await ctx.send(f"Als Coach ist {coach1} dabei.")
    else:
        await ctx.send(f"Die Coaches sind {coach1} und {coach2}.")


# Team registrieren
@client.command(name="register")
@commands.check(is_allowed_channel)
async def register_user(ctx):
    discord_id = ctx.author.id

    cursor.execute("SELECT * FROM fantasy WHERE discord_id = %s", (discord_id,))
    existing_user = cursor.fetchone()
    if not existing_user:
        name = ctx.author.name
        discord_id = ctx.author.id
        cursor.execute("INSERT INTO fantasy (discord_id, fantasyname) VALUES (%s,%s)", (discord_id, name))
        cursor.execute("INSERT INTO userstats (discord_id,elo) VALUES (%s,600)", (discord_id,))
        cursor.execute("UPDATE userstats SET fantasy_id = (SELECT fantasy_id FROM fantasy WHERE discord_id = %s) WHERE discord_id = %s", (discord_id,discord_id))
        cursor.execute("INSERT INTO experience (discord_id) VALUES (%s)", (discord_id,))
        cursor.execute("UPDATE experience SET fantasy_id = (SELECT fantasy_id FROM fantasy WHERE discord_id = %s) WHERE discord_id = %s", (discord_id,discord_id))
        await randomize_team(ctx)
        db.commit()

        await ctx.send(f"Du wurdest erfolgreich registriert!")
    else:
        await ctx.send("Du bist bereits registriert!")

async def randomize_team(ctx):
    discord_id = ctx.author.id

    cursor.execute("UPDATE fantasy SET toplaner = (SELECT player_id FROM players WHERE position = 'toplaner' ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET jungler = (SELECT player_id FROM players WHERE position = 'jungler' ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET midlaner = (SELECT player_id FROM players WHERE position = 'midlaner' ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET botlaner = (SELECT player_id FROM players WHERE position = 'botlaner' ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET supporter = (SELECT player_id FROM players WHERE position = 'supporter' ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET coach1 = (SELECT player_id FROM players WHERE position = 'coach1' ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))
       
    cursor.execute("UPDATE fantasy SET coach2 = (SELECT player_id FROM players WHERE position = 'coach2' ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET bench1 = (SELECT player_id FROM players ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET bench2 = (SELECT player_id FROM players ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    cursor.execute("UPDATE fantasy SET bench3 = (SELECT player_id FROM players ORDER BY RAND() Limit 1) WHERE discord_id = %s", (discord_id,))

    db.commit()
    await ctx.send("Deine Spieler und Coaches wurden ausgewählt.")


pulling_users = set()

# Spieler/Talents pullen
@commands.check(is_allowed_channel)
@commands.check(is_registered)
@client.command(name="pull")
async def pull(ctx):
    discord_id = ctx.author.id

    if discord_id not in pulling_users:
        # pulls und namen ziehen
        cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s", (discord_id,))
        fantasyname = cursor.fetchone()[0]
        cursor.execute("UPDATE userstats SET pulls = pulls WHERE discord_id = %s", (discord_id,))
        db.commit()
        cursor.execute("SELECT pulls FROM userstats WHERE discord_id = %s", (discord_id,))
        pulls = cursor.fetchone()[0]

        if pulls == 0:
            await ctx.send("Du hast keine Pulls mehr übrig.")
            return
        else:    
            # pull abziehen
            pulls = pulls - 1
            pulling_users.add(discord_id)
            cursor.execute("UPDATE userstats SET pulls = pulls -1 WHERE discord_id = %s", (discord_id,))
            db.commit()

            # Bild öffnen
            image = Image.open('graphics/pull.jpg')
            new_image = image.resize((1000, 1000))
            draw = ImageDraw.Draw(new_image)
            font_path = "fonts/Roboto-Black.ttf"
            font_size = 35
            font = ImageFont.truetype(font_path, font_size)

            # Den pull rollen
            liga = 0
            
            roll = "player"
            pos_roll = randint(1,7)
            if pos_roll == 6:
                roll = "coach1"
            elif pos_roll == 7:
                roll = "coach2"

            # Position
            player_info = None
            liga_roll = randint(1,750)
            if liga_roll <= 350:
                liga = 6
            elif liga_roll <= 600:
                liga = 5
            elif liga_roll <= 700:
                liga = 4
            elif liga_roll <= 730:
                liga = 3
            elif liga_roll <= 749:
                liga = 2
            elif liga_roll == 750:
                liga = 1

            if roll == "player":
                pos2_roll = randint(1,5)
                if pos2_roll == 1:
                    position = "toplaner"
                elif pos2_roll == 2:
                    position = "jungler"
                elif pos2_roll == 3:
                    position = "midlaner"
                elif pos2_roll == 4:
                    position = "botlaner"
                elif pos2_roll == 5:
                    position = "supporter"
                cursor.execute(f"SELECT {position} FROM teams WHERE liga = %s ORDER BY RAND() LIMIT 1",(liga,))
                ign = cursor.fetchone()[0]
                cursor.execute("SELECT ign, team, player_id FROM players WHERE ign = %s",(ign,))
                player_info = cursor.fetchone()

            if roll == "coach1":
                cursor.execute("SELECT ign, team, player_id FROM players WHERE position = 'coach1' ORDER BY RAND() LIMIT 1")
                player_info = cursor.fetchone() # 0=ign, 1=team, 2=player_id
                position = "coach1"
            if roll == "coach2":
                cursor.execute("SELECT ign, team, player_id FROM players WHERE position = 'coach2' ORDER BY RAND() LIMIT 1")
                player_info = cursor.fetchone() # 0=ign, 1=team, 2=player_id
                position = "coach2"

            if position == "toplaner":
                showed_position = "Toplaner"
            elif position == "jungler":
                showed_position = "Jungler"
            elif position == "midlaner":
                showed_position = "Midlaner"
            elif position == "botlaner":
                showed_position = "Botlaner"
            elif position == "supporter":
                showed_position = "Supporter"
            elif position == "coach1":
                showed_position = "1.Coach"
            elif position == "coach2":
                showed_position = "2.Coach"

            draw.text((185, 95), showed_position, fill="black", font=font)
            draw.text((610, 95), player_info[1], fill="black", font=font)
            draw.text((450, 725), player_info[0], fill="black", font=font)
            cursor.execute("SELECT liga FROM teams WHERE teamname = %s",(player_info[1],))
            liga = cursor.fetchone()[0]
            font_size = 60
            font = ImageFont.truetype(font_path, font_size)
            draw.text((480, 500), str(liga), fill="black", font=font) 

            # Das temp Bild saven und senden
            image_path = 'graphics/temp_pull.jpg'
            new_image.save('graphics/temp_pull.jpg')
            await ctx.send(file=discord.File('graphics/temp_pull.jpg'))

            # Temp Bild löschen
            os.remove(image_path)

            await ctx.send("ja um einen Spieler auszutauschen, nein um ihn abzulehnen und eine Bankposition b1/b2/b3 um ihn auf die Bank zu setzen.")

            def check(message):
                return message.author == ctx.author and message.content.lower() in ["ja","nein","b1","b2","b3"]
            try:
                response = await client.wait_for("message", check=check, timeout=45.0)
            except asyncio.TimeoutError:
                await ctx.send(f"Keine Antwort erbracht, du hast noch {pulls} pulls übrig.")
                pulling_users.remove(discord_id)
                return
            # Spieler austauschen
            if response.content.lower() == "ja":
                cursor.execute(f"UPDATE fantasy SET {position} = %s WHERE discord_id = %s",(player_info[2], discord_id))
                cursor.execute(f"UPDATE experience SET {position} = 0 WHERE discord_id = %s",(discord_id,))
                db.commit()
                await ctx.send(f"Du hast den Spieler/Coach ausgetauscht. Du hast noch {pulls} pulls übrig.")

            elif response.content.lower() == "nein":
                await ctx.send(f"Du hast den Spieler/Coach nicht in dein Team aufgenommen. Du hast noch {pulls} pulls übrig.")

            elif response.content.lower() == "b1":
                position = "bench1"
                cursor.execute(f"UPDATE fantasy SET bench1 = %s WHERE discord_id = %s", (player_info[2], discord_id))
                db.commit()
                await ctx.send("Du hast den Spieler auf Bank1 gesetzt.")

            elif response.content.lower() == "b2":
                position = "bench2"
                cursor.execute(f"UPDATE fantasy SET bench2 = %s WHERE discord_id = %s", (player_info[2],discord_id))
                db.commit()
                await ctx.send("Du hast den Spieler auf Bank2 gesetzt.")

            elif response.content.lower() == "b3":
                position = "bench3"
                cursor.execute(f"UPDATE fantasy SET bench3 = %s WHERE discord_id = %s", (player_info[2], discord_id))
                db.commit()
                await ctx.send("Du hast den Spieler auf Bank3 gesetzt.")

            pulling_users.remove(discord_id)

    else:
        await ctx.send("Du bist bereits dabei einen Spieler/Coach zu ziehen.")

q_users = []

@commands.check(is_allowed_channel)
@commands.check(is_registered)
@client.command(name="q")
async def q(ctx):
    discord_id = ctx.author.id                                         
    if ctx.channel.id not in q_channel:
        await ctx.send("Schau dir nochmal ganz genau den Channelnamen an...")
        return


    cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s", (discord_id,))
    fantasyname = cursor.fetchone()[0]                                 
    await ctx.send(f"{fantasyname} ist der Warteschlange beigetreten.")

    # Gegnersuche
    # Elo range
    cursor.execute("SELECT elo FROM userstats WHERE discord_id = %s",(discord_id,))
    elo = cursor.fetchone()[0]

    team2_id = str(discord_id)
    # Gegner (nicht selbst) suchen
    while team2_id == str(discord_id):
        cursor.execute("SELECT discord_id FROM userstats WHERE elo BETWEEN %s-100 AND %s+100 ORDER BY Rand() LIMIT 1",(elo,elo))       
        team2_id = cursor.fetchone()[0]
        if team2_id == str(discord_id):
            cursor.execute("SELECT discord_id FROM userstats ORDER BY Rand() LIMIT 1")
            team2_id = cursor.fetchone()[0]
        else:
            team2_id = team2_id

    # Game spielen
    # Spieler Ids der teams ziehen
    team1_id = str(discord_id)
    cursor.execute("SELECT toplaner, jungler, midlaner, botlaner, supporter, coach1 FROM fantasy WHERE discord_id = %s", (team1_id,))
    spieler_id_team1 = cursor.fetchone()
    cursor.execute("SELECT toplaner, jungler, midlaner, botlaner, supporter, coach1 FROM fantasy WHERE discord_id = %s", (team2_id,))
    spieler_id_team2 = cursor.fetchone()

    # Liste der IGN erstellen
    spieler_ign_1 = []
    spieler_ign_2 = []
    for spieler in spieler_id_team1:
        cursor.execute("SELECT ign FROM players WHERE player_id = %s",(spieler,))
        spieler_ign_1.append(cursor.fetchone()[0])
    for spieler in spieler_id_team2:
        cursor.execute("SELECT ign FROM players WHERE player_id = %s",(spieler,))
        spieler_ign_2.append(cursor.fetchone()[0])


    # Bild öffnen
    # Checken ob Orga #1 ist
    cursor.execute("SELECT clan FROM userstats WHERE discord_id = %s",(discord_id,))
    orga = cursor.fetchone()[0]
    if orga != "leer":
        cursor.execute("SELECT COUNT(*) FROM clans WHERE rep > (SELECT rep FROM clans WHERE clanname = %s)",(orga))
        rang = cursor.fetchone()[0]
        if rang == 0:
            image = Image.open('graphics/best_orga.jpg')
        else:
            image = Image.open('graphics/q.jpg')
    else:
        image = Image.open('graphics/q.jpg')
    new_image = image.resize((1000, 1000))
    draw = ImageDraw.Draw(new_image)
    font_path = "fonts/Roboto-Black.ttf"
    font_size = 25
    font = ImageFont.truetype(font_path, font_size)

    # IGN auf das Bild schreiben
    i = 0
    for spieler in spieler_ign_1:
        draw.text((140, 410 + (65*i)), spieler, fill="white", font=font)
        i = i + 1
    i = 0
    for spieler in spieler_ign_2:
        draw.text((700, 410 + (65*i)), spieler, fill="white", font=font)
        i = i + 1

    # Fantasynames schreiben
    cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s",(team1_id,))
    fantasyname_team1 = cursor.fetchone()[0]
    cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s", (team2_id,))
    fantasyname_team2 = cursor.fetchone()[0]
    font_size = 40
    font = ImageFont.truetype(font_path, font_size)
    draw.text((100, 220), fantasyname_team1, fill="white", font=font)
    draw.text((580, 220), fantasyname_team2, fill="white", font=font)

    # Arrows und mvp bild reinbringen
    arrow_left_image = Image.open('graphics/arrow_left.png').convert("RGBA")
    arrow_resize = (40, 40)
    mvp_image = Image.open('graphics/mvp.png').convert("RGBA")
    mvp_resize = (70, 30)
    mvp_image = mvp_image.resize(mvp_resize)
    arrow_right_image = Image.open('graphics/arrow_right.png').convert("RGBA")
    arrow_right_image = arrow_right_image.resize(arrow_resize)
    arrow_left_image = arrow_left_image.resize(arrow_resize)

    # Matchups der einzelnen Leute ausrechenn
    winners = await calculate_positions_online(team1_id, team2_id)

    # MVP wählen
    mvp = randint(0,5)
    winners.append(winners[mvp])

    # Gewinner ausrechnen und aufschreiben
    winner = 0
    if winners.count(1) >= 4:
        winner = 1
    else: 
        winner = 2
    fantasynames = [fantasyname_team1,fantasyname_team2]
    draw.text((390, 890), fantasynames[winner-1], fill="white", font=font)

    # Pfeile für Lane Wins
    i = 0
    while i < 6:
        arrow_position = (480, (405 + (i * 64)))
        if winners[i] == 1:
            new_image.paste(arrow_left_image, arrow_position, arrow_left_image)
        else:
            new_image.paste(arrow_right_image, arrow_position, arrow_right_image)
        i = i + 1

    # Mvp Plakette
    mvp_position = (400 + ((winners[6]) - 1) * 125, 400 + (mvp * 66))
    new_image.paste(mvp_image, mvp_position, mvp_image)

    # Winner und Looser setten
    winner_id = 0
    looser_id = 0
    if winner == 1:
        winner_id = team1_id
        looser_id = team2_id
    else:
        winner_id = team2_id
        looser_id = team1_id

    winner_id = str(winner_id)
    looser_id = str(looser_id)

    # Elo
    cursor.execute("SELECT elo FROM userstats WHERE discord_id = %s",(winner_id,))
    winner_elo = cursor.fetchone()[0]
    cursor.execute("SELECT elo FROM userstats WHERE discord_id = %s",(looser_id,))
    looser_elo = cursor.fetchone()[0]

    # Elo change berechnen
    change = 15
    if winner_elo > looser_elo:
        #smol
        value = (winner_elo - looser_elo) / 10
        change = round(change - value)
        if change <= 2:
            change = 3
    else:
        #big
        value = (looser_elo - winner_elo) / 10
        change = round(change + value)
        if change >= 21:
            change = 20

    # Elo change darstellen
    font_size = 30
    font = ImageFont.truetype(font_path, font_size)
    change = str(change)
    if winner == 1:
        draw.text((250, 900), "+" + change + " elo", fill="white", font=font)
        draw.text((770, 900), "-" + change + " elo", fill="white", font=font)
    else:
        draw.text((770, 900), "+" + change + " elo", fill="white", font=font)
        draw.text((250, 900), "-" + change + " elo", fill="white", font=font)

    # Elo change in db
    change = int(change)
    cursor.execute("UPDATE userstats SET elo = elo + %s, wins = wins + 1 WHERE discord_id = %s", (change, winner_id,))
    cursor.execute("UPDATE userstats SET elo = elo - %s, losses = losses + 1 WHERE discord_id = %s", (change, looser_id,))
    db.commit()

    # Experience adden
    # Erst Standard + 1
    cursor.execute("UPDATE experience SET toplaner=toplaner +1, jungler=jungler +1, midlaner=midlaner +1, botlaner=botlaner +1, supporter=supporter +1, coach1=coach1+1, coach2=coach2+1 WHERE discord_id = %s", (winner_id,))
    cursor.execute("UPDATE experience SET toplaner=toplaner +1, jungler=jungler +1, midlaner=midlaner +1, botlaner=botlaner +1, supporter=supporter +1, coach1=coach1+1, coach2=coach2+1 WHERE discord_id = %s", (looser_id,))
    db.commit()
    # Dann Sonder extra wegen Coach2 buff
    #Team1
    cursor.execute("SELECT coach2 FROM fantasy WHERE discord_id = %s",(winner_id,))
    coach2_winner = cursor.fetchone()[0]
    cursor.execute("SELECT team FROM players WHERE player_id = %s",(coach2_winner,))
    team_coach2_winner = cursor.fetchone()[0]
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s",(team_coach2_winner,))
    liga = cursor.fetchone()[0]
    dice = randint(1,12)
    chance = 7-liga
    if chance >= dice:
        print("1")
        cursor.execute("SELECT buff FROM userstats WHERE discord_id = %s",(winner_id,))
        position = cursor.fetchone()[0]
        cursor.execute(f"UPDATE experience SET {position} = {position} + 1 WHERE discord_id = %s",(winner_id,))
        db.commit()
    # Team2 
    cursor.execute("SELECT coach2 FROM fantasy WHERE discord_id = %s",(looser_id,))
    coach2_looser = cursor.fetchone()[0]
    cursor.execute("SELECT team FROM players WHERE player_id = %s",(coach2_looser,))
    team_coach2_looser = cursor.fetchone()[0]
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s",(team_coach2_looser,))
    liga = cursor.fetchone()[0]
    dice = randint(1,12)
    chance = 7-liga
    if chance >= dice:
        cursor.execute("SELECT buff FROM userstats WHERE discord_id = %s",(looser_id,))
        position = cursor.fetchone()[0]
        cursor.execute(f"UPDATE experience SET {position} = {position} + 1 WHERE discord_id = %s",(looser_id,))
        db.commit()

    # Coins adden
    # Team 1
    cursor.execute("SELECT wins,losses FROM userstats WHERE discord_id = %s",(winner_id,))
    games = cursor.fetchone()
    games = games[0] + games[1]
    if games % 15 == 0:
        cursor.execute("UPDATE userstats SET coins = coins + 1 WHERE discord_id = %s",(winner_id,))
        db.commit()
        await ctx.send(f"{winner} erhält einen coin für sein {games}. Spiel.")
    # Team 2
    cursor.execute("SELECT wins,losses FROM userstats WHERE discord_id = %s",(looser_id,))
    games = cursor.fetchone()
    games = games[0] + games[1]
    if games % 15 == 0:
        cursor.execute("UPDATE userstats SET coins = coins + 1 WHERE discord_id = %s",(looser_id,))
        db.commit()
        cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s",(looser_id,))
        fantasyname = cursor.fetchone()[0]
        await ctx.send(f"{fantasyname} erhält einen coin für sein {games}. Spiel.")

    # Das temp Bild saven und senden
    image_path = 'graphics/temp_q.jpg'
    new_image.save('graphics/temp_q.jpg')
    await ctx.send(file=discord.File('graphics/temp_q.jpg'))

    # Temp Bild löschen
    os.remove(image_path)

# Einzelne Rollen gegeneinander, Returned Gewinnerseiten i.e. (1,2,1,2,2,1)
async def calculate_positions_online(team1,team2):
    winners = []
    # Team 1
    cursor.execute("SELECT toplaner,jungler,midlaner,botlaner,supporter,coach1 FROM fantasy WHERE discord_id = %s",(team1,))
    team1_ids = cursor.fetchone()
    team1_prm_teams = []
    for spieler in team1_ids:
        cursor.execute("SELECT team FROM players WHERE player_id = %s",(spieler,))
        team1_prm_teams.append(cursor.fetchone()[0])
    team1_pool = []
    for spieler in team1_ids:
        cursor.execute("SELECT position FROM players WHERE player_id = %s", (spieler,))
        position = cursor.fetchone()[0]
        cursor.execute("SELECT liga FROM teams WHERE teamname = (SELECT team FROM players WHERE player_id = %s)",(spieler,))
        power = 7 - cursor.fetchone()[0]
        cursor.execute(f"SELECT {position} FROM experience WHERE discord_id = %s",(team1,))
        experience = cursor.fetchone()[0]
        power = power + (0.5 * math.floor(experience/1000))
        if len(set(team1_prm_teams)) == 1:
            power = power + 0.5
        elif position == "jungler" or position == "midlaner":
            if team1_prm_teams[1] == team1_prm_teams[2]:
                power = power + 0.25
        elif position == "botlaner" or position == "supporter":
            if team1_prm_teams[3] == team1_prm_teams[4]:
                power = power + 0.25
        power = round(2 ** power)
        team1_pool.append(power)
    
    # Team 2
    cursor.execute("SELECT toplaner,jungler,midlaner,botlaner,supporter,coach1 FROM fantasy WHERE discord_id = %s",(team2,))
    team2_ids = cursor.fetchone()
    team2_prm_teams = []
    for spieler in team2_ids:
        cursor.execute("SELECT team FROM players WHERE player_id = %s",(spieler,))
        team2_prm_teams.append(cursor.fetchone()[0])
    team2_pool = []

    for spieler in team2_ids:
        cursor.execute("SELECT position FROM players WHERE player_id = %s", (spieler,))
        position = cursor.fetchone()[0]
        cursor.execute("SELECT liga FROM teams WHERE teamname = (SELECT team FROM players WHERE player_id = %s)",(spieler,))
        power = 7 - cursor.fetchone()[0]
        cursor.execute(f"SELECT {position} FROM experience WHERE discord_id = %s",(team2,))
        experience = cursor.fetchone()[0]
        power = power + (0.5 * math.floor(experience/1000))
        if len(set(team2_prm_teams)) == 1:
            power = power + 0.5
        elif position == "jungler" or position == "midlaner":
            if team2_prm_teams[1] == team2_prm_teams[2]:
                power = power + 0.25
        elif position == "botlaner" or position == "supporter":
            if team2_prm_teams[3] == team2_prm_teams[4]:
                power = power + 0.25
        power = round(2 ** power)
        team2_pool.append(power)
    
    # Auswürfeln
    i = 0
    while i < 6:
        damn = (team1_pool[i] + team2_pool[i])
        dice = randint(0,damn)
        if dice <= team1_pool[i]:
            winners.append(1)
        else:
            winners.append(2)
        i = i + 1
    return winners

async def calculate_winner(team1,team2):
    winners = await calculate_positions_online(team1,team2)
    mvp = randint(0,5)
    winners.append(winners[mvp])
    winner = 0
    if winners.count(1) >= 4:
        winner = 1
    else: 
        winner = 2
    return winner

# Team Grafik
@commands.check(is_allowed_channel)
@commands.check(is_registered)
@client.command(name="team")
async def team(ctx,team_name=None):

    # Das Team festlegen was gesucht dargestellt werden soll
    if team_name == None:
        discord_id = ctx.author.id
    else:
        cursor.execute("SELECT discord_id FROM fantasy WHERE fantasyname = %s", (team_name,))
        discord_id = cursor.fetchone()
        if discord_id is None:
            await ctx.send("Dieses Team existiert nicht.")
            return
        discord_id = discord_id[0]
        
    # leeres Bild erstellen und font grundlegend festlegen
    image = Image.open('graphics/team.jpg')
    new_image = image.resize((1000, 1000))
    draw = ImageDraw.Draw(new_image)
    font_path = "fonts/Roboto-Black.ttf"

    # Teamname pullen und schreiben
    cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s", (discord_id,))
    team_name = cursor.fetchone()[0]
    font_size = 35
    font = ImageFont.truetype(font_path, font_size)
    draw.text((460, 4), team_name, fill="white", font=font)

    # stats pullen und schreiben
    cursor.execute("SELECT wins, losses, coins, elo, pulls FROM userstats WHERE discord_id = %s", (discord_id,))
    stats = cursor.fetchone()  # 0=wins, 1= losses, 2= coins, 3= elo, 4= pulls
    font_size = 25
    font = ImageFont.truetype(font_path, font_size)
    draw.text((105, 30), str(stats[3]), fill="white", font=font)
    draw.text((850, 30), str(stats[0])+"/"+str(stats[1]), fill="white", font=font)
    draw.text((110, 930), str(stats[4]), fill="white", font=font)
    draw.text((855, 930), str(stats[2]), fill="white", font=font)
    
    # Rang pullen und schreiben
    cursor.execute("SELECT COUNT (*) FROM userstats WHERE elo > %s",(stats[3]))
    rank = cursor.fetchone()[0] + 1
    draw.text((105, 60), "#" + str(rank), fill="white", font=font)

    # Spieler pullen und schreiben
    font_size = 20
    font = ImageFont.truetype(font_path, font_size)

    # toplaner
    cursor.execute("SELECT toplaner, jungler, midlaner, botlaner, supporter, coach1, coach2, bench1, bench2, bench3 FROM fantasy WHERE discord_id = %s", (discord_id,))
    spieler = cursor.fetchone()     # 0=toplaner,1=jungler,2=midlaner,3=botlaner,4=supporter,5=coach1,6=coach2,7=bench1,8=bench2,9=bench3
    cursor.execute("SELECT ign, team FROM players WHERE player_id = %s",(spieler[0],))
    toplaner = cursor.fetchone()  # 0=ign, 1=team
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (toplaner[1]))
    liga = cursor.fetchone()[0]
    cursor.execute("SELECT toplaner FROM experience WHERE discord_id = %s",(discord_id,))
    experience = cursor.fetchone()[0]
    draw.text((250,175), toplaner[0], fill="white", font=font)
    draw.text((450,175), toplaner[1], fill="white", font=font)
    draw.text((750,175), str(liga), fill="white", font=font)
    draw.text((900,175), str(experience), fill="white", font=font)

    # andere rollen jungle
    cursor.execute("SELECT ign, team FROM players WHERE player_id = %s",(spieler[1],))
    jungler = cursor.fetchone()  # 0=ign, 1=team
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (jungler[1]))
    liga = cursor.fetchone()[0]
    cursor.execute("SELECT jungler FROM experience WHERE discord_id = %s",(discord_id,))
    experience = cursor.fetchone()[0]
    draw.text((250,222), jungler[0], fill="white", font=font)
    draw.text((450,222), jungler[1], fill="white", font=font)
    draw.text((750,222), str(liga), fill="white", font=font)
    draw.text((900,222), str(experience), fill="white", font=font)

    # mitte
    cursor.execute("SELECT ign, team FROM players WHERE player_id = %s",(spieler[2],))
    midlaner = cursor.fetchone()  # 0=ign, 1=team
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (midlaner[1]))
    liga = cursor.fetchone()[0]
    cursor.execute("SELECT midlaner FROM experience WHERE discord_id = %s",(discord_id,))
    experience = cursor.fetchone()[0]
    draw.text((250,269), midlaner[0], fill="white", font=font)
    draw.text((450,269), midlaner[1], fill="white", font=font)
    draw.text((750,269), str(liga), fill="white", font=font)
    draw.text((900,269), str(experience), fill="white", font=font)

    # bot
    cursor.execute("SELECT ign, team FROM players WHERE player_id = %s",(spieler[3],))
    botlaner = cursor.fetchone()  # 0=ign, 1=team
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (botlaner[1]))
    liga = cursor.fetchone()[0]
    cursor.execute("SELECT botlaner FROM experience WHERE discord_id = %s",(discord_id,))
    experience = cursor.fetchone()[0]
    draw.text((250,316), botlaner[0], fill="white", font=font)
    draw.text((450,316), botlaner[1], fill="white", font=font)
    draw.text((750,316), str(liga), fill="white", font=font)
    draw.text((900,316), str(experience), fill="white", font=font)

    # support
    cursor.execute("SELECT ign, team FROM players WHERE player_id = %s",(spieler[4],))
    supporter = cursor.fetchone()  # 0=ign, 1=team
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (supporter[1]))
    liga = cursor.fetchone()[0]
    cursor.execute("SELECT supporter FROM experience WHERE discord_id = %s",(discord_id,))
    experience = cursor.fetchone()[0]
    draw.text((250,363), supporter[0], fill="white", font=font)
    draw.text((450,363), supporter[1], fill="white", font=font)
    draw.text((750,363), str(liga), fill="white", font=font)
    draw.text((900,363), str(experience), fill="white", font=font)

    # coach1
    cursor.execute("SELECT ign, team FROM players WHERE player_id = %s",(spieler[5],))
    coach1 = cursor.fetchone()  # 0=ign, 1=team
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (coach1[1]))
    liga = cursor.fetchone()[0]
    cursor.execute("SELECT coach1 FROM experience WHERE discord_id = %s",(discord_id,))
    experience = cursor.fetchone()[0]
    draw.text((250,411), coach1[0], fill="white", font=font)
    draw.text((450,411), coach1[1], fill="white", font=font)
    draw.text((750,411), str(liga), fill="white", font=font)
    draw.text((900,411), str(experience), fill="white", font=font)

    # coach2
    cursor.execute("SELECT ign, team FROM players WHERE player_id = %s",(spieler[6],))
    coach2 = cursor.fetchone()  # 0=ign, 1=team
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (coach2[1]))
    liga = cursor.fetchone()[0]
    cursor.execute("SELECT coach2 FROM experience WHERE discord_id = %s",(discord_id,))
    experience = cursor.fetchone()[0]
    draw.text((250,459), coach2[0], fill="white", font=font)
    draw.text((450,459), coach2[1], fill="white", font=font)
    draw.text((750,459), str(liga), fill="white", font=font)
    draw.text((900,459), str(experience), fill="white", font=font)

    # bench1
    if spieler[7] != 0:
        cursor.execute("SELECT ign, team, position FROM players WHERE player_id = %s",(spieler[7],))
        bench1 = cursor.fetchone()  # 0=ign, 1=team, 2=position
        cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (bench1[1]))
        liga = cursor.fetchone()[0]
        cursor.execute("SELECT bench1 FROM experience WHERE discord_id = %s",(discord_id,))
        experience = cursor.fetchone()[0]
        draw.text((250,595), bench1[0], fill="white", font=font)
        draw.text((450,595), bench1[1], fill="white", font=font)
        draw.text((750,595), str(liga), fill="white", font=font)
        draw.text((900,595), str(experience), fill="white", font=font)
        draw.text((450,615), bench1[2], fill="white", font=font)

    # bench2
    if spieler[8] != 0:
        cursor.execute("SELECT ign, team, position FROM players WHERE player_id = %s",(spieler[8],))
        bench2 = cursor.fetchone()  # 0=ign, 1=team
        cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (bench2[1]))
        liga = cursor.fetchone()[0]
        cursor.execute("SELECT bench2 FROM experience WHERE discord_id = %s",(discord_id,))
        experience = cursor.fetchone()[0]
        draw.text((250,643), bench2[0], fill="white", font=font)
        draw.text((450,643), bench2[1], fill="white", font=font)
        draw.text((750,643), str(liga), fill="white", font=font)
        draw.text((900,643), str(experience), fill="white", font=font)
        draw.text((450,663), bench2[2], fill="white", font=font)

    # bench3
    if spieler[9] != 0:
        cursor.execute("SELECT ign, team, position FROM players WHERE player_id = %s",(spieler[9],))
        bench3 = cursor.fetchone()  # 0=ign, 1=team
        cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (bench3[1]))
        liga = cursor.fetchone()[0]
        cursor.execute("SELECT bench3 FROM experience WHERE discord_id = %s",(discord_id,))
        experience = cursor.fetchone()[0]
        draw.text((250,691), bench3[0], fill="white", font=font)
        draw.text((450,691), bench3[1], fill="white", font=font)
        draw.text((750,691), str(liga), fill="white", font=font)
        draw.text((900,691), str(experience), fill="white", font=font)
        draw.text((450,711), bench3[2], fill="white", font=font)

    # Das temp Bild saven und senden
    image_path = 'graphics/team_image.jpg'
    new_image.save('graphics/team_image.jpg')
    await ctx.send(file=discord.File('graphics/team_image.jpg'))

    # Temp Bild löschen
    os.remove(image_path)

# Rename
@commands.check(is_allowed_channel)
@client.command(name="rename")
async def rename(ctx, new_name:str):
    discord_id = ctx.author.id

    # Checken ob alter Name = neuer Name
    cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s", (discord_id,))
    old_name = cursor.fetchone()[0]
    if old_name == new_name:
        await ctx.send("Das ist bereits dein aktueller Name.")
        return
    else:
        cursor.execute("SELECT COUNT(*) FROM fantasy WHERE fantasyname = %s", (new_name,))
        count = cursor.fetchone()[0]

        if count > 0:
            await ctx.send("Der angegebene Name existiert bereits. Bitte wähle einen anderen.")
            return
        cursor.execute("UPDATE fantasy SET fantasyname = %s WHERE discord_id = %s", (new_name, discord_id,))
        db.commit()
        await ctx.send(f"Du hast deinen Namen zu {new_name} geändert.")

traders = set()  # Ein set von aktiven tradern erstellen
open_trades = {} # ein Dictionary von trades erstellen

# Trade ausrichten
@commands.check(is_allowed_channel)
@client.command(name="trade")
async def trade(ctx, input_partner:str, input_position:str):
    discord_id = ctx.author.id
    input_partner = input_partner.lower()
    input_position = input_position.lower()
    display_name = ctx.author.display_name


    if input_partner is None:
        await ctx.send ("Du musst einen Handelspartner eingeben.")
        return
    if discord_id in traders:
        await ctx.send("Du bist bereits in einen Trade involviert.")
        return
    if input_position == "top" or input_position == "toplane":
        position = "toplaner"
    elif input_position == "jgl" or  input_position == "jungle":
        position = "jungler"
    elif input_position == "mid" or input_position == "midlane":
        position = "midlaner"
    elif input_position == "adc" or input_position == "adcarry":
        position = "botlaner"
    elif input_position == "sup" or input_position == "supp" or input_position == "supporter":
        position = "supporter"
    elif input_position == "hc" or input_position == "headcoach":
        position = "coach1"
    elif input_position == "ac" or input_position == "assistant coach" or input_position == "asscoach":
        position = "coach2"
    elif input_position == "b1" or input_position == "bench1":
        position = "bench1"
    elif input_position == "b2" or input_position == "bench2":
        position = "bench2"
    elif input_position == "b3" or input_position == "bench3":
        position = "bench3"
    else:
        await ctx.send("Keine valide position angegeben.")
        return

    cursor.execute("SELECT COUNT(*) FROM fantasy WHERE fantasyname = %s", (input_partner,))
    ergebnis = cursor.fetchone()[0]
    if ergebnis >0:
        partner = input_partner
        cursor.execute(f"SELECT {position} FROM fantasy WHERE discord_id = %s", (discord_id,))
        player_1 = cursor.fetchone()
        if player_1[0] == 0:
            await ctx.send("Du hast keinen Spieler auf dieser Position.")                             # Checken ob man Spieler auf der Position hat wegen bench
            return
        cursor.execute(f"SELECT {position},discord_id FROM fantasy WHERE fantasyname = %s", (partner,))
        player_2 = cursor.fetchone()
        if player_2[0] == 0:
            await ctx.send("Dein Tauschpartner hat keinen Spieler auf dieser Position.")                # Checken ob Gegner nen Spieler auf der Position hat wegen bench
            return
    else:
        await ctx.send("Das Team mit dem du tauschen willst existiert nicht.")
        return
    if player_2[1] in traders:
        await ctx.send("Dein Handelspartner ist bereits in einen Trade involviert.")
        return
    traders.add(discord_id)
    traders.add(int(player_2[1]))                                   ## Discord_ids der Beteiligten zum Handelsset zufügen.
    open_trades[(discord_id,int(player_2[1]),position)] = None

    cursor.execute("SELECT ign FROM players WHERE player_id = %s",({player_1[0]}))
    spieler_ign1 = cursor.fetchone()[0]
    cursor.execute("SELECT ign FROM players WHERE player_id = %s",({player_2[0]}))
    spieler_ign2 = cursor.fetchone()[0]
    await ctx.send(f"{display_name} möchte {spieler_ign1} gegen {spieler_ign2} vom Team {partner} auf der Position {position} tauschen. \n"
    "Verwende !accept oder !decline um den Tausch anzunehmen, bzw. abzulehnen. Ein Tausch kostet euch beide 50 Elo.")

# Trade annehmen
@commands.check(is_allowed_channel)
@client.command(name="accept")
async def accept(ctx):
    discord_id = ctx.author.id
    if discord_id not in traders:
        await ctx.send("Du bist nicht in einem Handel involviert.")
        return
    for trade_key in open_trades:
        if discord_id in trade_key:
            position = trade_key[2]
            if discord_id == trade_key[1]: 
                cursor.execute(f"SELECT {trade_key[2]} FROM fantasy WHERE discord_id = %s", (trade_key[0],))
                player_1 = cursor.fetchone()[0]
                cursor.execute(f"SELECT {trade_key[2]} FROM fantasy WHERE discord_id = %s", (trade_key[1],))
                player_2 = cursor.fetchone()[0]
                cursor.execute(f"UPDATE fantasy SET {position} = %s WHERE discord_id = %s", ( player_2, trade_key[0]))
                cursor.execute(f"UPDATE fantasy SET {position} = %s WHERE discord_id = %s", ( player_1, trade_key[1]))
                cursor.execute(f"UPDATE experience SET {position} = 0 WHERE discord_id = %s", (trade_key[0]))
                cursor.execute(f"UPDATE experience SET {position} = 0 WHERE discord_id = %s", (trade_key[1]))           
                db.commit()
                traders.remove(trade_key[0])
                traders.remove(trade_key[1])
                del open_trades[trade_key]
                await ctx.send("Du hast den Handel akzeptiert. Trade abgeschlossen.")
                break
            else: 
                await ctx.send("Du kannst nicht dein eigenes Angebot annehmen.")

# Trade ablehnen
@commands.check(is_allowed_channel)
@client.command(name="decline")
async def decline(ctx):
    discord_id = ctx.author.id
    if discord_id not in traders:
        await ctx.send("Du bist nicht in einem Handel involviert.")
        return
    for trade_key in open_trades:
        if discord_id in trade_key:
            del open_trades[trade_key]
            traders.remove(trade_key[0])
            traders.remove(trade_key[1])
            await ctx.send("Der Tausch wurde abegelehnt. Trade abgeschlossen.")

            break
    

joined_turnier = set()

@client.command(name="refill")
async def refill(ctx):  
    user_id = ctx.author.id
    if user_id == 284347406420803596 or user_id == 574953391705292801:
        cursor.execute("UPDATE fantasy SET pulls = 5")
        db.commit()
    else:
        await ctx.send("Du hast keine Berechtigung dazu")

# Leaderboard mit Variationen
@client.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx, selection=None):
    if selection is None:
        cursor.execute("SELECT discord_id, losses, wins, elo FROM userstats ORDER BY elo DESC LIMIT 10")
        top10 = cursor.fetchall()
    elif selection == "worst":
        cursor.execute("SELECT discord_id, losses, wins, elo FROM userstats ORDER BY elo ASC LIMIT 10")
        top10 = cursor.fetchall()
    elif selection == "wins":
        cursor.execute("SELECT discord_id, losses, wins, elo FROM userstats ORDER BY wins DESC LIMIT 10")
        top10 = cursor.fetchall()

    # Bild öffnen 
    image = Image.open('graphics/lb.jpg')
    new_image = image.resize((1000, 1000))
    draw = ImageDraw.Draw(new_image)
    font_path = "fonts/Roboto-Black.ttf"
    font_size = 30
    font = ImageFont.truetype(font_path, font_size)
    
    # Darstellung
    i = 0
    for team in top10:
        cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s", (team[0],))
        teamname = cursor.fetchone()[0]
        draw.text((200,(191 + (80 * i))), teamname, fill="white", font=font)
        draw.text((650,(191 + (80 * i))), str(team[1]), fill="white", font=font)
        draw.text((750,(191 + (80 * i))), str(team[2]), fill="white", font=font)
        draw.text((820,(191 + (80 * i))), str(team[3]), fill="white", font=font)
        i = i + 1
        
    # Das temp Bild saven und senden
    image_path = 'graphics/temp_lb.jpg'
    new_image.save('graphics/temp_lb.jpg')
    await ctx.send(file=discord.File('graphics/temp_lb.jpg'))

    # Temp Bild löschen
    os.remove(image_path)

# Neuesten Änderungen
@client.command(name="patchnotes", aliases=["pn"])
async def patchnotes(ctx):
    await ctx.send(settings.patchnotes)

# Assistant für mehr Experience auf einer Rolle
@commands.check(is_allowed_channel)
@client.command(name="assistant")
async def posten(ctx, position:str = None):
    if position is None:
        await ctx.send("Du musst eine neue Position für deinen Assistant Coach angeben.")
        return
    discord_id = ctx.author.id

    position = position.lower()
    if position == "toplane" or position == "top":
        new_postion = "toplaner"
    elif position == "jungle" or position == "jgl":
        new_postion = "jungler"
    elif position == "midlane" or position == "mid":
        new_postion = "midlaner"
    elif position == "adc" or position == "bot":
        new_postion = "botlaner"
    elif position == "sup" or position == "supp" or position == "support":
        new_postion = "supporter"
    else:
        await ctx.send("Bitte gib eine valide Position ein.")
        return
    cursor.execute("UPDATE userstats SET buff = %s WHERE discord_id = %s",(new_postion, discord_id))
    db.commit()
    await ctx.send(f"Dein Assistant Coach unterstützt jetzt die {new_postion} Position.")
 
# Spieler in einem Team suchen aber sucht noch nicht durch die Bank
@commands.check(is_allowed_channel)
@client.command(name="search")
async def search(ctx, player:str = None):
    if player is None:
        await ctx.send("Du musst einen Spieler zum Suchen angeben.")
        return
    cursor.execute("SELECT position,player_id FROM players WHERE ign = %s", (player,))
    position = cursor.fetchone()
    if position is None:
        await ctx.send("Diesen Spieler gibt es nicht.")
        return
    id = position[1]
    position = position[0]
    cursor.execute(f"SELECT fantasyname FROM fantasy WHERE {position} = %s",(id,))
    teams = cursor.fetchall()
    if len(teams) == 0:
        await ctx.send("Kein Team besitzt diesen Spieler.")
        return
    if teams is None:
        await ctx.send("Kein Team hat diesen Spieler.")
        return
    nachricht = "Folgende Teams besitzen diesen Spieler:"
    for team in teams:
        nachricht = nachricht + f" {team[0]},"
    await ctx.send(nachricht)

# Spieler von der Bank mit aktivem Spieler tauschen
@commands.check(is_allowed_channel)
@client.command(name="swap")
async def swap(ctx,bench_nr = None):
    if bench_nr is None:
        await ctx.send("Bitte gib die Bankposition ein die du tauschen möchtest mit b1/b2/b3.")
        return
    discord_id = ctx.author.id
    if bench_nr == "b1" or bench_nr == "1":
        bench_nr = 1
    elif bench_nr == "b2" or bench_nr == "2":
        bench_nr = 2
    elif bench_nr == "b3" or bench_nr == "3":
        bench_nr = 3
    else:
        await ctx.send("Bitte gib eine valide Bankposition zum Tauschen an (b1/b2/b3).")
        return
    if bench_nr == 1:
        cursor.execute("SELECT bench1 FROM fantasy WHERE discord_id = %s", (discord_id,))
        bench_player = cursor.fetchone()[0]
        if bench_player == 0:
            await ctx.send("Du hast keinen Bankspieler zum Tauschen.")
            return
        cursor.execute("SELECT position FROM players WHERE player_id = %s", (bench_player))
        position = cursor.fetchone()[0]
        cursor.execute(f"SELECT {position} FROM fantasy WHERE discord_id = %s", (discord_id,))
        active_player = cursor.fetchone()[0]
        cursor.execute(f"UPDATE fantasy SET {position} = %s, bench1 = %s WHERE discord_id = %s", (bench_player, active_player,discord_id))
        cursor.execute(f"SELECT {position},bench1 FROM experience WHERE discord_id = %s",(discord_id,))
        experience = cursor.fetchone()
        cursor.execute(f"UPDATE experience SET {position} = %s,bench1 = %s WHERE discord_id = %s",(experience[1],experience[0],discord_id))

    elif bench_nr == 2:
        cursor.execute("SELECT bench2 FROM fantasy WHERE discord_id = %s", (discord_id,))
        bench_player = cursor.fetchone()[0]
        if bench_player == 0:
            await ctx.send("Du hast keinen Bankspieler zum Tauschen.")
            return
        cursor.execute("SELECT position FROM players WHERE player_id = %s", (bench_player))
        position = cursor.fetchone()[0]
        cursor.execute(f"SELECT {position} FROM fantasy WHERE discord_id = %s", (discord_id,))
        active_player = cursor.fetchone()[0]
        cursor.execute(f"UPDATE fantasy SET {position} = %s, bench2 = %s WHERE discord_id = %s", (bench_player, active_player, discord_id))
        cursor.execute(f"SELECT {position},bench2 FROM experience WHERE discord_id = %s",(discord_id,))
        experience = cursor.fetchone()
        cursor.execute(f"UPDATE experience SET {position} = %s,bench2 = %s WHERE discord_id = %s",(experience[1],experience[0],discord_id))

    elif bench_nr == 3:
        cursor.execute("SELECT bench3 FROM fantasy WHERE discord_id = %s", (discord_id,))
        bench_player = cursor.fetchone()[0]
        if bench_player == 0:
            await ctx.send("Du hast keinen Bankspieler zum Tauschen.")
            return
        cursor.execute("SELECT position FROM players WHERE player_id = %s", (bench_player))
        position = cursor.fetchone()[0]
        cursor.execute(f"SELECT {position} FROM fantasy WHERE discord_id = %s", (discord_id,))
        active_player = cursor.fetchone()[0]
        cursor.execute(f"UPDATE fantasy SET {position} = %s, bench3 = %s WHERE discord_id = %s", (bench_player, active_player, discord_id))
        cursor.execute(f"SELECT {position},bench3 FROM experience WHERE discord_id = %s",(discord_id,))
        experience = cursor.fetchone()
        cursor.execute(f"UPDATE experience SET {position} = %s,bench3 = %s WHERE discord_id = %s",(experience[1],experience[0],discord_id))
    db.commit()
    await ctx.send("Spieler wurde gewechselt.")

# Spieler von der Bench oder dem TM releasen
@commands.check(is_allowed_channel)
@client.command(name="release", aliases=["entlassen"])
async def release(ctx,bench_nr = None):
    if bench_nr is None:
        await ctx.send("Bitte gib die Bank/Transfermarkt-Position ein die du entlassen möchtest mit b1/b2/b3 bzw. der TM-Nummer.")
        return
    user_id = ctx.author.id

    if bench_nr == "1" or bench_nr == "b1":
        cursor.execute("SELECT bench1 from fantasy WHERE discord_id = %s", (user_id))
        bench_player = cursor.fetchone()[0]
        if bench_player == 0:
            await ctx.send("Du hast keinen Spieler zum releasen.")
            return
        else:
            cursor.execute("UPDATE fantasy set bench1 = 0 WHERE discord_id = %s", (user_id))
            db.commit()
            await ctx.send("Spieler wurde entlassen.")
            return
    elif bench_nr == "2" or bench_nr == "b2":
        cursor.execute("SELECT bench2 from fantasy WHERE discord_id = %s", (user_id))
        bench_player = cursor.fetchone()[0]
        if bench_player == 0:
            await ctx.send("Du hast keinen Spieler zum releasen.")
            return
        else:
            cursor.execute("UPDATE fantasy set bench2 = 0 WHERE discord_id = %s", (user_id))
            db.commit()
            await ctx.send("Spieler wurde entlassen.")
    elif bench_nr == "3" or bench_nr == "b3":
        cursor.execute("SELECT bench3 FROM fantasy WHERE discord_id = %s", (user_id))
        bench_player = cursor.fetchone()[0]
        if bench_player == 0:
            await ctx.send("Du hast keinen Spieler zum releasen.")
            return
        else:
            cursor.execute("UPDATE fantasy set bench3 = 0 WHERE discord_id = %s", (user_id))
            db.commit()
            await ctx.send("Spieler wurde entlassen.")
    else:
        cursor.execute("SELECT seller_id FROM market WHERE id = %s",(bench_nr,))
        seller_id = cursor.fetchone()
        if seller_id is None:
            await ctx.send("Diese ID gibt es nicht auf dem Markt.")
            return
        seller_id = seller_id[0]
        if int(seller_id) == user_id:
            cursor.execute("DELETE FROM market WHERE id = %s",(bench_nr,))
            cursor.execute("UPDATE userstats SET tm_offers = tm_offers + 1 WHERE discord_id = %s",(user_id,))
            db.commit()
            await ctx.send("Spieler wurde entlassen.")
        else:
            await ctx.send("Das ist nicht dein Spieler auf dem Markt.")
            return

#Spieler verkaufen
@commands.check(is_allowed_channel)
@client.command(name="sell", aliases=["verkaufen"])
async def sell(ctx,bench_nr = None, price = None):
    # Eingabe validieren
    if bench_nr is None:
        await ctx.send("Bitte spezifizier die Bankposition , die du verkaufen willst mit b1 oder b2.")
        return
    if price is None:
        await ctx.send("Bitte gib einen Verkaufspreis an.")
        return
    try:
        price = int(price)
    except:
        await ctx.send("Bitte gib ein Zahl als Preis ein.")
        return
    
    discord_id = ctx.author.id

    cursor.execute("SELECT tm_offers FROM userstats WHERE discord_id = %s", (discord_id,))
    available_offers = cursor.fetchone()[0]
    if available_offers == 0:
        await ctx.send("Du hast bereits 3 Angebote auf dem Transfermarkt.")
        return
    if bench_nr == "b1" or bench_nr == "1":
        bench_nr = "bench1"
    elif bench_nr == "b2" or bench_nr == "2":
        bench_nr = "bench2"
    elif bench_nr == "b3" or bench_nr == "3":
        bench_nr = "bench3"
    else:
        await ctx.send("Bitte gib eine gültige Bankposition ein (b1/b2).")
        return

    # Spieler selecten und in die Datenbank stellen
    cursor.execute(f"SELECT {bench_nr} FROM fantasy WHERE discord_id = %s", (discord_id,))
    spieler_id = cursor.fetchone()[0]
    if spieler_id == 0:
        await ctx.send("Du hast keinen Spieler auf dieser Position zum Verkaufen.")
        return

    cursor.execute("SELECT team, position, ign FROM players WHERE player_id = %s",(spieler_id,))
    info = cursor.fetchone()
    spieler_team = info[0]
    spieler_position = info[1]
    spieler_ign = info[2]
    del info
    cursor.execute("SELECT liga FROM teams WHERE teamname = %s", (spieler_team,))
    spieler_liga = cursor.fetchone()[0]
    cursor.execute("INSERT INTO market (seller_id,player_ign,price,team,liga,position,player_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",(discord_id,spieler_ign,price,spieler_team,spieler_liga,spieler_position,spieler_id))
    cursor.execute(f"UPDATE fantasy SET {bench_nr} = 0 WHERE discord_id = %s", (discord_id,))
    cursor.execute(f"UPDATE userstats SET tm_offers = tm_offers - 1 WHERE discord_id = %s", (discord_id,))
    db.commit()
    await ctx.send(f"Du hast den Spieler/Coach {spieler_ign} für {price} auf dem Transfermarkt angeboten. Du kannst noch {available_offers} weitere Spieler/Coaches anbieten.")

# Transfermarkt anzeigen lassen
@commands.check(is_allowed_channel)
@client.command(name="transfermarkt", aliases=["tm"])
async def transfermarkt(ctx,filter=None, start=0):

    print(filter)
    print(start)
    # leeres Bild erstellen und font grundlegend festlegen
    image = Image.open('graphics/tm.jpg')
    new_image = image.resize((1400, 2000))
    draw = ImageDraw.Draw(new_image)
    font_path = "fonts/Roboto-Black.ttf"
    font_size = 20
    font = ImageFont.truetype(font_path, font_size)

    ids = 0
    try:
        filter = int(filter)
    except:
        print("no page passed")
    if filter is None or type(filter) == int:
        cursor.execute("SELECT id FROM market")
        ids = cursor.fetchall()
    if type(filter) == int:
        start = filter - 1
    ligen = ["liga1","liga2","liga3","liga4","liga5","liga6"]
    if filter in ligen:
        filter = int(filter[4])
        cursor.execute("SELECT id FROM market WHERE liga = %s",(filter,))
        ids = cursor.fetchall()
    positions = ["toplaner","jungler","midlaner","botlaner","supporter","coach1","coach2"]
    if filter in positions:
        cursor.execute("SELECT id FROM market WHERE position = %s",(filter,))
        ids = cursor.fetchall()

    i = 0
    for player in ids[(start * 16):]:
        cursor.execute("SELECT player_ign, liga, team, position, price, id FROM market WHERE id = %s",(player,))
        player_info = cursor.fetchone()
        abstand = 25
        x_position = 100
        y_position = 100
        if i % 2 == 0:
            x_position = 140
        else:
            x_position = 770
        y_indicator = math.floor(i/2)
        y_position = 322 + (y_indicator * 200)

        draw.text((x_position - 12,y_position), str(player_info[0]), fill="black", font=font)
        draw.text((x_position,y_position + abstand), str(player_info[1]), fill="black", font=font)
        draw.text((x_position + 10,y_position + abstand *2), str(player_info[2]), fill="black", font=font)
        draw.text((x_position + 45,y_position + abstand *3), str(player_info[3]), fill="black", font=font)
        draw.text((x_position + 10,y_position + abstand *4), str(player_info[4]), fill="black", font=font)
        draw.text((x_position - 23,y_position + abstand *5), str(player_info[5]), fill="black", font=font)

        if i == 15:
            break
        i = i+1


    # Das temp Bild saven und senden
    image_path = 'graphics/temp_tm.jpg'
    new_image.save('graphics/temp_tm.jpg')
    await ctx.send(file=discord.File('graphics/temp_tm.jpg'))

    # Temp Bild löschen
    os.remove(image_path)

# Spieler kaufen
@commands.check(is_allowed_channel)
@client.command(name="buy", aliases=["kaufen"])
async def kaufen(ctx,id = None):
    discord_id = ctx.author.id

    if id is None:
        await ctx.send("Bitte gib die ID ein, welche du kaufen willst.")
        return
    try:
        id = int(id)
    except:
        await ctx.send("Bitte gib eine Zahl als ID ein.")
        return
    cursor.execute("SELECT price FROM market WHERE id = %s",(id,))
    price_player = cursor.fetchone()[0]
    cursor.execute("SELECT coins FROM userstats WHERE discord_id = %s", (discord_id,))
    coins_user = cursor.fetchone()[0]
    if price_player > coins_user:
        await ctx.send("Du hast nicht genügend coins um diesen Spieler/Coach zu kaufen.")
        return
    cursor.execute("SELECT bench1, bench2, bench3 FROM fantasy WHERE discord_id = %s", (discord_id,))
    bench = cursor.fetchone()
    if bench[0] != 0 and bench[1] != 0 and bench[2] != 0:
        await ctx.send("Du hast kein Platz auf deiner Bank, bitte entlasse erst einen Spieler.")
        return
    cursor.execute("SELECT player_id,player_ign FROM market WHERE id = %s",(id,))
    player_info = cursor.fetchone()
    player_id = player_info[0]
    ign = player_info[1]
    if bench[0] == 0:
        bench = "bench1"
    elif bench[1] == 0:
        bench = "bench2"
    elif bench[2] == 0:
        bench = "bench3" 
    cursor.execute(f"UPDATE fantasy SET {bench} = %s WHERE discord_id = %s",(player_id,str(discord_id)))     # Spieler geben
    cursor.execute("UPDATE userstats SET coins = coins - %s WHERE discord_id = %s",(price_player,discord_id))
    db.commit()
    cursor.execute("SELECT seller_id FROM market WHERE id = %s",(id,))
    seller_id = cursor.fetchone()[0]
    cursor.execute("UPDATE userstats SET coins = coins + %s,tm_offers = tm_offers + 1 WHERE discord_id = %s",(price_player,str(seller_id)))                    # coins geben an seller
    cursor.execute("DELETE FROM market WHERE id = %s",(id))                                                          # Spieler vom Markt löschen
    db.commit()
    await ctx.send(f"Du hast {ign} gekauft.")

# Marktorder auflösen und Spieler zurück auf die Bank nehmen
@commands.check(is_allowed_channel)
@client.command(name="cancel")
async def cancel(ctx,id=None):
    discord_id = ctx.author.id
    if id is None:
        await ctx.send("Bitte gib eine market_id an die du zurücknehmen möchstest.")
        return
    try:
        int(id)
    except:
        await ctx.send("Bitte gib eine Zahl als id an.")
        return
    cursor.execute("SELECT player_id,seller_id,price FROM market WHERE id = %s",(id))
    request = cursor.fetchone()
    if request is None:
        await ctx.send("Diese Id ist momentan nicht auf dem Markt.")
        return
    discord_id = str(discord_id)
    if request[1] != discord_id:
        await ctx.send("Dieser Spieler gehörte nie dir.")
        return
    else:
        cursor.execute("SELECT bench1, bench2, bench3 FROM fantasy WHERE discord_id = %s", (discord_id,))
        bench = cursor.fetchone()
        if bench[0] != 0 and bench[1] != 0 and bench[2] != 0:
            await ctx.send("Du hast kein Platz auf deiner Bank, bitte entlasse erst einen Spieler.")
            return
        if bench[0] != 0 and bench[1] != 0:
            cursor.execute("UPDATE fantasy set bench3 = %s WHERE discord_id = %s", (request[0],discord_id))
        if bench[0] != 0:
            cursor.execute("UPDATE fantasy set bench2 = %s WHERE discord_id = %s", (request[0],discord_id))
        else:
            cursor.execute("UPDATE fantasy set bench1 = %s  WHERE discord_id = %s", (request[0],discord_id))
        cursor.execute("UPDATE userstats set tm_offers = tm_offers + 1 WHERE discord_id = %s", (discord_id,))
        cursor.execute("DELETE FROM market WHERE id = %s", (id,))
        db.commit()
        await ctx.send(f"Du hast den Spieler vom Transfermarkt genommen.")

# Checken welche Ids man auf dem Markt hat
@commands.check(is_allowed_channel)
@client.command(name="offers")
async def offers(ctx):
    discord_id = ctx.author.id
    cursor.execute("SELECT id FROM market WHERE seller_id = %s",(discord_id,))
    request = cursor.fetchall()
    if request is None:
        await ctx.send("Du hast keine Spieler auf dem Markt (Lüg nicht!).")
        return
    message = ("")
    anzahl = (len(request))
    if anzahl == 3:
        message = message + f"{request[0]}," + f"{request[1]}," + f"{request[2]}"
    elif anzahl == 2:
        message = message + f"{request[0]}," + f"{request[1]}"
    elif anzahl == 1:
        message = message + f"{request[0]}"
    await ctx.send(f"Du hast die Ids: {message} auf dem Markt.")
      
# pulls kaufen
@commands.check(is_allowed_channel)
@client.command(name="shop")
async def shop(ctx, anzahl = None):
    discord_id = ctx.author.id
    try:
        anzahl = int(anzahl)
    except:
        await ctx.send("Bitte gib eine valide Zahl zum Kaufen ein.")
        return
    cursor.execute("SELECT coins FROM userstats WHERE discord_id = %s",(discord_id,))
    coins = cursor.fetchone()[0]
    preis_requested = anzahl * 2
    if preis_requested > coins:
        await ctx.send("Das kannst du dir nicht leisten, 1 Pull kostet 2 prm-coins.")
        return

    cursor.execute("UPDATE userstats set pulls = pulls + %s,coins = coins - %s WHERE discord_id = %s",(anzahl,preis_requested,discord_id))
    db.commit()
    await ctx.send(f"Du hast {anzahl} pulls für {preis_requested} prm-coins gekauft.")

# Orga Features
@commands.check(is_allowed_channel)
@client.command(name="orga")
async def orga(ctx, befehl=None,choice=None):
    discord_id = ctx.author.id

    if befehl == None:
        await ctx.send("Du kannst eine Orga erstellen mit !orga create, einem beitreten mit !orga join und informationen bekommen mit !orga info, am Brawl kann deine Orga mit !orga signup teilnehmen.")
        return
    
    # Orga createn
    if befehl == "create":
        if choice is None:
            await ctx.send("Bitte gib einen Namen für die Orga ein.")
            return
        choice = str(choice)
        cursor.execute("SELECT COUNT(*) FROM clans WHERE clanname = %s LIMIT 1",(choice,))
        anzahl_clans = cursor.fetchone()[0]
        if anzahl_clans == 0:
            cursor.execute("INSERT INTO clans SET clanname = %s, leader = %s ",(choice,discord_id))
            cursor.execute("UPDATE userstats SET clan = %s WHERE discord_id = %s",(choice,discord_id))
            db.commit()
            await ctx.send(f"Orga {choice} wurde erstellt.")
            return
        else:
            await ctx.send("Diese Orga gibt es bereits.")
            return
        
    # Anfrage zum Joinen stellen
    elif befehl == "join":
        if choice is None:
            await ctx.send("Bitte gib einen Namen für die Orga ein.")
            return
        choice = str(choice)
        cursor.execute("SELECT COUNT(*) FROM clans WHERE clanname = %s LIMIT 1",(choice,))
        anzahl_clans = cursor.fetchone()[0]
        if anzahl_clans == 0:
            await ctx.send("Diese Orga gibt es nicht.")
            return
        else:
            cursor.execute("UPDATE userstats SET clan_req = %s WHERE discord_id = %s",(choice,discord_id))
            db.commit()
            await ctx.send("Anfrage gesendet, kann angekommen werden mit !orga accept und deinem Namen.")

    # Neues Mitglied aufnehmen
    elif befehl == "accept":
        if choice is None:
            await ctx.send("Bitte spezifizier wen du akzeptieren möchstest.")
            return
        cursor.execute("SELECT discord_id FROM fantasy WHERE fantasyname = %s",(choice,))
        new_discord_id = cursor.fetchone()
        if discord_id is None:
            await ctx.send("Team existiert nicht.")
            return
        new_discord_id = new_discord_id[0]
        cursor.execute("SELECT clan_req FROM userstats WHERE discord_id = %s",(new_discord_id,))
        req = cursor.fetchone()[0]
        if req == "leer":
            await ctx.send("Team hat keine Anfrage gestellt.")
            return
        cursor.execute("SELECT clanname FROM clans WHERE leader = %s",(discord_id,))
        eigener_clan = cursor.fetchone()
        if eigener_clan is None:
            await ctx.send("Du hast nicht die nötigen Rechte (nicht Leader?).")
            return
        else:
            eigener_clan = eigener_clan[0]
        if req == eigener_clan:
            cursor.execute("UPDATE userstats SET clan = %s, clan_req = 'leer' WHERE discord_id = %s",(req,new_discord_id))
            db.commit()
            await ctx.send(f"{choice} wurde in den Orga aufgenommen.")
        else:
            await ctx.send("Anfrage und deine Orga stimmen nicht überein.")

    # Info über einen Clan enthalten
    elif befehl == "info":
        if choice is None:
            await ctx.send("Bitte gib ein Organamen ein über den du mehr erfahren willst.")
            return
        cursor.execute("SELECT leader, rep FROM clans WHERE clanname = %s",(choice,))
        info = cursor.fetchone()
        if len(info) == 0:
            await ctx.send("Diese Orga gibt es nicht.")
            return
        cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s",(info[0]))
        fantasyname = cursor.fetchone()[0]
        await ctx.send(f"Die Orga wird geleitet von {fantasyname} und hat {info[1]} reputation.")

    # Orga verlassen als Einzeluser
    elif befehl == "leave":
        cursor.execute("SELECT clan FROM userstats WHERE discord_id = %s",(discord_id,))
        current_clan = cursor.fetchone()
        if current_clan == "leer":
            await ctx.send("Du bist in keiner Orga.")
            return
        cursor.execute("SELECT clanname FROM clans WHERE leader = %s",(discord_id,))
        leading_clan = cursor.fetchone()
        if leading_clan is None:
            cursor.execute("UPDATE userstats SET clan = 'leer' WHERE discord_id = %s",(discord_id,))
            db.commit()
            await ctx.send("Du hast die Orga verlassen.")
            return 
        else:
            await ctx.send(f"Du bist Leader von {leading_clan[0]} und kannst die Orga nicht einfach verlassen. Löse Sie auf mit !orga disband oder bleib.")
            return

    # Ganze Orga auflösen
    elif befehl == "disband":
        cursor.execute("SELECT clanname FROM clans WHERE leader = %s",(discord_id,))
        clan = cursor.fetchone()
        if clan is None:
            await ctx.send("Du bist nicht Leader einer Orga.")
            return
        else:
            cursor.execute("DELETE FROM clans WHERE leader = %s",(discord_id,))
            cursor.execute("UPDATE userstats SET clan = 'leer' WHERE clan = %s",(clan,))
            db.commit()
            await ctx.send("Orga wurde aufgelöst.")

    # Zum Orga Showdown anmelden
    elif befehl == "signup":
        cursor.execute("SELECT clanname FROM clans WHERE leader = %s",(discord_id,))
        clan = cursor.fetchone()
        if clan is None:
            await ctx.send("Du bist nicht Leader einer Orga.")
            return
        else:
            clan = clan[0]
        cursor.execute("SELECT COUNT(*) FROM userstats WHERE clan = %s",(clan,))
        member_count = cursor.fetchone()[0]
        if member_count >= 3:
            cursor.execute("UPDATE clans SET signup = 'yes' WHERE clanname = %s",(clan,))
            db.commit()
            await ctx.send("Erfolgreich für den Orga Showdown angemeldet.")
        else:
            await ctx.send("Zu wenige Mitglieder (mindestens 3) in der Orga.")
            return
        
        # Checken ob genügend Teams anwesend sind um ein Brawl zu veranstalten
        # Channel für den Brawl
        channel = client.get_channel(1248705401709662280)
        cursor.execute("SELECT COUNT(*) FROM clans WHERE signup = 'yes'")
        orgas_available = cursor.fetchone()[0]
        if orgas_available < 4:
            still_needed = 4 - orgas_available
            await channel.send(f"Noch {still_needed} Orgas für einen Brawl benötigt.")
            return
        else:
            cursor.execute("SELECT clanname FROM clans WHERE signup = 'yes'")
            orgas = cursor.fetchall()
            await ctx.send("Es findet ein Orga-Brawl in #Brawls statt.")
            orga1 = orgas[0][0]
            orga2 = orgas[1][0]
            orga3 = orgas[2][0]
            orga4 = orgas[3][0]
            await channel.send(f"Es treten an: {orga1}, {orga2}, {orga3} und {orga4}.")
            scenario = randint(1,3)
            # In Szenario 1 passiert nichts
            if scenario == 2:
                temp_orga = orga2
                orga2 = orga3
                orga3 = temp_orga
            elif scenario == 3:
                temp_orga = orga2
                orga2 = orga4
                orga4 = temp_orga
            await channel.send(f"Zuerst spielt {orga1} gegen {orga2} und {orga3} gegen {orga4}.")
            winner1 = await orga_duel(orga1,orga2)
            if winner1 == orga1:
                looser1 = orga2
            else:
                looser1 = orga1
            winner2 = await orga_duel(orga3,orga4)
            if winner2 == orga3:
                looser2 = orga4
            else:
                looser2 = orga3
            await channel.send(f"Duel 1 gewinnt die Orga {winner1}.")
            await channel.send(f"Duel 2 gewinnt die Orga {winner2}.")
            await channel.send("Es treten jeweils die Gewinner und Verlierer gegeneinander an.")
            first_place = await orga_duel(winner1,winner2)
            if first_place == winner1:
                second_place = winner2
            else:
                second_place = winner1
            third_palce = await orga_duel(looser1,looser2)
            if third_palce == looser1:
                fourth_place = looser2
            else:
                fourth_place = looser1
            cursor.execute("UPDATE clans SET rep = rep + 2, signup = 'no' WHERE clanname = %s",(first_place,))
            cursor.execute("UPDATE clans SET rep = rep + 1, signup = 'no' WHERE clanname = %s",(second_place,))
            cursor.execute("UPDATE clans SET rep = rep - 1, signup = 'no' WHERE clanname = %s",(third_palce,))
            cursor.execute("UPDATE clans SET rep = rep - 2, signup = 'no' WHERE clanname = %s",(fourth_place,))
            db.commit()
            await channel.send(f"{first_place} gewinnt den Brawl. {second_place} wird Zweiter, {third_palce} Dritter und {fourth_place} bildet das Schlusslicht.")

        
    # Orga Leaderboard anzeigen
    elif befehl == "leaderboard" or befehl == "lb":
        cursor.execute("SELECT clanname FROM clans ORDER BY rep DESC LIMIT 10")
        top10 = cursor.fetchall()
        image = Image.open('graphics/orga_lb.jpg')
        new_image = image.resize((1000, 1000))
        draw = ImageDraw.Draw(new_image)
        font_path = "fonts/Roboto-Black.ttf"
        font_size = 30
        font = ImageFont.truetype(font_path, font_size)

        i = 0
        for orga in top10:
            cursor.execute("SELECT rep FROM clans WHERE clanname = %s", (orga[0],))
            rep = cursor.fetchone()[0]
            draw.text((200,(191 + (80 * i))), orga[0], fill="white", font=font)
            draw.text((820,(191 + (80 * i))), str(rep), fill="white", font=font)
            i = i + 1

        # Das temp Bild saven und senden
        image_path = 'graphics/temp_orga_lb.jpg'
        new_image.save('graphics/temp_orga_lb.jpg')
        await ctx.send(file=discord.File('graphics/temp_orga_lb.jpg'))

        # Temp Bild löschen
        os.remove(image_path)

async def orga_duel(orga1,orga2):
    cursor.execute("SELECT discord_id FROM userstats WHERE clan = %s ORDER BY elo DESC LIMIT 2",(orga1,))
    top2 = cursor.fetchall()
    teams_orga1 = []
    teams_orga1.append(top2[0][0])
    teams_orga1.append(top2[1][0])
    cursor.execute("SELECT discord_id FROM userstats WHERE clan = %s ORDER BY elo ASC LIMIT 1",(orga1,))
    lowest_elo = cursor.fetchone()[0]
    teams_orga1.append(lowest_elo)

    cursor.execute("SELECT discord_id FROM userstats WHERE clan = %s ORDER BY elo DESC LIMIT 2",(orga2,))
    top2 = cursor.fetchall()
    teams_orga2 = []
    teams_orga2.append(top2[0][0])
    teams_orga2.append(top2[1][0])
    cursor.execute("SELECT discord_id FROM userstats WHERE clan = %s ORDER BY elo ASC LIMIT 1",(orga2,))
    lowest_elo = cursor.fetchone()[0]
    teams_orga2.append(lowest_elo)

    main = await calculate_winner(teams_orga1[0],teams_orga2[0])
    academy = await calculate_winner(teams_orga1[1],teams_orga2[1])
    rentner = await calculate_winner(teams_orga1[2],teams_orga2[1])
    ergebnis = main + academy + rentner
    if ergebnis >= 5:
        return orga2
    else:
        return orga1

# Rotieren der Bank
@commands.check(is_allowed_channel)
@client.command(name="rotate")
async def rotate(ctx):
    discord_id = ctx.author.id
    cursor.execute("SELECT bench1,bench2,bench3 FROM fantasy WHERE discord_id = %s",(discord_id))
    bench = cursor.fetchone()
    cursor.execute("UPDATE fantasy SET bench1 = %s, bench2 = %s, bench3 = %s WHERE discord_id = %s",(bench[2],bench[0],bench[1],discord_id))
    cursor.execute("SELECT bench1,bench2,bench3 FROM experience WHERE discord_id = %s",(discord_id))
    bench_experience = cursor.fetchone()
    cursor.execute("UPDATE experience SET bench1 = %s, bench2 = %s, bench3 = %s WHERE discord_id = %s",(bench_experience[2],bench_experience[0],bench_experience[1],discord_id))
    db.commit()
    await ctx.send("Spieler wurden rotiert.")

# Nach spezifischem Spieler auf dem Markt schauen
@commands.check(is_allowed_channel)
@client.command(name="scout")
async def scout(ctx,player=None):
    discord_id = ctx.author.id

    if player is None:
        await ctx.send("Bitte gib einen Spieler an, nachdem du suchen willst.")
        return
    cursor.execute("SELECT id,price FROM market WHERE player_ign = %s",(player,))
    talent = cursor.fetchone()
    if talent is None:
        await ctx.send("Spieler wurde nicht auf dem TM gefunden.")
        return
    await ctx.send(f"{player} ist auf dem Markt unter id {talent[0]} für {talent[1]} coins.")

@commands.check(is_allowed_channel)
@client.command(name="climb")
async def climb(ctx):
    discord_id = ctx.author.id
    cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s",(discord_id,))
    fantasyname = cursor.fetchone()[0]
    coins = 0
    wins = 0
    winner = ""
    Leben = 3
    while Leben > 0:
        if wins < 2:
            cursor.execute("SELECT teamname FROM teams WHERE liga = 5 ORDER BY RAND() LIMIT 1")
            team = cursor.fetchone()[0]
        elif wins < 4:
            cursor.execute("SELECT teamname FROM teams WHERE liga = 4 ORDER BY RAND() LIMIT 1")
            team = cursor.fetchone()[0]
        elif wins < 6:
            cursor.execute("SELECT teamname FROM teams WHERE liga = 3 ORDER BY RAND() LIMIT 1")
            team = cursor.fetchone()[0]
        elif wins < 8:
            cursor.execute("SELECT teamname FROM teams WHERE liga = 2 ORDER BY RAND() LIMIT 1")
            team = cursor.fetchone()[0]
        elif wins > 8:
            cursor.execute("SELECT teamname FROM teams WHERE liga = 1 ORDER BY RAND() LIMIT 1")
            team = cursor.fetchone()[0]
        print(team)
        winner = await bot_match(discord_id,team)
        if winner == "user":
            wins = wins + 1
            await ctx.send(f"Gewonnen gegen {team}")
        if winner == "bot":
            Leben = Leben - 1
            await ctx.send(f"Spiel verloren gegen {team}")
    coins = math.floor(wins/2)
    cursor.execute("UPDATE userstats SET coins = coins + %s WHERE discord_id = %s",(coins,discord_id))
    db.commit()
    await ctx.send(f"Die letzte Partie wurde gegen {team} verloren und du erhälst {coins} coins.")
    
    image = Image.open('graphics/climb.jpg')
    new_image = image.resize((1000, 1000))
    draw = ImageDraw.Draw(new_image)
    font_path = "fonts/Roboto-Black.ttf"
    font_size = 60
    font = ImageFont.truetype(font_path, font_size)

    draw.text((400, 180,), fantasyname, fill="white", font=font)
    font_size = 100
    font = ImageFont.truetype(font_path, font_size)
    draw.text((500, 450,), str(wins), fill="white", font=font)
    font_size = 50
    font = ImageFont.truetype(font_path, font_size)
    draw.text((855, 900,), str(coins), fill="white", font=font)
    draw.text((50, 900,), team, fill="white", font=font)


    # Das temp Bild saven und senden
    image_path = 'graphics/temp_climb.jpg'
    new_image.save('graphics/temp_climb.jpg')
    await ctx.send(file=discord.File('graphics/temp_climb.jpg'))

    # Temp Bild löschen
    os.remove(image_path)
    

async def bot_match(discord_id,team):
    winners = []
    # Team 1
    cursor.execute("SELECT toplaner,jungler,midlaner,botlaner,supporter FROM fantasy WHERE discord_id = %s",(discord_id,))
    team1_ids = cursor.fetchone()
    team1_prm_teams = []
    for spieler in team1_ids:
        cursor.execute("SELECT team FROM players WHERE player_id = %s",(spieler,))
        team1_prm_teams.append(cursor.fetchone()[0])
    team1_pool = []
    for spieler in team1_ids:
        cursor.execute("SELECT position FROM players WHERE player_id = %s", (spieler,))
        position = cursor.fetchone()[0]
        cursor.execute("SELECT liga FROM teams WHERE teamname = (SELECT team FROM players WHERE player_id = %s)",(spieler,))
        power = 7 - cursor.fetchone()[0]
        cursor.execute(f"SELECT {position} FROM experience WHERE discord_id = %s",(discord_id,))
        experience = cursor.fetchone()[0]
        power = power + (0.5 * math.floor(experience/1000))
        if len(set(team1_prm_teams)) == 1:
            power = power + 0.5
        elif position == "jungler" or position == "midlaner":
            if team1_prm_teams[1] == team1_prm_teams[2]:
                power = power + 0.25
        elif position == "botlaner" or position == "supporter":
            if team1_prm_teams[3] == team1_prm_teams[4]:
                power = power + 0.25
        power = round(2 ** power)
        team1_pool.append(power)
    
    # Team 2
    cursor.execute("SELECT toplaner,jungler,midlaner,botlaner,supporter FROM teams WHERE teamname = %s",(team,))
    igns = cursor.fetchone()
    print(igns)
    team2_ids = []
    for ign in igns:
        cursor.execute("SELECT player_id FROM players WHERE ign = %s",(ign,))
        team2_ids.append(cursor.fetchone()[0])

    team2_pool = []

    for spieler in team2_ids:
        cursor.execute("SELECT position FROM players WHERE player_id = %s", (spieler,))
        position = cursor.fetchone()[0]
        cursor.execute("SELECT liga FROM teams WHERE teamname = (SELECT team FROM players WHERE player_id = %s)",(spieler,))
        power = 7 - cursor.fetchone()[0]
        power = power + (0.5 * math.floor(experience/1000))
        power = power + 0.5
        power = round(2 ** power)
        team2_pool.append(power)
    
    # Auswürfeln
    winner = "x"
    i = 0
    while i < 5:
        damn = (team1_pool[i] + team2_pool[i])
        dice = randint(0,damn)
        if dice <= team1_pool[i]:
            winners.append(1)
        else:
            winners.append(2)
        i = i + 1
    
    # Entscheidung
    if winners.count(1) >= 3:
        winner = "user"
    else:
        winner = "bot"
    return winner



client.run("--")
