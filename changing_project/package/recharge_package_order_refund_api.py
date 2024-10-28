from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)

class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    note_id: int = Field(None, description="社区id")
    id: int = Field(None, description="id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

def _generate_where_sql(request_data):
    where_lst = ["(order_status=40 or order_status=30)"]
    mini_id = request_data['mini_id']
    id = request_data['id']
    note_id = request_data['note_id']
    keyword = request_data['keyword']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if note_id:
        where_lst.append(f"a.note_id={note_id}")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _recharge_package_order_refund(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*,
               nickname,avatar,a.plan_name,mobile,
               count(*) over() as total
            from
               wxapp_recharge_package_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_recharge_package c
            on a.package_id=c.id
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



#【套餐包退款记录】
def recharge_package_order_refund(request_data: QueryFilterFormat):
    try:
        res = _recharge_package_order_refund(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}