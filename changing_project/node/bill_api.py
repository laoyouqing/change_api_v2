from datetime import date

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
    id: int = Field(None, description="社区计费id (mini_id,id二选一)")
    note_id: int = Field(None, description="社区id")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")


class CreateFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    id: int = Field(None, description="id")
    note_id: int = Field(..., description="社区id")
    total_price: float = Field(0, description="总金额")
    price: float = Field(0, description="单价")
    title: str = Field(..., description="标题描述(0.5元/2小时)")
    billtype: int = Field(..., description="计费方式(0默认,1按小时计费,2充满自停,3分档计费)")
    is_ceil: int = Field(0, description="充满自停计费模式(0默认按分钟,1按小时(向上取整))")
    step: int = Field(1, description="步长/小时")
    duration: int = Field(0, description="时长")
    sort: int = Field(..., description="排序")


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="社区计费id")


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


def _get_bill(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              *, count(*) over() as total
            from
               wxapp_bill
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


def _create_bill(request_data: CreateFilterFormat):
    request_dict = request_data.dict()
    request_dict.update({"add_time":timer.get_now(),"update_time":timer.get_now()})
    hope_lst = list(request_dict.keys())
    hope_lst.remove('add_time')
    sob_handle = sob.sql_open(db_config)
    flag = sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_bill',[request_dict],hope_lst)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return

def _delete_bill(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_bill where id={request_data.id}"
    flag = sob.delete_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【获取社区计费】
def get_bill(request_data: QueryFilterFormat):
    try:
        res = _get_bill(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【创建修改社区计费】
def create_bill(request_data: CreateFilterFormat):
    try:
        res = _create_bill(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【删除社区计费】
def delete_bill(request_data: DeleteFilterFormat):
    try:
        res = _delete_bill(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


