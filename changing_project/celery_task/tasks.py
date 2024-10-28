import datetime
import json
import os
import time
from glom import glom
from celery_task.main import app
from celery_task.sql_orm import MysqlHelp
from config import TCP_PORT, db_config, REQ_HOST
from tool.normal_func import get_settings, calc_proportion_money
from tool.tcpc import TCPClient
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
from tool.wx_sdk import wx_mini_sdk, tl_pay_sdk, wx_pay_sdk

timer = wf_time_new()
sob = wf_mysql_class(cursor_type=True)
@app.task(name='check_order_settled')
def check_order_settled():
    '''结算'''
    shop_orders = MysqlHelp.getall('*', 'wxapp_order','pay_status=20 and order_status=20 and is_settled=0 and is_invalid=0')
    for shop_order in shop_orders:
        shop_dealer_setting_set = MysqlHelp.get('values_json', 'wxapp_setting','mini_id="{}" and title={}'.format(shop_order['mini_id'], '"settlement"'))
        values_json = json.loads(shop_dealer_setting_set['values_json'])
        settle_day = values_json['settle_day']  # 结算天数
        try:
            is_timeout_time = timer.time2timestamp(shop_order['pay_time'].strftime('%Y-%m-%d %H:%M:%S')) + int(settle_day) * 60 * 60
            if is_timeout_time<time.time():
                shop_dealer_order = MysqlHelp.getall('*', 'wxapp_dealer_order','order_id="{}" and mini_id={} and is_invalid=0 and is_settled=0'.format(shop_order['id'], shop_order['mini_id']))   #分成订单
                for order in shop_dealer_order:
                    shop_dealer_user = MysqlHelp.get('*', 'wxapp_dealer_note','mini_id={} and find_in_set({},note_id) and type={}'.format(shop_order['mini_id'],order['note_id'],order['type']))
                    freeze_money = shop_dealer_user['freeze_money'] - order['share_money']
                    money = shop_dealer_user['money'] + order['share_money']
                    pass
                    MysqlHelp.update('wxapp_dealer_note','money={},freeze_money={},update_time="{}"'.format(money, freeze_money, timer.get_now()),'id={}'.format(shop_dealer_user['id']))
                    MysqlHelp.update('wxapp_dealer_order', 'is_settled=1,update_time="{}"'.format(timer.get_now()),'id={}'.format(order['id']))
                    try:
                        MysqlHelp.insert('wxapp_dealer_order_detail',
                                         'mini_id,dealer_order_id,old_price,now_money,add_time,update_time',
                                         '{},{},{},{},"{}","{}"'.format(order['mini_id'], order['id'],
                                                                             shop_dealer_user['money'],
                                                                             money, timer.get_now(), timer.get_now()))
                    except:
                        pass
                MysqlHelp.update('wxapp_order', 'is_settled=1,update_time="{}"'.format(timer.get_now()), 'id={}'.format(shop_order['id']))
        except:
            pass

    ev_recharge_package_orders = MysqlHelp.getall('*', 'wxapp_recharge_package_order', 'pay_status=20 and order_status=20 and is_settled=0 and is_invalid=0')
    for package_orders in ev_recharge_package_orders:
        shop_dealer_setting_set = MysqlHelp.get('values_json', 'wxapp_setting','mini_id={} and title={}'.format(package_orders['mini_id'],'"settlement"'))
        values_json = json.loads(shop_dealer_setting_set['values_json'])
        settle_day = values_json['settle_day']  # 结算天数
        try:
            is_timeout_time = timer.time2timestamp(package_orders['pay_time'].strftime('%Y-%m-%d %H:%M:%S')) + int(settle_day) * 60 * 60
            if is_timeout_time < time.time():
                shop_dealer_orders = MysqlHelp.getall('*', 'wxapp_dealer_order','order_id="{}" and mini_id={} and is_invalid=0 and is_settled=0'.format(
                                                      package_orders['id'], package_orders['mini_id']))  # 分成订单
                for order in shop_dealer_orders:
                    shop_dealer_user = MysqlHelp.get('*', 'wxapp_dealer_note',
                                                     'mini_id={} and find_in_set({},note_id) and type={}'.format(package_orders['mini_id'],order['note_id'],order['type']))
                    freeze_money = shop_dealer_user['freeze_money'] - order['share_money']
                    money = shop_dealer_user['money'] + order['share_money']
                    MysqlHelp.update('wxapp_dealer_note',
                                     'money={},freeze_money={},update_time="{}"'.format(money, freeze_money, timer.get_now()),
                                     'id={}'.format(shop_dealer_user['id']))
                    try:
                        MysqlHelp.insert('wxapp_dealer_order_detail',
                                         'mini_id,dealer_order_id,old_price,now_money,add_time,update_time',
                                         '{},"{}",{},{},"{}","{}"'.format(order['mini_id'], order['id'],
                                                                             shop_dealer_user['money'],
                                                                             money, timer.get_now(),timer.get_now()))
                    except:
                        pass
                    MysqlHelp.update('wxapp_dealer_order', 'is_settled=1,update_time="{}"'.format(timer.get_now()), 'id={}'.format(order['id']))
                MysqlHelp.update('wxapp_recharge_package_order', 'is_settled=1,update_time="{}"'.format(timer.get_now()), 'id={}'.format(package_orders['id']))
        except:
            pass

    ev_recharge_package_order_renew = MysqlHelp.getall('*', 'wxapp_recharge_package_order_renew','pay_status=20 and order_status=20 and is_settled=0 and is_invalid=0')
    for order_renew in ev_recharge_package_order_renew:
        shop_dealer_setting_set = MysqlHelp.get('values_json', 'wxapp_setting','mini_id={} and title={}'.format(order_renew['mini_id'],'"settlement"'))
        values_json = json.loads(shop_dealer_setting_set['values_json'])
        settle_day = values_json['settle_day']  # 结算天数
        try:
            is_timeout_time = timer.get_now(order_renew['pay_time']) + int(settle_day) * 60 * 60
            if is_timeout_time < time.time():
                shop_dealer_orders = MysqlHelp.getall('*', 'wxapp_dealer_order',
                                                      'order_id="{}" and mini_id={} and is_invalid=0 and is_settled=0'.format(
                                                          order_renew['id'], order_renew['mini_id']))  # 分成订单
                for order in shop_dealer_orders:
                    shop_dealer_user = MysqlHelp.get('*', 'wxapp_dealer_note',
                                                     'mini_id={} and find_in_set({},note_id) and type={}'.format(
                                                         order_renew['mini_id'], order['note_id'], order['type']))
                    freeze_money = shop_dealer_user['freeze_money'] - order['share_money']
                    money = shop_dealer_user['money'] + order['share_money']
                    MysqlHelp.update('wxapp_dealer_note',
                                     'money={},freeze_money={},update_time="{}"'.format(money, freeze_money, timer.get_now()),
                                     'id={}'.format(shop_dealer_user['id']))
                    try:
                        MysqlHelp.insert('wxapp_dealer_order_detail',
                                         'mini_id,dealer_order_id,old_price,now_money,add_time,update_time',
                                         '{},"{}",{},{},"{}","{}"'.format(order['mini_id'], order['id'],
                                                                             shop_dealer_user['money'],
                                                                             money,timer.get_now(),timer.get_now()))
                    except:
                        pass
                    MysqlHelp.update('wxapp_dealer_order', 'is_settled=1,update_time="{}"'.format(timer.get_now()), 'id={}'.format(order['id']))
                MysqlHelp.update('wxapp_recharge_package_order_renew', 'is_settled=1,update_time="{}"'.format(timer.get_now()),
                                 'id={}'.format(order_renew['id']))
        except:
            pass


    ev_pod_door_logs = MysqlHelp.getall('*', 'wxapp_user_door_log','pay_status=2 and (pay_type=3 or pay_type=4) and is_settled=0 and is_invalid=0')
    for log in ev_pod_door_logs:
        shop_dealer_setting_set = MysqlHelp.get('values_json', 'wxapp_setting','mini_id="{}" and title={}'.format(log['mini_id'],'"settlement"'))
        values_json = json.loads(shop_dealer_setting_set['values_json'])
        settle_day = values_json['settle_day']  # 结算天数
        try:
            is_timeout_time = timer.time2timestamp(log['pay_time'].strftime('%Y-%m-%d %H:%M:%S')) + int(settle_day) * 60 * 60
            if is_timeout_time < time.time():
                shop_dealer_orders = MysqlHelp.getall('*', 'wxapp_dealer_order',
                                                      'order_id="{}" and mini_id={} and is_invalid=0 and is_settled=0'.format(
                                                          log['id'], log['mini_id']))  # 分成订单
                for order in shop_dealer_orders:
                    shop_dealer_user = MysqlHelp.get('*', 'wxapp_dealer_note',
                                                     'mini_id="{}" and find_in_set({},note_id) and type={}'.format(
                                                         log['mini_id'], order['note_id'], order['type']))
                    freeze_money = shop_dealer_user['freeze_money'] - order['share_money']
                    money = shop_dealer_user['money'] + order['share_money']
                    MysqlHelp.update('wxapp_dealer_note',
                                     'money={},freeze_money={},update_time="{}"'.format(money, freeze_money, timer.get_now()),
                                     'id={}'.format(shop_dealer_user['id']))

                    try:
                        MysqlHelp.insert('wxapp_dealer_order_detail',
                                         'mini_id,dealer_order_id,old_price,now_money,add_time,update_time',
                                         '{},"{}",{},{},"{}","{}"'.format(order['mini_id'], order['id'],
                                                                             shop_dealer_user['money'],
                                                                             money, timer.get_now(), timer.get_now()))
                    except:
                        pass
                    MysqlHelp.update('wxapp_dealer_order', 'is_settled=1,update_time="{}"'.format(timer.get_now()),'id={}'.format(order['id']))
                MysqlHelp.update('wxapp_pod_door_log', 'is_settled=1,update_time="{}"'.format(timer.get_now()),'id={}'.format(log['id']))
        except:
            pass







@app.task(name='check_pile_online')
def check_pile_online():
    '''查看设备是否在线'''
    stime = timer.get_now_bef_aft(minutes=6) #六分钟前
    ev_pod_pile = MysqlHelp.getall('*','wxapp_pod_pile','update_time<"{}" and isonline=1'.format(stime))
    for pile in ev_pod_pile:
        MysqlHelp.update('wxapp_pod_pile', 'isonline=0', 'id={}'.format(pile['id']))






@app.task(name='check_package_time')
def check_package_time():
    '''充电套餐到期前三天消息提醒'''
    over_time = timer.get_now_bef_aft(days=-3)  #三天后的时间戳  28到期 25提醒  10点执行   假设说 28 11:00:00
    two_time = timer.get_now_bef_aft(days=-2)  #两天后的时间戳  25 27
    ev_recharge_package_orders = MysqlHelp.getall('*', 'wxapp_recharge_package_order', 'pay_status=20 and order_status=20 and end_time<="{}" and end_time>="{}" and is_use=1'.format(over_time,two_time))

    for package_order in ev_recharge_package_orders:
        ev_settings = MysqlHelp.get('*','wxapp_setting','mini_id={} and title="{}"'.format(package_order['mini_id'],'submsg'))
        values_json = json.loads(ev_settings['values_json'])
        template_id = values_json['order']['expire_notice']['template_id']
        member_miniapp = MysqlHelp.get('*','wxapp_mini','id={}'.format(package_order['mini_id']))
        wx_deve = wx_mini_sdk()
        #订阅消息通知
        data = {
            "thing4": {
                "value": package_order['plan_name']
            },
            "time2": {
                "value": package_order['end_time']
            },
            "thing3": {
                "value": '充电套餐包即将到期，到期后将失去免费充电及停车特权，请及时续费'
            }
        }
        user = MysqlHelp.get('*','wxapp_user','id={}'.format(package_order['user_id']))
        wx_deve.send_tempalte_keyword(member_miniapp['access_token'], user['open_id'], template_id,'pages/user/children/monthly-charge', data)





@app.task(name='check_order_recharge_outtime')
def check_order_recharge_outtime():
    '''检测充电超时-自动下发结束指令'''
    print('检测充电超时-自动下发结束指令')
    ev_orders = MysqlHelp.getall('*', 'wxapp_order','order_status=10')
    for order in ev_orders:
        try:
            piles = MysqlHelp.get('*', 'wxapp_pod_pile', 'id={}'.format(order['pile_id']))
            if order['billtype'] == 2 or order['billtype'] == 4: #充满自停
                now = (time.time() - timer.time2timestamp(order['start_time'].strftime('%Y-%m-%d %H:%M:%S')))/60  #分钟
                if now > 710:
                    data = {}
                    data['token'] = 'qfevserver'
                    data['type'] = piles['type']
                    data['ip'] = piles['lastip']
                    data['duration'] = now
                    data['pattern'] = '1'
                    data['portnum'] = order['portnum']
                    data['command'] = 'ev_over_recharge'
                    data['serialnum'] = piles['serialnum']
                    data['onlytag'] = piles['gateway_id']
                    data['snum'] = piles['snum']
                    sock_data = 'evapi|{}'.format(json.dumps(data))

                    server1 = TCPClient(TCP_PORT)
                    server1.send_msg(sock_data)
                    try:
                        server1.recv_msg()
                    except:
                        pass
                    server1.close()
                    MysqlHelp.update('wxapp_order', 'order_status=11,end_time="{}",update_time="{}"'.format(timer.get_now(),timer.get_now()),
                                     'id={}'.format(order['id']))
            else:
                recharge_time = timer.time2timestamp(order['start_time'].strftime('%Y-%m-%d %H:%M:%S')) + order['recharge_time'] * 3600
                if time.time() >= recharge_time:
                    data = {}
                    data['token'] = 'qfevserver'
                    data['type'] = piles['type']
                    data['ip'] = piles['lastip']
                    data['duration'] = order['recharge_time'] * 60
                    data['pattern'] = '2'
                    data['portnum'] = order['portnum']
                    data['command'] = 'ev_over_recharge'
                    data['serialnum'] = piles['serialnum']
                    data['onlytag'] = piles['gateway_id']
                    data['snum'] = piles['snum']
                    data['command'] = 'ev_over_recharge'
                    sock_data = 'evapi|{}'.format(json.dumps(data))

                    server1 = TCPClient(TCP_PORT)
                    server1.send_msg(sock_data)
                    try:
                        server1.recv_msg()
                    except:
                        pass
                    server1.close()
                    MysqlHelp.update('wxapp_order', 'order_status=11,end_time="{}",update_time="{}"'.format(timer.get_now(),timer.get_now()), 'id={}'.format(order['id']))
        except:
            pass



@app.task(name='create_table_time')
def create_table_time():
    otherStyleTime = timer.get_now('%Y_%m_%d %H:%M:%S')[:10]
    table_name = 'wxapp_pod_port_electric_{}'.format(otherStyleTime) #电流表
    sql = """
            id int PRIMARY KEY AUTO_INCREMENT,
            mini_id int,
            pile_id int,
            serialnum varchar(50),
            portnum int,
            portvoltage int,
            portelectric int,
            portpulse int,
            power int,
            rechargetime int,
            add_time datetime
        """
    from celery_task.sql_orm import MysqlHelp
    MysqlHelp.create(table_name, sql)
    MysqlHelp.insert(table_name, 'id,mini_id,pile_id,serialnum,portnum,portvoltage,portelectric,portpulse,power,rechargetime,add_time','1,1,1,1,1,1,1,1,1,1,"{}"'.format(timer.get_now()))



@app.task(name='create_day_table_time')
def create_day_table_time():
    otherStyleTime = timer.get_now_bef_aft(days=-1)[:10].replace('-','_')
    table_name = 'wxapp_pod_port_electric_{}'.format(otherStyleTime) #电流表
    sql = """
            id int PRIMARY KEY AUTO_INCREMENT,
            mini_id int,
            pile_id int,
            serialnum varchar(50),
            portnum int,
            portvoltage int,
            portelectric int,
            portpulse int,
            power int,
            rechargetime int,
            add_time datetime
        """
    from celery_task.sql_orm import MysqlHelp
    MysqlHelp.create(table_name, sql)
    MysqlHelp.insert(table_name, 'id,mini_id,pile_id,serialnum,portnum,portvoltage,portelectric,portpulse,power,rechargetime,add_time','1,1,1,1,1,1,1,1,1,1,"{}"'.format(timer.get_now()))



@app.task(name='check_order_status')
def check_order_status():
    '''检查充电订单状态--退款'''
    print('检查充电订单状态--退款')
    starttime = timer.get_now_bef_aft(seconds=1800)
    ev_orders = MysqlHelp.getall('*', 'wxapp_order','pay_status=20 and (order_status=0 or order_status=11) and pay_price!=0 and start_time>"{}"'.format(starttime))
    for order in ev_orders:
        if order['pay_type'] == 20:
            member_payinfo = MysqlHelp.get('*','wxapp_payinfo','mini_id={}'.format(order['mini_id']))
            total_fee = int(order['pay_price'] * 100)
            out_refund_no = f"{timer.get_now(format='%Y%m%d%H%M%S')}{order['user_id']}"
            try:
                if member_payinfo['pay_type'] == 1:
                    notify_url = f'{REQ_HOST}/api/wx_order_fefunds_payback/{member_payinfo["orgid"]}'
                    results = wx_pay_sdk().refunds_v3(order['transaction_id'], out_refund_no, total_fee, total_fee,
                                                      member_payinfo['mchid'],
                                                      member_payinfo['apikey'], member_payinfo['key_pem'], notify_url)
                elif member_payinfo['pay_type'] == 2:
                    tl_pay = tl_pay_sdk()
                    resp = tl_pay.tl_refunds(member_payinfo['orgid'], member_payinfo['mchid'], member_payinfo['apikey'],
                                             total_fee, out_refund_no, order['transaction_id'], member_payinfo['key_pem'])
                    if resp['retcode'] == 'SUCCESS':
                        if resp['trxstatus'] == '0000':
                            trxid = resp['trxid']  # 收银宝交易单号
                            MysqlHelp.update('wxapp_order',
                                             'order_status=20,is_invalid=1,pay_status=30,refund_id="{}",refund_time="{}",end_time="{}"'.format(trxid,timer.get_now(),timer.get_now()),
                                             'id={}'.format(order['id']))
                MysqlHelp.update('wxapp_order','order_status=20,residue_money={}'.format(order['pay_price']),'id={}'.format(order['id']))
            except BaseException:
                print('退款异常')
        elif order['pay_type'] == 10:
            user = MysqlHelp.get('*','wxapp_user','id={}'.format(order['user_id']))
            balance = user['balance'] + order['pay_price']
            MysqlHelp.update('wxapp_user', 'balance={}'.format(balance),'id={}'.format(order['user_id']))
            MysqlHelp.update('wxapp_order', 'pay_status=30,order_status=20,residue_money={},refund_time="{}",end_time="{}"'.format(order['pay_price'],timer.get_now(),timer.get_now()),'id={}'.format(order['id']))



def over_chrange(order):
    try:
        time.sleep(3)
        piles = MysqlHelp.get('*', 'wxapp_pod_pile', 'id={}'.format(order['pile_id']))
        data = {}
        if order['billtype'] == 2 or order['billtype'] == 4:  # 充满自停
            data['pattern'] = '1'
        else:
            data['pattern'] = '2'
        data['token'] = 'qfevserver'
        data['type'] = piles['type']
        data['ip'] = piles['lastip']
        data['duration'] = order['recharge_time'] * 60
        data['portnum'] = order['portnum']
        data['command'] = 'ev_over_recharge'
        data['serialnum'] = piles['serialnum']
        data['onlytag'] = piles['gateway_id']
        data['snum'] = piles['snum']
        sock_data = 'evapi|{}'.format(json.dumps(data))

        server1 = TCPClient(TCP_PORT)
        server1.send_msg(sock_data)
        try:
            server1.recv_msg()
        except:
            pass
        server1.close()
        MysqlHelp.update('wxapp_order',
                         'order_status=11,end_time="{}",update_time="{}"'.format(timer.get_now(), timer.get_now()),
                         'id={}'.format(order['id']))
    except:
        pass



@app.task(name='check_order_fail_refund')
def check_order_fail_refund():
    '''检查启动中(充电失败)订单--退款'''
    print('检查启动中(充电失败)订单--退款')
    ev_orders = MysqlHelp.getall('*', 'wxapp_order','pay_status=20 and (order_status=1 or order_status=30) and pay_price!=0 and start_time<"{}"'.format(timer.get_now_bef_aft(seconds=90)))
    for order in ev_orders:
        MysqlHelp.update('wxapp_pod_pileport', 'portstatus=0', 'id={}'.format(order['pileport_id']))

        if order['pay_type'] == 20:
            member_payinfo = MysqlHelp.get('*','wxapp_payinfo','mini_id={}'.format(order['mini_id']))
            total_fee = int(order['pay_price'] * 100)
            out_refund_no = f"{timer.get_now(format='%Y%m%d%H%M%S')}{order['user_id']}"
            MysqlHelp.update('wxapp_order', 'end_time="{}"'.format(timer.get_now()), 'id={}'.format(order['id']))
            try:
                if member_payinfo['pay_type'] == 1:
                    notify_url = f'{REQ_HOST}/api/wx_order_fefunds_payback/{member_payinfo["orgid"]}'
                    results = wx_pay_sdk().refunds_v3(order['transaction_id'],out_refund_no, total_fee, total_fee,member_payinfo['mchid'],
                                                      member_payinfo['apikey'], member_payinfo['key_pem'],notify_url)
                    try:
                        if results.status_code == 400:
                            data = json.loads(results.text)
                            if data['code'] == 'INVALID_REQUEST' and data['message'] == '订单已全额退款':
                                MysqlHelp.update('wxapp_order', 'residue_money={},order_status=20,pay_status=30,refund_time="{}",end_time="{}",user_received_account="异常"'.format(order['pay_price'],timer.get_now(),timer.get_now()), 'id={}'.format(order['id']))
                    except:
                        pass
                elif member_payinfo['pay_type'] == 2:
                    tl_pay = tl_pay_sdk()
                    resp = tl_pay.tl_refunds(member_payinfo['orgid'], member_payinfo['mchid'], member_payinfo['apikey'],
                                             total_fee, out_refund_no, order['transaction_id'], member_payinfo['key_pem'])
                    if resp['retcode'] == 'SUCCESS':
                        if resp['trxstatus'] == '0000':
                            trxid = resp['trxid']  # 收银宝交易单号
                            MysqlHelp.update('wxapp_order',
                                             'order_status=20,is_invalid=1,pay_status=30,refund_id="{}",refund_time="{}",end_time="{}"'.format(trxid,timer.get_now(),timer.get_now()),
                                             'id={}'.format(order['id']))
                MysqlHelp.update('wxapp_order', 'order_status=20,residue_money={}'.format(order['pay_price']),'id={}'.format(order['id']))
            except BaseException:
                print('退款异常')
        elif order['pay_type'] == 10:
            user = MysqlHelp.get('*','wxapp_user','id={}'.format(order['user_id']))
            balance = user['balance'] + order['pay_price']
            MysqlHelp.update('wxapp_user', 'balance={}'.format(balance),'id={}'.format(order['user_id']))
            MysqlHelp.update('wxapp_order', 'pay_status=30,order_status=20,residue_money={},end_time="{}"'.format(order['pay_price'],timer.get_now()),'id={}'.format(order['id']))
        elif order['pay_type'] == 60:
            user = MysqlHelp.get('*', 'wxapp_user', 'id={}'.format(order['user_id']))
            balance = user['virtual_balance'] + order['pay_price']
            MysqlHelp.update('wxapp_user', 'virtual_balance={}'.format(balance), 'id={}'.format(order['user_id']))
            MysqlHelp.update('wxapp_order','pay_status=30,order_status=20,residue_money={},end_time="{}"'.format(order['pay_price'],timer.get_now()),'id={}'.format(order['id']))

        over_chrange(order)



    ev_orders = MysqlHelp.getall('*', 'wxapp_order','order_status=1 and (billtype=2 or pay_price=0) and start_time<"{}"'.format(timer.get_now_bef_aft(seconds=60)))
    for order in ev_orders:
        if order['pay_type'] == 30:
            ev_recharge_package_order = MysqlHelp.getall('*', 'wxapp_recharge_package_order', 'user_id={} and note_id={} and pay_status=20 and is_use=1 and type=2'.format(order['user_id'],order['note_id']))
            if ev_recharge_package_order:
                ev_recharge_package_order = ev_recharge_package_order[0]
                residue_time = ev_recharge_package_order['residue_time'] + order['recharge_time']
                MysqlHelp.update('wxapp_recharge_package_order','residue_time={}'.format(residue_time),'id={}'.format(ev_recharge_package_order['id']))
        MysqlHelp.update('wxapp_order','order_status=20,end_time="{}"'.format(timer.get_now()),'id={}'.format(order['id']))
        MysqlHelp.update('wxapp_pod_pileport', 'portstatus=0', 'id={}'.format(order['pileport_id']))
        
        over_chrange(order)



@app.task(name='check_order_fefund_update')
def check_order_fefund_update():
    '''检查订单退款记录更新是否成功'''
    ev_orders = MysqlHelp.getall('*', 'wxapp_order','pay_status=20 and residue_money!=0 and is_invalid=1 and is_settled=0 and add_time<"{}"'.format(timer.get_now()))
    for order in ev_orders:
        user_balance_logs = MysqlHelp.getall('*', 'wxapp_user_balance_log','user_id={} and note_id={} and type=1 and scene=40 and start_time="{}"'.format(order['user_id'],order['note_id'],order['start_time']))
        if user_balance_logs:
            MysqlHelp.update('wxapp_order', 'pay_status=30','id={}'.format(order['id']))



@app.task(name='auto_recharge_package_order')
def auto_recharge_package_order():
    """自动续期"""
    package_order = MysqlHelp.getall('*','wxapp_recharge_package_order',f'pay_status=20 and order_status=20 and is_auto_renew=1 and DATE(end_time)="{timer.get_day()}"')
    for order in package_order:
        user = MysqlHelp.get('*','wxapp_user',f'id={order["user_id"]}')
        package = MysqlHelp.get('*','wxapp_recharge_package',f"id={order['package_id']}")
        order_id = f"{timer.get_now(format='%Y%m%d%H%M%S')}{order['user_id']}"
        note = MysqlHelp.get('*','wxapp_note',f"id={package['note_id']}")
        money = package['money']
        days = package['days'] + 1
        recharge_time = package['recharge_time'] + package['gift_recharge_time']
        end_time = timer.get_now_bef_aft(now=order['end_time'].strftime("%Y-%m-%d %H:%M:%S"), days=-days)
        if note['is_ind_dealer'] == 1:  # 开启单独分成
            first_proportion = note['first_proportion']
            second_proportion = note['second_proportion']
        else:
            values_json = get_settings(order['mini_id'], 'settlement')
            first_proportion = int(values_json.get('first_proportion',0))  # 一级分成比例
            second_proportion = int(values_json.get('second_proportion',0))  # 二级分成比例

        first_proportion_money = money * (first_proportion / 100)  # 一级（代理商）分成
        second_proportion_money = money * (second_proportion / 100)  # 二级（物业）分成
        if user['balance'] < package['money']:
            continue
        else:
            sob_handle = sob.sql_open(db_config)
            value_info = {
                'order_id': order_id,
                'mini_id': order['mini_id'],
                'note_id': order['note_id'],
                'user_id': order['user_id'],
                'packageorder_id': order['id'],
                'start_time': str(order['end_time']),
                'end_time': end_time,
                'pay_type': 10,
                'pay_price': money,
                'pay_status':20,
                'order_status':20,
                'pay_time':timer.get_now(),
                'first_proportion_money': first_proportion_money,
                'second_proportion_money': second_proportion_money,
            }
            lastrowid = sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_recharge_package_order_renew',
                                                                   [value_info])
            cmd = f"update wxapp_user set balance=balance-{money} where id={order['user_id']}"
            sob.update_mysql_record(sob_handle, cmd)

            value_info = {
                'mini_id': order['mini_id'],
                'note_id': order['note_id'],
                'type': 1,
                'user_id': order['user_id'],
                'scene': 21,
                'money': money,
                'describes': '充电消费(钱包扣款)',
                'add_time':timer.get_now()
            }
            sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
            cmd = f"update wxapp_order set pay_status=20,pay_price=0 where note_id={order['note_id']} and user_id={order['user_id']} and pay_status=10"
            sob.update_mysql_record(sob_handle, cmd)

            cmd = f"update wxapp_recharge_package_order set end_time='{end_time}',recharge_time=recharge_time+{recharge_time},residue_time=residue_time+{recharge_time},is_use=1,is_renew=1 where id={order['id']}"
            sob.update_mysql_record(sob_handle, cmd)

            calc_proportion_money(second_proportion_money, first_proportion_money, order['note_id'],order['mini_id'], lastrowid, money)
            sob.sql_close(sob_handle)


@app.task(name='check_package_order_expird')
def check_package_order_expird():
    '''检测套餐包是否到期'''
    package_order_exipre = MysqlHelp.getall('*','wxapp_recharge_package_order',f'pay_status=20 and order_status=20 and is_use=1 and end_time<"{timer.get_now()}"')
    for order in package_order_exipre:
        MysqlHelp.update('wxapp_recharge_package_order', 'is_use=0', 'id={}'.format(order['id']))





@app.task(name='order_restart_rechage')
def order_restart_rechage():
    """启动中的订单-重新下发"""
    print('重新下发')
    start_time = timer.get_now_bef_aft(seconds=15) #已经启动15秒的订单重新下发指令
    ev_orders = MysqlHelp.getall('*', 'wxapp_order', f'order_status=1 and start_time<="{start_time}"')
    for order in ev_orders:
        try:
            piles = MysqlHelp.get('*', 'wxapp_pod_pile', 'id={}'.format(order['pile_id']))
            data = {}
            if order['billtype'] == 2 or order['billtype'] == 4:  # 充满自停
                data['pattern'] = '1'
            else:
                data['pattern'] = '2'
            data['token'] = 'qfevserver'
            data['type'] = piles['type']
            data['ip'] = piles['lastip']
            data['duration'] = order['recharge_time'] * 60
            data['portnum'] = order['portnum']
            data['serialnum'] = piles['serialnum']
            data['onlytag'] = piles['gateway_id']
            data['snum'] = piles['snum']
            data['command'] = 'recharge'
            sock_data = 'evapi|{}'.format(json.dumps(data))

            server1 = TCPClient(TCP_PORT)
            server1.send_msg(sock_data)
            try:
                server1.recv_msg()
            except:
                pass
            server1.close()
            MysqlHelp.update('wxapp_order','order_status=1,start_time="{}",update_time="{}"'.format(timer.get_now(),timer.get_now()),
                             'id={}'.format(order['id']))
        except:
            pass


@app.task(name='order_over_rechage')
def order_over_rechage():
    """结束充电-结束中"""
    print('结束充电-结束中')
    end_time = timer.get_now_bef_aft(seconds=10) #已经结束10秒还没完成的订单再次下发结束
    ev_orders = MysqlHelp.getall('*', 'wxapp_order', f'order_status=11 and end_time<="{end_time}"')
    for order in ev_orders:
        try:
            piles = MysqlHelp.get('*', 'wxapp_pod_pile', 'id={}'.format(order['pile_id']))
            data = {}
            if order['billtype'] == 2 or order['billtype'] == 4:  # 充满自停
                data['pattern'] = '1'
            else:
                data['pattern'] = '2'
            data['token'] = 'qfevserver'
            data['type'] = piles['type']
            data['ip'] = piles['lastip']
            data['duration'] = order['recharge_time'] * 60
            data['portnum'] = order['portnum']
            data['command'] = 'ev_over_recharge'
            data['serialnum'] = piles['serialnum']
            data['onlytag'] = piles['gateway_id']
            data['snum'] = piles['snum']
            sock_data = 'evapi|{}'.format(json.dumps(data))

            server1 = TCPClient(TCP_PORT)
            server1.send_msg(sock_data)
            try:
                server1.recv_msg()
            except:
                pass
            server1.close()
            MysqlHelp.update('wxapp_order','order_status=11,end_time="{}",update_time="{}"'.format(timer.get_now(),timer.get_now()),
                             'id={}'.format(order['id']))
        except:
            pass