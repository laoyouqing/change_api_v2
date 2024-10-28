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
    id: int = Field(None, description="社区电表数据id (mini_id,id二选一)")
    note_id: int = Field(None, description="社区id")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")


class CreateFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    id: int = Field(None, description="id")
    note_id: int = Field(..., description="社区id")
    ammeter_name: str = Field(..., description="电表名称")
    end_number: float = Field(..., description="最后读数")
    number: float = Field(..., description="上报读数")
    image: str = Field(..., description="图片")
    date_time: str = Field(..., description="时间")


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="社区电表数据id")


def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    note_id = request_data['note_id']
    keyword = request_data['keyword']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if note_id:
        where_lst.append(f"note_id={note_id}")
    if keyword:
        where_lst.append(f"ammeter_name like '%{sob.escape(keyword)}%'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_note_elecdata(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              *, count(*) over() as total
            from
               wxapp_note_elecdata
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


def _create_note_elecdata(request_data: CreateFilterFormat):
    request_dict = request_data.dict()
    request_dict.update({"add_time":timer.get_now(),"update_time":timer.get_now()})
    hope_lst = list(request_dict.keys())
    hope_lst.remove('add_time')
    sob_handle = sob.sql_open(db_config)
    print(request_dict)
    print(hope_lst)
    flag = sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_note_elecdata',[request_dict],hope_lst)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return

def _delete_note_elecdata(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_note_elecdata where id={request_data.id}"
    flag = sob.delete_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【获取社区电表数据】
def get_note_elecdata(request_data: QueryFilterFormat):
    try:
        res = _get_note_elecdata(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【创建修改社区电表数据】
def create_note_elecdata(request_data: CreateFilterFormat):
    try:
        res = _create_note_elecdata(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【删除社区电表数据】
def delete_note_elecdata(request_data: DeleteFilterFormat):
    try:
        res = _delete_note_elecdata(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


