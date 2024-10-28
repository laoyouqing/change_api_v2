import json

from fastapi import Body
from pydantic import BaseModel, Field

from config import db_config, REQ_HOST
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.normal_func import next_month, get_settings, calc_proportion_money, split_test
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import tl_pay_sdk, wx_pay_sdk

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()

class QueryFilterFormat(BaseModel):
    user_id: int = Field(None, description="用户id")
    note_id: int = Field(None, description="社区id")



def _get_note_recharge_package(request_data: QueryFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select a.id,plan_name,a.money,days,note_name,address,gift_recharge_time,CURRENT_TIMESTAMP as start_time,DATE_ADD(NOW(), INTERVAL days DAY) as end_time from wxapp_recharge_package a
            left join wxapp_note b on a.note_id=b.id
            where note_id={request_data.note_id}
        """
    recharge_package = sob.select_mysql_record(sob_handle,cmd)
    cmd = f"select balance from wxapp_user where id={request_data.user_id}"
    user = sob.select_mysql_record(sob_handle,cmd)
    balance = user[0]['balance']
    return {'recharge_package':recharge_package,'balance':balance}




#【小程序获取社区充电套餐包】
def get_note_recharge_package(request_data: QueryFilterFormat):
    try:
        res = _get_note_recharge_package(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class PackageBuyFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    package_id: int = Field(..., description="套餐包id")
    mini_id: int = Field(..., description="小程序id")
    is_effect: int = Field(..., description="是否立即生效(0否(次月) 1是)")
    is_auto_renew: int = Field(..., description="是否自动续费(0否 1是)")
    pay_type: int = Field(..., description="支付方式(10余额支付 20微信支付)")
    rechargeuser_id: int = Field(None, description="代他充值（被充值用户id）")

def _recharge_package_buy(request_data: PackageBuyFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_recharge_package where id={request_data.package_id}"
    recharge_package = sob.select_mysql_record(sob_handle,cmd)
    recharge_package = recharge_package[0]
    days = recharge_package['days']
    money = recharge_package['money']
    recharge_time = recharge_package['recharge_time']
    gift_recharge_time = recharge_package['gift_recharge_time']
    recharge_time = recharge_time + gift_recharge_time
    if request_data.is_effect == 1:
        start_time = str(timer.get_now())
        end_time = timer.get_now_bef_aft(days=-days)
    else:
        start_time = str(next_month())
        end_time = timer.get_now_bef_aft(now=start_time,days=-days)

    cmd = f"select * from wxapp_note where id={recharge_package['note_id']}"
    notes = sob.select_mysql_record(sob_handle, cmd)
    note = notes[0]
    if note['is_ind_dealer'] == 1:  # 开启单独分成
        first_proportion = note['first_proportion']
        second_proportion = note['second_proportion']
    else:
        values_json = get_settings(recharge_package['mini_id'], 'settlement')
        first_proportion = int(values_json.get('first_proportion',0))  # 一级分成比例
        second_proportion = int(values_json.get('second_proportion',0))  # 二级分成比例

    first_proportion_money = money * (first_proportion / 100)  # 一级（代理商）分成
    second_proportion_money = money * (second_proportion / 100)  # 二级（物业）分成
    order_id = f"{timer.get_now(format='%Y%m%d%H%M%S')}{request_data.user_id}"
    print('order_id',order_id)
    value_info = {
        'order_id':order_id,
        'mini_id':request_data.mini_id,
        'note_id':recharge_package['note_id'],
        'package_id':request_data.package_id,
        'pay_type':request_data.pay_type,
        'pay_price': money,
        'type': recharge_package['type'],
        'plan_name': recharge_package['plan_name'],
        'recharge_time': recharge_time,
        'residue_time': recharge_time,
        'is_effect': request_data.is_effect,
        'is_auto_renew': request_data.is_auto_renew,
        'start_time':start_time,
        'end_time':end_time,
        'first_proportion_money':first_proportion_money,
        'second_proportion_money':second_proportion_money,
        'add_time':timer.get_now()
    }
    print(value_info)
    user_id = request_data.user_id
    rechargeuser_id = request_data.rechargeuser_id
    if rechargeuser_id:  # 代他人充值(被充值用户)
        value_info.update({'user_id':rechargeuser_id,'rechargeuser_id':user_id})
    else:
        value_info.update({'user_id':user_id})
    lastrowid = sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_recharge_package_order',[value_info])
    cmd = f"select * from wxapp_user where id={request_data.user_id}"
    user = sob.select_mysql_record(sob_handle, cmd)
    user = user[0]
    if request_data.pay_type == 10:
        if user['balance'] < money:
            raise ValueError('账户余额不足')
        else:
            cmd = f"update wxapp_user set balance=balance-{money} where id={request_data.user_id}"
            sob.update_mysql_record(sob_handle,cmd)
        cmd = f"update wxapp_recharge_package_order set is_use=1,pay_status=20,order_status=20,pay_time='{timer.get_now()}' where id={lastrowid}"
        sob.update_mysql_record(sob_handle,cmd)
        value_info = {
            'mini_id': request_data.mini_id,
            'note_id': recharge_package['note_id'],
            'type': 1,
            'user_id': request_data.user_id,
            'scene': 21,
            'money': money,
            'describes': '套餐购买(钱包扣款)',
            'add_time': timer.get_now()
        }
        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
        cmd = f"update wxapp_order set pay_status=20,pay_price=0 where note_id={recharge_package['note_id']} and user_id={request_data.user_id} and pay_status=10"
        sob.update_mysql_record(sob_handle,cmd)
        calc_proportion_money(second_proportion_money, first_proportion_money, recharge_package['note_id'], request_data.mini_id, lastrowid, money)
        sob.sql_close(sob_handle)
        return {'msg': '支付成功', 'status': 200}
    else:
        total_money = int(money * 100)
        cmd = f"select * from wxapp_payinfo where mini_id={request_data.mini_id}"
        payinfo = sob.select_mysql_record(sob_handle, cmd)
        if payinfo:
            payinfo = payinfo[0]
            if payinfo['pay_type'] == 2:  # 通联支付
                notify_url = f'{REQ_HOST}/api/tl_recharge_package_payback'
                print(notify_url)
                tl_pay = tl_pay_sdk()
                resp = tl_pay.tl_mini_pay(payinfo['apikey'], payinfo['orgid'], payinfo['mchid'],
                                          order_id, total_money, notify_url,
                                          payinfo['key_pem'])
                sob.sql_close(sob_handle)
                return {'data': resp, 'status': 200}
            else:
                cmd = f"select * from wxapp_mini where id={request_data.mini_id}"
                wxapp_minis = sob.select_mysql_record(sob_handle, cmd)
                sob.sql_close(sob_handle)
                wxapp_mini = wxapp_minis[0]
                notify_url = f'{REQ_HOST}/api/wx_recharge_package_payback/{payinfo["orgid"]}'
                results, data = wx_pay_sdk().mini_pay(wxapp_mini['authorizer_appid'], payinfo['mchid'],
                                                      order_id, total_money, user['open_id'], notify_url,
                                                      payinfo['apikey'],payinfo['key_pem'])
                if results['xml']['return_code'] == 'SUCCESS':
                    if results['xml']['result_code'] == 'SUCCESS':
                        return {'result_code': results['xml']['result_code'], 'data': data, 'status': 200}
                    else:
                        return_msg = results['xml']['return_msg']
                else:
                    return_msg = results['xml']['return_msg']
                return {'return_msg': return_msg, 'status': 200}
        else:
            raise ValueError('支付信息不完善')



#【小程序充电包立即购买】
def recharge_package_buy(request_data: PackageBuyFilterFormat):
    try:
        res = _recharge_package_buy(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class PackageDueFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")


def _recharge_package_due(request_data: PackageDueFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_recharge_package_order where user_id={request_data.user_id} and order_status=20 and end_time>'{timer.get_now()}' and end_time<'{timer.get_now_bef_aft(days=-3)}'"
    package_order = sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return {'package_order':package_order[0] if package_order else ''}


#【小程序充电包即将到期判断】
def recharge_package_due(request_data: PackageDueFilterFormat):
    try:
        res = _recharge_package_due(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class RenewFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    log_id: int = Field(None, description="门禁欠费订单")
    order_id: int = Field(..., description="续费订单id")
    # pay_type: int = Field(..., description="支付方式(10余额支付 20微信支付)")


def _recharge_package_renew(request_data: RenewFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select b.*,a.end_time,a.user_id,a.start_time from wxapp_recharge_package_order a left join wxapp_recharge_package b on a.package_id=b.id where a.id={request_data.order_id}"
    order = sob.select_mysql_record(sob_handle,cmd)
    order = order[0]
    days = order['days']
    money = order['money']
    recharge_time = order['recharge_time']
    gift_recharge_time = order['gift_recharge_time']
    recharge_time = recharge_time + gift_recharge_time
    end_time = timer.get_now_bef_aft(now=order['end_time'].strftime("%Y-%m-%d %H:%M:%S"),days=-days)
    order_id = f"{timer.get_now(format='%Y%m%d%H%M%S')}{request_data.user_id}"
    cmd = f"select * from wxapp_note where id={order['note_id']}"
    notes = sob.select_mysql_record(sob_handle, cmd)
    note = notes[0]
    if note['is_ind_dealer'] == 1:  # 开启单独分成
        first_proportion = note['first_proportion']
        second_proportion = note['second_proportion']
    else:
        values_json = get_settings(order['mini_id'], 'settlement')
        first_proportion = int(values_json.get('first_proportion',0))  # 一级分成比例
        second_proportion = int(values_json.get('second_proportion',0))  # 二级分成比例

    first_proportion_money = money * (first_proportion / 100)  # 一级（代理商）分成
    second_proportion_money = money * (second_proportion / 100)  # 二级（物业）分成
    total_money = int(money * 100)
    cmd = f"select * from wxapp_user where id={request_data.user_id}"
    user = sob.select_mysql_record(sob_handle, cmd)
    user = user[0]
    if user['balance'] >= money:
        pay_type = 10
    else:
        pay_type = 20
    value_info = {
        'order_id':order_id,
        'mini_id':order['mini_id'],
        'note_id':order['note_id'],
        'user_id':order['user_id'],
        'packageorder_id':request_data.order_id,
        'start_time':str(order['end_time']),
        'end_time':str(end_time),
        'pay_type':pay_type,
        'pay_price':money,
        'first_proportion_money':first_proportion_money,
        'second_proportion_money':second_proportion_money,
        'add_time':timer.get_now(),
        'recharge_time':recharge_time
    }
    lastrowid = sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_recharge_package_order_renew',[value_info])
    if pay_type == 10:
        cmd = f"update wxapp_user set balance=balance-{money} where id={request_data.user_id}"
        sob.update_mysql_record(sob_handle, cmd)
        cmd = f"update wxapp_recharge_package_order_renew set pay_status=20,order_status=20,pay_time='{timer.get_now()}' where id={lastrowid}"
        sob.update_mysql_record(sob_handle, cmd)
        value_info = {
            'mini_id': order['mini_id'],
            'note_id': order['note_id'],
            'type': 1,
            'user_id': request_data.user_id,
            'scene': 21,
            'money': money,
            'describes': '套餐购买(钱包扣款)',
            'add_time': timer.get_now()
        }
        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
        cmd = f"update wxapp_order set pay_status=20,pay_price=0 where note_id={order['note_id']} and user_id={request_data.user_id} and pay_status=10"
        sob.update_mysql_record(sob_handle, cmd)

        cmd = f"update wxapp_recharge_package_order set end_time='{end_time}',recharge_time=recharge_time+{recharge_time},residue_time=residue_time+{recharge_time},is_use=1,is_renew=1 where id={request_data.order_id}"
        sob.update_mysql_record(sob_handle,cmd)

        calc_proportion_money(second_proportion_money, first_proportion_money, order['note_id'],
                              order['mini_id'], lastrowid, money)
        sob.sql_close(sob_handle)

        if request_data.log_id:
            if end_time < timer.get_now():
                cmd = f"update wxapp_user_door_log set due_time='{end_time}' where id='{request_data.log_id}'"
            else:
                cmd = f"update wxapp_user_door_log set is_due=0 where id='{request_data.log_id}'"
            sob.update_mysql_record(sob_handle,cmd)
        sob.sql_close(sob_handle)
        return ''
    else:
        cmd = f"select * from wxapp_payinfo where mini_id={order['mini_id']}"
        payinfo = sob.select_mysql_record(sob_handle, cmd)
        if payinfo:
            payinfo = payinfo[0]
            if payinfo['pay_type'] == 2:  # 通联支付
                notify_url = f'{REQ_HOST}/api/tl_recharge_package_renew_payback/{request_data.log_id}'
                tl_pay = tl_pay_sdk()
                resp = tl_pay.tl_mini_pay(payinfo['apikey'], payinfo['orgid'], payinfo['mchid'],
                                          order_id, total_money, notify_url,
                                          payinfo['key_pem'])
                sob.sql_close(sob_handle)
                return {'data': resp, 'status': 200}
            else:
                cmd = f"select * from wxapp_mini where id={order['mini_id']}"
                wxapp_minis = sob.select_mysql_record(sob_handle, cmd)
                sob.sql_close(sob_handle)
                wxapp_mini = wxapp_minis[0]
                notify_url = f'{REQ_HOST}/api/wx_recharge_package_renew_payback/{payinfo["orgid"]}/{request_data.log_id}'
                results, data = wx_pay_sdk().mini_pay(wxapp_mini['authorizer_appid'], payinfo['mchid'],
                                                      order_id, total_money, user['open_id'], notify_url,
                                                      payinfo['apikey'],payinfo['key_pem'])
                if results['xml']['return_code'] == 'SUCCESS':
                    if results['xml']['result_code'] == 'SUCCESS':
                        return {'result_code': results['xml']['result_code'], 'data': data, 'status': 200}
                    else:
                        return_msg = results['xml']['return_msg']
                else:
                    return_msg = results['xml']['return_msg']
                return {'return_msg': return_msg, 'status': 200}






#【小程序充电包续费】
def recharge_package_renew(request_data: RenewFilterFormat):
    try:
        res = _recharge_package_renew(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【小程序套餐包-微信回调】
def wx_recharge_package_payback(orgid,data=Body(None)):
    try:
        sob_handle = sob.sql_open(db_config)
        re_dict = data
        return_code = re_dict['event_type']
        if return_code == 'TRANSACTION.SUCCESS':
            wx_deve = wx_pay_sdk()
            data = wx_deve.decrypt(re_dict['resource']['nonce'], re_dict['resource']['ciphertext'],
                                   re_dict['resource']['associated_data'],orgid)  # 商户对resource对象进行解密后，得到的资源对象示例
            data = json.loads(data.decode())
            # 拿到这次支付的订单号
            out_trade_no = data['out_trade_no']
            trade_state = data['trade_state']
            transaction_id = data['transaction_id']
            if trade_state == 'SUCCESS':
                cmd = f"update wxapp_recharge_package_order set is_use=1,pay_status=20,order_status=20,pay_time='{timer.get_now()}',transaction_id='{transaction_id}' where order_id='{out_trade_no}'"
                sob.update_mysql_record(sob_handle, cmd)
                cmd = f"select * from wxapp_recharge_package_order where order_id='{out_trade_no}'"
                package_order = sob.select_mysql_record(sob_handle, cmd)
                package_order = package_order[0]
                value_info = {
                    'mini_id': package_order['mini_id'],
                    'note_id': package_order['note_id'],
                    'type': 1,
                    'user_id': package_order['rechargeuser_id'] if package_order['rechargeuser_id'] else package_order['user_id'],
                    'scene': 20,
                    'money': package_order['pay_price'],
                    'describes': '套餐购买(微信扣款)',
                    'add_time': timer.get_now()
                }
                sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                cmd = f"update wxapp_order set pay_status=20,pay_price=0 where note_id={package_order['note_id']} and user_id={package_order['user_id']} and pay_status=10"
                sob.update_mysql_record(sob_handle, cmd)
                calc_proportion_money(package_order['second_proportion_money'], package_order['first_proportion_money'], package_order['note_id'],
                                      package_order['mini_id'], package_order['id'], package_order['pay_price'])
        sob.sql_close(sob_handle)
        return {'code': 'SUCCESS', 'message': '成功'}
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}




#【小程序套餐包-通联回调】
def tl_recharge_package_payback(data=Body(None)):
    try:
        sob_handle = sob.sql_open(db_config)
        data = data.decode('utf-8')
        re_dict = split_test(data)
        trxstatus = re_dict['trxstatus']
        trxid = re_dict['trxid']  # 收银宝交易单号
        cusorderid = re_dict['cusorderid']  # 统一下单对应的reqsn订单号
        if trxstatus == '0000':
            cmd = f"update wxapp_recharge_package_order set is_use=1,pay_status=20,order_status=20,pay_time='{timer.get_now()}',transaction_id='{trxid}' where order_id='{cusorderid}'"
            sob.update_mysql_record(sob_handle, cmd)
            cmd = f"select * from wxapp_recharge_package_order where order_id='{cusorderid}'"
            package_order = sob.select_mysql_record(sob_handle, cmd)
            package_order = package_order[0]
            value_info = {
                'mini_id': package_order['mini_id'],
                'note_id': package_order['note_id'],
                'type': 1,
                'user_id': package_order['rechargeuser_id'] if package_order['rechargeuser_id'] else package_order['user_id'],
                'scene': 20,
                'money': package_order['pay_price'],
                'describes': '套餐购买(微信扣款)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
            cmd = f"update wxapp_order set pay_status=20,pay_price=0 where note_id={package_order['note_id']} and user_id={package_order['user_id']} and pay_status=10"
            sob.update_mysql_record(sob_handle, cmd)
            calc_proportion_money(package_order['second_proportion_money'], package_order['first_proportion_money'],
                                  package_order['note_id'],package_order['mini_id'], package_order['id'], package_order['pay_price'])
        sob.sql_close(sob_handle)
        return 'success'
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}




#【小程序套餐包续费-微信回调】
def wx_recharge_package_renew_payback(orgid,log_id,data=Body(None)):
    # try:
        with open("./cccc.txt", "a+", encoding="utf8") as f:
            f.write(str(data))
            f.write("\n")
            f.write(str(type(data)))
        log_id = ''
        sob_handle = sob.sql_open(db_config)
        print(data)
        re_dict = data
        return_code = re_dict['event_type']
        if return_code == 'TRANSACTION.SUCCESS':
            wx_deve = wx_pay_sdk()
            data = wx_deve.decrypt(re_dict['resource']['nonce'], re_dict['resource']['ciphertext'],
                                   re_dict['resource']['associated_data'],orgid)  # 商户对resource对象进行解密后，得到的资源对象示例
            data = json.loads(data.decode())
            # 拿到这次支付的订单号
            out_trade_no = data['out_trade_no']
            trade_state = data['trade_state']
            transaction_id = data['transaction_id']
            if trade_state == 'SUCCESS':
                cmd = f"update wxapp_recharge_package_order_renew set pay_status=20,order_status=20,pay_time='{timer.get_now()}',transaction_id='{transaction_id}' where order_id='{out_trade_no}'"
                sob.update_mysql_record(sob_handle, cmd)
                cmd = f"select * from wxapp_recharge_package_order_renew where order_id='{out_trade_no}'"
                package_order_renew = sob.select_mysql_record(sob_handle, cmd)
                package_order_renew = package_order_renew[0]
                recharge_time = package_order_renew['recharge_time']
                end_time = package_order_renew['end_time']
                cmd = f"update wxapp_recharge_package_order set end_time='{end_time}',recharge_time=recharge_time+{recharge_time},residue_time=residue_time+{recharge_time},is_use=1,is_renew=1 where id={package_order_renew['packageorder_id']}"
                sob.update_mysql_record(sob_handle,cmd)
                value_info = {
                    'mini_id': package_order_renew['mini_id'],
                    'note_id': package_order_renew['note_id'],
                    'type': 1,
                    'user_id': package_order_renew['user_id'],
                    'scene': 20,
                    'money': package_order_renew['pay_price'],
                    'describes': '套餐购买(微信扣款)',
                    'add_time': timer.get_now()
                }
                sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                cmd = f"update wxapp_order set pay_status=20,pay_price=0 where note_id={package_order_renew['note_id']} and user_id={package_order_renew['user_id']} and pay_status=10"
                sob.update_mysql_record(sob_handle, cmd)
                calc_proportion_money(package_order_renew['second_proportion_money'], package_order_renew['first_proportion_money'], package_order_renew['note_id'],
                                      package_order_renew['mini_id'], package_order_renew['id'], package_order_renew['pay_price'])

                if log_id != None and log_id != 'None':
                    cmd = f"update wxapp_user_door_log set is_due=0 where id='{log_id}'"
                    sob.update_mysql_record(sob_handle, cmd)
            sob.sql_close(sob_handle)
        return {'code': 'SUCCESS', 'message': '成功'}
    # except Exception as exc:
    #     return {"status": 400, "msg": exc.__str__()}



#【小程序套餐包续费-通联回调】
def tl_recharge_package_renew_payback(data=Body(None)):
    try:
        log_id = ''
        sob_handle = sob.sql_open(db_config)
        print(data)
        data = data.decode('utf-8')
        re_dict = split_test(data)
        trxstatus = re_dict['trxstatus']
        trxid = re_dict['trxid']  # 收银宝交易单号
        cusorderid = re_dict['cusorderid']  # 统一下单对应的reqsn订单号
        if trxstatus == '0000':
            cmd = f"update wxapp_recharge_package_order_renew set pay_status=20,order_status=20,pay_time='{timer.get_now()}',transaction_id='{trxid}' where order_id='{cusorderid}'"
            sob.update_mysql_record(sob_handle, cmd)
            cmd = f"select * from wxapp_recharge_package_order_renew where order_id='{cusorderid}'"
            package_order_renew = sob.select_mysql_record(sob_handle, cmd)
            package_order_renew = package_order_renew[0]
            recharge_time = package_order_renew['recharge_time']
            end_time = package_order_renew['end_time']
            cmd = f"update wxapp_recharge_package_order set end_time='{end_time}',recharge_time=recharge_time+{recharge_time},residue_time=residue_time+{recharge_time},is_use=1,is_renew=1 where id={package_order_renew['packageorder_id']}"
            sob.update_mysql_record(sob_handle,cmd)
            value_info = {
                'mini_id': package_order_renew['mini_id'],
                'note_id': package_order_renew['note_id'],
                'type': 1,
                'user_id': package_order_renew['user_id'],
                'scene': 20,
                'money': package_order_renew['pay_price'],
                'describes': '套餐购买(微信扣款)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
            cmd = f"update wxapp_order set pay_status=20,pay_price=0 where note_id={package_order_renew['note_id']} and user_id={package_order_renew['user_id']} and pay_status=10"
            sob.update_mysql_record(sob_handle, cmd)
            calc_proportion_money(package_order_renew['second_proportion_money'], package_order_renew['first_proportion_money'], package_order_renew['note_id'],
                                  package_order_renew['mini_id'], package_order_renew['id'], package_order_renew['pay_price'])

            if log_id != None and log_id != 'None':
                cmd = f"update wxapp_user_door_log set is_due=0 where id='{log_id}'"
                sob.update_mysql_record(sob_handle, cmd)
        sob.sql_close(sob_handle)
        return 'success'
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}




#【小程序套餐包退款-微信回调】
def wx_package_order_fefunds_payback(orgid,data=Body(None)):
    sob_handle = sob.sql_open(db_config)
    re_dict = data
    return_code = re_dict['event_type']
    if return_code == 'REFUND.SUCCESS':
        wx_deve = wx_pay_sdk()
        data = wx_deve.decrypt(re_dict['resource']['nonce'], re_dict['resource']['ciphertext'],
                               re_dict['resource']['associated_data'],orgid)  # 商户对resource对象进行解密后，得到的资源对象示例
        data = json.loads(data.decode())
        # 拿到这次支付的订单号
        refund_id = data['refund_id']  # 微信退款单号
        refund_status = data['refund_status']  # 退款状态
        transaction_id = data['transaction_id']
        user_received_account = data['user_received_account']  # 退款入账账户
        out_refund_no = data['out_refund_no']   #商户退款单号
        if refund_status == 'SUCCESS':
            cmd = f"update wxapp_recharge_package_order_refund set order_status=20,refund_id='{refund_id}',user_received_account='{user_received_account}' where id='{out_refund_no}'"
            sob.update_mysql_record(sob_handle,cmd)
            cmd = f"update wxapp_recharge_package_order set residue_time=0,refund_time='{timer.get_now()}',order_status=40 where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle,cmd)
            cmd = f"select * from wxapp_recharge_package_order where transaction_id='{transaction_id}'"
            package_order = sob.select_mysql_record(sob_handle,cmd)
            package_order = package_order[0]
            value_info = {
                'mini_id': package_order['mini_id'],
                'note_id': package_order['note_id'],
                'type': 1,
                'user_id': package_order['user_id'],
                'scene': 40,
                'money': package_order['pay_price'],
                'describes': '订单退款(包月套餐退款)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
        elif refund_status == 'ABNORMAL':
            cmd = f"update wxapp_recharge_package_order set order_status=60,is_use=1 where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle, cmd)
        else:
            cmd = f"update wxapp_recharge_package_order set order_status=20,is_use=1 where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    return {'code': 'SUCCESS', 'message': '成功'}


#【小程序套餐包续费退款-微信回调】
def wx_renew_order_fefunds_payback(orgid,data=Body(None)):
    with open("./c.txt", "a+", encoding="utf8") as f:
        f.write(str(data))
        f.write("\n")
        f.write(str(type(data)))
    sob_handle = sob.sql_open(db_config)
    re_dict = data
    return_code = re_dict['event_type']
    if return_code == 'REFUND.SUCCESS':
        wx_deve = wx_pay_sdk()
        data = wx_deve.decrypt(re_dict['resource']['nonce'], re_dict['resource']['ciphertext'],
                               re_dict['resource']['associated_data'],orgid)  # 商户对resource对象进行解密后，得到的资源对象示例
        data = json.loads(data.decode())
        # 拿到这次支付的订单号
        refund_id = data['refund_id']  # 微信退款单号
        refund_status = data['refund_status']  # 退款状态
        transaction_id = data['transaction_id']
        user_received_account = data['user_received_account']  # 退款入账账户
        if refund_status == 'SUCCESS':
            cmd = f"update wxapp_recharge_package_order_renew set refund_time='{timer.get_now()}',order_status=40 where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle,cmd)

            cmd = f"select * from wxapp_recharge_package_order_renew where transaction_id='{transaction_id}'"
            package_order_renew = sob.select_mysql_record(sob_handle,cmd)
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
            package = sob.select_mysql_record(sob_handle,cmd)
            package = package[0]
            residue_time = package_order['residue_time'] - package['recharge_time'] - package['gift_recharge_time']
            if residue_time > 0:
                cmd = f"update wxapp_recharge_package_order set residue_time={residue_time},end_time='{package_order_renew['start_time']}',is_use=1,order_status=20 where id={package_order['id']}"
                sob.update_mysql_record(sob_handle,cmd)
            else:
                cmd = f"update wxapp_recharge_package_order set residue_time=0,is_use=0,order_status=20 where id={package_order['id']}"
                sob.update_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    return {'code': 'SUCCESS', 'message': '成功'}



class IsBuyFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    user_id: int = Field(None, description="用户id")
    package_id: int = Field(None, description="套餐包id")


def _is_user_recharge_buy(request_data: IsBuyFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_recharge_package_order where user_id={request_data.user_id} and mini_id={request_data.mini_id} and package_id={request_data.package_id} and pay_status=20 and order_status=20 and end_time>'{timer.get_now()}'"
    info = sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return info


def is_user_recharge_buy(request_data: IsBuyFilterFormat):
    try:
        res = _is_user_recharge_buy(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}