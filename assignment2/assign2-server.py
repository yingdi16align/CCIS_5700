import socket
import time
import _thread
import re
import sys
import logging
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
host_port = 8181
bufsize = 1024 
serverName = ''
port=80
error405='HTTP_BAD_METHOD: 405'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host_ip, host_port))
s.listen(5)

print('\nServer started. Waiting for connection...\n')
def now():
	return time.ctime(time.time())
    
def handler(conn):
     while True:
        conn.settimeout(15)
        data = conn.recv(bufsize)
        request = data.decode('utf-8')
        print('----------------The request is: ',request)
        for line in request.splitlines():
            # we only consider GET method
             if line[0:3] == 'GET':
                 url = line.split(' ')[1]
                 length = len(url)
                 path = url[7:length]
                 logging.info('the complete request path is : ', path)
                 serverName = path.split("/", 1)[0]
                 logging.info('the host name is: ', serverName)
                 fileName =  path.split("/", 1)[1]
                 logging.info('the fileName is : ', fileName)
                 break
             # all other methods return 405
             else:
                 # HTTP_BAD_METHOD = 405
                 logging.error(error405)
                 print('wrong request: ',request)
                 raise ValueError(error405)
                 break
                 return
        serverSocket = None
        try:
            # this is just a format example, I didn't test google because it is https
            # serverSocket = socket.create_connection(('www.google.com', port))
            serverSocket = socket.create_connection((serverName, port))
            #'GET / HTTP/1.1\r\nConnection: close\r\n\r\n'
            requestRealServer= "GET /{} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(fileName, serverName) 
            logging.info('sending the request to the real server: ', requestRealServer)
            serverSocket.sendall(requestRealServer.encode('utf-8'))
            haveContent = False
            # when we see "Content-Type" or all response data is read, we shouldn't continue
            shouldContinue=True
            receivedBytes = 0   
            serverSocket.settimeout(15)
            while True:
                responseData = serverSocket.recv(bufsize)
                response = responseData.strip().decode('utf-8')
                receivedBytes = receivedBytes + len(response)
                
                if(shouldContinue == True):
                    for line in response.splitlines():
                        if line[0:12] == 'Content-Type':
                            haveContent = True
                            shouldContinue=False
                            receivedBytes = len(response.split('\r\n\r\n')[1])
                            break
                    shouldContinue=False
                if(haveContent == True):   
                    logging.info(response)
                    print(response)
                    if(receivedBytes >= bufsize):
                        break
                if(haveContent == False):
                    if (len(response.strip()) > 0):
                        logging.info(response)
                        print(response)
                    else:
                        break
                
            serverSocket.close()
            conn.close()
            return
        except socket.error as message:
            logging.error('an error occurred',message)
            if serverSocket:
                serverSocket.close()
            if conn:
                conn.close()
            sys.exit(1)
     conn.close()
	
while True:
    # the proxy server name
    print('host name:', host_name)
    conn, addr = s.accept()
    print('Server connected by', addr,'at', now())
    _thread.start_new(handler, (conn,))
    