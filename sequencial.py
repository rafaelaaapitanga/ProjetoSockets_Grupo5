import time
import os
import socket
import threading

class SequencialNode:
    def __init__(self, id, ip, porta, vizinhos):
        self.id = id
        self.ip = ip
        self.porta = porta
        self.vizinhos = vizinhos
        self.files = {}
        self.lock = threading.Lock()
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reutiliza o endereço
        server_socket.bind((self.ip, self.porta))
        server_socket.listen(5)
        print(f'Node {self.id} listening on {self.ip}:{self.porta}')

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
            # print(f"Nó {self.id} recebeu {file_name} de {id}")
            self.save_file(file_name, file_content)
        client_socket.close()

    def forward_request(self, file_name, origem_ip, origem_porta):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(self.vizinhos)
                s.send(f"GET {file_name} {origem_ip} {origem_porta}".encode('utf-8'))
                print(f"Nó {self.id} encaminhou a solicitação para o nó {self.vizinhos}")
                response = s.recv(1024).decode('utf-8')
                if response.startswith("NOT FOUND"):
                    return False
                else:
                    return True
            except ConnectionRefusedError:
                print(f"Connection to vizinhos {self.vizinhos} refused.")

    def request_file(self, file_name, destino, starting_node):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                if self.id == starting_node:
                    s.connect(destino)
                    s.send(f"GET {file_name} {self.ip} {self.porta}".encode('utf-8'))
                    response = s.recv(1024).decode('utf-8')
                    if response.startswith("NOT FOUND"):
                        return False
                    else:
                        return True
                else:
                    return self.forward_request(file_name, nodes[starting_node - 1].ip, nodes[starting_node - 1].porta)
            except ConnectionRefusedError:
                pass

    def save_file(self, file_name, file_content):
        os.makedirs(f"nodo_{self.id}", exist_ok=True)
        with open(f"nodo_{self.id}/{file_name}", 'w') as f:
            f.write(file_content)
        # print(f"Node {self.id} saved {file_name}")


nodes = [
    SequencialNode(1, '127.0.0.1', 5006, ('127.0.0.1', 5007)),
    SequencialNode(2, '127.0.0.1', 5007, ('127.0.0.1', 5008)),
    SequencialNode(3, '127.0.0.1', 5008, ('127.0.0.1', 5009)),
    SequencialNode(4, '127.0.0.1', 5009, ('127.0.0.1', 5010)),
    SequencialNode(5, '127.0.0.1', 5010, ('127.0.0.1', 5006))
]

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

def request_file_sequentially(starting_node, file_name):
    destino = nodes[starting_node - 1].vizinhos
    cont = starting_node
    while True:
        print(destino)
        print(cont)
        if nodes[cont - 1].request_file(file_name, destino, starting_node):
            if cont == 5:
                cont = 0
            print(f"Arquivo {file_name} achado pelo nó {destino}!, que corresponde ao nó {cont + 1}")
            break
        if cont == 5:
            cont = 1
        else:
            cont += 1
        destino = nodes[cont - 1].vizinhos
        if destino == (nodes[starting_node - 1].ip, nodes[starting_node - 1].porta):
            print(f"Nó {cont} não tinha o arquivo {file_name}.")
            print(f"O arquivo {file_name} não existe na rede!!")
            break
        else:
            print(f"Nó {cont} não tinha o arquivo {file_name}, checando próximo nó.")


time.sleep(5)

tempo_inicial = time.time()

request_file_sequentially(2, 'arquivo_1.txt')
request_file_sequentially(3, 'arquivo_1.txt')
request_file_sequentially(4, 'arquivo_1.txt')
request_file_sequentially(5, 'arquivo_1.txt')

request_file_sequentially(1, 'arquivo_3.txt')
request_file_sequentially(2, 'arquivo_3.txt')
request_file_sequentially(4, 'arquivo_3.txt')
request_file_sequentially(5, 'arquivo_3.txt')

request_file_sequentially(1, 'arquivo_4.txt')
request_file_sequentially(2, 'arquivo_4.txt')
request_file_sequentially(3, 'arquivo_4.txt')
request_file_sequentially(5, 'arquivo_4.txt')

request_file_sequentially(1, 'arquivo_5.txt')

tempo_final = time.time()

print(f"Tempo necessário para que todas as requisições fossem atendendidas foi de {tempo_final - tempo_inicial:.10f}")
