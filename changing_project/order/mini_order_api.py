import json

from fastapi import Body
from pydantic import BaseModel, Field

from config import TCP_PORT, db_config, REQ_HOST
from tool.format_data import format_response_data
from tool.normal_func import five_order_refund, split_test, invalid_dealer_order
from tool.tcpc import TCPClient
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import tl_pay_sdk, wx_pay_sdk

sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()

class OrderFailFilterFormat(BaseModel):
    order_id: int = Field(..., description="订单id")


class RechargeFilterFormat(BaseModel):
    data: str = Field(..., description="请求数据")


class UserOrderFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    order_status: int = Field(..., description="订单状态 1充电中 2其他")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")



def _mini_order_fail(request_data: OrderFailFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"update wxapp_order set order_status=30,end_time='{timer.get_now()}' where id={request_data.order_id}"
    sob.update_mysql_record(sob_handle, cmd)
    cmd = f"select * from wxapp_order where id={request_data.order_id}"
    order = sob.select_mysql_record(sob_handle, cmd)
    order = order[0]
    cmd = f"update wxapp_pod_pileport set portstatus=0 where id={order['pileport_id']}"
    sob.update_mysql_record(sob_handle, cmd)
    five_order_refund(order)


#【小程序充电失败】
def mini_order_fail(request_data: OrderFailFilterFormat):
    try:
        res = _mini_order_fail(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


def _mini_recharge_emergency(request_data: RechargeFilterFormat):
    server = TCPClient(TCP_PORT)
    server.send_msg(request_data.data)
    # try:
    resp = server.recv_msg()
    server.close()
    return resp
    # except:
    #     server.close()
    #     raise ValueError('请求失败')


# 【小程序应急充电】
def mini_recharge_emergency(request_data: RechargeFilterFormat):
    # try:
    print(request_data)
    res = _mini_recharge_emergency(request_data)
    response = format_response_data(res)
    return response
    # except Exception as exc:
    #     return {"status": 400, "msg": exc.__str__()}


def _mini_user_order_list(request_data: UserOrderFilterFormat):
    sob_handle = sob.sql_open(db_config)
    if request_data.order_status != 1:
        cmd = f"select a.id,snum,portnum,start_time,end_time,pay_price,electrct_price,server_price,pay_type,order_status,pay_status,note_name,a.add_time,count(*) over() as total from wxapp_order a left join wxapp_note b on a.note_id=b.id where user_id={request_data.user_id} order by a.add_time desc limit {request_data.size} offset {request_data.offset}"
        order = sob.select_mysql_record(sob_handle,cmd)
        if isinstance(order, list):
            if order:
                total = order[0].get("total", 0)
            else:
                total = 0
        else:
            raise ValueError('error sql')
        for _ in order:
            del _["total"]
        sob.sql_close(sob_handle)
        return {
            "total": total,
            "order": order
        }
    else:
        cmd = f"select a.id,snum,portnum,start_time,end_time,note_name from wxapp_order a left join wxapp_note b on a.note_id=b.id where user_id={request_data.user_id} and order_status=10"
        order = sob.select_mysql_record(sob_handle,cmd)
        order = order[0] if order else ''
        sob.sql_close(sob_handle)
        return {'order':order}




# 【小程序充电记录】
def mini_user_order_list(request_data: UserOrderFilterFormat):
    try:
        res = _mini_user_order_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class PayOrderFilterFormat(BaseModel):
    order_id: int = Field(..., description="订单id")

def _mini_order_topay(request_data: PayOrderFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_order where id={request_data.order_id}"
    order = sob.select_mysql_record(sob_handle,cmd)
    order = order[0]
    total_money = int(order['pay_price'] * 100)
    cmd = f"select * from wxapp_user where id={order['user_id']}"
    user = sob.select_mysql_record(sob_handle,cmd)
    user = user[0]
    cmd = f"select * from wxapp_payinfo where mini_id={order['mini_id']}"
    payinfo = sob.select_mysql_record(sob_handle, cmd)
    if payinfo:
        payinfo = payinfo[0]
        if payinfo['pay_type'] == 2:  # 通联支付
            notify_url = f'{REQ_HOST}/api/tl_order_payback'
            tl_pay = tl_pay_sdk()
            resp = tl_pay.tl_mini_pay(payinfo['apikey'], payinfo['orgid'], payinfo['mchid'],
                                      order['order_id'], total_money, notify_url,
                                      payinfo['key_pem'])
            sob.sql_close(sob_handle)
            return {'data': resp, 'status': 200}
        else:
            cmd = f"select * from wxapp_mini where id={order['mini_id']}"
            wxapp_minis = sob.select_mysql_record(sob_handle, cmd)
            sob.sql_close(sob_handle)
            wxapp_mini = wxapp_minis[0]
            notify_url = f'{REQ_HOST}/api/wx_order_payback/{payinfo["orgid"]}'
            results, data = wx_pay_sdk().mini_pay(wxapp_mini['authorizer_appid'], payinfo['mchid'],
                                                  order['order_id'], total_money, user['open_id'], notify_url,
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


# 【小程序消息订阅-付款】
def mini_order_topay(request_data: PayOrderFilterFormat):
    try:
        res = _mini_order_topay(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

#【小程序充电支付-微信回调】
def wx_order_payback(orgid,data=Body(None)):
    try:
        with open('./c.txt', 'a+', encoding='utf8') as f:
            f.write(str(data))
            f.write('\n')
            f.write(str(type(data)))
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
                cmd = f"select * from wxapp_order where order_id='{out_trade_no}'"
                order = sob.select_mysql_record(sob_handle,cmd)
                order = order[0]
                _cmd = order['cmd']
                if _cmd == 1:
                    order_status = 1
                    cmd = f"select * from wxapp_pod_pile where id={order['pile_id']}"
                    pod_pile = sob.select_mysql_record(sob_handle,cmd)
                    pod_pile = pod_pile[0]
                    pattern = '2'
                    if order['billtype'] == 2 or order['billtype']== 4:
                        pattern = '1'
                    data = {}
                    data['token'] = 'qfevserver'
                    data['ip'] = pod_pile['lastip']
                    data['pattern'] = pattern
                    data['duration'] = order['recharge_time'] * 60
                    data['pile_id'] = pod_pile['id']
                    data['portnum'] = order['portnum']
                    data['order_id'] = order['id']
                    data['cmd'] = '01'
                    data['command'] = 'payback_recharge'
                    try:
                        sock_data = 'evapi|{}'.format(json.dumps(data))
                        server1 = TCPClient(TCP_PORT)
                        server1.send_msg(sock_data)
                        resp = server1.recv_msg()
                        resp = json.loads(resp)
                        print('resp',resp)
                        print('resp',type(resp))
                        server1.close()
                        if resp['status'] == 200:
                            print('1111')
                            value_info = {
                                'mini_id': order['mini_id'],
                                'note_id': order['note_id'],
                                'type': 1,
                                'user_id': order['user_id'],
                                'scene': 20,
                                'start_time':str(order['start_time']),
                                'money': order['pay_price'],
                                'describes': '充电消费(微信扣款)',
                                'add_time': timer.get_now()
                            }
                            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',[value_info])
                            cmd = f"update wxapp_pod_pileport set portstatus=1 where id={order['pileport_id']}"
                            sob.update_mysql_record(sob_handle,cmd)
                        else:
                            print(222)
                            cmd = f"update wxapp_pod_pileport set trouble_status=1 where id={order['pileport_id']}"
                            sob.update_mysql_record(sob_handle, cmd)
                            order_status = 30
                    except:
                        cmd = f"update wxapp_pod_pileport set trouble_status=1 where id={order['pileport_id']}"
                        sob.update_mysql_record(sob_handle, cmd)
                        order_status = 30
                else:
                    order_status = order['order_status']
                print('order_status',order_status)
                cmd = f"update wxapp_order set pay_status=20,pay_type=20,transaction_id='{transaction_id}',pay_time='{timer.get_now()}',order_status={order_status} where order_id='{out_trade_no}'"
                sob.update_mysql_record(sob_handle,cmd)
        sob.sql_close(sob_handle)
        return {'code': 'SUCCESS', 'message': '成功'}
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【小程序充电支付-通联回调】
def tl_order_payback(data=Body(None)):
    try:
        sob_handle = sob.sql_open(db_config)
        print(data)
        data = data.decode('utf-8')
        re_dict = split_test(data)
        trxstatus = re_dict['trxstatus']
        trxid = re_dict['trxid']  # 收银宝交易单号
        cusorderid = re_dict['cusorderid']  # 统一下单对应的reqsn订单号
        if trxstatus == '0000':
            cmd = f"select * from wxapp_order where order_id='{cusorderid}'"
            order = sob.select_mysql_record(sob_handle,cmd)
            order = order[0]
            _cmd = order['cmd']
            if _cmd == 1:
                order_status = 1
                cmd = f"select * from wxapp_pod_pile where id={order['pile_id']}"
                pod_pile = sob.select_mysql_record(sob_handle,cmd)
                pod_pile = pod_pile[0]
                pattern = '2'
                if order['billtype'] == 2 or order['billtype']== 4:
                    pattern = '1'
                data = {}
                data['token'] = 'qfevserver'
                data['ip'] = pod_pile['lastip']
                data['pattern'] = pattern
                data['duration'] = order['recharge_time'] * 60
                data['pile_id'] = pod_pile['id']
                data['portnum'] = order['portnum']
                data['order_id'] = order['id']
                data['cmd'] = '01'
                data['command'] = 'payback_recharge'
                try:
                    sock_data = 'evapi|{}'.format(json.dumps(data))
                    server1 = TCPClient(TCP_PORT)
                    server1.send_msg(sock_data)
                    resp = server1.recv_msg()
                    resp = json.loads(resp)
                    server1.close()
                    if resp['status'] == 200:
                        value_info = {
                            'mini_id': order['mini_id'],
                            'note_id': order['note_id'],
                            'type': 1,
                            'user_id': order['user_id'],
                            'scene': 20,
                            'start_time':str(order['start_time']),
                            'money': order['pay_price'],
                            'describes': '充电消费(微信扣款)',
                            'add_time': timer.get_now()
                        }
                        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',[value_info])
                        cmd = f"update wxapp_pod_pileport set portstatus=1 where id={order['pileport_id']}"
                        sob.update_mysql_record(sob_handle,cmd)
                    else:
                        cmd = f"update wxapp_pod_pileport set trouble_status=1 where id={order['pileport_id']}"
                        sob.update_mysql_record(sob_handle, cmd)
                        order_status = 30
                except:
                    cmd = f"update wxapp_pod_pileport set trouble_status=1 where id={order['pileport_id']}"
                    sob.update_mysql_record(sob_handle, cmd)
                    order_status = 30
            else:
                order_status = order['order_status']
            cmd = f"update wxapp_order set pay_status=20,pay_type=20,transaction_id='{trxid}',pay_time='{timer.get_now()}',order_status={order_status} where order_id='{cusorderid}'"
            sob.update_mysql_record(sob_handle,cmd)
        sob.sql_close(sob_handle)
        return 'success'
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【小程序充电退款-微信回调】
def wx_order_fefunds_payback(orgid,data=Body(None)):
    with open("./aaa.txt", "a+", encoding="utf8") as f:
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
            cmd = f"update wxapp_order set order_status=20,is_invalid=1,pay_status=30,refund_id='{refund_id}',refund_time='{timer.get_now()}',user_received_account='{user_received_account}' where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle,cmd)
            cmd = f"select * from wxapp_order where transaction_id='{transaction_id}'"
            order = sob.select_mysql_record(sob_handle,cmd)
            order = order[0]
            value_info = {
                'mini_id': order['mini_id'],
                'note_id': order['note_id'],
                'type': 1,
                'start_time': str(order['start_time']),
                'end_time': str(order['end_time']),
                'user_id': order['user_id'],
                'scene': 40,
                'money': order['residue_money'],
                'describes': '订单退款到微信(充电时长不足)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
            invalid_dealer_order(order)
        else:
            cmd = f"update wxapp_order set pay_status=40 where transaction_id='{transaction_id}'"
            sob.update_mysql_record(sob_handle, cmd)
        return {'code': 'SUCCESS', 'message': '成功'}
    else:
        return {"status": 400, "msg": return_code}

