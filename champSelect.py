import threading
from PIL import Image, ImageTk, ImageEnhance
import requests
import urllib3
from lcu_driver import Connector
import tkinter as tk
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

connector = Connector()
global phase, blueBans, bluePicks, redBans, redPicks, in_champ_select, closed, ready, bluePickCanvases, redPickCanvases, blueBanCanvases, redBanCanvases, notInChampSelectText, notConnectedText, reconnectButtonFlag, conThread, redPlayers, bluePlayers, redName, blueName
ready = False
closed = False
reconnectButtonFlag = False
reconnectButton = None
phase = ''
bluePicks = {'hover': 0, 'pick': []}
blueBans = {'hover': 0, 'pick': []}
redPicks = {'hover': 0, 'pick': []}
redBans = {'hover': 0, 'pick': []}


def getApiVersion():
    response = requests.get(
        'https://ddragon.leagueoflegends.com/api/versions.json', verify=False)
    return response.json()[0]


def getChampionBanImage(champion):
    if "Kog'Maw" in champion:
        champion = "KogMaw"
    elif "K'Sante" in champion:
        champion = "KSante"
    elif "Rek'Sai" in champion:
        champion = "RekSai"
    elif "Renata Glasc" in champion:
        champion = "Renata"
    elif "Nunu & Willump" in champion:
        champion = "Nunu"
    elif "LeBlanc" in champion:
        champion = "Leblanc"
    elif "Wukong" in champion:
        champion = "MonkeyKing"
    elif "'" in champion:
        champion = champion.replace("'", "")
        champion = champion[0].upper() + champion[1:].lower()
    elif " " in champion:
        champion = champion.replace(" ", "")
    return f"http://ddragon.leagueoflegends.com/cdn/{getApiVersion()}/img/champion/{champion}.png"



def getChampionPickImage(champion):
    # If champion has ' in name, remove it and lowercase the next letter
    if "Kog'Maw" in champion:
        champion = "KogMaw"
    elif "K'Sante" in champion:
        champion = "KSante"
    elif "Rek'Sai" in champion:
        champion = "RekSai"
    elif "Renata Glasc" in champion:
        champion = "Renata"
    elif "Nunu & Willump" in champion:
        champion = "Nunu"
    elif "LeBlanc" in champion:
        champion = "Leblanc"
    elif "Wukong" in champion:
        champion = "MonkeyKing"
    elif "'" in champion:
        champion = champion.replace("'", "")
        champion = champion[0].upper() + champion[1:].lower()
    elif " " in champion:
        champion = champion.replace(" ", "")
    champion = champion.replace(".", "")
    return f"http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion}_0.jpg"


def getChampions():
    response = requests.get(
        f'http://ddragon.leagueoflegends.com/cdn/{getApiVersion()}/data/en_US/champion.json', verify=False)
    champions = response.json()['data']
    champions_map = {}
    for champion in champions:
        champions_map[int(champions[champion]['key'])
                      ] = champions[champion]['name']
    return champions_map


champs = getChampions()


@connector.ready
async def connect(connection):
    global ready
    print('LCU API is ready to be used.')
    deleteNotConnectedText()
    ready = True

@connector.ws.register('/chat/v5/participants/champ-select', event_types=('CREATE', 'UPDATE', 'DELETE'))
async def champ_chat_select_changed(connection, event):
    print(event.data)
@connector.ws.register('/lol-champ-select/v1/session', event_types=('CREATE', 'UPDATE', 'DELETE'))
async def champ_select_changed(connection, event):
    global bluePicks, blueBans, redPicks, redBans, phase, in_champ_select, bluePickCanvases, redPickCanvases, blueBanCanvases, redBanCanvases
    eventType = event.type
    if eventType == "Create":
        print("Champ select started!")
        in_champ_select = True
        bluePicks = {'hover': 0, 'pick': []}
        blueBans = {'hover': 0, 'pick': []}
        redPicks = {'hover': 0, 'pick': []}
        redBans = {'hover': 0, 'pick': []}
        clearAllCanvases()
        deleteNotInChampSelectText()
        return
    elif eventType == "Delete":
        print("Champ select ended!")
        in_champ_select = False
        bluePicks = {'hover': 0, 'pick': []}
        blueBans = {'hover': 0, 'pick': []}
        redPicks = {'hover': 0, 'pick': []}
        redBans = {'hover': 0, 'pick': []}
        clearAllCanvases()
        makeNotInChampSelectText()
        return
    else:
        deleteNotInChampSelectText()
    lobby_phase = event.data['timer']['phase']
    if lobby_phase == 'FINALIZATION':
        myTeam = []
        enemyTeam = []
        for teammate in event.data['myTeam']:
            myTeam.append(teammate['championId'])
        for enemy in event.data['theirTeam']:
            enemyTeam.append(enemy['championId'])
        if bluePicks['pick'] != myTeam:
            bluePicks['pick'] = myTeam
            updateBluePicks()
        if redPicks['pick'] != enemyTeam:
            redPicks['pick'] = enemyTeam
            updateRedPicks()

    # print(f"\nlobby_phase: {lobby_phase}")
    # print(f"event.data: {event.data}")
    # print(f"event.data['actions']: {event.data['actions']}")

    # use most recent action
    for action in event.data['actions']:
        for actionArr in action:
            phase = actionArr['type']
            hovering = actionArr['isInProgress']
            action_id = actionArr['id']
            team = 'blue' if actionArr['isAllyAction'] else 'red'
            print(f"phase: {phase}")
            if actionArr['championId'] == 0:
                print("No champion selected")
                if not actionArr['completed']:
                    continue
                else:
                    champion = "None"
            else:
                champion = champs[actionArr['championId']]
            if phase == 'ban':
                if team == 'blue':
                    if hovering:
                        print(f"Blue hovering over {champion} to ban")
                        blueBans['hover'] = actionArr['championId']
                    else:
                        if actionArr['championId'] in blueBans['pick']:
                            continue
                        print(f"Blue banned {champion}")
                        blueBans['pick'].append(actionArr['championId'])
                        blueBans['hover'] = 0
                        if champion == "None":
                            print("Blue banned None")
                        updateBlueBans()
                else:
                    if hovering:
                        print(f"Red hovering over {champion} to ban")
                        redBans['hover'] = actionArr['championId']
                    else:
                        if actionArr['championId'] in redBans['pick']:
                            continue
                        print(f"Red banned {champion}")
                        redBans['pick'].append(actionArr['championId'])
                        redBans['hover'] = 0
                        if champion == "None":
                            print("Blue banned None")
                        updateRedBans()
            if phase == 'pick':
                if team == 'blue':
                    if hovering:
                        print(f"Blue hovering over {champion} to pick")
                        bluePicks['hover'] = actionArr['championId']
                    else:
                        if actionArr['championId'] in bluePicks['pick']:
                            continue
                        print(f"Blue picked {champion}")
                        bluePicks['pick'].append(actionArr['championId'])
                        bluePicks['hover'] = 0
                    updateBluePicks()

                else:
                    if hovering:
                        print(f"Red hovering over {champion} to pick")
                        redPicks['hover'] = actionArr['championId']
                    else:
                        if actionArr['championId'] in redPicks['pick']:
                            continue
                        print(f"Red picked {champion}")
                        redPicks['pick'].append(actionArr['championId'])
                        redPicks['hover'] = 0
                    updateRedPicks()


@connector.ws.register('/')
async def on_event(connection, event):
    global closed
    # only way to close the program is to sys.exit() in the event loop
    if closed:
        sys.exit()


@connector.close
async def disconnect(connection):
    global reconnectButtonFlag
    print('Finished task')
    reconnectButtonFlag = True
    makeNotConnectedText()
    sys.exit()


def on_closing():
    global closed
    closed = True
    root.destroy()


def drawPickChampion(pickNum, champion, blue, hover=False):
    global redPickCanvases, bluePickCanvases
    image = Image.open(requests.get(
        getChampionPickImage(champion), stream=True).raw)
    # crop image to 310x123 with middle of image'
    if champion == "Kayle":
        image = image.resize((372, 220))
        image = image.crop((186, 30, 372, 104))
        image = image.resize((372, 148))
    elif champion == "Morgana":
        image = image.resize((372, 220))
        image = image.crop((186, 30, 372, 104))
        image = image.resize((372, 148))
    else:
        image = image.resize((372, 220))
        image = image.crop((0, 0, 372, 148))
    photo = ImageTk.PhotoImage(image)
    if hover:
        # make image little bit darker
        photo = ImageTk.PhotoImage(ImageEnhance.Brightness(image).enhance(0.5))
    if blue:
        bluePickCanvases[pickNum].delete("all")
        bluePickCanvases[pickNum].create_image(0, 0, image=photo, anchor=tk.NW)
        bluePickCanvases[pickNum].image = photo
        bluePickCanvases[pickNum].create_text(0, 0, text=bluePlayers[pickNum], font=("Arial", 30), fill="white", anchor=tk.NW)
    else:
        redPickCanvases[pickNum].delete("all")
        redPickCanvases[pickNum].create_image(0, 0, image=photo, anchor=tk.NW)
        redPickCanvases[pickNum].image = photo
        redPickCanvases[pickNum].create_text(370, 0, text=redPlayers[pickNum], font=("Arial", 30), fill="white", anchor=tk.NE)

def drawBanChampion(pickNum, champion, blue):
    global redPickCanvases, bluePickCanvases
    image = Image.open(requests.get(
        getChampionBanImage(champion), stream=True).raw)
    # crop image to 310x123 with middle of image
    image = image.resize((78, 78))
    # convert image to grayscale
    image = image.convert('L')
    photo = ImageTk.PhotoImage(image)
    if blue:
        blueBanCanvases[pickNum].create_image(0, 0, image=photo, anchor=tk.NW)
        blueBanCanvases[pickNum].image = photo
    else:
        redBanCanvases[pickNum].create_image(0, 0, image=photo, anchor=tk.NW)
        redBanCanvases[pickNum].image = photo


def updateBluePicks():
    global bluePicks
    for i in range(len(bluePicks['pick'])):
        drawPickChampion(i, champs[bluePicks['pick'][i]], True)
    if bluePicks['hover']:
        drawPickChampion(
            len(bluePicks['pick']), champs[bluePicks['hover']], True, hover=True)


def updateRedPicks():
    global redPicks
    for i in range(len(redPicks['pick'])):
        drawPickChampion(i, champs[redPicks['pick'][i]], False)
    if redPicks['hover']:
        drawPickChampion(
            len(redPicks['pick']), champs[redPicks['hover']], False, hover=True)


def updateBlueBans():
    global blueBans
    for i in range(len(blueBans['pick'])):
        if blueBans['pick'][i] == 0:
            continue
        drawBanChampion(i, champs[blueBans['pick'][i]], True)

def drawPlayerLabels():
    global bluePickCanvases, redPickCanvases, blueBanCanvases, redBanCanvases, bluePlayers, redPlayers
    for i in range(5):
        bluePickCanvases[i].create_text(0, 0, text=bluePlayers[i], font=("Arial", 30), fill="white", anchor=tk.NW)
        redPickCanvases[i].create_text(370, 0, text=redPlayers[i], font=("Arial", 30), fill="white", anchor=tk.NE)

def updateRedBans():
    global redBans
    for i in range(len(redBans['pick'])):
        if redBans['pick'][i] == 0:
            continue
        drawBanChampion(i, champs[redBans['pick'][i]], False)


def clearAllCanvases():
    global bluePickCanvases, redPickCanvases, blueBanCanvases, redBanCanvases
    for canvas in bluePickCanvases:
        canvas.delete("all")
    for canvas in redPickCanvases:
        canvas.delete("all")
    for canvas in blueBanCanvases:
        canvas.delete("all")
    for canvas in redBanCanvases:
        canvas.delete("all")
    drawPlayerLabels()


def makeBluePickCanvases():
    bluePickCanvases = []
    for i in range(5):
        if i % 2 == 0:
            backgroundColor = '#e1721c'
        else:
            backgroundColor = '#ef7b22'
        bluePickCanvases.append(tk.Canvas(
            root, width=372, height=148, background=backgroundColor, highlightthickness=0))
        bluePickCanvases[i].place(x=108, y=210 + (i*148))
    return bluePickCanvases


def makeNotInChampSelectText():
    notInChampSelectText = tk.Label(
        root, text="Not in champion select", font=("Arial", 30), highlightbackground='#000000', highlightthickness=0)
    notInChampSelectText.place(x=720, y=840)
    return notInChampSelectText


def deleteNotInChampSelectText():
    global notInChampSelectText
    notInChampSelectText.destroy()


def makeNotConnectedText():
    global reconnectButtonFlag
    if reconnectButtonFlag:
        text="League client was closed\nPlease close and reopen this window"
    else:
        text="Not connected to league client"
    notConnectedText = tk.Label(
        root, text=text, font=("Arial", 30), highlightbackground='#000000', highlightthickness=0)
    notConnectedText.place(x=648, y=240)
    return notConnectedText

def deleteNotConnectedText():
    global notConnectedText
    notConnectedText.destroy()


def makeRedPickCanvases():
    redPickCanvases = []
    for i in range(5):
        if i % 2 == 0:
            backgroundColor = '#022562'
        else:
            backgroundColor = '#022a6f'
        redPickCanvases.append(tk.Canvas(
            root, width=372, height=148, background=backgroundColor, highlightthickness=0))
        redPickCanvases[i].place(x=1440, y=210 + (i*148))
    return redPickCanvases

def setRedPlayers():
    global redPlayers, redName
    # players from red.txt
    redPlayers = []
    with open('red.txt', 'r') as f:
        # first line is team name
        redName = f.readline()
        for i in range(5):
            redPlayers.append(f.readline())

def setBluePlayers():
    global bluePlayers, blueName
    # players from blue.txt
    bluePlayers = []
    with open('blue.txt', 'r') as f:
        # first line is team name
        blueName = f.readline()
        for i in range(5):
            bluePlayers.append(f.readline())
def makeTeamNameCanvas():
    global blueName, redName
    blueTeamCanvas = tk.Canvas(root, width=824, height=165, background='#16171b', highlightthickness=0)
    redTeamCanvas = tk.Canvas(root, width=824, height=165, background='#16171b', highlightthickness=0)
    blueTeamCanvas.place(x=132, y=35)
    redTeamCanvas.place(x=965, y=35)
    blueTeamCanvas.create_text(412, 100, text=blueName.upper(), font=("Arial", 30, 'bold'), fill="white", anchor=tk.CENTER)
    redTeamCanvas.create_text(412, 100, text=redName.upper(), font=("Arial", 30, 'bold'), fill="white", anchor=tk.CENTER)
    
def makeBlueBanCanvases():
    bluePickCanvases = []
    for i in range(3):
        bluePickCanvases.append(tk.Canvas(
            root, width=78, height=78, background='#ef7b22', highlightthickness=0))
        bluePickCanvases[i].place(x=152+(84*i), y=964)
    for i in range(2):
        bluePickCanvases.append(tk.Canvas(
            root, width=78, height=78, background='#ef7b22', highlightthickness=0))
        bluePickCanvases[i+3].place(x=426+(84*i), y=964)
    return bluePickCanvases


def makeRedBanCanvases():
    redBansCanvases = []
    for i in range(3):
        redBansCanvases.append(tk.Canvas(
            root, width=78, height=78, background='#022a6f', highlightthickness=0))
        redBansCanvases[i].place(x=1360+(84*i), y=964)
    for i in range(2):
        redBansCanvases.append(tk.Canvas(
            root, width=78, height=78, background='#022a6f', highlightthickness=0))
        redBansCanvases[i+3].place(x=1633+(84*i), y=964)
    return redBansCanvases


conThread = threading.Thread(target=connector.start)
conThread.start()
root = tk.Tk()
root.title("League of Legends Champ Select")
root.geometry("1600x900")
# make background background.png
canvas = tk.Canvas(root, width=1920, height=1080, highlightbackground='#000000', highlightthickness=0)
canvas.pack()
background = tk.PhotoImage(file="background.png")
canvas.create_image(0, 0, anchor=tk.NW, image=background)
bluePickCanvases = makeBluePickCanvases()
redPickCanvases = makeRedPickCanvases()
blueBanCanvases = makeBlueBanCanvases()
redBanCanvases = makeRedBanCanvases()
setRedPlayers()
setBluePlayers()
drawPlayerLabels()
makeTeamNameCanvas()
notInChampSelectText = makeNotInChampSelectText()
notConnectedText = makeNotConnectedText()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.attributes('-fullscreen',True)
root.mainloop()
