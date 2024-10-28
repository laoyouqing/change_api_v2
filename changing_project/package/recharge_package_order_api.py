from datetime import datetime

from pydantic import BaseModel, Field

from config import db_config, REQ_HOST
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.normal_func import invalid_dealer_order
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import tl_pay_sdk, wx_pay_sdk

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()
class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    note_id: int = Field(None, description="社区id")
    user_id: int = Field(None, description="用户id")
    package_id: int = Field(None, description="套餐包id")
    id: int = Field(None, description="id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")
    pay_time :datetime = Field(None,description='付款时间')

def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    user_id = request_data['user_id']
    id = request_data['id']
    note_id = request_data['note_id']
    package_id = request_data['package_id']
    keyword = request_data['keyword']
    pay_time = request_data['pay_time']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if id:
        where_lst.append(f"a.id={id}")
    if note_id:
        where_lst.append(f"a.note_id={note_id}")
    if user_id:
        where_lst.append(f"a.user_id={user_id}")
    if package_id:
        where_lst.append(f"a.package_id={package_id}")
    if pay_time:
        where_lst.append(f"DATE(a.pay_time)='{pay_time}'")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _recharge_package_order_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*,
               nickname,avatar,a.plan_name,note_name,address,mobile,
               c.type,
               count(*) over() as total
            from
               wxapp_recharge_package_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_recharge_package c
            on a.package_id=c.id
            left join wxapp_note d
            on a.note_id=d.id
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
        cmd = f"select * from wxapp_recharge_package_order_refund where order_id={_['id']} and order_status!=50"
        refund = sob.select_mysql_record(sob_handle,cmd)
        _['refund'] = refund
        cmd = f"select * from wxapp_recharge_package_order_renew where packageorder_id={_['id']}"
        renew = sob.select_mysql_record(sob_handle,cmd)
        _['renew'] = renew
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "info": info
    }



#【充电包充值记录】
def recharge_package_order_list(request_data: QueryFilterFormat):
    try:
        res = _recharge_package_order_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class RefundFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    order_id: int = Field(..., description="订单id")
    user_id: int = Field(..., description="用户id")
    apply_desc: str = Field(None, description="申请原因")


def _package_refunds_apply(request_data: RefundFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"update wxapp_recharge_package_order set order_status=30,is_use=0 where id={request_data.order_id}"
    sob.update_mysql_record(sob_handle,cmd)
    out_refund_no = f"{timer.get_now(format='%Y%m%d%H%M%S')}{request_data.user_id}"
    value_info = {
        'id':out_refund_no,
        'mini_id':request_data.mini_id,
        'order_id':request_data.order_id,
        'user_id':request_data.user_id,
        'apply_desc':request_data.apply_desc,
        'add_time':timer.get_now()
    }
    sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_recharge_package_order_refund',[value_info])
    sob.sql_close(sob_handle)
    return ''



#【充电包退款申请】
def package_refunds_apply(request_data: RefundFilterFormat):
    try:
        res = _package_refunds_apply(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

class CancalRefundFilterFormat(BaseModel):
    order_id: int = Field(..., description="订单id")


def _cancal_package_refunds_apply(request_data: CancalRefundFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"update wxapp_recharge_package_order set order_status=20,is_use=1 where id={request_data.order_id}"
    sob.update_mysql_record(sob_handle,cmd)
    cmd = f"update wxapp_recharge_package_order_refund set order_status=50 where order_id={request_data.order_id}"
    sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return


#【充电包取消退款申请】
def cancal_package_refunds_apply(request_data: CancalRefundFilterFormat):
    try:
        res = _cancal_package_refunds_apply(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class RefundsFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    refund_id: str = Field(..., description="退款id")
    is_agree: int = Field(..., description="商家审核状态(0待审核 10已同意 20已拒绝)")
    refuse_desc: str = Field(None, description="商家拒绝原因")


def _package_refunds(request_data: RefundsFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_recharge_package_order_refund where id='{request_data.refund_id}'"
    order_refund = sob.select_mysql_record(sob_handle,cmd)
    order_refund = order_refund[0]
    is_agree = request_data.is_agree
    if is_agree == 20:
        cmd = f"update wxapp_recharge_package_order set order_status=20,is_use=1 where id={order_refund['order_id']}"
        sob.update_mysql_record(sob_handle,cmd)
    else:
        cmd = f"select * from wxapp_recharge_package_order where id={order_refund['order_id']}"
        package_order = sob.select_mysql_record(sob_handle,cmd)
        package_order = package_order[0]
        invalid_dealer_order(package_order)
        if package_order['pay_type'] == 20:
            cmd = f"select * from wxapp_payinfo where mini_id={request_data.mini_id}"
            payinfo = sob.select_mysql_record(sob_handle, cmd)
            if payinfo:
                payinfo = payinfo[0]
                total_fee = int(package_order['pay_price'] * 100)
                if payinfo['pay_type'] == 2:  # 通联支付
                    tl_pay = tl_pay_sdk()
                    resp = tl_pay.tl_refunds(payinfo['orgid'], payinfo['mchid'],
                                             payinfo['apikey'],
                                             total_fee, request_data.refund_id,
                                             package_order['transaction_id'],
                                             payinfo['key_pem'])
                    if resp['retcode'] == 'SUCCESS':
                        if resp['trxstatus'] == '0000':
                            trxid = resp['trxid']  # 收银宝交易单号
                            cmd = f"update wxapp_recharge_package_order_refund set order_status=20,refund_id='{trxid}' where id='{request_data.refund_id}'"
                            sob.update_mysql_record(sob_handle, cmd)
                            cmd = f"update wxapp_recharge_package_order set residue_time=0,refund_time='{timer.get_now()}',order_status=40 where id={order_refund['order_id']}"
                            sob.update_mysql_record(sob_handle, cmd)
                            value_info = {
                                'mini_id': package_order['mini_id'],
                                'type': 1,
                                'user_id': package_order['user_id'],
                                'scene': 40,
                                'money': package_order['pay_price'],
                                'describes': '订单退款(包月套餐退款)',
                                'add_time': timer.get_now()
                            }
                            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',
                                                                       [value_info])
                        else:
                            cmd = f"update wxapp_recharge_package_order set order_status=20,is_use=1 where id={package_order['id']}"
                            sob.update_mysql_record(sob_handle, cmd)
                            cmd = f"update wxapp_recharge_package_order_refund set order_status=50 where id='{request_data.refund_id}'"
                            sob.update_mysql_record(sob_handle, cmd)
                    else:
                        cmd = f"update wxapp_recharge_package_order set order_status=20,is_use=1 where id={package_order['id']}"
                        sob.update_mysql_record(sob_handle, cmd)
                        cmd = f"update wxapp_recharge_package_order_refund set order_status=50 where id='{request_data.refund_id}'"
                        sob.update_mysql_record(sob_handle, cmd)
                else:
                    notify_url = f'{REQ_HOST}/api/wx_package_order_fefunds_payback/{payinfo["orgid"]}'
                    wx_pay_sdk().refunds_v3(package_order['transaction_id'], request_data.refund_id,
                                            total_fee, total_fee, payinfo['mchid'], payinfo['apikey'],payinfo['key_pem'], notify_url)
            else:
                prolog.error('支付信息不完善，退款失败')
        else:
            cmd = f"update wxapp_recharge_package_order_refund set order_status=20,user_received_account='退回用户余额' where id='{request_data.refund_id}'"
            sob.update_mysql_record(sob_handle, cmd)
            cmd = f"update wxapp_recharge_package_order set residue_time=0,refund_time='{timer.get_now()}',order_status=40 where id={order_refund['order_id']}"
            sob.update_mysql_record(sob_handle, cmd)
            value_info = {
                'mini_id': package_order['mini_id'],
                'type': 1,
                'user_id': package_order['user_id'],
                'scene': 40,
                'money': package_order['pay_price'],
                'describes': '订单退款(包月套餐退款)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',[value_info])
            cmd = f"update wxapp_user set balance=balance+{package_order['pay_price']} where id={package_order['user_id']}"
            sob.update_mysql_record(sob_handle,cmd)
    cmd = f"update wxapp_recharge_package_order_refund set is_agree={is_agree},refuse_desc='{request_data.refuse_desc}' where id='{request_data.refund_id}'"
    sob.update_mysql_record(sob_handle,cmd)
    return ''


#【充电包退款】
def package_refunds(request_data: RefundsFilterFormat):
    try:
        res = _package_refunds(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



class VirtualFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    package_id: int = Field(..., description="充电包id")
    user_id: int = Field(..., description="用户id")
    note_id: str = Field(None, description="社区id")


def _virtual_user_rechage_buy(request_data: VirtualFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_recharge_package where id={request_data.package_id}"
    recharge_package = sob.select_mysql_record(sob_handle,cmd)
    recharge_package = recharge_package[0]
    order_id = f"{timer.get_now(format='%Y%m%d%H%M%S')}{request_data.user_id}"
    money = recharge_package['money']
    days = recharge_package['days']
    recharge_time = recharge_package['recharge_time']
    gift_recharge_time = recharge_package['gift_recharge_time']
    recharge_time = recharge_time + gift_recharge_time
    start_time = timer.get_now()
    end_time = timer.get_now_bef_aft(days=-days)
    value_info = {
        'order_id': order_id,
        'mini_id': request_data.mini_id,
        'note_id': recharge_package['note_id'],
        'package_id': request_data.package_id,
        'pay_type': 40,
        'pay_price': money,
        'type': recharge_package['type'],
        'plan_name': recharge_package['plan_name'],
        'recharge_time': recharge_time,
        'residue_time': recharge_time,
        'start_time': start_time,
        'end_time': end_time,
        'add_time':timer.get_now()
    }
    sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_recharge_package_order',[value_info])
    sob.sql_close(sob_handle)
    return ''





#【充电包后台虚拟用户购买】
def virtual_user_rechage_buy(request_data: VirtualFilterFormat):
    try:
        res = _virtual_user_rechage_buy(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}