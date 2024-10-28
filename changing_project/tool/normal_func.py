import datetime
import json

from config import db_config, REQ_HOST
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import wx_mini_sdk, tl_pay_sdk, wx_pay_sdk
prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()

def get_access_token(mini_id):
    access_token = ''
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_mini where id={mini_id}"
    info = sob.select_mysql_record(sob_handle,cmd)
    if info:
        info = info[0]
        if info['expird_time'] and str(info['expird_time']) > timer.get_now():
            access_token = info['access_token']
        else:
            re_dict = wx_mini_sdk().get_access_token(info['authorizer_appid'],info['secret'])
            print("re_dict",re_dict)
            access_token = re_dict['access_token']
            expird_time = timer.get_now_bef_aft(seconds=-7000)
            cmd = f"update wxapp_mini set access_token='{access_token}',expird_time='{expird_time}' where id={info['id']}"
            sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return access_token

def invalid_dealer_order(order):
    try:
        sob_handle = sob.sql_open(db_config)
        cmd = f"update wxapp_dealer_order set is_invalid=1 where order_id={order['id']}"
        sob.update_mysql_record(sob_handle,cmd)
        if order['is_settled'] == 1:# 已结算
            cmd = f"select account_id from wxapp_dealer_order where order_id={order['id']} and is_settled=1"
            dealer_orders = sob.select_mysql_record(sob_handle,cmd)
            for dealer in dealer_orders:
                cmd = f"update wxapp_dealer_note set money=money-{dealer['share_money']} where account_id={dealer['account_id']}"
                sob.update_mysql_record(sob_handle,cmd)
        sob.sql_close(sob_handle)
    except:
        prolog.error('结算回退出错')

def five_order_refund(order):
    sob_handle = sob.sql_open(db_config)
    if order['pay_status'] == 20:  # 已支付
        if order['pay_type'] == 10:  # 余额支付
            cmd = f"update wxapp_order set pay_status=30,residue_money={order['pay_price']},refund_time='{timer.get_now()}' where id={order['id']}"
            sob.update_mysql_record(sob_handle, cmd)
            cmd = f"update wxapp_user set balance=balance+{order['pay_price']} where id={order['user_id']}"
            sob.update_mysql_record(sob_handle, cmd)
            value_info = {
                'mini_id': order['mini_id'],
                'note_id': order['note_id'],
                'type': 1,
                'start_time': str(order['start_time']),
                'end_time': str(order['end_time']),
                'user_id': order['user_id'],
                'scene': 40,
                'money': order['pay_price'],
                'describes': '订单退款到余额(充电时长小于5分钟)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
        elif order['pay_type'] == 60:  # 虚拟支付
            cmd = f"update wxapp_order set pay_status=30,residue_money={order['pay_price']},refund_time='{timer.get_now()}' where id={order['id']}"
            sob.update_mysql_record(sob_handle, cmd)
            cmd = f"update wxapp_user set virtual_balance=virtual_balance+{order['pay_price']} where id={order['user_id']}"
            sob.update_mysql_record(sob_handle, cmd)
            value_info = {
                'mini_id': order['mini_id'],
                'note_id': order['note_id'],
                'type': 1,
                'start_time': str(order['start_time']),
                'end_time': str(order['end_time']),
                'user_id': order['user_id'],
                'scene': 40,
                'money': order['pay_price'],
                'describes': '订单退款到虚拟金额(充电时长小于5分钟)',
                'add_time': timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',
                                                       [value_info])
        elif order['pay_type'] == 20:  # 微信支付
            cmd = f"select * from wxapp_payinfo where mini_id={order['mini_id']}"
            payinfo = sob.select_mysql_record(sob_handle, cmd)
            if payinfo:
                payinfo = payinfo[0]
                out_refund_no = f"{timer.get_now('%Y%m%d%H%M%S')}{order['user_id']}"
                total_fee = int(order['pay_price'] * 100)
                if payinfo['pay_type'] == 2:  # 通联支付
                    tl_pay = tl_pay_sdk()
                    resp = tl_pay.tl_refunds(payinfo['orgid'], payinfo['mchid'],
                                             payinfo['apikey'],
                                             total_fee, out_refund_no,
                                             order['transaction_id'],
                                             payinfo['key_pem'])
                    if resp['retcode'] == 'SUCCESS':
                        if resp['trxstatus'] == '0000':
                            trxid = resp['trxid']  # 收银宝交易单号
                            cmd = f"update wxapp_order set order_status=20,is_invalid=1,pay_status=30,residue_money={order['pay_price']},refund_id='{trxid}',refund_time='{timer.get_now()}' where id={order['id']}"
                            sob.update_mysql_record(sob_handle, cmd)
                            value_info = {
                                'mini_id': order['mini_id'],
                                'note_id': order['note_id'],
                                'type': 1,
                                'start_time': str(order['start_time']),
                                'end_time': str(order['end_time']),
                                'user_id': order['user_id'],
                                'scene': 40,
                                'money': order['pay_price'],
                                'describes': '订单退款到通联(充电时长小于5分钟)',
                                'add_time': timer.get_now()
                            }
                            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log',
                                                                       [value_info])
                            invalid_dealer_order(order)
                        else:
                            cmd = f"update wxapp_order set pay_status=40 where id={order['id']}"
                            sob.update_mysql_record(sob_handle, cmd)
                    else:
                        cmd = f"update wxapp_order set pay_status=40,residue_money={order['pay_price']} where id={order['id']}"
                        sob.update_mysql_record(sob_handle, cmd)
                else:
                    notify_url = f'{REQ_HOST}/api/wx_order_fefunds_payback/{payinfo["orgid"]}'
                    wx_pay_sdk().refunds_v3(order['transaction_id'], out_refund_no,
                                            total_fee, total_fee, payinfo['mchid'], payinfo['apikey'],payinfo['key_pem'], notify_url)
                    cmd = f"update wxapp_order set residue_money={order['pay_price']} where id={order['id']}"
                    sob.update_mysql_record(sob_handle, cmd)
            else:
                prolog.error('支付信息不完善，退款失败')
        else:
            cmd = f"update wxapp_recharge_package_order set residue_time=residue_time+{order['recharge_time']} " \
                  f"where user_id={order['user_id']} and type=2 and start_time<='{timer.get_now()}' and end_time>='{timer.get_now()}' and order_status=20"
            sob.update_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)



def next_month():
    # 获取当前时间
    now = datetime.datetime.now()
    # 计算次月一号
    next_month = now.month + 1 if now.month < 12 else 1  # 计算下一个月的月份
    next_year = now.year + 1 if now.month == 12 else now.year  # 计算下一个月的年份
    first_day_of_next_month = datetime.datetime(next_year, next_month, 1)
    return first_day_of_next_month



def get_settings(mini_id,title):
    values_json = {}
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_setting where mini_id={mini_id} and title='{title}'"
    info = sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if info:
        values_json = json.loads(info[0].values_json)
    return values_json


def calc_proportion_money(second_proportion_money,first_proportion_money,note_id,mini_id,order_id,pay_price):
    try:
        sob_handle = sob.sql_open(db_config)
        if second_proportion_money:
            cmd = f"update wxapp_dealer_note set freeze_money=freeze_money+{second_proportion_money} where find_in_set({note_id},note_id) and type=6"
            sob.update_mysql_record(sob_handle,cmd)
            cmd = f"select * from wxapp_user where find_in_set({note_id},note_id) and type=6"
            account = sob.select_mysql_record(sob_handle,cmd)
            value_info = {
                'mini_id':mini_id,
                'note_id':note_id,
                'user_id':account[0]['id'],
                'order_id':order_id,
                'order_price':pay_price,
                'share_money':second_proportion_money,
                'type':6,
                'add_time':timer.get_now(),
                'update_time':timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_dealer_order',[value_info])
        if first_proportion_money:
            cmd = f"update wxapp_dealer_note set freeze_money=freeze_money+{first_proportion_money} where find_in_set({note_id},note_id) and type=5"
            sob.update_mysql_record(sob_handle, cmd)
            cmd = f"select * from wxapp_user where find_in_set({note_id},note_id) and type=5"
            account = sob.select_mysql_record(sob_handle, cmd)
            value_info = {
                'mini_id':mini_id,
                'note_id':note_id,
                'user_id':account[0]['id'],
                'order_id':order_id,
                'order_price':pay_price,
                'share_money':first_proportion_money,
                'type':5,
                'add_time':timer.get_now(),
                'update_time':timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_dealer_order', [value_info])
        sob.sql_close(sob_handle)
    except:
        prolog.error('分成收入异常')



def split_test(msg):
    # 将字符串分割成键值对列表
    key_value_pairs = msg.split('&')
    # 创建一个空字典
    result_dict = {}
    # 遍历键值对列表，并将其添加到字典中
    for pair in key_value_pairs:
        key, value = pair.split('=')
        result_dict[key] = value
    # 打印结果字典
    print(result_dict)
    return result_dict



