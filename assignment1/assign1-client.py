import socket
import struct

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = '10.142.0.2'
server_port = 8181
s.connect((server_ip, server_port))
print('Connected to server ', server_ip, ':', server_port)
message = [2,4,"3+12", 6, "1+12/3"]
bufsize = 16
for line in message:
    if isinstance(line, int):
        s.sendall(struct.pack('!h',line))
    if isinstance(line, str):
        s.sendall(line.encode('utf-8'))
    print('Client sent:', line)
    data = s.recv(bufsize)
    print('Clinet received: ', data.decode('utf-8'))
    #print('Client received:',struct.unpack('!h', data)[0])
s.close()
