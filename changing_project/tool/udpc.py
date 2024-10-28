
from socket import *
from threading import Thread
import time


class Client():

    def __init__(self, data_info, server_post):
        # 初始化
        self.ServerPost = server_post
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.data_info = data_info


    def start(self):
        # 运行
        print(self.getTime(), '系统：您已加入聊天')
        thread_send = Thread(target=self.send_msg,args=(self.data_info,))
        thread_send.start()
        thread_send.join()

    def recv_msg(self):
        # 接收信息
        self.udp_socket.settimeout(15)
        recv_data, dest_ip = self.udp_socket.recvfrom(
            1024)  # 1024 表示接收最大字节  防止内存溢出

        if recv_data.decode(
                "utf-8") == 'exit' and dest_ip == self.ServerPost:
            print(self.getTime(), '客户端已退出')
            self.udp_socket.close()
        return recv_data.decode("utf-8")

    def send_msg(self,data_info):
        # 发送信息
        self.udp_socket.sendto(data_info.encode('utf-8'), self.ServerPost)

    def getTime(self):
        # 返回时间
        return '[' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ']'


if __name__ == '__main__':
    try:
        Postnum = 37884
        name  = '3333'
        client = Client(name, ('120.78.174.162', 57882))
        client.start()
        resp = client.recv_msg()
        print(resp)
    except:
        print('超时')


