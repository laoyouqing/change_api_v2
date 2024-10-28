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
    packageorder_id: int = Field(None, description="订单id")
    id: int = Field(None, description="id (mini_id,id二选一)")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    packageorder_id = request_data['packageorder_id']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if packageorder_id:
        where_lst.append(f"packageorder_id={packageorder_id}")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _recharge_package_order_renew_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*,
               nickname,avatar,plan_name,note_name,address
               count(*) over() as total
            from
               wxapp_recharge_package_order_renew a
            left join wxapp_user b
            on a.user_id=b.id
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
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "info": info
    }



#【充电包续费详情】
def recharge_package_order_renew_list(request_data: QueryFilterFormat):
    try:
        res = _recharge_package_order_renew_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



class RefundsFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    order_id: int = Field(..., description="订单id")


def _package_renew_refunds(request_data: RefundsFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_recharge_package_order_renew where id={request_data.order_id}"
    renew_package_order = sob.select_mysql_record(sob_handle,cmd)
    renew_package_order = renew_package_order[0]
    invalid_dealer_order(renew_package_order)
    if renew_package_order['pay_type'] == 20:
        cmd = f"select * from wxapp_payinfo where mini_id={request_data.mini_id}"
        payinfo = sob.select_mysql_record(sob_handle, cmd)
        if payinfo:
            payinfo = payinfo[0]
            total_fee = int(renew_package_order['pay_price'] * 100)
            out_refund_no = f"{timer.get_now('%Y%m%d%H%M%S')}{renew_package_order['user_id']}"

            if payinfo['pay_type'] == 2:  # 通联支付
                tl_pay = tl_pay_sdk()
                resp = tl_pay.tl_refunds(payinfo['orgid'], payinfo['mchid'],
                                         payinfo['apikey'],
                                         total_fee, out_refund_no,
                                         renew_package_order['transaction_id'],
                                         payinfo['key_pem'])
                if resp['retcode'] == 'SUCCESS':
                    if resp['trxstatus'] == '0000':
                        cmd = f"update wxapp_recharge_package_order_renew set refund_time='{timer.get_now()}',order_status=40 where id={request_data.order_id}"
                        sob.update_mysql_record(sob_handle, cmd)

                        cmd = f"select * from wxapp_recharge_package_order_renew where id={request_data.order_id}"
                        package_order_renew = sob.select_mysql_record(sob_handle, cmd)
                        package_order_renew = package_order_renew[0]
                        cmd = f"select * from wxapp_recharge_package_order where id='{package_order_renew['packageorder_id']}'"
                        package_order = sob.select_mysql_record(sob_handle, cmd)
                        package_order = package_order[0]
                        value_info = {
                            'mini_id': package_order_renew['mini_id'],
                            'note_id': package_order_renew['note_id'],
                            'type': 1,
                            'user_id': package_order_renew['user_id'],
                            'scene': 40,
                            'money': package_order_renew['pay_price'],
                            'describes': '订单退款(包月套餐退款)',
                            'add_time': timer.get_now()
                        }
                        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                        cmd = f"select * from wxapp_recharge_package where id={package_order['package_id']}"
                        package = sob.select_mysql_record(sob_handle, cmd)
                        package = package[0]
                        residue_time = package_order['residue_time'] - package['recharge_time'] - package['gift_recharge_time']
                        if residue_time > 0:
                            cmd = f"update wxapp_recharge_package_order set residue_time={residue_time},end_time='{package_order_renew['start_time']}',is_use=1,order_status=20 where id={package_order['id']}"
                            sob.update_mysql_record(sob_handle, cmd)
                        else:
                            cmd = f"update wxapp_recharge_package_order set residue_time=0,is_use=0,order_status=20 where id={package_order['id']}"
                            sob.update_mysql_record(sob_handle, cmd)
                    else:
                        raise ValueError('退款失败')
                else:
                    raise ValueError('退款失败')
            else:
                notify_url = f'{REQ_HOST}/api/wx_renew_order_fefunds_payback/{payinfo["orgid"]}'
                wx_pay_sdk().refunds_v3(renew_package_order['transaction_id'], out_refund_no,
                                        total_fee, total_fee, payinfo['mchid'], payinfo['apikey'],payinfo['key_pem'], notify_url)
        else:
            prolog.error('支付信息不完善，退款失败')
    else:
        cmd = f"update wxapp_user set balance=balance+{renew_package_order['pay_price']} where id={renew_package_order['user_id']}"
        sob.update_mysql_record(sob_handle,cmd)
        cmd = f"update wxapp_recharge_package_order_renew set refund_time='{timer.get_now()}',order_status=40 where id={request_data.order_id}"
        sob.update_mysql_record(sob_handle, cmd)

        cmd = f"select * from wxapp_recharge_package_order_renew where id={request_data.order_id}"
        package_order_renew = sob.select_mysql_record(sob_handle, cmd)
        package_order_renew = package_order_renew[0]
        cmd = f"select * from wxapp_recharge_package_order where id='{package_order_renew['packageorder_id']}'"
        package_order = sob.select_mysql_record(sob_handle, cmd)
        package_order = package_order[0]
        value_info = {
            'mini_id': package_order_renew['mini_id'],
            'note_id': package_order_renew['note_id'],
            'type': 1,
            'user_id': package_order_renew['user_id'],
            'scene': 40,
            'money': package_order_renew['pay_price'],
            'describes': '订单退款(包月套餐退款)',
            'add_time': timer.get_now()
        }
        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
        cmd = f"select * from wxapp_recharge_package where id={package_order['package_id']}"
        package = sob.select_mysql_record(sob_handle, cmd)
        package = package[0]
        residue_time = package_order['residue_time'] - package['recharge_time'] - package[
            'gift_recharge_time']
        if residue_time > 0:
            cmd = f"update wxapp_recharge_package_order set residue_time={residue_time},end_time='{package_order_renew['start_time']}',is_use=1,order_status=20 where id={package_order['id']}"
            sob.update_mysql_record(sob_handle, cmd)
        else:
            cmd = f"update wxapp_recharge_package_order set residue_time=0,is_use=0,order_status=20 where id={package_order['id']}"
            sob.update_mysql_record(sob_handle, cmd)
    cmd = f"update wxapp_recharge_package_order set order_status=20 where id={renew_package_order['packageorder_id']}"
    sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return ''


#【充电包续费退款】
def package_renew_refunds(request_data: RefundsFilterFormat):
    try:
        res = _package_renew_refunds(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}