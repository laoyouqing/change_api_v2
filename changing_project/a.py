from jose import jwt
from jose.constants import ALGORITHMS

claims={
    "user":1,
    "expire":10
}

token = jwt.encode(claims, 'x2s2d', algorithm=ALGORITHMS.HS256)
print(token)
payload = jwt.decode(token, key='x2s2d', algorithms=ALGORITHMS.HS256)
print(payload)

from fastapi import FastAPI
from passlib.context import CryptContext

app = FastAPI()

# 创建密码哈希上下文对象
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.post("/register")
async def register_user(username: str, password: str):
    # 对密码进行哈希加密
    hashed_password = pwd_context.hash(password)

    # 在此处将用户名和哈希密码保存到数据库中，这里只是一个示例

    return {"message": "User registered successfully"}


@app.post("/login")
async def login(username: str, password: str):
    # 从数据库中获取保存的用户名和哈希密码，这里只是一个示例

    # 比较用户输入的密码与保存的哈希密码是否匹配
    password_matched = pwd_context.verify(password, stored_hashed_password)
    if not password_matched:
        return {"message": "Invalid credentials"}

    return {"message": "Logged in successfully"}