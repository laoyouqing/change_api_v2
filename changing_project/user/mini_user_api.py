import hashlib
from jose import jwt
from jose.constants import ALGORITHMS
from pydantic import Field, BaseModel
from config import db_config, SECRET_KEY
from tool.format_data import format_response_data
from tool.normal_func import get_access_token
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import wx_mini_sdk
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()


class AuthorizeFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    code: str = Field(..., description="code")
    gender: int = Field(..., description="性别")
    is_manage: int = Field(0, description="账号类型 0:微信用户")


class BindMobieFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    user_id: int = Field(..., description="用户id")
    code: str = Field(..., description="code")


def _authorize_login_user(request_data: AuthorizeFilterFormat):
    mini_id = request_data.mini_id
    gender = request_data.gender
    is_manage = request_data.is_manage
    code = request_data.code
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_mini where id={mini_id}"
    minis = sob.select_mysql_record(sob_handle, cmd)
    if minis:
        mini = minis[0]
        result = wx_mini_sdk().mini_login(mini['authorizer_appid'], mini['secret'], code)
        openid = result.get('openid')
        session_key = result.get('session_key')
        cmd = f"select * from wxapp_user where mini_id={mini_id} and open_id='{openid}'"
        # cmd = f"select * from wxapp_user limit 1"
        user = sob.select_mysql_record(sob_handle, cmd)
        print(user)
        if not user:
            value_info = {
                'mini_id': mini_id,
                'gender': gender,
                'is_manage': is_manage,
                'open_id': openid,
                "add_time":timer.get_now(),
            }
            lastrowid = sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user', [value_info])
            cmd = f"select * from wxapp_user where id={lastrowid}"
            user = sob.select_mysql_record(sob_handle, cmd)
        user = user[0]
        del user['add_time']
        user['expire'] = timer.get_now_bef_aft(days=-1)
        s = f"{user['id']}-{user['nickname']}-{user['expire']}-{SECRET_KEY}"
        signature = hashlib.sha1(s.encode('utf-8')).hexdigest()
        user['signature'] = signature
        token = jwt.encode(user, SECRET_KEY, algorithm=ALGORITHMS.HS256)
        user['token'] = token
        user['authorizer_appid'] = mini['authorizer_appid']
        cmd = f"select * from wxapp_payinfo where mini_id={mini_id}"
        payinfo = sob.select_mysql_record(sob_handle, cmd)
        user['pay_type'] = payinfo[0]['pay_type'] if payinfo else 1
        return user
    else:
        raise ValueError("小程序不存在")


def authorize_login_user(request_data: AuthorizeFilterFormat):
    try:
        res = _authorize_login_user(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

def _bind_mobile_user(request_data: BindMobieFilterFormat):
    sob_handle = sob.sql_open(db_config)
    code = request_data.code
    user_id = request_data.user_id
    mini_id = request_data.mini_id
    access_token = get_access_token(mini_id)
    if access_token:
        resp = wx_mini_sdk().get_mobile(access_token,code)
        print('----------')
        print(resp)
        if resp['errcode'] == 0:
            mobile = resp['phone_info']['phoneNumber']
            cmd = f"update wxapp_user set mobile='{mobile}' where id={user_id}"
            sob.update_mysql_record(sob_handle,cmd)
            cmd = f"select * from wxapp_user where id={user_id}"
            user = sob.select_mysql_record(sob_handle, cmd)
            sob.sql_close(sob_handle)
            return user[0]
        else:
            raise ValueError('获取手机号失败')
    else:
        raise ValueError('token不存在')




def bind_mobile_user(request_data: BindMobieFilterFormat):
    try:
        res = _bind_mobile_user(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class UserFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    nickname: str = Field(..., description="昵称")
    avatar: str = Field(..., description="头像")
    mobile: str = Field(..., description="手机号")

def _update_user_info(request_data: UserFilterFormat):
    sob_handle = sob.sql_open(db_config)
    nickname = request_data.nickname
    avatar = request_data.avatar
    user_id = request_data.user_id
    mobile = request_data.mobile
    cmd = f"update wxapp_user set nickname='{nickname}',avatar='{avatar}',mobile='{mobile}' where id={user_id}"
    sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return


def update_user_info(request_data: UserFilterFormat):
    try:
        res = _update_user_info(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


