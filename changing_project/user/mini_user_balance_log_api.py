from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.wf_mysql import wf_mysql_class

sob = wf_mysql_class(cursor_type=True)

class LogFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    scene: int = Field(..., description="10用户充值 20用户消费")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")


def _user_balance_log(request_data: LogFilterFormat):
    sob_handle = sob.sql_open(db_config)
    if request_data.scene == 10:
        cmd = f"select *,count(*) over() as total from wxapp_user_balance_log where (user_id={request_data.user_id} or rechargeuser_id={request_data.user_id}) and scene=10 order by add_time desc limit {request_data.size} offset {request_data.offset}"
    else:
        cmd = f"select *,count(*) over() as total from wxapp_user_balance_log where user_id={request_data.user_id} and scene!=10 order by add_time desc limit {request_data.size} offset {request_data.offset}"
    logs = sob.select_mysql_record(sob_handle,cmd)
    if isinstance(logs, list):
        if logs:
            total = logs[0].get("total", 0)
        else:
            total = 0
    else:
        raise ValueError('error sql')
    for _ in logs:
        del _["total"]
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "logs": logs
    }




#【小程序-充值/消费记录】
def user_balance_log(request_data: LogFilterFormat):
    try:
        res = _user_balance_log(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


