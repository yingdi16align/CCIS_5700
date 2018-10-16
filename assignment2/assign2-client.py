import socket
import sys
request = sys.argv[1]
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = '192.168.1.7'
server_port = 8181
s.connect((server_ip, server_port))
print('Connected to server ', server_ip, ':', server_port)
#message = ['GET http://www.washington.edu/index.html HTTP/1.1\nConnection: close']
bufsize = 1024
#for line in message:
s.sendall(request.encode('utf-8'))
print('Client sent:', request)
data = s.recv(bufsize)
print('Client received:', data)
s.close()