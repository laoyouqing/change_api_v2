from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()


class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    user_id: int = Field(None, description="用户id")
    id: int = Field(None, description="用户门禁卡id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

class CreateFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    id: int = Field(..., description="id")
    user_id: int = Field(..., description="user_id")
    note_id: int = Field(..., description="note_id")
    idno: str = Field(None, description="idno")
    rfid: str = Field(None, description="rfid")


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="用户门禁卡id")


def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    user_id = request_data['user_id']
    id = request_data['id']
    keyword = request_data['keyword']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if id:
        where_lst.append(f"a.id={id}")
    if user_id:
        where_lst.append(f"a.user_id={user_id}")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%' or idno like '%{sob.escape(keyword)}%' or rfid like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_door_idno(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*, nickname,avatar,note_name,mobile,a.add_time,
               count(*) over() as total
            from
               wxapp_door_idno a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_note c
            on a.note_id=c.id
            {where_sql}
            order by add_time desc
            limit {request_data.size} offset {request_data.offset}
        """
    prolog.info(cmd)
    info = sob.select_mysql_record(sob_handle, cmd)
    if isinstance(info, list):
        if info:
            total = info[0].get("total", 0)
        else:
            total = 0
    else:
        raise ValueError('error sql')
    for _ in info:
        del _["total"]
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "info": info
    }


def _create_door_idno(request_data: CreateFilterFormat):
    sob_handle = sob.sql_open(db_config)
    if request_data.idno:
        cmd = f"select * from wxapp_door_cards where type=1 and cardid='{request_data.idno}' and mini_id={request_data.mini_id}"
        info = sob.select_mysql_record(sob_handle,cmd)
        if not info:
            raise ValueError('无效IC卡')
        if request_data.id:
            cmd = f"select * from wxapp_door_idno where id={request_data.id}"
            info = sob.select_mysql_record(sob_handle,cmd)
            if request_data.idno != info[0]['idno']:
                cmd = f"select * from wxapp_door_idno where idno='{request_data.idno}' and mini_id={request_data.mini_id}"
                info = sob.select_mysql_record(sob_handle,cmd)
                if info:
                    raise ValueError('门禁卡ID已被绑定')
        else:
            cmd = f"select * from wxapp_door_idno where idno='{request_data.idno}' and mini_id={request_data.mini_id}"
            info = sob.select_mysql_record(sob_handle, cmd)
            if info:
                raise ValueError('门禁卡ID已被绑定')
    if request_data.rfid:
        cmd = f"select * from wxapp_door_cards where type=2 and cardid='{request_data.rfid}' and mini_id={request_data.mini_id}"
        info = sob.select_mysql_record(sob_handle,cmd)
        if not info:
            raise ValueError('无效FRID卡')
        if request_data.id:
            cmd = f"select * from wxapp_door_idno where id={request_data.id}"
            info = sob.select_mysql_record(sob_handle, cmd)
            if request_data.rfid != info[0]['rfid']:
                cmd = f"select * from wxapp_door_idno where rfid='{request_data.rfid}' and mini_id={request_data.mini_id}"
                info = sob.select_mysql_record(sob_handle, cmd)
                if info:
                    raise ValueError('FRID卡已被绑定')
        else:
            cmd = f"select * from wxapp_door_idno where rfid='{request_data.rfid}' and mini_id={request_data.mini_id}"
            info = sob.select_mysql_record(sob_handle, cmd)
            if info:
                raise ValueError('FRID卡已被绑定')
    request_dict = request_data.dict()
    request_dict.update({"add_time": timer.get_now(), "update_time": timer.get_now()})
    hope_lst = list(request_dict.keys())
    hope_lst.remove('add_time')
    sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_door_idno', [request_dict], hope_lst)
    sob.sql_close(sob_handle)
    return




def _delete_door_idno(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_door_idno where id={request_data.id}"
    flag = sob.delete_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【获取用户门禁卡】
def get_door_idno(request_data: QueryFilterFormat):
    try:
        res = _get_door_idno(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【创建修改用户门禁卡】
def create_door_idno(request_data: CreateFilterFormat):
    try:
        res = _create_door_idno(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【删除用户门禁卡】
def delete_door_idno(request_data: DeleteFilterFormat):
    try:
        res = _delete_door_idno(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

