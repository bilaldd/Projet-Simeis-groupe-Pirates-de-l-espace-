import os
import json
import time
import queue
import threading


class GameActor(threading.Thread):
    def __init__(self, msg):
        threading.Thread.__init__(self)
        self.msg = msg
        self.alive = True

    def run(self):
        self.init()
        while self.alive:
            try:
                nsleep = self.loop()
                tstart = time.time()
                src, msg = self.msg.get(timeout=nsleep)
                while msg != None:
                    self.handle_message(src, msg)
                    dt = time.time() - tstart
                    if nsleep - dt > 0:
                        src, msg = self.msg.get(timeout=nsleep - dt)
                    else:
                        msg = None

            except Exception as err:
                self.msg.error(err)
                return

    def log(self, *msg):
        log(self.msg.src, *msg)

    def init(self):
        pass

    def loop(self):
        return 1

    def handle_message(self, src, msg):
        if src == None and msg == "exit":
            self.alive = False
            return


# Petit utilitaire pour logger dans un fichier tout ce qu'il se passe
# Utilisation:  log("toto", "je suis", "une truite")    -> Écrira "je suis une truite" dans "logs/toto.log"
def log(fpath, *msg):
    date = time.strftime('%d/%m/%Y %H:%M:%S')
    data = f"{date}| " + " ".join(msg)
    with open(f"logs/{fpath}.log", "a") as f:
        f.write(data)
        f.write("\n")
    print(data)


# Utilitaire qui transmet les messages à tous les threads
# PAS BESOIN DE LIRE & COMPRENDRE CE CODE
class BureauDePoste:
    def __init__(self, sdk, player_id):
        self.player_id = player_id
        self.sdk = sdk
        self.q = queue.Queue()
        self.threads = {}
        self.alive = True

    def loop(self):
        while self.alive:
            (src, data) = self.q.get(True)
            if src is None:
                self.event(data)
                continue
            for (dst, q) in self.threads.items():
                if src == dst:
                    continue
                q.put((src, data))

    def event(self, data):
        if data == "exit":
            return self.exit()
        if "event" not in data:
            log("main", "WARN| Invalid event:", json.dumps(data, indent=1))
            return
        if data["event"] == "new-ship":
            if "assigned_station" not in data:
                log("main", "WARN| New ship event without assigned station:", json.dumps(data, indent=1))
                return
            if "id" not in data:
                log("main", "WARN| New ship event without new ship ID:", json.dumps(data, indent=1))
                return
            sid = event["id"]
            ship = Ship(self.sdk, self.player_id, event["assigned_station"], sid, self.new(f"ship-{sid}"))
            ship.start()

    def exit(self):
        for t in self.threads.values():
            t.put((None, "exit"))
        self.alive = False

    def new(self, src):
        log("main", f"New thread {src} registered in PostOffice")
        thread_q = queue.Queue()
        self.threads[src] = thread_q
        return Facteur(src, self.q, thread_q)


# Utilitaire qui envoie un message au bureau de poste
class Facteur:
    def __init__(self, src, send, recv):
        self.src = src
        self.sendq = send
        self.recvq = recv

    # Utilisation:  fact.put(a=3, b=5, toto=tutu) -> Enverra '{ a: 3, b: 5, "toto": "tutu" }' à tous les autres acteurs
    def put(self, **data):
        msg = f"{self.src} > " + json.dumps(data, sort_keys=True).replace("{\"", "{ \"").replace("}", " }")
        log(self.src, msg)
        self.sendq.put((self.src, data))

    # Récupère le dernier message envoyé
    # Peut attendre un message (block=True), ou pas (block=False)
    def get(self, block=True, timeout=1):
        try:
            src, data = self.recvq.get(block=block, timeout=timeout)
            assert src != self.src
            return src, data
        except queue.Empty:
            return None, None

    def error(self, err):
        import traceback
        tb = ''.join(traceback.format_exception(None, err, err.__traceback__))
        log(self.src, f"Error: {err}", "\n#####\nTraceback: \n", tb, "\n#####")
        self.sendq.put((None, "exit"))

    # Si on veut créer un nouveau vaisseau, cette fonction va demander au BureauDePoste
    # de créer le thread et tout ce qu'il faut pour qu'il s'exécute correctement
    def declare_new_ship(self, assigned_station, new_ship_id):
        newsrc = f"ship-{new_ship_id}"
        log(newsrc, f"New ship declared by {self.src}")
        self.recvq.put((None, {"event": "new-ship", "assigned_station": assigned_station, "id": new_ship_id}))
        


### Game init

USERNAME = "mon_user"
IP = "0.0.0.0"
PORT = 8080

# Condition pour checker si on importe le code,
#   ou si on l'exécute dans le terminal
if __name__ == "__main__":
    from sdk import SimeisSDK
    from upgrader import Upgrader
    from ship import Ship, acheter_premier_vaisseau
    from trader import Trader

    os.makedirs("logs", exist_ok=True)  # On créé le dossier de logs s'il n'existe pas
    log("main", "Init game")

    sdk = SimeisSDK(USERNAME, IP, PORT)
    player_id = sdk.player["playerId"]

    poste = BureauDePoste(sdk, player_id)
    upg = Upgrader(sdk, player_id, poste.new("upgrader"))

    player = sdk.get_player_status()
    station_id = player["stations"][0]
    trader = Trader(sdk, player_id, station_id, poste.new("trader"))

    ship = acheter_premier_vaisseau(sdk, player_id, station_id, poste)

    # On démarre tous les threads en background
    upg.start()
    trader.start()
    ship.start()

    # Et on lance le système de poste
    try:
        poste.loop()
    except KeyboardInterrupt:
        print("*** INTERRUPTION ***")
    except Exception as err:
        poste.new("main").error(err)
    finally:
        print("Quittage en cours...")
        poste.exit()
