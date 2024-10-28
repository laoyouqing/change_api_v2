# tcp客户端

from socket import *
from threading import Thread

from config import TCP_PORT


class TCPClient():
    def __init__(self, server_post):

        # 1创建套接字
        self.tcp_socket = socket(AF_INET,SOCK_STREAM)
        # 3连接服务器
        self.tcp_socket.connect(server_post)
        self.thread_rece = Thread(target=self.recv_msg)
        self.thread_send = Thread(target=self.send_msg)

    def recv_msg(self):
        # 接收信息
        self.tcp_socket.settimeout(60)
        recv_data = self.tcp_socket.recv(1024)  # 1024 表示接收最大字节  防止内存溢出
        recv_data = recv_data.decode('utf-8')
        return recv_data

    def send_msg(self,data):
        # 接收信息
        # while True:
        send_data = data.encode('utf-8')
        print(send_data)
        self.tcp_socket.send(send_data)

    def close(self):
        self.tcp_socket.close()



# #
if __name__ == '__main__':
    server1 = TCPClient(TCP_PORT)
    server1.send_msg('evapi|{"ip":"","token":"qfevserver"}')
    try:
        resp = server1.recv_msg()
        print('mini|{"ip":"","token":"qfevserver"}')
        print(resp)
        server1.close()
    except:
        print('超时')





