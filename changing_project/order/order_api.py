import json
from datetime import datetime, date

from pydantic import BaseModel, Field

from celery_task.sql_orm import MysqlHelp
from config import db_config, TCP_PORT, REQ_HOST
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.normal_func import invalid_dealer_order
from tool.tcpc import TCPClient
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
    order_status: int = Field(None, description="订单状态(0未开始充电 1启动中 10充电中 11结束中 20充电结束 30充电失败)")
    pay_status: int = Field(None, description="支付状态(10待支付 20已支付 30已退款 40退款异常)")
    snum: str = Field(None, description="设备SN编码")
    portnum: int = Field(None, description="端口编号")
    id: int = Field(None, description="id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    end_time: date = Field(None, description="结束时间")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    note_id = request_data['note_id']
    user_id = request_data['user_id']
    order_status = request_data['order_status']
    snum = request_data['snum']
    portnum = request_data['portnum']
    pay_status = request_data['pay_status']
    keyword = request_data['keyword']
    end_time = request_data['end_time']
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
    if order_status:
        where_lst.append(f"order_status={order_status}")
    if snum:
        where_lst.append(f"snum='{snum}'")
    if portnum:
        where_lst.append(f"portnum='{portnum}'")
    if pay_status:
        where_lst.append(f"pay_status={pay_status}")
    if end_time:
        where_lst.append(f"DATE(end_time)='{end_time}'")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%' or snum like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _order_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*,
               nickname,avatar,note_name,mobile,
               count(*) over() as total
            from
               wxapp_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_note c
            on a.note_id=c.id
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



#【订单列表】
def order_list(request_data: QueryFilterFormat):
    try:
        res = _order_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



class DeleteFilterFormat(BaseModel):
    order_id: int = Field(None, description="订单id")

def _delete_order(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_order where id={request_data.order_id}"
    sob.delete_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return


#【删除订单】
def delete_order(request_data: DeleteFilterFormat):
    try:
        res = _delete_order(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


def _order_over(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    end_time = timer.get_now()
    cmd = f"update wxapp_order set order_status=11,end_time='{end_time}' where id={request_data.order_id}"
    sob.update_mysql_record(sob_handle,cmd)
    cmd = f"select * from wxapp_order where id={request_data.order_id}"
    order = sob.select_mysql_record(sob_handle,cmd)
    order = order[0]
    cmd = f"select * from wxapp_pod_pile where id={order['pile_id']}"
    pod_pile = sob.select_mysql_record(sob_handle,cmd)
    pod_pile = pod_pile[0]
    sob.sql_close(sob_handle)
    pattern = '2'
    if order['billtype'] == 2:
        pattern = '1'
    if not order['recharge_time']:
        recharge_time = (timer.time2timestamp(end_time) - timer.time2timestamp(order['start_time'].strftime('%Y-%m-%d %H:%M:%S'))) / 360
    else:
        recharge_time = order['recharge_time']
    data = {}
    data['token'] = 'qfevserver'
    data['type'] = pod_pile['type']
    data['ip'] = pod_pile['lastip']
    data['duration'] = recharge_time * 60
    data['pattern'] = pattern
    data['portnum'] = order['portnum']
    data['serialnum'] = pod_pile['serialnum']
    data['onlytag'] = pod_pile['gateway_id']
    data['snum'] = pod_pile['snum']
    data['command'] = 'ev_over_recharge'
    sock_data = 'evapi|{}'.format(json.dumps(data))

    server1 = TCPClient(TCP_PORT)
    server1.send_msg(sock_data)
    try:
        resp = server1.recv_msg()
        resp = json.loads(resp)
        server1.close()
        return resp
    except:
        print('接收数据失败')
        server1.close()
        return {'msg': '结束异常', 'status': 400}

#【结束充电】
def order_over(request_data: DeleteFilterFormat):
    try:
        res = _order_over(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



class RefundFilterFormat(BaseModel):
    order_id: int = Field(..., description="订单id")
    residue_type: int = Field(..., description="退款方式 10余额 20微信 30套餐 40虚拟")
    residue_money: float = Field(..., description="退款金额")


def _order_refunds(request_data: RefundFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_order where id={request_data.order_id}"
    order = sob.select_mysql_record(sob_handle,cmd)
    order = order[0]
    if order['pay_status'] != 20:
        raise ValueError('该订单不能退款...')
    if order['order_status'] == 10:
        raise ValueError('该订单正在充电中...')
    residue_type = request_data.residue_type
    residue_money = request_data.residue_money
    if residue_money:
        if residue_money > order['pay_price']:
            raise ValueError('超出允许退款最大金额...')
    if residue_type == 10:  # 余额支付
        cmd = f"update wxapp_order set fefund_type=1,is_invalid=1,pay_status=30,residue_money={residue_money},refund_time='{timer.get_now()}' where id={request_data.order_id}"
        sob.update_mysql_record(sob_handle,cmd)
        cmd = f"update wxapp_user set balance=balance+{residue_money} where id={order['user_id']}"
        sob.update_mysql_record(sob_handle,cmd)
        value_info = {
            'mini_id': order['mini_id'],
            'note_id': order['note_id'],
            'type': 1,
            'start_time': str(order['start_time']),
            'end_time': str(order['end_time']),
            'user_id': order['user_id'],
            'scene': 40,
            'money': residue_money,
            'describes': '订单退款到钱包(充电时长不足)',
            'add_time': timer.get_now()
        }
        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
        invalid_dealer_order(order)
    elif residue_type == 40:  # 虚拟余额支付
        cmd = f"update wxapp_order set fefund_type=1,is_invalid=1,pay_status=30,residue_money={residue_money},refund_time='{timer.get_now()}' where id={request_data.order_id}"
        sob.update_mysql_record(sob_handle, cmd)
        cmd = f"update wxapp_user set virtual_balance=virtual_balance+{residue_money} where id={order['user_id']}"
        sob.update_mysql_record(sob_handle, cmd)
        value_info = {
            'mini_id': order['mini_id'],
            'note_id': order['note_id'],
            'type': 1,
            'start_time': str(order['start_time']),
            'end_time': str(order['end_time']),
            'user_id': order['user_id'],
            'scene': 40,
            'money': residue_money,
            'describes': '订单退款到虚拟钱包(充电时长不足)',
            'add_time': timer.get_now()
        }
        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_user_balance_log', [value_info])
        invalid_dealer_order(order)
    elif residue_type == 20:  # 微信支付
        cmd = f"select * from wxapp_payinfo where mini_id={order['mini_id']}"
        payinfo = sob.select_mysql_record(sob_handle, cmd)
        if payinfo:
            payinfo = payinfo[0]
            out_refund_no = f"{timer.get_now('%Y%m%d%H%M%S')}{order['user_id']}"
            total_fee = int(residue_money * 100)
            total = int(order['total_price'] * 100)
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
                        cmd = f"update wxapp_order set order_status=20,refund_type=1,is_invalid=1,pay_status=30,residue_money={residue_money},refund_id='{trxid}',refund_time='{timer.get_now()}' where id={order['id']}"
                        sob.update_mysql_record(sob_handle, cmd)
                        value_info = {
                            'mini_id': order['mini_id'],
                            'note_id': order['note_id'],
                            'type': 1,
                            'start_time': str(order['start_time']),
                            'end_time': timer.get_now(),
                            'user_id': order['user_id'],
                            'scene': 40,
                            'money': residue_money,
                            'describes': '订单退款到通联(充电时长不足)',
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
                with open("./c.txt", "a+", encoding="utf8") as f:
                    f.write(str(notify_url))
                    f.write("\n")
                wx_pay_sdk().refunds_v3(order['transaction_id'], out_refund_no,
                                        total_fee, total, payinfo['mchid'], payinfo['apikey'],payinfo['key_pem'], notify_url)
                cmd = f"update wxapp_order set residue_money={order['pay_price']},refund_type=1 where id={order['id']}"
                sob.update_mysql_record(sob_handle, cmd)
        else:
            prolog.error('支付信息不完善，退款失败')
    else:
        cmd = f"update wxapp_recharge_package_order set residue_time=residue_time+{order['recharge_time']} " \
              f"where user_id={order['user_id']} and type=2 and start_time<='{timer.get_now()}' and end_time>='{timer.get_now()}' and order_status=20"
        sob.update_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    return ''




#【充电时长不足-退款】
def order_refunds(request_data: RefundFilterFormat):
    try:
        res = _order_refunds(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

def _order_electric(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_order where id={request_data.order_id}"
    order = sob.select_mysql_record(sob_handle,cmd)
    order = order[0]

    if order['order_status'] == 20:
        end_time = timer.get_now_bef_aft(now=order['end_time'].strftime("%Y-%m-%d %H:%M:%S"),seconds=60)
    elif order['order_status'] == 10:
        end_time = timer.get_now_bef_aft(seconds=60)
    else:
        end_time = str(order['end_time'])
    end_otherStyleTime = end_time[:10]
    start_time = str(order['start_time'])
    start_otherStyleTime = start_time[:10]
    if order['order_status'] == 20:
        table_name = f'wxapp_pod_port_electric_{end_otherStyleTime}'
        table_name = table_name.replace('-','_')
        pod_port_electric = MysqlHelp.getall('*', table_name,
                                             'mini_id="{}" and pile_id="{}" and portnum="{}" and add_time="{}"'.format(
                                                 order['mini_id'], order['pile_id'], order['portnum'],
                                                 order['end_time']))
        if not pod_port_electric:
            MysqlHelp.insert(table_name,
                             'mini_id,pile_id,serialnum,portnum,portvoltage,portelectric,portpulse,add_time',
                             '{},{},"{}",{},{},{},"{}","{}"'.format(order['mini_id'], order['pile_id'],
                                                                      order['snum'],
                                                                      order['portnum'], order['powerwaste'],
                                                                      order['endelectric'], order['portpulse'],
                                                                      order['end_time']))

    try:
        if start_otherStyleTime == end_otherStyleTime:
            table_name = f'wxapp_pod_port_electric_{end_otherStyleTime}'
            table_name = table_name.replace('-', '_')
            ev_pod_port_electric = MysqlHelp.getall('*', table_name,
                                                    'mini_id={} and pile_id={} and portnum="{}" and add_time>"{}" and add_time<"{}"'.format(
                                                        order['mini_id'],
                                                        order['pile_id'], order['portnum'],
                                                        start_time, end_time))
            print(ev_pod_port_electric)
        else:
            end_other = end_otherStyleTime.replace('-', '_')
            start_other = start_otherStyleTime.replace('-', '_')
            ev_pod_port_electric = MysqlHelp.getall('*', 'wxapp_pod_port_electric_{}'.format(start_other),
                                                    'mini_id={} and pile_id={} and portnum="{}" and add_time>"{}" and add_time<"{}"'.format(
                                                        order['mini_id'], order['pile_id'], order['portnum'],
                                                        start_time, end_time))
            ev_pod_port_electric2 = MysqlHelp.getall('*', 'wxapp_pod_port_electric_{}'.format(end_other),
                                                     'mini_id={} and pile_id={} and portnum="{}" and add_time>"{}" and add_time<"{}"'.format(
                                                         order['mini_id'], order['pile_id'], order['portnum'],
                                                         start_time, end_time))
            ev_pod_port_electric = ev_pod_port_electric + ev_pod_port_electric2

    except:
        ev_pod_port_electric = []
    sob.sql_close(sob_handle)
    return {'ev_pod_port_electric': ev_pod_port_electric}


#【电流图】
def order_electric(request_data: DeleteFilterFormat):
    # try:
        res = _order_electric(request_data)
        response = format_response_data(res)
        return response
    # except Exception as exc:
    #     return {"status": 400, "msg": exc.__str__()}



