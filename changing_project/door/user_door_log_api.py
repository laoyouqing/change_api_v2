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
    user_id: int = Field(None, description="用户id")
    id: int = Field(None, description="门禁信息id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    keyword = request_data['keyword']
    user_id = request_data['user_id']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if user_id:
        where_lst.append(f"a.user_id={user_id}")
    if id:
        where_lst.append(f"a.id={id}")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or note_name like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%' or idno like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _user_door_log(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*,
               nickname,avatar,note_name,mobile,
               count(*) over() as total
            from
               wxapp_user_door_log a
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



#【门禁刷卡记录】
def user_door_log(request_data: QueryFilterFormat):
    try:
        res = _user_door_log(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}