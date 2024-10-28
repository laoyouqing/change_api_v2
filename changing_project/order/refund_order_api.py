from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()

class ListFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    refund_type: int = Field(None, description="10手动退款 20自动退款")
    note_refund: int = Field(None, description="1：退全款 2：开启社区充电不足退款")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")


def _refund_orders_list(request_data: ListFilterFormat):
    sob_handle = sob.sql_open(db_config)
    refund_type = request_data.refund_type
    note_refund = request_data.note_refund
    if refund_type == 10:
        cmd = f"select *, count(*) over() as total from wxapp_order where mini_id={request_data.mini_id} and refund_type=1 and pay_status=30 order by add_time desc limit {request_data.size} offset {request_data.offset}"
    else:
        if note_refund == 1:
            cmd = f"select *, count(*) over() as total from wxapp_order where mini_id={request_data.mini_id} and refund_type!=1 and pay_status=30 order by add_time desc limit {request_data.size} offset {request_data.offset}"
        else:
            cmd = f"select *, count(*) over() as total from wxapp_order where mini_id={request_data.mini_id} and refund_type!=1 and total_price>pay_price and pay_status=20 and residue_money!=0 order by add_time desc limit {request_data.size} offset {request_data.offset}"
    orders = sob.select_mysql_record(sob_handle,cmd)
    if isinstance(orders, list):
        if orders:
            total = orders[0].get("total", 0)
        else:
            total = 0
    else:
        raise ValueError('error sql')
    for order in orders:
        del order["total"]
        cmd = f"select nickname,avatar,mobile from wxapp_user where id={order['user_id']}"
        user = sob.select_mysql_record(sob_handle,cmd)
        cmd = f"select note_name from wxapp_note where id={order['note_id']}"
        note = sob.select_mysql_record(sob_handle,cmd)
        order['user'] = user[0]
        order['note'] = note[0]
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "orders": orders
    }


# 【退款订单列表】
def refund_orders_list(request_data: ListFilterFormat):
    try:
        res = _refund_orders_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}