from pydantic import BaseModel, Field

from config import db_config, REQ_HOST
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import tl_pay_sdk, wx_pay_sdk

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()
class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    id: int = Field(None, description="id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    keyword = request_data['keyword']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _recharge_order_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*,
               nickname,avatar,plan_name,mobile,
               count(*) over() as total
            from
               wxapp_recharge_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_recharge_plan c
            on a.plan_id=c.id
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



#【余额充值记录】
def recharge_order_list(request_data: QueryFilterFormat):
    try:
        res = _recharge_order_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class RefundFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    money: float = Field(None, description="退款金额")
    order_id: str = Field(None, description="订单id")


def _recharge_order_fefund(request_data: RefundFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_recharge_order where id={request_data.order_id}"
    recharge_order = sob.select_mysql_record(sob_handle,cmd)
    recharge_order = recharge_order[0]
    if recharge_order['is_represent'] == 1:
        user_id = recharge_order['rechargeuser_id']
    else:
        user_id = recharge_order['user_id']
    money = request_data.money
    print(money)
    cmd = f"select * from wxapp_user where id={user_id}"
    user = sob.select_mysql_record(sob_handle,cmd)
    user = user[0]
    if user['balance'] < money:
        raise ValueError('退款金额超过钱包余额')
    if recharge_order['pay_price'] < money:
        raise ValueError('退款金额超过订单支付金额')
    cmd = f"select * from wxapp_payinfo where mini_id={request_data.mini_id}"
    payinfo = sob.select_mysql_record(sob_handle, cmd)
    if payinfo:
        payinfo = payinfo[0]
        out_refund_no = f"{timer.get_now('%Y%m%d%H%M%S')}{user['id']}"
        pay_price = int(recharge_order['pay_price'] * 100)
        total_fee = int(money * 100)
        if payinfo['pay_type'] == 2:  # 通联支付
            tl_pay = tl_pay_sdk()
            resp = tl_pay.tl_refunds(payinfo['orgid'], payinfo['mchid'],
                                     payinfo['apikey'],
                                     total_fee, out_refund_no,
                                     recharge_order['transaction_id'],
                                     payinfo['key_pem'])
            if resp['retcode'] == 'SUCCESS':
                if resp['trxstatus'] == '0000':
                    trxid = resp['trxid']  # 收银宝交易单号
                    cmd = f"update wxapp_recharge_order set refund_money={money},is_refund=1,refund_id='{trxid}',refund_time='{timer.get_now()}' where id={recharge_order['id']}"
                    sob.update_mysql_record(sob_handle, cmd)
                    value_info = {
                        'mini_id': recharge_order['mini_id'],
                        'type': 1,
                        'user_id': recharge_order['user_id'],
                        'scene': 40,
                        'money': money,
                        'describes': '余额退款',
                        'add_time': timer.get_now()
                    }
                    sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',
                                                               [value_info])
                    cmd = f"update wxapp_user set balance=balance-{money} where id={user_id}"
                    sob.update_mysql_record(sob_handle,cmd)
                else:
                    cmd = f"update wxapp_recharge_order set pay_status=40 where id={recharge_order['id']}"
                    sob.update_mysql_record(sob_handle, cmd)
            else:
                cmd = f"update wxapp_recharge_order set pay_status=40,refund_money={money} where id={recharge_order['id']}"
                sob.update_mysql_record(sob_handle, cmd)
        else:
            notify_url = f'{REQ_HOST}/api/wx_recharge_fefunds_payback/{payinfo["orgid"]}'
            print(notify_url)
            wx_pay_sdk().refunds_v3(recharge_order['transaction_id'], out_refund_no,
                                    total_fee, pay_price, payinfo['mchid'], payinfo['apikey'],payinfo['key_pem'], notify_url)
            cmd = f"update wxapp_recharge_order set refund_money={money} where id={recharge_order['id']}"
            sob.update_mysql_record(sob_handle, cmd)
    else:
        prolog.error('支付信息不完善，退款失败')
        raise ValueError('支付信息不完善，退款失败')
    sob.sql_close(sob_handle)
    return



#【钱包充值套餐退款】
def recharge_order_fefund(request_data: RefundFilterFormat):
    try:
        res = _recharge_order_fefund(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="钱包充值套餐id")

def _delete_recharge_order(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_recharge_order where id={request_data.id}"
    flag = sob.delete_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【删除充值记录】
def delete_recharge_order(request_data: DeleteFilterFormat):
    try:
        res = _delete_recharge_order(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}