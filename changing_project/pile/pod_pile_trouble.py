from typing import List

from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)



class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")



class UpdateFilterFormat(BaseModel):
    id: List = Field(None, description="充电桩端口id列表")



def _generate_where_sql(request_data):
    where_lst = ["trouble_status=1"]
    mini_id = request_data['mini_id']

    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_pile_trouble(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              a.*, 
              note_name,
              snum,
              count(*) over() as total
            from
               wxapp_pod_pileport a
            left join wxapp_pod_pile b
            on a.pile_id=b.id
            left join wxapp_note c
            on a.note_id=c.id
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



#【故障处理列表】
def get_pile_trouble(request_data: QueryFilterFormat):
    try:
        res = _get_pile_trouble(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


def _update_pile_trouble(request_data: UpdateFilterFormat):
    sob_handle = sob.sql_open(db_config)
    for id in request_data.id:
        cmd = f"update wxapp_pod_pileport set trouble_status=0 where id={id}"
        sob.update_mysql_record(sob_handle,cmd)
    return


#【故障恢复】
def update_pile_trouble(request_data: UpdateFilterFormat):
    try:
        res = _update_pile_trouble(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}
