from game import GameActor

class Ship(GameActor):
    def __init__(self, sdk, player_id, station_id, ship_id, msg):
        GameActor.__init__(self, msg)
        self.player_id = player_id
        self.station_id = station_id
        self.ship_id = ship_id
        self.sdk = sdk
        self.alive = True

    # Ici, j'initialise mon ship
    # Exécuté une seule fois
    def init(self):
        self.log("Init ship")      # Message à afficher dans les logs

    # Ici, je gère les messages envoyés par mes compatriotes
    def handle_message(self, src, msg):
        super().handle_message(src, msg)    # LAISSEZ ÇA ICI SVP

    # Ici, le code qui sera appelé en boucle
    # Retourne le nombre de secondes à attendre avant l'exécution
    # de la prochaine boucle
    def loop(self):
        self.msg.put(ship_message="coucou") # Message à envoyer aux autres acteurs
        return 1    # J'ai décidé que j'attendrai 1 sec avant la prochaine boucle

def acheter_premier_vaisseau(sdk, player_id, station_id, poste):
    all_ships = sdk.shop_list_ship(station_id)
    # Ordonnés du - cher au + cher
    # je prends le 1er prix
    ship_id = all_ships[0]["id"]
    sdk.buy_ship(station_id, ship_id)
    return Ship(sdk, player_id, station_id, ship_id, poste.new(f"ship-{ship_id}"))
