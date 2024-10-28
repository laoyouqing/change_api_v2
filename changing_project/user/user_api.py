import hashlib

from pydantic import BaseModel, Field

from config import PWD_CONTENT, db_config, SECRET_KEY
from tool.format_data import format_response_data
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from jose import jwt
from jose.constants import ALGORITHMS
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()

class RegisterFilterFormat(BaseModel):
    id: int = Field(None, description="id")
    mini_id: int = Field(..., description="小程序id")
    note_id: str = Field('', description="社区id,多个社区,隔开")
    mobile: str = Field(..., description="手机号(编辑时手机号不能变)")
    nickname: str = Field(..., description="昵称")
    password: str = Field(..., description="密码")
    is_manage: int = Field(..., description="账号类型0:微信用户 1:系统管理员 2:操作员 3:区域操作员 5:代理商 6:物业")


class LoginFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    mobile: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")




def _register_user(request_data: RegisterFilterFormat):
    request_dict = request_data.dict()
    sob_handle = sob.sql_open(db_config)
    #除小程序用户外-其他用户手机号不能重复
    cmd = f"select * from wxapp_user where mini_id={request_data.mini_id} and mobile='{request_data.mobile}' and is_manage!=0"
    info = sob.select_mysql_record(sob_handle,cmd)
    if info:
        raise ValueError("该手机号已被注册")
    request_dict['password'] = PWD_CONTENT.hash(request_data.password)
    request_dict.update({"add_time": timer.get_now()})
    hope_lst = list(request_data.dict().keys())
    lastrowid = sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user', [request_dict], hope_lst)
    if request_data.is_manage == 5 or request_data.is_manage == 6: #5:代理商 6:物业
        value_info = {
            "mini_id":request_data.mini_id,
            "note_id":request_data.note_id,
            "type":request_data.note_id,
            "account_id":lastrowid,
            "add_time":timer.get_now(),
            "update_time":timer.get_now()
        }
        sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_dealer_note',[value_info])
    sob.sql_close(sob_handle)
    return


def _login_user(request_data: LoginFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select id,mobile,password,nickname,is_manage,authority_id from wxapp_user where mini_id={request_data.mini_id} and mobile='{request_data.mobile}' and is_manage!=0"
    info = sob.select_mysql_record(sob_handle, cmd)

    if not info:
        raise ValueError("该手机号不存在")
    user = info[0]
    password_matched = PWD_CONTENT.verify(request_data.password, user['password'])
    if not password_matched:
        raise ValueError("密码错误")
    user['expire'] = timer.get_now_bef_aft(days=-1)
    s = f"{user['id']}-{user['nickname']}-{user['expire']}-{SECRET_KEY}"
    signature = hashlib.sha1(s.encode('utf-8')).hexdigest()
    user['signature'] = signature
    token = jwt.encode(user, SECRET_KEY, algorithm=ALGORITHMS.HS256)
    user['token'] = token
    del user['password']
    if user['authority_id']:
        cmd = f"select * from wxapp_authority where id={user['authority_id']}"
        authority = sob.select_mysql_record(sob_handle,cmd)
        user['authority'] = authority[0] if authority else {}
    else:
        user['authority'] = {}
    sob.sql_close(sob_handle)
    return user


def _modify_user(request_data: RegisterFilterFormat):
    request_dict = request_data.dict()
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_user where id={request_data.id}"
    info = sob.select_mysql_record(sob_handle, cmd)
    if info[0]['mobile'] != request_data.mobile:
        raise ValueError('手机号不能改变')
    request_dict['password'] = PWD_CONTENT.hash(request_data.password)
    hope_lst = list(request_data.dict().keys())
    sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user', [request_dict], hope_lst)
    if info[0]['note_id'] != request_data.note_id:
        cmd = f"update wxapp_dealer_note set note_id='{request_data.note_id}' where account_id={request_data.id}"
        sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return


#【账户注册】
def register_user(request_data: RegisterFilterFormat):
    try:
        res = _register_user(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

#【修改账户信息】
def modify_user(request_data: RegisterFilterFormat):
    # try:
        res = _modify_user(request_data)
        response = format_response_data(res)
        return response
    # except Exception as exc:
    #     return {"status": 400, "msg": exc.__str__()}


#【账户登录】
def login_user(request_data: LoginFilterFormat):
    # try:
        res = _login_user(request_data)
        response = format_response_data(res)
        return response
    # except Exception as exc:
    #     return {"status": 400, "msg": exc.__str__()}



class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    id: int = Field(None, description="用户id (mini_id,id二选一)")
    is_manage: int = Field(None, description="账号类型0:微信用户 1:系统管理员 2客服 3:财务 4:工程 5:代理商 6:物业")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")
    note_id: int = Field(None, description="社区id")



def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    note_id = request_data['note_id']
    id = request_data['id']
    is_manage = request_data['is_manage']
    keyword = request_data['keyword']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if id:
        where_lst.append(f"a.id={id}")
    if note_id:
        where_lst.append(f"a.note_id={note_id}")
    if is_manage or is_manage==0:
        where_lst.append(f"is_manage={is_manage}")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_user(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              a.*, 
              b.name,
              count(*) over() as total
            from 
               wxapp_user a
            left join 
              wxapp_authority b
            on a.authority_id=b.id
            {where_sql}
            order by a.id desc
            limit {request_data.size} offset {request_data.offset}
        """
    print(cmd)
    info = sob.select_mysql_record(sob_handle, cmd)
    if isinstance(info, list):
        if info:
            total = info[0].get("total", 0)
        else:
            total = 0
    else:
        raise ValueError('error sql')
    for _ in info:
        if _['note_id']:
            cmd = f"select note_name from wxapp_note where id in ({_['note_id']})"
            note_info = sob.select_mysql_record(sob_handle,cmd)
            _['note_info'] = note_info
        else:
            _['note_info'] = []
        cmd = f"select * from wxapp_white_list where user_id={_['id']}"
        white = sob.select_mysql_record(sob_handle,cmd)
        if white:
            is_white = 1
        else:
            is_white = 0
        _['is_white'] = is_white
        cmd = f"select * from wxapp_door_idno where user_id={_['id']}"
        door_idno = sob.select_mysql_record(sob_handle, cmd)
        _['door_idno'] = door_idno
        del _["total"]
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "info": info
    }



#【获取用户】
def get_user(request_data: QueryFilterFormat):
    try:
        res = _get_user(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="用户id")


class FreezeFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    is_freeze: int = Field(..., description="是否冻结 1是 0否")


def _delete_user(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_user where id={request_data.id}"
    flag = sob.delete_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【删除用户】
def delete_user(request_data: DeleteFilterFormat):
    try:
        res = _delete_user(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


def _freeze_user(request_data: FreezeFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"update wxapp_user set is_freeze={request_data.is_freeze} where id={request_data.user_id}"
    sob.update_mysql_record(sob_handle,cmd)
    return ''

#【冻结用户】
def freeze_user(request_data: FreezeFilterFormat):
    try:
        res = _freeze_user(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class RechargeFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    money: float = Field(..., description="金额")


def _recharge_user(request_data: RechargeFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"update wxapp_user set virtual_balance=virtual_balance+{request_data.money} where id={request_data.user_id}"
    sob.update_mysql_record(sob_handle, cmd)
    return ''

#【用户充值虚拟金额】
def recharge_user(request_data: RechargeFilterFormat):
    try:
        res = _recharge_user(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}