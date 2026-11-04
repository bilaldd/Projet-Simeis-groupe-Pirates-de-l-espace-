from game import GameActor

class Upgrader(GameActor):
    def __init__(self, sdk, player_id, msg):
        GameActor.__init__(self, msg)
        self.player_id = player_id
        self.sdk = sdk
        self.alive = True

    # Ici, j'initialise mon upgrader
    # Exécuté une seule fois
    def init(self):
        self.log("Init upgrader")      # Message à afficher dans les logs

    # Ici, je gère les messages envoyés par mes compatriotes
    def handle_message(self, src, msg):
        super().handle_message(src, msg)    # LAISSEZ ÇA ICI SVP

    # Ici, le code qui sera appelé en boucle
    # Retourne le nombre de secondes à attendre avant l'exécution
    # de la prochaine boucle
    def loop(self):
        self.msg.put(upgrader_message="coucou") # Message à envoyer aux autres acteurs
        return 1    # J'ai décidé que j'attendrai 1 sec avant la prochaine boucle
