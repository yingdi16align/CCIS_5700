import socket
import time
import _thread
import struct
import re
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
host_port = 8181
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host_ip, host_port))
s.listen(5)
print('\nServer started. Waiting for connection...\n')
def now():
    return time.ctime(time.time())
bufsize = 16
# recursively evaluate the expression
def evaluate(expression):
    # / and * have haigher priority over - and +, so we need to deal with / and * first
    if expression.__contains__("/"):
        expression = split_string(expression,"/")
        return evaluate(expression)
    if expression.__contains__("*"):
        expression = split_string(expression, "*")
        return evaluate(expression)
    if expression.__contains__("-"):
        expression = split._string(expression, "-")
        return evaluate(expression)
    if expression.__contains__("+"):
        expression = split_string(expression, "+")
        return evaluate(expression)
    return expression

def split_string(s, operation):
    left_str = s[0:s.index(operation)]
    right_str = s[s.index(operation)+1:len(s)]
    num1_str = re.search('\d+$', left_str).group()
    num1 = int(num1_str)
    num2_str = re.search('\d+', right_str).group()
    num2 = int(num2_str)
    result = left_str.rstrip(num1_str) + str(calculate(num1,num2, operation))+ right_str.lstrip(num2_str)
    return result
    
def calculate(a, b, operation):
    num1 = a
    num2 = b
    if operation == "+":
        return num1 + num2
    elif operation == "-":
        return num1 - num2
    elif operation == "/":
        if  num2 == 0:
            return "error"
        else:
            return num1 / num2
    elif operation == "*":
        return num1 * num2
    
error_message="error"
def handler(conn):
    # count of the data received
    cnt = 0;
    # number of expression to evaluate 
    #total = 0;
    # accumulated  bytes count
    total_bytes = 0
    while True:
        cnt = cnt + 1;
        data = conn.recv(bufsize)
        if not data: break
        if cnt == 1: 
            #total = cnt
            print('Server received expression number:', (struct.unpack('!h', data)[0]))
        elif cnt > 1:
            if cnt % 2 == 0: 
                print('Server received byte number:', (struct.unpack('!h',data)[0]))
                total_bytes = total_bytes+ struct.unpack('!h', data)[0]
                if total_bytes > bufsize:
                    data = error_message
            if cnt % 2 == 1:
                expression = data.decode('utf-8')
                print('Server received expression:', expression)
                data = evaluate(expression).encode('utf-8')
                total_bytes = 0
                #conn.sendall(data)
        time.sleep(10)
        conn.sendall(data)
    conn.close()
    
    
while True:
    conn, addr = s.accept()
    print('Server connected by', addr,'at', now())
    _thread.start_new(handler, (conn,))