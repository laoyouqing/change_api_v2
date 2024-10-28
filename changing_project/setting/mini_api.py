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
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")





def _get_mini(request_data: QueryFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              *, count(*) over() as total
            from
               wxapp_mini
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





#【获取小程序列表】
def get_mini(request_data: QueryFilterFormat):
    try:
        res = _get_mini(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

