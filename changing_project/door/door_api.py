from pydantic import BaseModel, Field

from config import db_config, UDP_PORT
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.udpc import Client
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()



class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    note_id: int = Field(None, description="社区id")
    id: int = Field(None, description="门禁信息id (mini_id,id二选一)")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

class CreateFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    id: int = Field(None, description="id")
    note_id: int = Field(None, description="社区id")
    title: str = Field(None, description="标题")
    serialnum: str = Field(None, description="设备序列号")
    doorindex: str = Field(..., description="门号(01,02,03,04)")
    readhead_num: int = Field(..., description="读头数（1单读头 2双读头")
    status: int = Field(..., description="状态(0离线 1在线)")
    lastip: str = Field(..., description="最后上线IP")


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="门禁信息id")


def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    note_id = request_data['note_id']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if note_id:
        where_lst.append(f"note_id={note_id}")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_pod_door(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              *, count(*) over() as total
            from
               wxapp_pod_door
            {where_sql}
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


def _create_pod_door(request_data: CreateFilterFormat):
    sob_handle = sob.sql_open(db_config)
    request_dict = request_data.dict()
    request_dict.update({"add_time": timer.get_now(),"update_time": timer.get_now()})
    hope_lst = list(request_dict.keys())
    hope_lst.remove('add_time')
    flag = sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_pod_door',[request_dict],hope_lst)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return

def _delete_pod_door(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_pod_door where id={request_data.id}"
    flag = sob.delete_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【获取门禁信息】
def get_pod_door(request_data: QueryFilterFormat):
    try:
        res = _get_pod_door(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【创建修改门禁信息】
def create_pod_door(request_data: CreateFilterFormat):
    try:
        res = _create_pod_door(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【删除门禁信息】
def delete_pod_door(request_data: DeleteFilterFormat):
    try:
        res = _delete_pod_door(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class FilterFormat(BaseModel):
    data: str = Field(..., description="请求数据")

def _mini_udp_req(request_data: FilterFormat):
    client = Client(request_data.data, UDP_PORT)
    try:
        client.start()
        resp = client.recv_msg()
        return resp
    except:
        client.udp_socket.close()
        raise ValueError('请求失败')


# 【udp操作请求】
def mini_udp_req(request_data: FilterFormat):
    try:
        res = _mini_udp_req(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}