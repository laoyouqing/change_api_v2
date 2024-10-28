import json
import re

from fastapi import Body
from pydantic import BaseModel, Field

from config import db_config, UDP_PORT, REQ_HOST
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.normal_func import calc_proportion_money, split_test, invalid_dealer_order
from tool.udpc import Client
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import wx_pay_sdk, tl_pay_sdk

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()



#【小程序门禁扫码-微信回调】
def wx_door_scancode_payback(orgid,data=Body(None)):
    try:
        with open('./d.txt', 'a+', encoding='utf8') as f:
            f.write(str(data))
            f.write('\n')
            f.write(str(type(data)))
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
                cmd = f"update wxapp_user_door_log set pay_status=2,is_due=0,pay_time='{timer.get_now()}',transaction_id='{transaction_id}' where id='{out_trade_no}'"
                sob.update_mysql_record(sob_handle, cmd)
                cmd = f"select * from wxapp_user_door_log where id='{out_trade_no}'"
                door_order = sob.select_mysql_record(sob_handle, cmd)
                door_order = door_order[0]
                value_info = {
                    'mini_id': door_order['mini_id'],
                    'note_id': door_order['note_id'],
                    'type': 1,
                    'user_id':door_order['user_id'],
                    'scene': 20,
                    'money': door_order['money'],
                    'describes': '门禁消费(微信扣款)',
                    'add_time': timer.get_now()
                }
                sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
                cmd = f"select * from wxapp_pod_door where note_id={door_order['note_id']} and serialnum='{door_order['serialnum']}'"
                pod_door = sob.select_mysql_record(sob_handle,cmd)
                pod_door = pod_door[0]
                data = {}
                data['ip'] = pod_door['lastip']
                data['serialnum'] = pod_door['serialnum']
                data['doorindex'] = pod_door['doorindex']
                data['token'] = 'qfevserver'
                data['command'] = 'payback_door'
                sock_data = 'evapi|{}'.format(json.dumps(data))

                client = Client(sock_data, UDP_PORT)
                client.start()
                resp = client.recv_msg()
                print(resp)
                cmd = f"update wxapp_user_door_log set status=1 where id='{out_trade_no}'"
                sob.update_mysql_record(sob_handle, cmd)
                calc_proportion_money(door_order['second_proportion_money'], door_order['first_proportion_money'], door_order['note_id'],
                                      door_order['mini_id'], door_order['id'], door_order['money'])
        sob.sql_close(sob_handle)
        return {'code': 'SUCCESS', 'message': '成功'}
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}





#【小程序门禁扫码-通联回调】
def tl_door_scancode_payback(data=Body(None)):
    try:
        sob_handle = sob.sql_open(db_config)
        print(data)
        data = data.decode('utf-8')
        re_dict = split_test(data)
        trxstatus = re_dict['trxstatus']
        trxid = re_dict['trxid']  # 收银宝交易单号
        cusorderid = re_dict['cusorderid']  # 统一下单对应的reqsn订单号
        if trxstatus == '0000':
            cmd = f"update wxapp_user_door_log set pay_status=2,is_due=0,pay_time='{timer.get_now()}',transaction_id='{trxid}' where id='{cusorderid}'"
            sob.update_mysql_record(sob_handle, cmd)
            cmd = f"select * from wxapp_user_door_log where id='{cusorderid}'"
            door_order = sob.select_mysql_record(sob_handle, cmd)
            door_order = door_order[0]
            value_info = {
                'mini_id': door_order['mini_id'],
                'note_id': door_order['note_id'],
                'type': 1,
                'user_id':door_order['user_id'],
                'scene': 20,
                'money': door_order['money'],
                'describes': '门禁消费(微信扣款)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
            cmd = f"select * from wxapp_pod_door where note_id={door_order['note_id']} and serialnum='{door_order['serialnum']}'"
            pod_door = sob.select_mysql_record(sob_handle,cmd)
            pod_door = pod_door[0]
            data = {}
            data['ip'] = pod_door['lastip']
            data['serialnum'] = pod_door['serialnum']
            data['doorindex'] = pod_door['doorindex']
            data['token'] = 'qfevserver'
            data['command'] = 'payback_door'
            sock_data = 'evapi|{}'.format(json.dumps(data))

            client = Client(sock_data, UDP_PORT)
            client.start()
            resp = client.recv_msg()
            cmd = f"update wxapp_user_door_log set status=1 where id='{cusorderid}'"
            sob.update_mysql_record(sob_handle, cmd)
            calc_proportion_money(door_order['second_proportion_money'], door_order['first_proportion_money'], door_order['note_id'],
                                  door_order['mini_id'], door_order['id'], door_order['money'])
        sob.sql_close(sob_handle)
        return 'success'
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}




#【小程序门禁退款-微信回调】
def wx_door_fefunds_payback(orgid,data=Body(None)):
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
            cmd = f"update wxapp_user_door_log set refund_time='{timer.get_now()}',is_invalid=1,refund_id='{refund_id}',pay_status=3,user_received_account='{user_received_account}' where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle,cmd)
            cmd = f"select * from wxapp_user_door_log where transaction_id='{transaction_id}'"
            door_log = sob.select_mysql_record(sob_handle, cmd)
            door_log = door_log[0]
            value_info = {
                'mini_id': door_log['mini_id'],
                'note_id': door_log['note_id'],
                'type': 1,
                'user_id': door_log['user_id'],
                'scene': 40,
                'money': door_log['residue_money'],
                'describes': '门禁退款到微信',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
            invalid_dealer_order(door_log)
    sob.sql_close(sob_handle)
    return {'code': 'SUCCESS', 'message': '成功'}



class QueryFilterFormat(BaseModel):
    id: str = Field(None, description="id")
    money: float = Field(None, description="退款金额")


def _user_door_refund(request_data: QueryFilterFormat):
    sob_handle = sob.sql_open(db_config)
    id = request_data.id
    money = request_data.money
    cmd = f"select * from wxapp_user_door_log where id='{id}'"
    pod_door_log = sob.select_mysql_record(sob_handle,cmd)
    pod_door_log = pod_door_log[0]
    if money > pod_door_log['money']:
        raise ValueError('超出该笔订单最大退款金额')
    if pod_door_log['pay_status'] == 1:
        raise ValueError('该订单未支付')
    if pod_door_log['pay_type'] == 3: #退余额
        cmd = f"update wxapp_user set balance=balance+{money} where id={pod_door_log['user_id']}"
        sob.update_mysql_record(sob_handle,cmd)
        cmd = f"update wxapp_user_door_log set pay_status=3,residue_money={money},is_invalid=1,refund_time='{timer.get_now()}' where id='{id}'"
        sob.update_mysql_record(sob_handle,cmd)
    elif pod_door_log['pay_type'] == 4: #退微信
        cmd = f"select * from wxapp_payinfo where mini_id={pod_door_log['mini_id']}"
        payinfo = sob.select_mysql_record(sob_handle, cmd)
        if payinfo:
            out_refund_no = f"{timer.get_now('%Y%m%d%H%M%S')}{pod_door_log['user_id']}"
            payinfo = payinfo[0]
            refund_fee = int(money * 100)
            total_fee = int(pod_door_log['money'] * 100)
            if payinfo['pay_type'] == 2:  # 通联支付
                tl_pay = tl_pay_sdk()
                resp = tl_pay.tl_refunds(payinfo['orgid'], payinfo['mchid'],
                                         payinfo['apikey'],
                                         refund_fee, out_refund_no,
                                         pod_door_log['transaction_id'],
                                         payinfo['key_pem'])
                if resp['retcode'] == 'SUCCESS':
                    if resp['trxstatus'] == '0000':
                        trxid = resp['trxid']  # 收银宝交易单号
                        cmd = f"update wxapp_user_door_log set pay_status=3,residue_money={money},is_invalid=1,refund_id='{trxid}',refund_time='{timer.get_now()}' where id='{id}'"
                        sob.update_mysql_record(sob_handle, cmd)
                        value_info = {
                            'mini_id': pod_door_log['mini_id'],
                            'note_id': pod_door_log['note_id'],
                            'type': 2,
                            'user_id': pod_door_log['user_id'],
                            'scene': 40,
                            'money': money,
                            'describes': '订单退款到通联(门禁退款)',
                            'add_time': timer.get_now()
                        }
                        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',[value_info])
                else:
                    raise ValueError('退款失败')
            else:
                notify_url = f'{REQ_HOST}/api/wx_door_fefunds_payback/{payinfo["orgid"]}'
                response = wx_pay_sdk().refunds_v3(pod_door_log['transaction_id'], out_refund_no,
                                        refund_fee, total_fee, payinfo['mchid'], payinfo['apikey'], payinfo['key_pem'],
                                        notify_url)
                print(response.text)
                cmd = f"update wxapp_user_door_log set residue_money={money} where id='{id}'"
                sob.update_mysql_record(sob_handle, cmd)
        else:
            raise ValueError('支付信息不完整')
    sob.sql_close(sob_handle)
    return


#【门禁退款】
def user_door_refund(request_data: QueryFilterFormat):
    try:
        res = _user_door_refund(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}