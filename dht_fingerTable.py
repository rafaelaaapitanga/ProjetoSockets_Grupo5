import time
import os
import socket
import threading
import hashlib

class DHTNode:
    def __init__(self, id, ip, porta, finger_table):
        self.id = id
        self.ip = ip
        self.porta = porta
        self.finger_table = finger_table
        self.files = {}
        self.lock = threading.Lock()
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # reutiliza o endereço
        server_socket.bind((self.ip, self.porta))
        server_socket.listen(5)
        print(f'Nó {self.id} ouvindo em {self.ip}:{self.porta}')

        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, )).start()

    def handle_client(self, client_socket):
        request = client_socket.recv(1024).decode('utf-8')
        if request.startswith("GET "):
            file_name, origem_ip, origem_porta = request.split()[1:]
            origem_porta = int(origem_porta)
            with self.lock:
                if file_name in self.files:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        client_socket.send("FOUND".encode('utf-8'))
                        s.connect((origem_ip, origem_porta))
                        s.send(f"FOUND {file_name} {self.files[file_name]} {self.id}".encode('utf-8'))
                else:
                    client_socket.send("NOT FOUND".encode('utf-8'))
        elif request.startswith("FOUND "):
            file_name, file_content, id = request.split(' ', 3)[1:]
            with self.lock:
                self.files[file_name] = file_content
            self.save_file(file_name, file_content)
        elif request.startswith("PUT "):
            file_name, file_content = request.split(' ', 2)[1:]
            with self.lock:
                self.files[file_name] = file_content
            self.save_file(file_name, file_content)
        client_socket.close()

    def forward_request(self, file_name, origem_ip, origem_porta):
        for (ip, porta, node_id) in self.finger_table:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((ip, porta))
                    s.send(f"GET {file_name} {origem_ip} {origem_porta}".encode('utf-8'))
                    print(f"Nó {self.id} encaminhou a solicitação para o nó {node_id}")
                    response = s.recv(1024).decode('utf-8')
                    if response.startswith("NOT FOUND"):
                        continue
                    else:
                        return True
                except ConnectionRefusedError:
                    print(f"Conexão com o nó {node_id} recusada.")
        return False

    def request_file(self, file_name, starting_node):
        if self.id == starting_node:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((self.ip, self.porta))
                    s.send(f"GET {file_name} {self.ip} {self.porta}".encode('utf-8'))
                    response = s.recv(1024).decode('utf-8')
                    if response.startswith("NOT FOUND"):
                        return False
                    else:
                        return True
                except ConnectionRefusedError:
                    pass
        else:
            return self.forward_request(file_name, nodes[starting_node - 1].ip, nodes[starting_node - 1].porta)

    def save_file(self, file_name, file_content):
        os.makedirs(f"nodo_{self.id}", exist_ok=True)
        with open(f"nodo_{self.id}/{file_name}", 'w') as f:
            f.write(file_content)
        print(f"Nó {self.id} salvou {file_name}")

    def put_file(self, file_name, file_content):
        hashed_id = hash_id(file_name)
        target_node = self.find_successor(hashed_id)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_node.ip, target_node.porta))
            s.send(f"PUT {file_name} {file_content}".encode('utf-8'))
        print(f"Arquivo {file_name} armazenado no nó {target_node.id}")

    def find_successor(self, hashed_id):
        # Método simples para encontrar o nó sucessor
        for node in nodes:
            if node.id == hashed_id % len(nodes) + 1:
                return node
        return self

def hash_id(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16) % (2 ** 160)

# configuração dos nós DHT
nodes = [
    DHTNode(1, '127.0.0.1', 5006, [('127.0.0.1', 5007, 2), ('127.0.0.1', 5010, 5)]),
    DHTNode(2, '127.0.0.1', 5007, [('127.0.0.1', 5006, 1), ('127.0.0.1', 5008, 3)]),
    DHTNode(3, '127.0.0.1', 5008, [('127.0.0.1', 5007, 2), ('127.0.0.1', 5009, 4)]),
    DHTNode(4, '127.0.0.1', 5009, [('127.0.0.1', 5008, 3), ('127.0.0.1', 5010, 5)]),
    DHTNode(5, '127.0.0.1', 5010, [('127.0.0.1', 5009, 4), ('127.0.0.1', 5006, 1)])
]

# configuração dos arquivos iniciais
os.makedirs(f"nodo_{1}", exist_ok=True)
with open(f"nodo_{1}/arquivo_1.txt", 'w') as f:
    f.write("Conteúdo do arquivo 1")

os.makedirs(f"nodo_{2}", exist_ok=True)
os.makedirs(f"nodo_{3}", exist_ok=True)
with open(f"nodo_{3}/arquivo_3.txt", 'w') as f:
    f.write("Conteúdo do arquivo 3")

os.makedirs(f"nodo_{4}", exist_ok=True)
with open(f"nodo_{4}/arquivo_4.txt", 'w') as f:
    f.write("Conteúdo do arquivo 4")

os.makedirs(f"nodo_{5}", exist_ok=True)

nodes[0].files['arquivo_1.txt'] = "Conteúdo do arquivo 1"
nodes[2].files['arquivo_3.txt'] = "Conteúdo do arquivo 3"
nodes[3].files['arquivo_4.txt'] = "Conteúdo do arquivo 4"

time.sleep(1)

def request_file_dht(starting_node, file_name):
    for node in nodes:
        if node.id != starting_node:
            print(f"Nó {starting_node} solicitando {file_name} para o nó {node.id}")
            if node.request_file(file_name, starting_node):
                print(f"Arquivo {file_name} achado pelo nó {node.id}!")
                break
        else:
            print(f"Nó {node.id} já possui o arquivo {file_name}.")

time.sleep(5)

tempo_inicial = time.time()

# Realizando operações PUT
nodes[0].put_file('arquivo_1.txt', 'Conteúdo do arquivo 1')
nodes[2].put_file('arquivo_3.txt', 'Conteúdo do arquivo 3')
nodes[3].put_file('arquivo_4.txt', 'Conteúdo do arquivo 4')

# Realizando operações GET
request_file_dht(1, 'arquivo_1.txt')
request_file_dht(2, 'arquivo_1.txt')
request_file_dht(3, 'arquivo_1.txt')
request_file_dht(4, 'arquivo_1.txt')
request_file_dht(5, 'arquivo_1.txt')

request_file_dht(1, 'arquivo_3.txt')
request_file_dht(2, 'arquivo_3.txt')
request_file_dht(3, 'arquivo_3.txt')
request_file_dht(4, 'arquivo_3.txt')
request_file_dht(5, 'arquivo_3.txt')

request_file_dht(1, 'arquivo_4.txt')
request_file_dht(2, 'arquivo_4.txt')
request_file_dht(3, 'arquivo_4.txt')
request_file_dht(4, 'arquivo_4.txt')
request_file_dht(5, 'arquivo_4.txt')

tempo_final = time.time()

print(f"Tempo necessário para que todas as requisições fossem atendidas foi de {tempo_final - tempo_inicial:.10f} segundos")