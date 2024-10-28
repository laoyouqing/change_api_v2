from pydantic import BaseModel, Field

from tool.format_data import format_response_data
from tool.wf_mysql import wf_mysql_class
from config import db_config
sob = wf_mysql_class(cursor_type=True)

class QueryFilterFormat(BaseModel):
    level: int = Field(None, description="层级 1省 2市 3 区(县)")
    pid: int = Field(None, description="父id")
    keyword: str = Field(None, description="关键字搜索")


def _generate_where_sql(request_data):
    where_lst = []
    pid = request_data['pid']
    level = request_data['level']
    keyword = request_data['keyword']
    if pid:
        where_lst.append(f"pid={pid}")
    if level:
        where_lst.append(f"level={level}")
    if keyword:
        where_lst.append(f"name like '%{sob.escape(keyword)}%'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_region(request_data: QueryFilterFormat):
    sob_handle = sob.sql_open(db_config)
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    cmd = f"select * from wxapp_region {where_sql}"
    info = sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return info




#【获取地区】
def get_region(request_data: QueryFilterFormat):
    try:
        res = _get_region(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


