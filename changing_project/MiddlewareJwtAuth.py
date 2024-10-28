#!encoding:utf-8
import hashlib
from jose import jwt
from starlette.authentication import AuthenticationError, AuthCredentials
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse
from starlette_jwt import JWTAuthenticationBackend, JWTUser
from config import db_config, SECRET_KEY
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

timer = wf_time_new()



def get_user(user_id):
    sob = wf_mysql_class(cursor_type=True)
    sob_handle = sob.sql_open(db_config)
    cmd = f"SELECT * FROM wxapp_user WHERE id={user_id}"
    info = sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if info:
        return info[0]
    else:
        raise AuthenticationError(f"无效账户,账户不存在")



class JWTAuthenticationBackendMd(JWTAuthenticationBackend):

    async def authenticate(self, request):
        url = str(request.url)
        if 'doc' in url:
            return
        if 'openapi' in url:
            return
        if 'export' in url:  #所有导出
            return
        if 'register' in url:
            return
        if 'login' in url:
            return
        if 'get_setting' in url:
            return
        if 'get_guide' in url:
            return
        if 'get_color' in url:
            return
        if 'get_pictures' in url:
            return
        if 'upload' in url:
            return

        if "Authorization" not in request.headers:
            raise AuthenticationError("headers need param Authorization")
        auth = request.headers["Authorization"]
        token = self.get_token_from_header(authorization=auth, prefix=self.prefix)
        try:
            payload = jwt.decode(token, key=self.secret_key, algorithms=self.algorithm)
            user_id = payload['id']
            expire = payload['expire']
            if expire < timer.get_now():
                raise AuthenticationError(f"TOKEN已过期")
            user = get_user(user_id)
            s = f"{user['id']}-{user['nickname']}-{expire}-{SECRET_KEY}"
            if payload['signature'] != hashlib.sha1(s.encode('utf-8')).hexdigest():
                raise AuthenticationError("Token authentication failed.")
            request.__user__ = user
        except Exception as _:
            raise AuthenticationError("Token authentication failed.")
        return AuthCredentials(["authenticated"]), JWTUser(username=user['mobile'], token=token,
                                                           payload=payload)


class AuthenticationMiddlewareMd(AuthenticationMiddleware):

    @staticmethod
    def default_on_error(conn: HTTPConnection, exc: Exception):
        return JSONResponse({
            "status": 401,
            "message": "Token authentication failed."
        }, status_code=401)
