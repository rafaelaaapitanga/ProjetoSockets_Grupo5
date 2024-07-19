# ProjetoSockets_Grupo5
Projeto de Sockets da disciplina Infraestrutura de Comunicação da Universidade Federal de Pernambuco (UFPE). 

O projeto tem como objetivo comparar o tempo para que todos os usuários recebam determinados arquivos. Essa comparação se dá por meio de uma aplicação P2P que utiliza o DHT com finger table, e outra por meio de um protocolo de roteamento sequencial baseado em vizinhança, a partir do protocolo TCP.
A rede é constituída por 5 nós que solicitam arquivos de seus vizinhos, seguindo uma ordem específica em que, ao fim, os 5 nós possam conter os arquivos 1, 3 e 4 que forneceram o serviço aos outros nós.

# Rodando o código:
Cada um dos arquivos, dht_fingerTable.py e sequencial.py, deverá ser rodado de forma individual. Na execução, 5 pastas com os devidos nós serão criadas automaticamente, recebendo os arquivos solicitados dentro da especificação presente no código. Fique atento(a) e apague as pastas criadas sempre que desejar rodar o código novamente, além de abrir um novo terminal para que seja iniciada uma nova comunicação na rede.
