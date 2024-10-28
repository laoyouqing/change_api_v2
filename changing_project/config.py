from passlib.context import CryptContext

db_config = {
    "host": "60.204.222.113",
    "user": "root",
    "password": "Qf123456",
    "port": 3306,
    "database": "qf_change",
    "charset": "utf8mb4",
}


# 创建密码哈希上下文对象
PWD_CONTENT = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = 'HDJBFHDQFHJF'
TCP_PORT = ('123.60.187.198',37881)
UDP_PORT = ('123.60.187.198',37882)
# UDP_PORT = ('127.0.0.1',37882)
REQ_HOST = 'https://www.fjqfzl.top'
# REQ_HOST = 'http://123.60.187.198:9001'

# pip install python-multipart -i https://mirrors.aliyun.com/pypi/simple
