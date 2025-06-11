import json
import random
import socket

from card import Card
from message import RingMessage, RingMessageType

NUM_MACHINES = 4
BASE_PORT = 5000
HOST = '127.0.0.1'
MACHINE_ADDR_MAP = {i: (HOST, BASE_PORT + i) for i in range(NUM_MACHINES)}

choosen_cards = []

class RingMachine:
    hand = []
    mount = []
    connected_machines = {}
    has_token = False
    points = 0

    def __init__(self, machine_id: int):
        self.machine_id = machine_id
        self.my_address = MACHINE_ADDR_MAP[machine_id]
        
        self.next_machine_id = (machine_id + 1) % 4
        self.next_machine_address = MACHINE_ADDR_MAP[self.next_machine_id]

        self.has_token = machine_id == 0

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((self.my_address))
        except socket.error as e:
            print(f"[M{self.machine_id}] ERRO Fatal ao fazer bind no socket {self.my_address}: {e}")
            print("Verifique se as portas estão disponíveis ou se há outra instância rodando.")
            raise

        print(f"[M{self.machine_id}] Online. Escutando em {self.my_address}. Próxima: M{self.next_machine_id} ({self.next_machine_address}).")

    def _send_udp_message(self, message_bytes: bytes, address: tuple):
        """Envia uma mensagem UDP para o endereço especificado."""
        self.sock.sendto(message_bytes, address)

    def _send_connection_message(self):
        message_to_send = RingMessage(
            RingMessageType.CONNECT,
            f"{self.machine_id}",
            0
        )

        self._send_udp_message(message_to_send.to_bytes(), MACHINE_ADDR_MAP[0])

    def _play_card(self):

        if not self.mount:
            self.mount.append(self.hand.pop())
        else:
            mount_suit = self.mount[0].suit
            if mount_suit in [card.suit for card in self.hand]:
                suited_cards = [card for card in self.hand if card.suit == mount_suit]
                smaller_card = min(suited_cards, key=lambda c: c.value, default=None)

            else:
                smaller_card = min(self.hand, key=lambda c: c.value)
            
            self.mount.append(smaller_card)
            self.hand.remove(smaller_card)
        
    def _send_token(self):
        message_to_send = RingMessage(
            RingMessageType.TOKEN,
            json.dumps([card.to_dict() for card in self.mount]),
            self.next_machine_id
        )
        self.has_token = False
        self._send_udp_message(message_to_send.to_bytes(), self.next_machine_address)

    def _handle_incoming_message(self, message_str: str):
        """Processa a chegada de uma mensagem de dados."""
        try:
            # Extrai componentes da mensagem: "TYPE:TARGET:<payload>"
            message_type, target, payload = message_str.split(";")
            message_type = int(message_type)
            target = int(target)

            if target != self.machine_id:
                print("Mensagem não para mim")
                self._send_udp_message(message_str.encode("utf-8"), self.next_machine_address)
                return
            
            if message_type == RingMessageType.CONNECT.value:
                self.connected_machines[payload] = 1
            
            elif message_type == RingMessageType.SETUP.value:
                self.hand = [Card.from_dict(c) for c in json.loads(payload)]
            
            elif message_type == RingMessageType.TOKEN.value:
                self.has_token = True
                self.mount = [Card.from_dict(c) for c in json.loads(payload)]
                
                if self.machine_id in [card.sender for card in self.mount]:
                    self._determine_loser()
                    return
                if not self.hand:
                    self._trigger_end_game({})
                    return

                self._play_card()
            
            elif message_type == RingMessageType.POINTS.value:
                self.has_token = True
                self.points += int(json.loads(payload))
                self.mount = []

                if not self.hand:
                    self._trigger_end_game({})
                    return

                self._play_card()
            
            elif message_type == RingMessageType.END.value:
                machine_points = json.loads(payload)

                if len(machine_points) == 4:
                    print(machine_points)
                    print(f"Máquina vencedora: {min(machine_points, key=machine_points.get)}")
                    self.close_socket()
                else:
                    self._trigger_end_game(machine_points)
            
            elif message_type == RingMessageType.TURN_OFF.value:
                self.close_socket()
            
        except Exception as e:
            print(f"Falha ao receber mensagem: {str(e)}")

    def run(self):
        if(self.machine_id == 0):
            print("Esperando pelas outras máquinas")
            while(len(self.connected_machines) < 3):
                data, _ = self.sock.recvfrom(1024)
                message_str = data.decode('utf-8')

                self._handle_incoming_message(message_str)
            
            self._initiate_cards()
            self._play_card()
            self._send_token()
        else:
            self._send_connection_message()

        while True:
            try:
                data, _ = self.sock.recvfrom(1024) # Tamanho do buffer de 1024 bytes
                message_str = data.decode('utf-8')

                self._handle_incoming_message(message_str)

                if self.has_token:
                    print("Token recebido. Enviando para a próxima máquina")
                    self._send_token()

            except socket.error as e:
                print(f"[M{self.machine_id}] Erro de socket: {e}. Saindo do loop de execução.")
                self.close_socket()
                
                break
            except Exception as e:
                print(f"[M{self.machine_id}] ERRO durante recebimento/processamento: {e}")
                self.close_socket()
                break

    def close_socket(self):
        """Fecha o socket da máquina."""
        print(f"[M{self.machine_id}] Fechando socket.")

        message_to_send = RingMessage(
            RingMessageType.TURN_OFF,
            "",
            self.next_machine_id
        )
        self._send_udp_message(message_to_send.to_bytes(), self.next_machine_address)
        self.sock.close()

    def _initiate_cards(self):
        for i in range(0, 4, 1):
            cards_to_be_sent = []

            while len(cards_to_be_sent) < 7:
                random_num = random.randrange(1, 12, 1)
                random_suit = random.randrange(1, 4, 1)

                new_card = Card(
                    value=random_num,
                    suit=random_suit,
                    machine_id=i
                )

                if str(new_card) not in [str(card) for card in choosen_cards]:
                    choosen_cards.append(new_card)
                    cards_to_be_sent.append(new_card)
            
            if i == 0:
                self.hand = cards_to_be_sent
            else:
                message_to_send = RingMessage(
                    RingMessageType.SETUP,
                    json.dumps([card.to_dict() for card in cards_to_be_sent]),
                    i
                )
                self._send_udp_message(message_to_send.to_bytes(), MACHINE_ADDR_MAP[i])
    
    def _determine_loser(self):
        biggest_card = max(self.mount, key=lambda c: c.value, default=None)

        message_to_send = RingMessage(
            RingMessageType.POINTS,
            json.dumps(biggest_card.points()),
            biggest_card.sender
        )
        self.has_token=False
        self._send_udp_message(message_to_send.to_bytes(), MACHINE_ADDR_MAP[message_to_send.target])
    
    def _calculate_points(self):
        for card in self.hand:
            self.points += card.points()
        
        return self.points

    def _trigger_end_game(self, points_dict: dict):
        points_dict[self.machine_id] = self._calculate_points()

        message_to_send = RingMessage(
            type=RingMessageType.END,
            content=json.dumps(points_dict),
            target=self.next_machine_id
        )
        self._send_udp_message(message_to_send.to_bytes(), self.next_machine_address)
