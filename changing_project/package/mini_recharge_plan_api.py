import json

from fastapi import Body
from pydantic import BaseModel, Field

from config import db_config, REQ_HOST
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.normal_func import split_test
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import tl_pay_sdk, wx_pay_sdk

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()


class BalanceFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    mini_id: int = Field(..., description="小程序id")

class RepresentFilterFormat(BaseModel):
    mobile: str = Field(None, description="手机号")
    mini_id: int = Field(..., description="小程序id")

def _user_balance(request_data: BalanceFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select id,balance,virtual_balance,point from wxapp_user where id={request_data.user_id}"
    user = sob.select_mysql_record(sob_handle,cmd)
    user = user[0]
    cmd = f"select * from wxapp_recharge_plan where mini_id={request_data.mini_id}"
    recharge_plan = sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return {'user':user,'recharge_plan':recharge_plan}


def _represent_user_balance(request_data: RepresentFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"""select a.id,balance,virtual_balance,point,nickname,avatar,idno,rfid from wxapp_user a left join wxapp_door_idno b on a.id=b.user_id
          where (mobile='{request_data.mobile}' and is_manage=0 or idno='{request_data.mobile}' or rfid='{request_data.mobile}') and a.mini_id={request_data.mini_id}"""
    user = sob.select_mysql_record(sob_handle,cmd)
    if not user:
        raise ValueError('用户不存在')
    user = user[0]
    cmd = f"select * from wxapp_recharge_plan where mini_id={request_data.mini_id}"
    recharge_plan = sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return {'user':user,'recharge_plan':recharge_plan}


#【小程序-钱包】
def user_balance(request_data: BalanceFilterFormat):
    try:
        res = _user_balance(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



#【小程序-代他充值钱包】
def represent_user_balance(request_data: RepresentFilterFormat):
    try:
        res = _represent_user_balance(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class BuyFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    mini_id: int = Field(..., description="小程序id")
    plan_id: int = Field(None, description="充值包id")
    money: float = Field(None, description="自定义充值金额")
    is_represent: int = Field(0, description="是否代他充值 0:否 1：是")
    rechargeuser_id: int = Field(None, description="被充值用户id")



def _recharge_plan_buy(request_data: BuyFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select id,balance,virtual_balance,point,open_id from wxapp_user where id={request_data.user_id}"
    user = sob.select_mysql_record(sob_handle, cmd)
    user = user[0]
    cmd = f"select * from wxapp_payinfo where mini_id={request_data.mini_id}"
    payinfo = sob.select_mysql_record(sob_handle, cmd)
    if payinfo:
        order_id = f"{timer.get_now(format='%Y%m%d%H%M%S')}{request_data.user_id}"
        print('order_id',order_id)
        payinfo = payinfo[0]
        if request_data.plan_id:
            cmd = f"select * from wxapp_recharge_plan where id={request_data.plan_id}"
            recharge_plan = sob.select_mysql_record(sob_handle,cmd)
            recharge_plan = recharge_plan[0]
            money = recharge_plan['money']
            total_money = int(money * 100)
            actual_money = money + recharge_plan['gift_money']
            value_info = {
                'order_id': order_id,
                'mini_id': request_data.mini_id,
                'user_id': request_data.user_id,
                'plan_id': request_data.plan_id,
                'recharge_type': 20,
                'pay_price': money,
                'gift_money': recharge_plan['gift_money'],
                'actual_money': actual_money,
                'pay_status': 10,
                'is_represent': request_data.is_represent,
                'rechargeuser_id': request_data.rechargeuser_id,
                'add_time':timer.get_now(),
                'update_time':timer.get_now(),
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_recharge_order',[value_info])
        else:
            money = request_data.money
            total_money = int(float(money) * 100)
            print(total_money)
            value_info = {
                'order_id': order_id,
                'mini_id': request_data.mini_id,
                'user_id': request_data.user_id,
                'recharge_type': 10,
                'pay_price': money,
                'actual_money': money,
                'pay_status': 10,
                'is_represent': request_data.is_represent,
                'rechargeuser_id': request_data.rechargeuser_id,
                'add_time': timer.get_now(),
                'update_time': timer.get_now(),
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_recharge_order', [value_info])
        if payinfo['pay_type'] == 2:  # 通联支付
            notify_url = f'{REQ_HOST}/api/tl_recharge_plan_buy_payback'
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
            notify_url = f'{REQ_HOST}/api/wx_recharge_plan_buy_payback/{payinfo["orgid"]}'
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

#【小程序-余额充值】
def recharge_plan_buy(request_data: BuyFilterFormat):
    try:
        res = _recharge_plan_buy(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

#【小程序余额充值-微信回调】
def wx_recharge_plan_buy_payback(orgid,data=Body(None)):
    try:
        print(orgid)
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
                cmd = f"select * from wxapp_recharge_order where order_id='{out_trade_no}' and pay_status=20 and transaction_id='{transaction_id}'"
                exist_order = sob.select_mysql_record(sob_handle, cmd)
                if exist_order:
                    sob.sql_close(sob_handle)
                    return {'code': 'SUCCESS', 'message': '成功'}
                cmd = f"update wxapp_recharge_order set pay_status=20,transaction_id='{transaction_id}',pay_time='{timer.get_now()}' where order_id='{out_trade_no}'"
                sob.update_mysql_record(sob_handle,cmd)
                cmd = f"select * from wxapp_recharge_order where order_id='{out_trade_no}'"
                order = sob.select_mysql_record(sob_handle, cmd)
                order = order[0]
                is_represent = order['is_represent']
                if is_represent == 0:
                    remark = '(支%s赠%s)' % (order['pay_price'], order['gift_money'])
                    value_info = {
                        'mini_id': order['mini_id'],
                        'type': 1,
                        'user_id': order['user_id'],
                        'scene': 10,
                        'money': order['actual_money'],
                        'describes': '微信充值',
                        'remark':remark,
                        'add_time':timer.get_now()
                    }
                    sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                    cmd = f"update wxapp_user set balance=balance+{order['actual_money']} where id={order['user_id']}"
                    sob.update_mysql_record(sob_handle,cmd)
                else:
                    remark = '(支%s赠%s)' % (order['pay_price'], order['gift_money'])
                    value_info = {
                        'mini_id': order['mini_id'],
                        'type': 1,
                        'user_id': order['user_id'],
                        'scene': 10,
                        'money': order['actual_money'],
                        'describes': '微信充值',
                        'remark': remark,
                        'rechargeuser_id':order['rechargeuser_id'],
                        'add_time': timer.get_now()
                    }
                    sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                    cmd = f"update wxapp_user set balance=balance+{order['actual_money']} where id={order['rechargeuser_id']}"
                    sob.update_mysql_record(sob_handle, cmd)
        sob.sql_close(sob_handle)
        return {'code': 'SUCCESS', 'message': '成功'}
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



#【小程序余额充值-通联回调】
def tl_recharge_plan_buy_payback(data=Body(None)):
    try:
        sob_handle = sob.sql_open(db_config)
        print(data)
        data = data.decode('utf-8')
        re_dict = split_test(data)
        trxstatus = re_dict['trxstatus']
        trxid = re_dict['trxid']  # 收银宝交易单号
        cusorderid = re_dict['cusorderid']  # 统一下单对应的reqsn订单号
        if trxstatus == '0000':
            cmd = f"update wxapp_recharge_order set pay_status=20,transaction_id='{trxid}',pay_time='{timer.get_now()}' where order_id='{cusorderid}'"
            sob.update_mysql_record(sob_handle,cmd)
            cmd = f"select * from wxapp_recharge_order where order_id='{cusorderid}'"
            order = sob.select_mysql_record(sob_handle, cmd)
            order = order[0]
            is_represent = order['is_represent']
            if is_represent == 0:
                remark = '(支%s赠%s)' % (order['pay_price'], order['gift_money'])
                value_info = {
                    'mini_id': order['mini_id'],
                    'type': 1,
                    'user_id': order['user_id'],
                    'scene': 10,
                    'money': order['actual_money'],
                    'describes': '微信充值',
                    'remark':remark,
                    'add_time': timer.get_now()
                }
                sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                cmd = f"update wxapp_user set balance=balance+{order['actual_money']} where id={order['user_id']}"
                sob.update_mysql_record(sob_handle,cmd)
            else:
                remark = '(支%s赠%s)' % (order['pay_price'], order['gift_money'])
                value_info = {
                    'mini_id': order['mini_id'],
                    'type': 1,
                    'user_id': order['user_id'],
                    'scene': 10,
                    'money': order['actual_money'],
                    'describes': '微信充值',
                    'remark': remark,
                    'rechargeuser_id':order['rechargeuser_id'],
                    'add_time': timer.get_now()
                }
                sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                cmd = f"update wxapp_user set balance=balance+{order['actual_money']} where id={order['rechargeuser_id']}"
                sob.update_mysql_record(sob_handle, cmd)
        sob.sql_close(sob_handle)
        return 'success'
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



#【小程序余额退款-微信回调】
def wx_recharge_fefunds_payback(orgid,data=Body(None)):
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
            cmd = f"update wxapp_recharge_order set refund_time='{timer.get_now()}',is_refund=1,refund_id='{refund_id}' where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle,cmd)

            cmd = f"select * from wxapp_recharge_order where transaction_id='{transaction_id}'"
            package_order = sob.select_mysql_record(sob_handle, cmd)
            package_order = package_order[0]
            value_info = {
                'mini_id': package_order['mini_id'],
                'type': 1,
                'user_id': package_order['user_id'],
                'scene': 40,
                'money': package_order['pay_price'],
                'describes': '订单退款到微信(钱包退款)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
            if package_order['is_represent'] == 1:
                user_id = package_order['rechargeuser_id']
            else:
                user_id = package_order['user_id']
            cmd = f"update wxapp_user set balance=balance-{package_order['refund_money']} where id={user_id}"
            sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return {'code': 'SUCCESS', 'message': '成功'}