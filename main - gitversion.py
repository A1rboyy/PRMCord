import discord
from discord.ext import commands
import pymysql
from random import randint
import asyncio
import settings
import math

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    print("We are ready")
    print("-------")


db = pymysql.connect(host = "--", user = "--", password = "--", database = "--", port = --)
cursor = db.cursor()

allowed_channel_id = [1211285687714971679,1211307699107536926,1211296263115636766,1215689387342434366,1215802619709362217]

AceChannel = [1215774155140632618,1215774179144765510,1215774203987361994,1215774294055976970,1215775381588545556,1216782260594937947]

allowed_channel_id = allowed_channel_id + AceChannel

q_channel = [1215689387342434366,1215774179144765510]

client.remove_command("help")

@client.command(name="help")
async def help(ctx):
    embed = discord.Embed(title="Alle Commands", color=discord.Color.blue())
    embed.set_image(url="https://cdn.discordapp.com/attachments/1195342755610759219/1204485581611081799/info.png?ex=65d4e79c&is=65c2729c&hm=adccc077d4082aff54a603cfc574d2291db7404fa693eb81eba79302aa99a120&")
    await ctx.send(embed=embed)

async def is_allowed_channel(ctx):
    if ctx.channel.id not in allowed_channel_id:
        print("Command im falschen Channel")
        return False
    return True

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Bitte benutze den offiziell Server. https://discord.gg/QtEkcCQnRq ")

@client.command(name="odds", aliases=["wahrscheinlichkeiten"])
async def odds(ctx):
    embed = discord.Embed(title="Alle Wahrscheinlichkeiten", color=discord.Color.blue())
    embed.add_field(name="Stärke von Spielern", value=settings.explain_spieler)
    embed.add_field(name="Einfluss von Coaches", value=settings.einfluss_coaches)
    embed.add_field(name="Synergien", value=settings.synergies)
    embed.add_field(name="Pulls", value=settings.chances_pulls)
    
    await ctx.send(embed=embed)


@client.command()
async def noice(ctx):
    await ctx.send("Du bist nice")

@client.command(name="info")
async def get_team_info(ctx, team: str,):
    if team is None:
        await ctx.send("Du musst ein Teamnamen in Anführungszeichen angeben!")
        return
    cursor.execute("SELECT toplaner, jungler, midlaner, adc, supporter FROM teams WHERE teamname = %s", (team,))     
    players = cursor.fetchone()

    if not players:
        await ctx.send(f"Zu dem Team {team} gibt es keine Information.")
    else:
        player_list = ",".join(players)
        await ctx.send(f"Die Spieler in {team} sind: {player_list}")


@client.command(name="register")
@commands.check(is_allowed_channel)
async def register_user(ctx):
    user_id = ctx.author.id

    cursor.execute("SELECT * FROM fantasy WHERE discord_id = %s", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute("INSERT INTO fantasy (discord_id) VALUES (%s)", (user_id,))
        await randomize_team(ctx)
        db.commit()

        await ctx.send(f"Du wurdest erfolgreich registriert!")
    else:
        await ctx.send("Du bist bereits registriert!")

pulling_users = set()

@commands.check(is_allowed_channel)
@client.command(name="pull")
async def pull(ctx):
    user_id = ctx.author.id
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if user_id not in pulling_users:
        cursor.execute("SELECT fantasyname,pulls FROM fantasy WHERE discord_id = %s", (user_id,))
        infos_team = cursor.fetchone()
        if infos_team is None:
            await ctx.send("Du musst dich erst registrieren mit !register.")
            return
        anzahl_pulls = infos_team[1]
        team_name = infos_team[0]
        if anzahl_pulls >0:
            anzahl_pulls = anzahl_pulls - 1
            pulling_users.add(user_id)
            cursor.execute("UPDATE fantasy SET pulls = pulls -1 WHERE discord_id = %s", (user_id,))
            db.commit()

            cursor.execute("SELECT ign, team24sp, position from players ORDER BY RAND()")              ## Das actual Pulling
            player = cursor.fetchone()
            cursor.execute("SELECT div24sp FROM teams WHERE teamname = %s", (player[1]))
            teamdiv_von_player = cursor.fetchone()[0]
            embed = discord.Embed(title=f"{team_name} hat Spieler/Coach gezogen!", color=discord.Colour.blue())
            value = (f"Spieler: **{player[0]}** \n Team: **{player[1]}** \n Liga: **({teamdiv_von_player})** \n Position: **{player[2]}**")
            embed.add_field(name="Gezogener Spieler/Coach", value=value)
            value = ('Mit "ja" tauschst du gegen deinen aktuellen Spieler auf der Position, mit "b1" oder "b2" gegen deinen Spieler auf der jeweilligen Bankposition, mit "nein", lehnst du ihn ab.')
            embed.add_field(name="Hinzufügen?", value=value)

            await ctx.send(embed=embed)   ## Embed absenden

            def check(message):
                return message.author == ctx.author and message.content.lower() in ["ja", "nein","b1","b2"]
            try:
                response = await client.wait_for("message", check=check, timeout=45.0)
            except asyncio.TimeoutError:
                await ctx.send(f"Keine Antwort erbracht, du hast noch {anzahl_pulls} pulls übrig.")
                pulling_users.remove(user_id)
                return
            if response.content.lower() == "ja":
                position = player[2]
                if player[2] == "headcoach":
                    position = "coach1"
                elif player[2] == "asscoach":
                    position = "coach2"
                
                cursor.execute(f"UPDATE fantasy SET {position} = %s WHERE discord_id = %s", ({player[0]}, user_id))
                db.commit()

                await ctx.send(f"Du hast den Spieler/Coach ausgetauscht. Du hast noch {anzahl_pulls} pulls übrigs.")

            elif response.content.lower() == "nein":
                await ctx.send(f"Du hast den Spieler/Coach nicht in dein Team aufgenommen. Du hast noch {anzahl_pulls} pulls übrig.")

            elif response.content.lower() == "b1":
                position = "bench1"
                cursor.execute(f"UPDATE fantasy SET {position} = %s WHERE discord_id = %s", ({player[0]}, user_id))
                db.commit()
                await ctx.send("Du hast den Spieler auf Bank1 gesetzt.")

            elif response.content.lower() == "b2":
                position = "bench2"
                cursor.execute(f"UPDATE fantasy SET {position} = %s WHERE discord_id = %s", ({player[0]}, user_id))
                db.commit()
                await ctx.send("Du hast den Spieler auf Bank2 gesetzt.")

            pulling_users.remove(user_id)
            
        else:
            await ctx.send("Du hast keine Pulls mehr übrig.")
    else:
        await ctx.send("Du bist bereits dabei einen Spieler/Coach zu ziehen.")

q_users = []
channel_von_q = []

@commands.check(is_allowed_channel)
@client.command(name="q")
async def q(ctx):
    user_id = ctx.author.id                                             ## Die discord Id vom user abfragen der in q geht
    channel_id = ctx.channel.id
    channel_id = client.get_channel(channel_id)
    user_name = ctx.author.display_name

    if ctx.channel.id not in q_channel:
        await ctx.send("Schau dir nochmal ganz genau den Channelnamen an...")
        return

    global channel_von_q
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if user_id not in q_users:
        q_users.append(user_id)                                         ## ihn in die q hinzufügen
        if channel_id not in channel_von_q:
            channel_von_q.append(channel_id)
        await ctx.send(f"{user_name} ist der Warteschlange beigetreten.")

        team_1 = None                                                   ## alte teams leeren
        team_2 = None

        if len(q_users) >= 2:                                       # Wenn der user der zweite ist der in q geht
            team_1 = q_users.pop(0)                                 # beide User aus der q werfen und als team 1 und 2 abspeichern
            team_2 = q_users.pop(0)
            print(team_1, team_2)
            print(q_users)  
        elif len(q_users) == 1:                                     # wenn der user alleine in q ist
            await asyncio.sleep(30)
            if len(q_users) == 1:
                team_2 = generate_random_enemy()
                team_1 = q_users.pop(0)                             # user aus der q werfen
            else:
                return
                
        cursor.execute("SELECT toplaner, jungler, midlaner, adc, supporter, coach1, coach2, fantasyname, elo FROM fantasy WHERE discord_id = %s", (team_1,))
        team1 = cursor.fetchone()
        cursor.execute("SELECT toplaner, jungler, midlaner, adc, supporter, coach1, coach2, fantasyname, elo FROM fantasy WHERE discord_id = %s", (team_2,))
        team2 = cursor.fetchone()
        if team1 is None:
            print("Fehler in der Q ohne Folge")
            return
        if team2 is None:
            await ctx.send("Fehler 2")
            return
        embed = discord.Embed(title="Matchup")
        value = (f"{team1[0]}\n{team1[1]}\n{team1[2]}\n{team1[3]}\n{team1[4]}\n\nCoaches\n{team1[5]}\n{team1[6]}")
        embed.add_field(name=f"{team1[7]}", value=value)
        value = (f"{team2[0]}\n{team2[1]}\n{team2[2]}\n{team2[3]}\n{team2[4]}\n\nCoaches\n{team2[5]}\n{team2[6]}")
        embed.add_field(name=f"{team2[7]}", value=value)

        winners = await matchup(team_1,team_2)

        value = (f"Toplane gewinnt {winners[0]} \nJungle gewinnt {winners[1]} \nMidlane gewinnt {winners[2]} \nAdc gewinnt {winners[3]} \n Support gewinnt {winners[4]}.")
        embed.add_field(name="Winners", value=value)

        team1_wins = winners.count(team1[7])            ### Overall decision

        if team1_wins >= 3:
            gewinner = team1[7]
            verlierer = team2[7]
        else:
            gewinner = team2[7]
            verlierer = team1[7]

        
        my_team_elo = team1[8]
        enemy_team_elo = team2[8]                                  ##  Konsequenzen

        def kleiner_change():
            return round(20 - (abs(my_team_elo - enemy_team_elo) / 25))
        def großer_change():
            return round(20 + (abs(my_team_elo - enemy_team_elo) / 40))
        def gleicher_change():
            return 20


        if gewinner == team1[7]:               ### Wenn der gewinner das erste Team ist
            if my_team_elo > enemy_team_elo:
                elo_change = kleiner_change()
            elif my_team_elo < enemy_team_elo:
                elo_change = großer_change()
            else:
                elo_change = gleicher_change()    
        else:                                       ### Sonst ist das zweite Team der Gewinner
            if enemy_team_elo > my_team_elo:
                elo_change = kleiner_change()
            elif enemy_team_elo < my_team_elo:
                elo_change = großer_change()
            else:
                elo_change = gleicher_change()
        if elo_change <3:
            elo_change = 3
        elif elo_change >30:
            elo_change = 30


        cursor.execute("UPDATE fantasy SET elo = elo + %s, wins = wins + 1 WHERE fantasyname = %s", (elo_change +1, gewinner,))
        cursor.execute("UPDATE fantasy SET elo = elo - %s, losses = losses + 1 WHERE fantasyname = %s", (elo_change, verlierer,))
        db.commit()
        cursor.execute("SELECT wins,losses FROM fantasy WHERE fantasyname = %s",(gewinner,))
        games_gewinner = cursor.fetchone()
        games_gewinner = games_gewinner[0] + games_gewinner[1]
        cursor.execute("SELECT wins,losses FROM fantasy WHERE fantasyname = %s",(verlierer,))
        games_verlierer = cursor.fetchone()
        games_verlierer = games_verlierer[0] + games_verlierer[1]

        if games_verlierer % 25 == 0:                                                                               
            cursor.execute("UPDATE fantasy SET coins = coins + 1 WHERE fantasyname = %s", (verlierer,))
            db.commit()
            embed.add_field(name="Zusatz",value=f"Außerdem erhält {verlierer} einen prm-coin für sein {games_verlierer}. Game. (25 Games)")                 ## Pulls adden wenn 25.Benchmark erreicht
        if games_verlierer % 1000 == 0:                                                                               
            cursor.execute("UPDATE fantasy SET coins = coins + 3 WHERE fantasyname = %s", (verlierer,))
            db.commit()
            embed.add_field(name="Zusatz",value=f"Außerdem erhält {verlierer} 3 prm-coin für sein {games_verlierer}. Game. (1000 Games)") 

        if games_gewinner % 25 == 0:
            cursor.execute("UPDATE fantasy SET coins = coins + 1 WHERE fantasyname = %s", (gewinner,))
            db.commit()
            embed.add_field(name="Zusatz",value=f"Außerdem erhält {gewinner} einen prm-coin für sein {games_gewinner}. Game. (25 Games Benchmark)")
        if games_gewinner % 1000 == 0:
            cursor.execute("UPDATE fantasy SET coins = coins + 3 WHERE fantasyname = %s", (gewinner,))
            db.commit()
            embed.add_field(name="Zusatz",value=f"Außerdem erhält {gewinner} 3 prm-coins für sein {games_gewinner}. Game (1000 Games).")


        embed.add_field(name="Ergebnis",value=f"Damit gewinnt das Team {gewinner}. Das Team erhält +{elo_change +1} Elo. Der Verlierer {verlierer} verliert {elo_change} Elo.")
        
        if len(channel_von_q) >= 2:
            await channel_von_q[1].send(embed=embed)
        await channel_von_q[0].send(embed=embed)

        channel_von_q = []
    else:
        await ctx.send("Du bist schon in der Warteschlange.")

 
def generate_random_enemy():
    while True:
        cursor.execute("SELECT discord_id FROM fantasy ORDER BY RAND() LIMIT 1")
        random_enemy_id = int(cursor.fetchone()[0])
        if random_enemy_id not in q_users:
            return random_enemy_id

@commands.check(is_allowed_channel)
@client.command(name="team")
async def team(ctx,team_name=None):
    user_id = ctx.author.id
    if team_name == None:
        if await hat_team(user_id) == False:
            await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
            return
    else:
        cursor.execute("SELECT discord_id FROM fantasy WHERE fantasyname = %s", (team_name,))
        user_id = cursor.fetchone()[0]
        if user_id is None:
            await ctx.send("Dieses Team existiert nicht.")
            return
    cursor.execute("SELECT * FROM fantasy WHERE discord_id = %s", (user_id,))
    row = cursor.fetchone() # Die ganze row als tuple nehmen
    cursor.execute("SELECT coins FROM fantasy WHERE discord_id = %s",(user_id,))
    coins = cursor.fetchone()[0]
    cursor.execute("SELECT teamname, div24sp FROM teams WHERE toplaner = %s", (row[2]))
    info_top = cursor.fetchone()
    cursor.execute("SELECT teamname, div24sp FROM teams WHERE jungler = %s", (row[3]))
    info_jgl = cursor.fetchone()
    cursor.execute("SELECT teamname, div24sp FROM teams WHERE midlaner = %s", (row[4]))
    info_mid = cursor.fetchone()
    cursor.execute("SELECT teamname, div24sp FROM teams WHERE adc = %s", (row[5]))               ### infos über die einzelnen rollen collecten
    info_adc = cursor.fetchone()
    cursor.execute("SELECT teamname, div24sp FROM teams WHERE supporter = %s", (row[6]))
    info_sup = cursor.fetchone()
    cursor.execute("SELECT teamname, div24sp FROM teams WHERE headcoach = %s", (row[7]))
    info_c1 = cursor.fetchone()
    cursor.execute("SELECT teamname, div24sp FROM teams WHERE asscoach = %s", (row[8]))
    info_c2 = cursor.fetchone()

    cursor.execute("SELECT position FROM players WHERE ign = %s", (row[9]))
    position_b1 = cursor.fetchone()
    if position_b1 is not None:
        position_b1 = position_b1[0]
        cursor.execute(f"SELECT teamname, div24sp FROM teams WHERE {position_b1} = %s", (row[9],))               ### Info benchplayer           
        info_b1 = cursor.fetchone()
        b1 = True
    else:
        b1 = False

    cursor.execute(f"SELECT position FROM players WHERE ign = %s", (row[10]))
    position_b2 = cursor.fetchone()
    if position_b2 is not None:
        position_b2 = position_b2[0]
        cursor.execute(f"SELECT teamname, div24sp FROM teams WHERE {position_b2} = %s", (row[10],))
        info_b2 = cursor.fetchone()
        b2 = True
    else:
        b2 = False

    spieler = (
        f"**Toplane**      {row[2]} ({info_top[0]}) (Liga {info_top[1]})\n"           ### Formattieren fürs Design
        f"**Jungle**         {row[3]} ({info_jgl[0]}) (Liga {info_jgl[1]})\n"
        f"**Midlane**        {row[4]} ({info_mid[0]}) (Liga {info_mid[1]})\n"
        f"**ADC**              {row[5]} ({info_adc[0]}) (Liga {info_adc[1]})\n"
        f"**Support**         {row[6]} ({info_sup[0]}) (Liga {info_sup[1]})\n"
    )
    cursor.execute("SELECT wins, losses FROM fantasy WHERE discord_id = %s",(user_id,))
    win_loss = cursor.fetchone()
    cursor.execute("SELECT clan FROM fantasy WHERE discord_id = %s",(user_id,))
    clan = cursor.fetchone()[0]
    if clan == "leer":
        clan = "-"
    cursor.execute("SELECT Liga FROM fantasy WHERE discord_id = %s",(user_id,))
    liga = cursor.fetchone()[0]
    value = f"Elo: **{row[12]}** \n  Win/Loss: **{win_loss[0]}/{win_loss[1]}**.\n Verfügbare pulls: **{row[13 ]}** \nCoins: {coins} \n Liga: {liga} \n clan: {clan}"

    embed = discord.Embed(title=f"**{row[11]}**", description=value, color=discord.Color.blue())
    embed.add_field(name="Spieler", value=spieler)

    value = (        
        f"**Headcoach**      {row[7]} ({info_c1[0]}) (Liga {info_c1[1]})\n"
        f"**Assistant/Positional Coach**     {row[8]} ({info_c2[0]}) (Liga {info_c2[1]})"
    )
    embed.add_field(name="Coaches", value=value)

    if b1 == True and b2 == True:  
        value = (
            f"**Bench 1**      {row[9]} ({info_b1[0]}) (Liga {info_b1[1]}) ({position_b1})\n"
            f"**Bench 2**     {row[10]} ({info_b2[0]}) (Liga {info_b2[1]}) ({position_b2})"
        )
    elif b1 == True and b2 == False:
        value = (
            f"**Bench 1**      {row[9]} ({info_b1[0]}) (Liga {info_b1[1]}) ({position_b1})\n"
            f"**Bench 2**     --leer--"
        )
    elif b1 == False and b2 == True:
        value = (
            f"**Bench 1**      --leer--\n"
            f"**Bench 2**     {row[10]} ({info_b2[0]}) (Liga {info_b2[1]}) ({position_b2})"
        )
    elif b1 == False and b2 == False:
        value = (
            f"**Bench 1**      --leer--\n"
            f"**Bench 2**     --leer--"
        )

    embed.add_field(name="Bankspieler", value=value)

    await ctx.send(embed=embed)

@commands.check(is_allowed_channel)
@client.command(name="rename")
async def rename(ctx, new_name:str):
    user_id = ctx.author.id
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT fantasyname FROM fantasy WHERE discord_id = %s", (user_id,))
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
        cursor.execute("UPDATE fantasy SET fantasyname = %s WHERE discord_id = %s", (new_name, user_id,))
        db.commit()
        await ctx.send(f"Du hast deinen Namen zu {new_name} geändert.")

traders = set()  # Ein set von aktiven tradern erstellen
open_trades = {} # ein Dictionary von trades erstellen

@commands.check(is_allowed_channel)
@client.command(name="trade")
async def trade(ctx, input_partner:str, input_position:str):
    user_id = ctx.author.id
    input_partner = input_partner.lower()
    input_position = input_position.lower()
    cursor.execute("SELECT wins,losses FROM fantasy WHERE discord_id = %s",(user_id,))
    games = cursor.fetchone()
    games = games[0] + games[1]
    if games < 300:
        await ctx.send("nicht genügend gespielte Spiele.(300)")
        return
    cursor.execute("SELECT liga FROM fantasy WHERE discord_id = %s",(user_id,))
    liga = cursor.fetchone()[0]
    if liga == 2:
        await ctx.send("In dieser Liga kannst du weder den TM, noch trades nutzen.")
        return
    cursor.execute("SELECT elo FROM fantasy WHERE discord_id = %s",(user_id,))
    elo = cursor.fetchone()[0]
    if elo < 50:
        await ctx.send("Du hast zu wenig Elo um zu traden.")
        return
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    display_name = ctx.author.display_name
    if input_partner is None:
        await ctx.send ("DU musst einen Handelspartner eingeben.")
        return
    if user_id in traders:
        await ctx.send("Du bist bereits in einen Trade involviert.")
        return
    if input_position == "top" or input_position == "toplane":
        position = "toplaner"
    elif input_position == "jgl" or  input_position == "jungle":
        position = "jungler"
    elif input_position == "mid" or input_position == "midlane":
        position = "midlaner"
    elif input_position == "adc" or input_position == "adcarry":
        position = "adc"
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
    else:
        await ctx.send("Keine valide position angegeben.")
        return

    cursor.execute("SELECT COUNT(*) FROM fantasy WHERE fantasyname = %s", (input_partner,))
    ergebnis = cursor.fetchone()[0]
    if ergebnis >0:
        partner = input_partner
        cursor.execute(f"SELECT {position} FROM fantasy WHERE discord_id = %s", (user_id,))
        player_1 = cursor.fetchone()
        if player_1[0] == "leer":
            await ctx.send("Du hast keinen Spieler auf dieser Position.")                             # Checken ob man Spieler auf der Position hat wegen bench
            return
        cursor.execute(f"SELECT {position},discord_id FROM fantasy WHERE fantasyname = %s", (partner,))
        player_2 = cursor.fetchone()
        if player_2[0] == "leer":
            await ctx.send("Dein Tauschpartner hat keinen Spieler auf dieser Position.")                # Checken ob Gegner nen Spieler auf der Position hat wegen bench
            return
    else:
        await ctx.send("Das Team mit dem du tauschen willst existiert nicht.")
        return
    if player_2[1] in traders:
        await ctx.send("Dein Handelspartner ist bereits in einen Trade involviert.")
        return
    traders.add(user_id)
    traders.add(int(player_2[1]))                    ## Discord_ids der Beteiligten zum Handelsset zufügen.
    open_trades[(user_id,int(player_2[1]),position)] = None
    await ctx.send(f"{display_name} möchte {player_1[0]} gegen {player_2[0]} vom Team {partner} auf der Position {position} tauschen. \n"
    "Verwende !accept oder !decline um den Tausch anzunehmen, bzw. abzulehnen. Ein Tausch kostet euch beide 50 Elo.")

@commands.check(is_allowed_channel)
@client.command(name="accept")
async def accept(ctx):
    user_id = ctx.author.id
    cursor.execute("SELECT wins,losses FROM fantasy WHERE discord_id = %s",(user_id,))
    games = cursor.fetchone()
    games = games[0] + games[1]
    if games < 300:
        await ctx.send("nicht genügend gespielte Spiele.(300)")
        return
    cursor.execute("SELECT liga FROM fantasy WHERE discord_id = %s",(user_id,))
    liga = cursor.fetchone()[0]
    if liga == 2:
        await ctx.send("In dieser Liga kannst du weder den TM, noch trades nutzen.")
        return
    cursor.execute("SELECT elo FROM fantasy WHERE discord_id = %s",(user_id,))
    elo = cursor.fetchone()[0]
    if elo < 50:
        await ctx.send("Du hast zu wenig Elo um zu traden.")
        return
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if user_id not in traders:
        await ctx.send("Du bist nicht in einem Handel involviert.")
        return
    for trade_key in open_trades:
        if user_id in trade_key:
            position = trade_key[2]
            if user_id == trade_key[1]:  
                cursor.execute(f"SELECT {trade_key[2]} FROM fantasy WHERE discord_id = %s", (trade_key[0],))
                player_1 = cursor.fetchone()[0]
                cursor.execute(f"SELECT {trade_key[2]} FROM fantasy WHERE discord_id = %s", (trade_key[1],))
                player_2 = cursor.fetchone()[0]
                cursor.execute(f"UPDATE fantasy SET {position} = %s, elo = elo -50 WHERE discord_id = %s", ( player_2, trade_key[0]))
                cursor.execute(f"UPDATE fantasy SET {position} = %s, elo = elo -50 WHERE discord_id = %s", ( player_1, trade_key[1]))           
                db.commit()
                traders.remove(trade_key[0])
                traders.remove(trade_key[1])
                del open_trades[trade_key]
                await ctx.send("Du hast den Handel akzeptiert. Trade abgeschlossen.")

                break
            else: 
                await ctx.send("Du kannst nicht dein eigenes Angebot annehmen.")

@commands.check(is_allowed_channel)
@client.command(name="decline")
async def decline(ctx):
    user_id = ctx.author.id
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if user_id not in traders:
        await ctx.send("Du bist nicht in einem Handel involviert.")
        return
    for trade_key in open_trades:
        if user_id in trade_key:
            del open_trades[trade_key]
            traders.remove(trade_key[0])
            traders.remove(trade_key[1])
            await ctx.send("Der Tausch wurde abegelehnt. Trade abgeschlossen.")

            break
    
    
anzahl_teams = 401

joined_turnier = set()


async def host(ctx,eintrittspreis):
    user_id = ctx.author.id
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if eintrittspreis is None:                              ### Check ob er einen Preis angegeben hat
        await ctx.send("Bitte gib einen validen Betrag als Eintrittspreis ein")
        return
    try:
        eintrittspreis = int(eintrittspreis)              ## Check ob der Preis ein Int ist.
    except ValueError:
        await ctx.send("Der Eintrittspreis muss eine ganze Zahl sein.")
        return
    if eintrittspreis <= 0:
        await ctx.send("Bitte gib einen positiven Betrag ein.")
        return
    cursor.execute("SELECT COUNT(*) FROM tournaments WHERE host = %s", (user_id,))  ## Check ob er schon ein turnier hostet
    count = cursor.fetchone()[0]
    if count > 0:
        await ctx.send("Du bist bereits dabei ein Turnier zu veranstalten.")
        return
    cursor.execute("SELECT elo FROM fantasy WHERE discord_id = %s", (user_id,))
    elo = cursor.fetchone()[0]
    if elo <= 250:
        await ctx.send("Du brauchst mindestens 250 Elo um ein Turnier zu veranstalten.")
    elo = round(elo / 2)
    if elo < eintrittspreis:
        await ctx.send("Der Eintrittspreis darf maximal die Hälfte deiner aktuellen Elo betragen.")
        return
    cursor.execute("INSERT INTO tournaments (host,entry) VALUES (%s,%s)", (user_id,eintrittspreis))
    cursor.execute("UPDATE fantasy SET elo = elo - %s WHERE discord_id = %s", (eintrittspreis,user_id))
    db.commit()
    await ctx.send(f"Du hast ein Turnier aufgemacht mit einem Eintrittspreis von {eintrittspreis}. Andere Spieler können beitreten mit !turnier (dein name) beitreten.")


async def turnier(ctx, host, aktion):
    user_id = ctx.author.id
    if user_id in joined_turnier:
        await ctx.send("Du musst einen Moment warten.")
        return
    if await hat_team(user_id) == False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if host is None:
        await ctx.send("Du musst einen host angeben")
        return
    joined_turnier.add(user_id)
    cursor.execute("SELECT discord_id FROM fantasy WHERE fantasyname = %s", (host))
    host_id = cursor.fetchone()[0]
    if host_id is None:
        await ctx.send("Dieses Team existiert nicht.")
        joined_turnier.remove(user_id)
        return
    print(host_id)
    cursor.execute("SELECT player_2,player_3,player_4,entry FROM tournaments WHERE host = %s", (host_id,))
    turnier_info = cursor.fetchone()
    if turnier_info is None:
        await ctx.send("Dieses Team veranstaltet kein Turnier.")
        joined_turnier.remove(user_id)
        return
    print(turnier_info)
    open_spots = 0
    eintrittspreis = turnier_info[3]
    if turnier_info[0] is None:
        open_spots = 3
    elif turnier_info[1] is None:
        open_spots = 2
    elif turnier_info[2] is None:
        open_spots = 1
    if aktion == "info":
        await ctx.send(f"Das Turnier von {host} hat einen Eintrittspreis von {eintrittspreis} und es sind noch {open_spots} Plätze offen. Du kannst beitreten mit !turnier (Name des Veranstalters) join.")
        joined_turnier.remove(user_id)
        return
    elif aktion == "join":
        if user_id == host_id:
            await ctx.send("Du kannst nicht deinem eigenen Turnier beitreten.")
            joined_turnier.remove(user_id)
            return
        cursor.execute("SELECT elo FROM fantasy WHERE discord_id = %s", (user_id,))
        elo = cursor.fetchone()[0]
        elo = round(elo /2)
        if elo < eintrittspreis:
            await ctx.send("Deine Elo muss mindestens die Hälfte des Eintrits betragen.")
            joined_turnier.remove(user_id)
            return
        if open_spots == 0:
            await ctx.send("Das Turnier ist bereits voll.")
            joined_turnier.remove(user_id)
            return
        if open_spots == 3:
            cursor.execute("UPDATE tournaments SET player_2 = %s WHERE host = %s", (user_id,host_id))
            cursor.execute("UPDATE fantasy SET elo = elo - %s WHERE discord_id = %s", (eintrittspreis, user_id))
            db.commit()
            await ctx.send(f"Du bist dem Turnier beigetreten und hast {eintrittspreis} Elo bezahlt.")
            joined_turnier.remove(user_id)
            return
        elif open_spots == 2:
            cursor.execute("UPDATE tournaments SET player_3 = %s WHERE host = %s", (user_id,host_id))
            cursor.execute("UPDATE fantasy SET elo = elo - %s WHERE discord_id = %s", (eintrittspreis, user_id))
            db.commit()
            await ctx.send(f"Du bist dem Turnier beigetreten und hast {eintrittspreis} Elo bezahlt.")
            joined_turnier.remove(user_id)
            return
        elif open_spots == 1:
            cursor.execute("UPDATE tournaments SET player_4 = %s WHERE host = %s", (user_id,host_id))
            cursor.execute("UPDATE fantasy SET elo = elo - %s WHERE discord_id = %s", (eintrittspreis, user_id))
            db.commit()
            await ctx.send(f"Du bist dem Turnier beigetreten und hast {eintrittspreis} Elo bezahlt.")
            open_spots = 0
        

        if open_spots == 0:  # turnier beginnen
            cursor.execute("SELECT host FROM tournaments WHERE player_4 = %s", (user_id,))
            spieler1_id = cursor.fetchone()[0]
            cursor.execute("SELECT player_2 FROM tournaments WHERE player_4 = %s", (user_id,))
            spieler2_id = cursor.fetchone()[0]
            cursor.execute("SELECT player_3 FROM tournaments WHERE player_4 = %s", (user_id,))
            spieler3_id = cursor.fetchone()[0]
            spieler4_id = user_id
            gewinn = round(eintrittspreis * 3)
            turnier_überschrift = f"Turnier von {host}"
            turnier_description = f"Der Gewinner erhält {gewinn}."
            embed=discord.Embed(title=turnier_überschrift,description=turnier_description)
            winners = await matchup(spieler1_id,spieler2_id)
            spieler1 = await spieler_von_team_name(spieler1_id)
            spieler2 = await spieler_von_team_name(spieler2_id)
            embed.add_field(name="Halbfinale 1", value=f"Match zwischen \n{spieler1[7]} und {spieler2[7]}")
            embed.add_field(name="",value=f"{spieler1[7]}\n{spieler1[0]}\n{spieler1[1]}\n{spieler1[2]}\n{spieler1[3]}\n{spieler1[4]}\n\n Coaches\n{spieler1[5]}\n{spieler1[6]}")
            embed.add_field(name="",value=f"{spieler2[7]}\n{spieler1[0]}\n{spieler2[1]}\n{spieler2[2]}\n{spieler2[3]}\n{spieler2[4]}\n\n Coaches\n{spieler2[5]}\n{spieler2[6]}")
            embed.add_field(name="Gewinner", value=f"{winners[0]}\n{winners[1]}\n{winners[2]}\n{winners[3]}\n{winners[4]}")
            team1_wins = winners.count(spieler1[7])   ## Nur die wins des ersten Teams checken weil bei weniger als 3 hat gegner gewonnen                   
            if team1_wins >= 3:
                gewinner_id = spieler1_id
                gewinner = spieler1[7]
            else:
                gewinner_id = spieler2_id
                gewinner = spieler2[7]
            embed.add_field(name="Sieger des Matches",value=gewinner)
            finalist1 = gewinner_id
            message = await ctx.send(embed=embed)

            await asyncio.sleep(10)

            new_embed = discord.Embed(title=turnier_überschrift,description=turnier_description)
            winners = await matchup(spieler3_id,spieler4_id)
            spieler1 = await spieler_von_team_name(spieler3_id)
            spieler2 = await spieler_von_team_name(spieler4_id)
            new_embed.add_field(name="Halbfinale 2",value=f"Match zwischen \n{spieler1[7]} und {spieler2[7]}")
            new_embed.add_field(name="",value=f"{spieler1[7]}\n{spieler1[0]}\n{spieler1[1]}\n{spieler1[2]}\n{spieler1[3]}\n{spieler1[4]}\n\n Coaches\n{spieler1[5]}\n{spieler1[6]}")
            new_embed.add_field(name="",value=f"{spieler2[7]}\n{spieler1[0]}\n{spieler2[1]}\n{spieler2[2]}\n{spieler2[3]}\n{spieler2[4]}\n\n Coaches\n{spieler2[5]}\n{spieler2[6]}")
            new_embed.add_field(name="Gewinner", value=f"{winners[0]}\n{winners[1]}\n{winners[2]}\n{winners[3]}\n{winners[4]}")
            team1_wins = winners.count(spieler1[7])                
            if team1_wins >= 3:
                gewinner_id = spieler3_id
                gewinner = spieler1[7]
            else:
                gewinner_id = spieler4_id
                gewinner = spieler2[7]
            new_embed.add_field(name="Sieger des Matches",value=gewinner)
            finalist2 = gewinner_id

            await message.edit(embed=new_embed)

            await asyncio.sleep(10)

            new_embed = discord.Embed(title=turnier_überschrift,description=turnier_description)
            winners = await matchup(finalist1,finalist2)
            spieler1 = await spieler_von_team_name(finalist1)
            spieler2 = await spieler_von_team_name(finalist2)
            new_embed.add_field(name="Grand Final",value=f"Match zwischen \n{spieler1[7]} und {spieler2[7]}")
            new_embed.add_field(name="",value=f"{spieler1[7]}\n{spieler1[0]}\n{spieler1[1]}\n{spieler1[2]}\n{spieler1[3]}\n{spieler1[4]}\n\n Coaches\n{spieler1[5]}\n{spieler1[6]}")
            new_embed.add_field(name="",value=f"{spieler2[7]}\n{spieler1[0]}\n{spieler2[1]}\n{spieler2[2]}\n{spieler2[3]}\n{spieler2[4]}\n\n Coaches\n{spieler2[5]}\n{spieler2[6]}")
            new_embed.add_field(name="Gewinner", value=f"{winners[0]}\n{winners[1]}\n{winners[2]}\n{winners[3]}\n{winners[4]}")
            team1_wins = winners.count(spieler1[7])                    
            if team1_wins >= 3:
                gewinner_id = finalist1
                gewinner = spieler1[7]
            else:
                gewinner_id = finalist2
                gewinner = spieler2[7]
            new_embed.add_field(name="Sieger des Matches",value=gewinner)

            await message.edit(embed=new_embed)
            cursor.execute("UPDATE fantasy set elo = elo + %s WHERE discord_id = %s", (gewinn,gewinner_id))
            cursor.execute("DELETE FROM tournaments WHERE host = %s",(spieler1_id,))
            db.commit()
            joined_turnier.remove(user_id)
            await ctx.send(f"Der Gewinner des Turniers war {gewinner}. Er erhält {gewinn} Elo.")

async def hat_team(user_id):
    cursor.execute("SELECT COUNT(*) FROM fantasy WHERE discord_id = %s", (user_id))
    count = cursor.fetchone()[0]
    if count >0:
        return True
    else:
        return False

async def randomize_team(ctx):
    user_id = ctx.author.id

    cursor.execute("UPDATE fantasy SET elo = 500, pulls = 10 WHERE discord_id = %s", (user_id,))


    cursor.execute("UPDATE fantasy SET toplaner = (SELECT toplaner FROM teams ORDER BY RAND() Limit 1) WHERE discord_id = %s", ( user_id,))


    cursor.execute("UPDATE fantasy SET jungler = (SELECT jungler FROM teams ORDER BY RAND() Limit 1) WHERE discord_id = %s", ( user_id,))


    cursor.execute("UPDATE fantasy SET midlaner = (SELECT midlaner FROM teams ORDER BY RAND() Limit 1) WHERE discord_id = %s", ( user_id,))


    cursor.execute("UPDATE fantasy SET adc = (SELECT adc FROM teams ORDER BY RAND() Limit 1) WHERE discord_id = %s", (user_id,))


    cursor.execute("UPDATE fantasy SET supporter = (SELECT supporter FROM teams ORDER BY RAND() Limit 1) WHERE discord_id = %s", (user_id,))

    cursor.execute("UPDATE fantasy SET coach1 = (SELECT headcoach FROM teams WHERE headcoach IS NOT NULL ORDER BY RAND() Limit 1) WHERE discord_id = %s", (user_id,))
       
    cursor.execute("UPDATE fantasy SET coach2 = (SELECT asscoach FROM teams WHERE asscoach IS NOT NULL ORDER BY RAND() Limit 1) WHERE discord_id = %s", (user_id,))


    cursor.execute("UPDATE fantasy SET bench1 = (SELECT ign FROM players ORDER BY RAND() Limit 1) WHERE discord_id = %s", (user_id,))

    cursor.execute("UPDATE fantasy SET bench2 = (SELECT ign FROM players ORDER BY RAND() Limit 1) WHERE discord_id = %s", (user_id,))


    db.commit()
    await ctx.send("Deine Spieler und Coaches wurden ausgewählt.")

@client.command(name="refill")
async def refill(ctx):  
    user_id = ctx.author.id
    if user_id == 284347406420803596 or user_id == 574953391705292801:
        cursor.execute("UPDATE fantasy SET pulls = 10")
        db.commit()
        cursor.execute("UPDATE fantasy SET pulls = pulls + 5 ORDER BY elo DESC LIMIT 5")
        db.commit()
        cursor.execute("UPDATE fantasy SET pulls = pulls + 4 WHERE liga = 1")
        cursor.execute("UPDATE fantasy SET pulls = pulls + 3 WHERE liga = 2")
        cursor.execute("UPDATE fantasy SET pulls = pulls + 2 WHERE liga = 3")
        cursor.execute("UPDATE fantasy SET pulls = pulls + 1 WHERE liga = 4")
        db.commit()
    else:
        await ctx.send("Du hast keine Berechtigung dazu")


@client.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx,selection=None):
    if selection is None:
        cursor.execute("SELECT fantasyname, elo FROM fantasy ORDER BY elo DESC LIMIT 10")
        top10 = cursor.fetchall()
        value = (f"1.{top10[0][0]} hat {top10[0][1]} Elo.\n"
                f"2.{top10[1][0]} hat {top10[1][1]} Elo.\n"
                f"3.{top10[2][0]} hat {top10[2][1]} Elo.\n"
                f"4.{top10[3][0]} hat {top10[3][1]} Elo.\n"
                f"5.{top10[4][0]} hat {top10[4][1]} Elo.\n"
                f"6.{top10[5][0]} hat {top10[5][1]} Elo.\n"
                f"7.{top10[6][0]} hat {top10[6][1]} Elo.\n"
                f"8.{top10[7][0]} hat {top10[7][1]} Elo.\n"
                f"9.{top10[8][0]} hat {top10[8][1]} Elo.\n"
                f"10.{top10[9][0]} hat {top10[9][1]} Elo.\n"
                )
        embed=discord.Embed(title="Top 10", description="Ranked by **Elo**", color=discord.Color.blue())
        embed.add_field(name="Teams und Elo", value=value)
        await ctx.send(embed=embed)
    if selection == "wins" or selection == "win":
        cursor.execute("SELECT fantasyname, wins FROM fantasy ORDER BY wins DESC LIMIT 10")
        top10 = cursor.fetchall()
        value = (f"1.{top10[0][0]} hat {top10[0][1]} Wins.\n"
                f"2.{top10[1][0]} hat {top10[1][1]} Wins.\n"
                f"3.{top10[2][0]} hat {top10[2][1]} Wins.\n"
                f"4.{top10[3][0]} hat {top10[3][1]} Wins.\n"
                f"5.{top10[4][0]} hat {top10[4][1]} Wins.\n"
                f"6.{top10[5][0]} hat {top10[5][1]} Wins.\n"
                f"7.{top10[6][0]} hat {top10[6][1]} Wins.\n"
                f"8.{top10[7][0]} hat {top10[7][1]} Wins.\n"
                f"9.{top10[8][0]} hat {top10[8][1]} Wins.\n"
                f"10.{top10[9][0]} hat {top10[9][1]} Wins.\n"
                )
        embed=discord.Embed(title="Top 10", description="Ranked by **Wins**", color=discord.Color.blue())
        embed.add_field(name="Teams und Wins", value=value)
        await ctx.send(embed=embed)
    if selection == "worse" or selection == "worst":
        cursor.execute("SELECT fantasyname,elo FROM fantasy ORDER BY elo ASC LIMIT 10")
        top10 = cursor.fetchall()
        value = (f"1.{top10[0][0]} hat {top10[0][1]} Elo.\n"
                f"2.{top10[1][0]} hat {top10[1][1]} Elo.\n"
                f"3.{top10[2][0]} hat {top10[2][1]} Elo.\n"
                f"4.{top10[3][0]} hat {top10[3][1]} Elo.\n"
                f"5.{top10[4][0]} hat {top10[4][1]} Elo.\n"
                f"6.{top10[5][0]} hat {top10[5][1]} Elo.\n"
                f"7.{top10[6][0]} hat {top10[6][1]} Elo.\n"
                f"8.{top10[7][0]} hat {top10[7][1]} Elo.\n"
                f"9.{top10[8][0]} hat {top10[8][1]} Elo.\n"
                f"10.{top10[9][0]} hat {top10[9][1]} Elo.\n"
                )
        embed=discord.Embed(title="Worst 10", description="Ranked by **Elo**", color=discord.Color.blue())
        embed.add_field(name="Teams und Elo", value=value)
        await ctx.send(embed=embed)


## returned liste von spielern und coaches
async def spieler_von_team_name(discord_id):
    cursor.execute("SELECT toplaner,jungler,midlaner,adc,supporter,coach1,coach2,fantasyname FROM fantasy WHERE discord_id = %s", (discord_id,))
    team = cursor.fetchone()
    return team

# returned eine liste mit gewinnern der Gewinner
async def matchup(team1,team2):
    winners = []

    cursor.execute("SELECT toplaner, jungler, midlaner, adc, supporter, coach1, coach2, fantasyname, elo, buff FROM fantasy WHERE discord_id = %s", (team1,))
    team1 = cursor.fetchone()
    cursor.execute("SELECT toplaner, jungler, midlaner, adc, supporter, coach1, coach2, fantasyname, elo, buff FROM fantasy WHERE discord_id = %s", (team2,))
    team2 = cursor.fetchone()

    #top
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE toplaner = %s", (team1[0]))
    toplane_1_info = cursor.fetchone()   ### 0 ist das Team, 1 ist die Div
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE toplaner = %s", (team2[0]))
    toplane_2_info = cursor.fetchone()
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE jungler = %s", (team1[1]))
    #jungle
    jungle_1_info = cursor.fetchone()   
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE jungler = %s", (team2[1]))
    jungle_2_info = cursor.fetchone()
    #mid
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE midlaner = %s", (team1[2]))
    midlane_1_info = cursor.fetchone()   
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE midlaner = %s", (team2[2]))
    midlane_2_info = cursor.fetchone()
    #adc
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE adc = %s", (team1[3]))
    adc_1_info = cursor.fetchone()  
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE adc = %s", (team2[3]))
    adc_2_info = cursor.fetchone()
    #sup
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE supporter = %s", (team1[4]))
    support_1_info = cursor.fetchone()   
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE supporter = %s", (team2[4]))
    support_2_info = cursor.fetchone()
    #headcoach
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE headcoach = %s", (team1[5]))
    headcoach_1_info = cursor.fetchone()  
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE headcoach = %s", (team2[5]))
    headcoach_2_info = cursor.fetchone()
    #asscoach
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE asscoach = %s", (team1[6]))
    asscoach_1_info = cursor.fetchone()  
    cursor.execute("SELECT teamname,div24sp FROM teams WHERE asscoach = %s", (team2[6]))
    asscoach_2_info = cursor.fetchone()

    teambuff1 = False
    teambuff2 = False
    mid_jungle1 = False
    mid_jungle2 = False
    duo_bot1 = False
    duo_bot2 = False

    #asscoach buff
    buffed_position1 = team1[9]
    buffed_position2 = team2[9]

    #teambuff1
    team_check = toplane_1_info[0]
    if jungle_1_info[0] == team_check and midlane_1_info[0] == team_check and adc_1_info[0] == team_check and support_1_info[0] == team_check:
        teambuff1 = True
    #teambuff2
    team_check = toplane_2_info[0]
    if jungle_2_info[0] == team_check and midlane_2_info[0] == team_check and adc_2_info[0] == team_check and support_2_info[0] == team_check:
        teambuff2 = True
    
    #mid_jungle_duo1
    if jungle_1_info[0] == midlane_1_info[0]:
        mid_jungle1 = True
    #mid_jungle_duo2
    if jungle_2_info[0] == midlane_2_info[0]:
         mid_jungle2 = True

    #bot_duo1
    if adc_1_info[0] == support_1_info[0]:
        duo_bot1 = True
    #bot_duo2
    if adc_2_info[0] == support_2_info[0]:
        duo_bot2 = True
        
    def div_check(div):
        value = 0
        if div == 1:
            value = 160
        elif div == 2:
            value = 80
        elif div == 3:
            value = 40
        elif div == 4:
            value = 20
        elif div == 5:
            value = 10
        elif div == 6:
            value = 5
        return value

    def headcoach_buff(div):
        value = 0.0
        if div == 1:
            value = 2.0
        elif div == 2:
            value = 1.75
        elif div == 3:
            value = 1.5
        elif div == 4:
            value = 1.25
        elif div == 5:
            value = 1.15
        elif div == 6:
            value = 1.1
        return value
    
    def asscoach_buff(div):
        value = 0.0
        if div == 1:
            value = 1.4
        if div == 2:
            value = 1.3
        elif div == 3:
            value = 1.2
        elif div == 4:
            value = 1.1
        return value

    def top_value(team):
        if team == 1:
            div = toplane_1_info[1]
        else:
            div = toplane_2_info[1]
        value = div_check(div)
        if team == 1:
            value = round(value * headcoach_buff(headcoach_1_info[1]))
            if teambuff1 == True:
                value = round(value * 1.5)
            if buffed_position1 == "top":
                value = round(value * asscoach_buff(asscoach_1_info[1]))
        else:
            if teambuff2 == True:
                round(value * headcoach_buff(headcoach_2_info[1]))
                value = round(value * 1.5)
            if buffed_position2 == "top":
                value = round(value * asscoach_buff(asscoach_2_info[1]))
        return value           

    def jgl_value(team):
        if team == 1:
            div = jungle_1_info[1]   # Div von jgl holen
        else:
            div = jungle_2_info[1]   # Div von jgl holen
        value = div_check(div)      # Je nach div value geben
        if team == 1:
            value = round(value * headcoach_buff(headcoach_1_info[1]))    # coach buff verrechenn
            if teambuff1 == True:                          # team buff verrechnen
                value = round(value * 1.5)
            elif mid_jungle1 == True:                      # synergy buff verrechnen
                value = round(value * 1.25)
            if buffed_position1 == "jgl":
                value = round(value * asscoach_buff(asscoach_1_info[1]))
        else:
            value = round(value * headcoach_buff(headcoach_2_info[1]))
            if teambuff2 == True:
                value = round(value * 1.5)
            elif mid_jungle2 == True:
                value = round(value * 1.25) 
            if buffed_position1 == "jgl":
                value = round(value * asscoach_buff(asscoach_2_info[1]))
        return value    

    def mid_value(team):
        if team == 1:
            div = midlane_1_info[1]
        else:
            div = midlane_2_info[1]
        value = div_check(div)
        if team == 1:
            value = round(value * headcoach_buff(headcoach_1_info[1]))
            if teambuff1 == True:
                value = round(value * 1.5)
            elif mid_jungle1 == True:
                value = round(value * 1.25)
            if buffed_position1 == "mid":
                value = round(value * asscoach_buff(asscoach_1_info[1]))
        else:
            value = round(value * headcoach_buff(headcoach_2_info[1]))
            if teambuff2 == True:
                value = round(value * 1.5)
            elif mid_jungle2 == True:
                value = round(value * 1.25)
            if buffed_position1 == "mid":
                value = round(value * asscoach_buff(asscoach_2_info[1]))
        return value

    def adc_value(team):
        if team == 1:
            div = adc_1_info[1]
        else:
            div = adc_2_info[1]
        value = div_check(div)
        if team == 1:
            value = round(value * headcoach_buff(headcoach_1_info[1]))
            if teambuff1 == True:
                value = round(value * 1.5)
            elif duo_bot1 == True:
                value = round(value * 1.25)
            if buffed_position1 == "adc":
                value = round(value * asscoach_buff(asscoach_1_info[1]))
        else:
            value = round(value * headcoach_buff(headcoach_2_info[1]))
            if teambuff2 == True:
                value = round(value * 1.5)
            elif duo_bot2 == True:
                    value = round(value * 1.25)
            if buffed_position1 == "adc":
                value = round(value * asscoach_buff(asscoach_2_info[1]))
        return value

    def sup_value(team):
        if team == 1:
            div = support_1_info[1]
        else:
            div = support_2_info[1]
        value = div_check(div)
        if team == 1:
            value = round(value * headcoach_buff(headcoach_1_info[1]))
            if teambuff1 == True:
                value = round(value * 1.5)
            elif duo_bot1 == True:
                value = round(value * 1.25)
            if buffed_position1 == "sup":
                value = round(value * asscoach_buff(asscoach_1_info[1]))
        else:
            value = round(value * headcoach_buff(headcoach_2_info[1]))
            if teambuff2 == True:
                value = round(value * 1.5)
            elif duo_bot2 == True:
                value = round(value * 1.25)
            if buffed_position1 == "sup":
                value = round(value * asscoach_buff(asscoach_2_info[1]))
        return value


    pool = top_value(1) + top_value(2)         # top matchup
    chance = randint(1, pool) 
    if chance <= top_value(1):
        winners.append(team1[7])
    else:
        winners.append(team2[7])  

    pool = jgl_value(1) + jgl_value(2)
    chance = randint(1, pool)                   # sup matchup
    if chance <= jgl_value(1):
        winners.append(team1[7])
    else:
        winners.append(team2[7])  

    pool = mid_value(1) + mid_value(2)
    chance = randint(1, pool)
    if chance <= mid_value(1):                  # sup matchup
        winners.append(team1[7])
    else:
        winners.append(team2[7])  

    pool = adc_value(1) + adc_value(2)
    chance = randint(1, pool)
    if chance <= adc_value(1):                  # sup matchup
        winners.append(team1[7])
    else:
        winners.append(team2[7])  

    pool = sup_value(1) + sup_value(2)
    chance = randint(1, pool)                  # sup matchup
    if chance <= sup_value(1):
        winners.append(team1[7])
    else:
        winners.append(team2[7]) 
    return winners


@client.command(name="patchnotes", aliases=["pn"])
async def patchnotes(ctx):
    await ctx.send(settings.patchnotes)

@commands.check(is_allowed_channel)
@client.command(name="assistant")
async def posten(ctx, position:str = None):
    if position is None:
        await ctx.send("Du musst eine neue Position für deinen Assistant Coach angeben.")
        return
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    position = position.lower()
    if position == "toplane" or position == "top":
        new_postion = "top"
    elif position == "jungle" or position == "jgl":
        new_postion = "jgl"
    elif position == "midlane" or position == "mid":
        new_postion = "mid"
    elif position == "adc" or position == "bot":
        new_postion = "adc"
    elif position == "sup" or position == "supp" or position == "support":
        new_postion = "sup"
    else:
        await ctx.send("Bitte gib eine valide Position ein.")
        return
    cursor.execute("UPDATE fantasy SET buff = %s WHERE discord_id = %s",(new_postion, user_id))
    db.commit()
    await ctx.send(f"Dein Assistant Coach unterstützt jetzt die {new_postion} Position.")

@commands.check(is_allowed_channel)
@client.command(name="search")
async def search(ctx, player:str = None):
    if player is None:
        await ctx.send("Du musst einen Spieler zum Suchen angeben.")
        return
    user_id = ctx.author.id
    cursor.execute("SELECT position FROM players WHERE ign = %s", (player))                     ### Position des Spielers suchen
    position = cursor.fetchone()
    if position is None:
        await ctx.send("Diesen Spieler gibt es nicht.")
        return
    position = position[0]                                                                     # Readability verbessern
    if position == "headcoach":
        position = "coach1"
    elif position == "asscoach":
        position = "coach2"
    cursor.execute(f"SELECT fantasyname FROM fantasy WHERE {position} = %s",(player))
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

@commands.check(is_allowed_channel)
@client.command(name="swap")
async def swap(ctx,bench_nr = None):
    if bench_nr is None:
        await ctx.send("Bitte gib die Bankposition ein die du tauschen möchtest mit b1 oder b2.")
        return
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if bench_nr == "b1" or bench_nr == "1":
        bench_nr = 1
    elif bench_nr == "b2" or bench_nr == "2":
        bench_nr = 2
    else:
        await ctx.send("Bitte gib eine valide Bankposition zum Tauschen an (b1/b2).")
        return
    if bench_nr == 1:
        cursor.execute("SELECT bench1 FROM fantasy WHERE discord_id = %s", (user_id,))
        bench_player = cursor.fetchone()[0]
        if bench_player == "leer":
            await ctx.send("Du hast keinen Bankspieler zum Tauschen.")
            return
        cursor.execute("SELECT position FROM players WHERE ign = %s", (bench_player))
        position = cursor.fetchone()[0]
        if position == "headcoach":
            position = "coach1"
        elif position == "asscoach":
            position = "coach2"
        cursor.execute(f"SELECT {position} FROM fantasy WHERE discord_id = %s", (user_id,))
        active_player = cursor.fetchone()[0]
        cursor.execute(f"UPDATE fantasy SET {position} = %s, bench1 = %s WHERE discord_id = %s", (bench_player, active_player,user_id))
    elif bench_nr == 2:
        cursor.execute("SELECT bench2 FROM fantasy WHERE discord_id = %s", (user_id,))
        bench_player = cursor.fetchone()[0]
        if bench_player == "leer":
            await ctx.send("Du hast keinen Bankspieler zum Tauschen.")
            return
        cursor.execute("SELECT position FROM players WHERE ign = %s", (bench_player))
        position = cursor.fetchone()[0]
        if position == "headcoach":
            position = "coach1"
        elif position == "asscoach":
            position = "coach2"
        cursor.execute(f"SELECT {position} FROM fantasy WHERE discord_id = %s", (user_id,))
        active_player = cursor.fetchone()[0]
        cursor.execute(f"UPDATE fantasy SET {position} = %s, bench2 = %s WHERE discord_id = %s", (bench_player, active_player, user_id))
    db.commit
    await ctx.send("Spieler wurde gewechselt.")

@commands.check(is_allowed_channel)
@client.command(name="release", aliases=["entlassen"])
async def release(ctx,bench_nr = None):
    if bench_nr is None:
        await ctx.send("Bitte gib die Bank/Transfermarkt-Position ein die du entlassen möchtest mit b1 oder b2 bzw. der TM-Nummer.")
        return
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if bench_nr == "1" or bench_nr == "b1":
        cursor.execute("SELECT bench1 from fantasy WHERE discord_id = %s", (user_id))
        bench_player = cursor.fetchone()[0]
        if bench_player == "leer":
            await ctx.send("Du hast keinen Spieler zum releasen.")
            return
        else:
            cursor.execute("UPDATE fantasy set bench1 = 'leer' WHERE discord_id = %s", (user_id))
            db.commit()
            await ctx.send("Spieler wurde entlassen.")
            return
    elif bench_nr == "2" or bench_nr == "b2":
        cursor.execute("SELECT bench2 from fantasy WHERE discord_id = %s", (user_id))
        bench_player = cursor.fetchone()[0]
        if bench_player == "leer":
            await ctx.send("Du hast keinen Spieler zum releasen.")
            return
        else:
            cursor.execute("UPDATE fantasy set bench2 = 'leer' WHERE discord_id = %s", (user_id))
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
            cursor.execute("UPDATE fantasy SET offers = offers + 1 WHERE discord_id = %s",(user_id,))
            db.commit()
            await ctx.send("Spieler wurde entlassen.")
            print("test3")
        else:
            await ctx.send("Das ist nicht dein Spieler auf dem Markt.")
            return


@commands.check(is_allowed_channel)
@client.command(name="sell", aliases=["verkaufen"])
async def sell(ctx,bench_nr = None, price = None):
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
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT wins,losses FROM fantasy WHERE discord_id = %s",(user_id,))
    games = cursor.fetchone()
    games = games[0] + games[1]
    if games < 300:
        await ctx.send("nicht genügend gespielte Spiele.(500)")
        return
    cursor.execute("SELECT offers FROM fantasy WHERE discord_id = %s", (user_id,))
    available_offers = cursor.fetchone()[0]
    if available_offers == 0:
        await ctx.send("Du hast bereits 3 Angebote auf dem Transfermarkt.")
        return
    available_offers = available_offers - 1
    if bench_nr == "b1" or bench_nr == "1":
        bench_nr = "bench1"
    elif bench_nr == "b2" or bench_nr == "2":
        bench_nr = "bench2"
    else:
        await ctx.send("Bitte gib eine gültige Bankposition ein (b1/b2).")
        return
    cursor.execute(f"SELECT {bench_nr} FROM fantasy WHERE discord_id = %s", (user_id,))
    spieler = cursor.fetchone()[0]
    if spieler == "leer":
        await ctx.send("Du hast keinen Spieler auf dieser Position zum Verkaufen.")
        return
    cursor.execute("INSERT INTO market (seller_id,player_ign,price) VALUES (%s, %s, %s)",(user_id,spieler,price))
    cursor.execute(f"UPDATE fantasy SET {bench_nr} = 'leer',offers = offers - 1  WHERE discord_id = %s", (user_id,))
    db.commit()
    await ctx.send(f"Du hast den Spieler/Coach {spieler} für {price} auf dem Transfermarkt angeboten. Du kannst noch {available_offers} weitere Spieler/Coaches anbieten.")

@commands.check(is_allowed_channel)
@client.command(name="transfermarkt", aliases=["tm"])
async def transfermarkt(ctx,start=None):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT liga FROM fantasy WHERE discord_id = %s",(user_id,))
    liga = cursor.fetchone()[0]
    if liga == 2:
        await ctx.send("In dieser Liga kannst du weder den TM, noch trades nutzen.")
        return
    
    try:
        start = int(start)
    except:
        await ctx.send("Bitte gib eine Zahl als Seitenangabe an.")
    if start is None:
        start = 1
    embed=discord.Embed(title="Transfermarkt", description="Die Liste von allen Spielern/Coaches die aktuell auf dem Transfermarkt sind.")

    cursor.execute("SELECT id,player_ign,price FROM market")
    angebote = cursor.fetchall()

    start_index = start * 20 - 20
    end_index = start_index + 20
    print(start_index)
    print(end_index)
    for eintrag in angebote[start_index:end_index]:
        cursor.execute("SELECT position FROM players WHERE ign = %s",(eintrag[1]))
        position = cursor.fetchone()[0]
        cursor.execute(f"SELECT teamname,div24sp FROM teams WHERE {position} = %s",(eintrag[1]))
        div_und_name = cursor.fetchone()
        embed.add_field(name=f"{eintrag[1]}", value=f"Preis: {eintrag[2]},id:{eintrag[0]},position:{position},Liga:{div_und_name[1]},Team:{div_und_name[0]}")        
    embed.add_field(name="Infor", value="Mit !tm 2 kannst du weitere Seiten des Tms anschauen.")
    await ctx.send(embed=embed)

@commands.check(is_allowed_channel)
@client.command(name="buy", aliases=["kaufen"])
async def kaufen(ctx,id = None):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT liga FROM fantasy WHERE discord_id = %s",(user_id,))
    liga = cursor.fetchone()[0]
    if liga == 2:
        await ctx.send("In dieser Liga kannst du weder den TM, noch trades nutzen.")
        return
    if id is None:
        await ctx.send("Bitte gib die ID ein, welche du kaufen willst.")
        return
    try:
        id = int(id)
    except:
        await ctx.send("Bitte gib eine Zahl als ID ein.")
        return
    cursor.execute("SELECT wins,losses FROM fantasy WHERE discord_id = %s",(user_id,))
    games = cursor.fetchone()
    games = games[0] + games[1]
    if games < 300:
        await ctx.send("nicht genügend gespielte Spiele.(500)")
        return
    cursor.execute("SELECT price FROM market WHERE id = %s",(id,))
    price_player = cursor.fetchone()[0]
    cursor.execute("SELECT coins FROM fantasy WHERE discord_id = %s", (user_id,))
    coins_user = cursor.fetchone()[0]
    if price_player > coins_user:
        await ctx.send("Du hast nicht genügend coins um diesen Spieler/Coach zu kaufen.")
        return
    cursor.execute("SELECT bench1, bench2 FROM fantasy WHERE discord_id = %s", (user_id,))
    bench = cursor.fetchone()
    if bench[0] != "leer" and bench[1] != "leer":
        await ctx.send("Du hast kein Platz auf deiner Bank, bitte entlasse erst einen Spieler.")
        return
    cursor.execute("SELECT player_ign FROM market WHERE id = %s",(id,))
    ign = cursor.fetchone()[0]
    if bench[0] == "leer":
        bench = "bench1"
    elif bench[1] == "leer":
        bench = "bench2"
    cursor.execute(f"UPDATE fantasy SET {bench} = %s, coins = coins - %s WHERE discord_id = %s",(ign,price_player,str(user_id)))     # coins abziehen und Spieler geben
    
    cursor.execute("SELECT seller_id FROM market WHERE id = %s",(id,))
    seller_id = cursor.fetchone()[0]
    cursor.execute("UPDATE fantasy SET coins = coins + %s,offers = offers + 1 WHERE discord_id = %s",(price_player,str(seller_id)))                    # coins geben an seller
    cursor.execute("DELETE FROM market WHERE id = %s",(id))                                                          # Spieler vom Markt löschen
    db.commit()
    await ctx.send(f"Du hast {ign} gekauft.")

@commands.check(is_allowed_channel)
@client.command(name="cancel")
async def cancel(ctx,id=None):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if id is None:
        await ctx.send("Bitte gib eine market_id an die du zurücknehmen möchstest.")
        return
    try:
        int(id)
    except:
        await ctx.send("Bitte gib eine Zahl als id an.")
        return
    cursor.execute("SELECT player_ign,seller_id,price FROM market WHERE id = %s",(id))
    request = cursor.fetchone()
    if request is None:
        await ctx.send("Diese Id ist momentan nicht auf dem Markt.")
        return
    user_id = str(user_id)
    if request[1] != user_id:
        await ctx.send("Dieser Spieler gehörte nie dir.")
        return
    else:
        cursor.execute("SELECT bench1, bench2 FROM fantasy WHERE discord_id = %s", (user_id,))
        bench = cursor.fetchone()
        if bench[0] != "leer" and bench[1] != "leer":
            await ctx.send("Du hast kein Platz auf deiner Bank, bitte entlasse erst einen Spieler.")
            return
        if bench[0] != "leer":
            cursor.execute("UPDATE fantasy set bench2 = %s WHERE discord_id = %s", (request[0],user_id))
        else:
            cursor.execute("UPDATE fantasy set bench1 = %s  WHERE discord_id = %s", (request[0],user_id))
        cursor.execute("UPDATE fantasy set offers = offers + 1 WHERE discord_id = %s", (user_id,))
        cursor.execute("DELETE FROM market WHERE id = %s", (id,))
        db.commit()
        await ctx.send(f"Du hast den Spieler vom Transfermarkt genommen.")

@commands.check(is_allowed_channel)
@client.command(name="offers")
async def offers(ctx):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT id FROM market WHERE seller_id = %s",(user_id,))
    request = cursor.fetchall()
    print(request)
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
    

@commands.check(is_allowed_channel)
@client.command(name="shop")
async def shop(ctx, anzahl = None):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    try:
        anzahl = int(anzahl)
    except:
        await ctx.send("Bitte gib eine valide Zahl zum Kaufen ein.")
        return
    cursor.execute("SELECT coins FROM fantasy WHERE discord_id = %s",(user_id,))
    coins = cursor.fetchone()[0]
    preis_requested = anzahl * 2
    if preis_requested > coins:
        await ctx.send("Das kannst du dir nicht leisten, 1 Pull kostet 2 prm-coins.")
        return

    cursor.execute("UPDATE fantasy set pulls = pulls + %s,coins = coins - %s WHERE discord_id = %s",(anzahl,preis_requested,user_id))
    db.commit()
    await ctx.send(f"Du hast {anzahl} pulls für {preis_requested} prm-coins gekauft.")


@commands.check(is_allowed_channel)
@client.command(name="clan")
async def shop(ctx, befehl=None,choice=None):
    user_id = ctx.author.id
    print(choice)
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if befehl == None:
        await ctx.send("Du kannst ein Clan erstellen mit !clan create, einem beitreten mit !clan join und informationen bekommen mit !clan info")
        return
    if befehl == "create":
        if choice is None:
            await ctx.send("Bitte gib einen Namen für den Clan ein.")
            return
        choice = str(choice)
        cursor.execute("SELECT COUNT(*) FROM fantasy WHERE clan = %s LIMIT 1",(choice,))
        anzahl_clans = cursor.fetchone()[0]
        print(anzahl_clans)
        if anzahl_clans == 0:
            cursor.execute("UPDATE fantasy SET clan = %s WHERE discord_id = %s",(choice,user_id))
            db.commit()
            await ctx.send(f"Clan {choice} wurde erstellt.")
            return
        else:
            await ctx.send("Diesen Clan gibt es bereits.")
            return
    elif befehl == "join":
        if choice is None:
            await ctx.send("Bitte gib einen Namen für den Clan ein.")
            return
        choice = str(choice)
        cursor.execute("SELECT COUNT(*) FROM fantasy WHERE clan = %s LIMIT 1",(choice,))
        anzahl_clans = cursor.fetchone()[0]
        print(anzahl_clans)
        if anzahl_clans == 0:
            await ctx.send("Diesen Clan gibt es nicht.")
            return
        else:
            cursor.execute("UPDATE fantasy SET anfrage = %s WHERE discord_id = %s",(choice,user_id))
            db.commit()
            await ctx.send("Anfrage gesendet, kann angekommen werden mit !clan accept und deinem Namen.")

    elif befehl == "accept":
        if choice is None:
            await ctx.send("Bitte spezifizier wen du akzeptieren möchstest.")
            return
        cursor.execute("SELECT anfrage FROM fantasy WHERE fantasyname = %s",(choice,))
        anfrage = cursor.fetchone()
        if anfrage is None:
            await ctx.send("Keine Anfrage vorhanden von diesem Team.")
            return
        else:
            anfrage = anfrage[0]
        cursor.execute("SELECT clan FROM fantasy WHERE discord_id = %s",(user_id,))
        eigener_clan = cursor.fetchone()
        if eigener_clan is None:
            await ctx.send("Du bist in keinem Clan.")
            return
        else:
            eigener_clan = eigener_clan[0]
        if anfrage == eigener_clan:
            cursor.execute("UPDATE fantasy SET clan = %s WHERE fantasyname = %s",(anfrage,choice))
            db.commit()
            await ctx.send(f"{choice} wurde in den Clan aufgenommen.")
        else:
            await ctx.send("Anfrage und dein Clan stimmen nicht überein.")
    elif befehl == "info":
        if choice is None:
            await ctx.send("Bitte gib ein Clannamen ein über den du mehr erfahren willst.")
            return
        cursor.execute("SELECT fantasyname FROM fantasy WHERE clan = %s",(choice,))
        info = cursor.fetchall()
        if len(info) == 0:
            await ctx.send("Diesen Clan gibt es nicht.")
            return
        message = "In diesem Clan sind die Teams: "
        for team in info:
            message = message + team[0] + ","
        await ctx.send(message)

        
@commands.check(is_allowed_channel)
@client.command(name="legacy")
async def legacy(ctx, benchnr = None,slot = None):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if benchnr is None:
        await ctx.send("Bitte gib eine Banknummer ein die du ins Legacy Roster aufnehmen willst (b1/b2).")
        return
    if benchnr == "b1":
        benchnr = "bench1"
    elif benchnr == "b2":
        benchnr = "bench2"
    else:
        await ctx.send("Bitte gib eine Banknummer ein die du ins Legacy Roster aufnehmen willst (b1/b2).")
        return
    cursor.execute("SELECT liga FROM fantasy WHERE discord_id = %s",(user_id,))
    liga = cursor.fetchone()[0]
    if slot is None:
        await ctx.send("Bitte gib einen Slot für die Legende ein (1-3).")
        return
    elif slot == "1":
        slot = "legacy1"
    elif slot == "2":
        slot = "legacy2"
    elif slot == "3":
        slot = "legacy3"
    elif slot == "4":
        if liga < 5:
            slot = "legacy4"    
        else:
            await ctx.send("Deine Liga ist nicht hoch genug für diesen Slot.")
    elif slot == "5":
        if liga < 4:
            slot = "legacy5"    
        else:
            await ctx.send("Deine Liga ist nicht hoch genug für diesen Slot.")
    elif slot == "6":
        if liga < 3:
            slot = "legacy6"    
        else:
            await ctx.send("Deine Liga ist nicht hoch genug für diesen Slot.")
    elif slot == "7":
        if liga < 2:
            slot = "legacy7"    
        else:
            await ctx.send("Deine Liga ist nicht hoch genug für diesen Slot.")
    else:
        await ctx.send("Bitte gib einen Slot für die Legende ein (1-7).")
        return
    cursor.execute(f"SELECT {benchnr} FROM fantasy WHERE discord_id = %s",(user_id,))
    spieler = cursor.fetchone()[0]
    if spieler == "leer":
        await ctx.send("Du hast dort keinen Spieler.")
        return
    cursor.execute(f"UPDATE fantasy SET {slot} = %s, {benchnr} = 'leer' WHERE discord_id = %s",(spieler,user_id))
    db.commit()
    await ctx.send("Spieler wurde in die Legacy aufgenommen.")
    
@commands.check(is_allowed_channel)
@client.command(name="showroom")
async def showroom(ctx):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT fantasyname,legacy1,legacy2,legacy3,legacy4,legacy5,legacy6,legacy7 FROM fantasy WHERE discord_id = %s",(user_id,))
    team = cursor.fetchone()
    embed = discord.Embed(title=f"Die Legacy von {team[0]}", color=discord.Color.red())

    if team[1] == "leer":
        value = "Noch keine Legenden gefunden."
    else:
        value = team[1]
    embed.add_field(name="Legende 1", value=value)
    
    if team[2] == "leer":
        value = "Noch keine Legenden gefunden."
    else:
        value = team[2]
    embed.add_field(name="Legende 2", value=value)

    if team[3] == "leer":
        value = "Noch keine Legenden gefunden."
    else:
        value = team[3]
    embed.add_field(name="Legende 3", value=value)
    
    if team[4] == "leer":
        value = "Noch keine Legenden gefunden."
    else:
        value = team[4]
    embed.add_field(name="Legende 4", value=value)
    
    if team[5] == "leer":
        value = "Noch keine Legenden gefunden."
    else:
        value = team[5]
    embed.add_field(name="Legende 5", value=value)

    if team[6] == "leer":
        value = "Noch keine Legenden gefunden."
    else:
        value = team[6]
    embed.add_field(name="Legende 6", value=value)

    if team[7] == "leer":
        value = "Noch keine Legenden gefunden."
    else:
        value = team[7]
    embed.add_field(name="Legende 7", value=value)

    await ctx.send(embed=embed)

@commands.check(is_allowed_channel)
@client.command(name="rotate")
async def rotate(ctx):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT bench1,bench2 FROM fantasy WHERE discord_id = %s",(user_id))
    bench = cursor.fetchone()
    cursor.execute("UPDATE fantasy SET bench1 = %s, bench2 = %s WHERE discord_id = %s",(bench[1],bench[0],user_id))
    db.commit()
    await ctx.send("Spieler wurden rotiert.")

@commands.check(is_allowed_channel)
@client.command(name="scout")
async def scout(ctx,player=None):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    if player is None:
        await ctx.send("Bitte gib einen Spieler an, nachdem du suchen willst.")
        return
    cursor.execute("SELECT id,price FROM market WHERE player_ign = %s",(player,))
    talent = cursor.fetchone()
    if talent is None:
        await ctx.send("Spieler wurde nicht auf dem TM gefunden.")
        return
    await ctx.send(f"{player} ist auf dem Markt unter id {talent[0]} für {talent[1]} coins.")

div_1_team = ["Eintracht Spandau","BIG","SK Gaming","Austrian Force","EWI","MOUZ","Schalke 04","No Need Orga","Unicorns of Love","Eintracht Frankfurt"]

@commands.check(is_allowed_channel)
@client.command(name="promote")
async def promote(ctx, zustand=None):
    user_id = ctx.author.id
    if await hat_team(user_id) is False:
        await ctx.send("Bitte erstelle zuerst ein Team mit !register.")
        return
    cursor.execute("SELECT toplaner, liga FROM fantasy WHERE discord_id = %s",(user_id,))
    toplaner_spieler = cursor.fetchone()
    toplaner = toplaner_spieler[0]
    liga = toplaner_spieler[1]
    if liga == 1:
        await ctx.send("Du bist schon Liga 1.")
        return
    cursor.execute("SELECT team24sp FROM players WHERE ign = %s",(toplaner,))
    team_top = cursor.fetchone()[0]
    cursor.execute("SELECT jungler,midlaner,adc,supporter,coach1 FROM fantasy WHERE discord_id = %s",(user_id,))
    restliche = cursor.fetchone()
    for rest in restliche:
        cursor.execute("SELECT team24sp FROM players WHERE ign = %s",(rest))
        team = cursor.fetchone()[0]
        if team != team_top:
            await ctx.send("Nicht alle deine Spieler + Headcoach sind aus einem Team.")
            return
    if team_top not in div_1_team:
        await ctx.send("Du hast kein volles Liga 1 team.")
        return
    if zustand != "confirm":
        await ctx.send("Wenn du dir sicher sein willst, dass du dein Team, deine market orders, deine pulls und alles andere verlieren willst um aufzusteigen, drücke !promote confirm.")
        return
    cursor.execute("SELECT promote1, promote2, promote3 FROM fantasy WHERE discord_id = %s",(user_id,))
    promotes = cursor.fetchone()
    print(promotes)
    if promotes[0] == team_top or promotes[1] == team_top or promotes[2] == team_top:
        await ctx.send("Du bist mit diesem Team bereits aufgestiegen.")
        return
    await randomize_team(ctx)
    cursor.execute("SELECT liga FROM fantasy WHERE discord_id = %s",(user_id,))
    x_promote = cursor.fetchone()[0]
    print("passed 1")
    print(x_promote)
    if x_promote == 5:
        cursor.execute("UPDATE fantasy SET promote1 = %s WHERE discord_id = %s",(team_top,user_id))
        db.commit()
    elif x_promote == 4:
        cursor.execute("UPDATE fantasy SET promote2 = %s WHERE discord_id = %s",(team_top,user_id))
        db.commit()
    elif x_promote == 3:
        cursor.execute("UPDATE fantasy SET promote3 = %s WHERE discord_id = %s",(team_top,user_id))
        db.commit()
    elif x_promote == 2:
        cursor.execute("UPDATE fantasy SET promote4 = %s WHERE discord_id = %s",(team_top,user_id))
        db.commit()
    cursor.execute("UPDATE fantasy SET coins = 0, liga = liga - 1, offers = 3 WHERE discord_id = %s",(user_id,))
    db.commit()
    cursor.execute("DELETE FROM market WHERE seller_id = %s",(user_id,))
    db.commit()
    await ctx.send("Herzlich Willkommen... Am Anfang?")


client.run("--")
