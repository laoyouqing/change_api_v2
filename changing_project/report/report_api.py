from datetime import datetime

from glom import glom
from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()


class ReportFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    note_id: int = Field(None, description="社区id")
    pile_id: int = Field(None, description="设备id")
    start_time: datetime = Field(None, description="开始时间")
    end_time: datetime = Field(None, description="结束时间")



def _data_report_total(request_data: ReportFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select count(*) as total from wxapp_note where mini_id={request_data.mini_id}"
    note = sob.select_mysql_record(sob_handle,cmd)
    note = note[0]['total']
    cmd = f"select count(*) as total from wxapp_pod_pile a left join wxapp_pod_pileport b on a.id=b.pile_id where a.mini_id={request_data.mini_id}"
    port_total = sob.select_mysql_record(sob_handle,cmd)
    port_total = port_total[0]['total']
    cmd = f"select count(*) as total from wxapp_pod_pile a left join wxapp_pod_pileport b on a.id=b.pile_id where a.mini_id={request_data.mini_id} and isonline=1"
    online_port = sob.select_mysql_record(sob_handle,cmd)
    online_port = online_port[0]['total']
    not_online_port = port_total - online_port
    # 充电成交额
    cmd = f"select sum(pay_price) as pay_price from wxapp_order where mini_id={request_data.mini_id} and pay_type=20 and pay_status=20"
    order_sale = sob.select_mysql_record(sob_handle,cmd)
    order_sale = order_sale[0]['pay_price']
    order_sale = order_sale if order_sale else 0

    # 充值包成交额
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_order where mini_id={request_data.mini_id} and pay_type=10 and pay_status=20 and is_refund=1"
    recharge_sale = sob.select_mysql_record(sob_handle, cmd)
    recharge_sale = recharge_sale[0]['pay_price']
    recharge_sale = recharge_sale if recharge_sale else 0
    # 套餐包成交额
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where mini_id={request_data.mini_id} and pay_type=20 and pay_status=20 and (order_status=20 or order_status=30)"
    package_sale = sob.select_mysql_record(sob_handle, cmd)
    package_sale = package_sale[0]['pay_price']
    package_sale = package_sale if package_sale else 0
    # 续费包成交额
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where mini_id={request_data.mini_id} and pay_type=20 and pay_status=20 and (order_status=20 or order_status=30)"
    renew_package_sale = sob.select_mysql_record(sob_handle, cmd)
    renew_package_sale = renew_package_sale[0]['pay_price']
    renew_package_sale = renew_package_sale if renew_package_sale else 0
    # 门禁交额
    cmd = f"select sum(money) as pay_price from wxapp_user_door_log where mini_id={request_data.mini_id} and pay_status=2 and pay_type=4"
    door_sale = sob.select_mysql_record(sob_handle, cmd)
    door_sale = door_sale[0]['pay_price']
    door_sale = door_sale if door_sale else 0

    sum_total = order_sale + recharge_sale + package_sale + renew_package_sale + door_sale
    #充电订单数
    cmd = f"select count(*) as total from wxapp_order where mini_id={request_data.mini_id}"
    order_total = sob.select_mysql_record(sob_handle,cmd)
    order_total = order_total[0]['total']
    # 充电用户数
    cmd = f"SELECT count(*) as total from wxapp_user where is_manage=0 and mini_id={request_data.mini_id}"
    user_total = sob.select_mysql_record(sob_handle, cmd)
    user_total = user_total[0]['total'] if user_total else 0
    sob.sql_close(sob_handle)
    data = {
        "note":note,
        "port_total":port_total,
        "online_port":online_port,
        "not_online_port":not_online_port,
        "sum_total":round(sum_total,2),
        "order_total":order_total,
        "user_total":user_total,
    }
    return {'data':data}




#【数据报表】
def data_report_total(request_data: ReportFilterFormat):
    try:
        res = _data_report_total(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}




def _country_data_report_total(request_data: ReportFilterFormat):
    sob_handle = sob.sql_open(db_config)
    start_time = request_data.start_time
    end_time = request_data.end_time
    strs = refund_strs = f"mini_id={request_data.mini_id}"
    if start_time:
        strs += ' and pay_time>="{}" and pay_time<"{}"'.format(start_time, end_time)
        refund_strs += ' and refund_time>="{}" and refund_time<"{}"'.format(start_time, end_time)  # 退款时间
    # 充电微信支付(包括退款)
    cmd = f"select sum(total_price) as total_price from wxapp_order where {strs} and pay_type=20 and pay_status!=10"
    order_wx = sob.select_mysql_record(sob_handle,cmd)
    order_wx = order_wx[0]['total_price'] if order_wx[0]['total_price'] else 0
    # 套餐充值
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_order where {strs} and pay_status=20 and transaction_id!=''"
    ev_recharge_price = sob.select_mysql_record(sob_handle, cmd)
    ev_recharge_price = ev_recharge_price[0]['pay_price'] if ev_recharge_price[0]['pay_price'] else 0
    # 充电包微信支付(包括退款)
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {strs} and pay_status=20 and pay_type=20"
    ev_recharge_package_order_wx = sob.select_mysql_record(sob_handle, cmd)
    ev_recharge_package_order_wx = ev_recharge_package_order_wx[0]['pay_price'] if ev_recharge_package_order_wx[0]['pay_price'] else 0
    # 续费包微信支付(包括退款)
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {strs} and pay_status=20 and pay_type=20"
    recharge_package_order_renew_wx = sob.select_mysql_record(sob_handle, cmd)
    recharge_package_order_renew_wx = recharge_package_order_renew_wx[0]['pay_price'] if recharge_package_order_renew_wx[0]['pay_price'] else 0
    # 门禁微信支付(包括退款)
    cmd = f"select sum(money) as total_price from wxapp_user_door_log where {strs} and pay_status=2 and pay_type=4"
    day_pod_door_log_income_num_wx = sob.select_mysql_record(sob_handle, cmd)
    day_pod_door_log_income_num_wx = day_pod_door_log_income_num_wx[0]['total_price'] if day_pod_door_log_income_num_wx[0]['total_price'] else 0
    # 总营收(包括退款)
    count_income = order_wx + ev_recharge_price + ev_recharge_package_order_wx + recharge_package_order_renew_wx + day_pod_door_log_income_num_wx
    # 总订单（充电)
    cmd = f"select count(*) as total from wxapp_order where {strs} and pay_status!=10"
    order_num = sob.select_mysql_record(sob_handle,cmd)
    order_num = order_num[0]['total']
    # 总订单（门禁）
    cmd = f"select count(*) as total from wxapp_user_door_log where {strs} and pay_status!=1"
    day_pod_door_log_income_num = sob.select_mysql_record(sob_handle,cmd)
    day_pod_door_log_income_num = day_pod_door_log_income_num[0]['total']
    # 用户数
    cmd = f"SELECT count(*) as total from (select user_id from wxapp_order where {strs} and pay_status=20 group by user_id) a"
    order_user_num = sob.select_mysql_record(sob_handle,cmd)
    order_user_num = order_user_num[0]['total'] if order_user_num else 0

    # 总充电时长
    cmd = f"select sum(recharge_time) as recharge_time from wxapp_order where {strs} and pay_status=20"
    ordewr_recharge_time = sob.select_mysql_record(sob_handle,cmd)
    ordewr_recharge_time = ordewr_recharge_time[0]['recharge_time'] if ordewr_recharge_time[0]['recharge_time'] else 0
    # 充电退款
    cmd = f"select sum(pay_price) as pay_price from wxapp_order where {refund_strs} and pay_type=20 and pay_status=30 and (pay_price=residue_money or residue_money=0) and refund_id!=''"
    orders_refuse = sob.select_mysql_record(sob_handle,cmd)
    orders_refuse = orders_refuse[0]['pay_price'] if orders_refuse[0]['pay_price'] else 0
    # 套餐充值退款
    cmd = f"select sum(refund_money) as refund_money from wxapp_recharge_order where {refund_strs} and pay_status=20 and pay_type=10 and is_refund=1"
    recharge_price_refund = sob.select_mysql_record(sob_handle,cmd)
    recharge_price_refund = recharge_price_refund[0]['refund_money'] if recharge_price_refund[0]['refund_money'] else 0
    #充电退款(手动)
    cmd = f"select sum(residue_money) as residue_money from wxapp_order where {refund_strs} and pay_type=20 and residue_money!=0 and (pay_status=30 and pay_price>residue_money and refund_id!='' or total_price>pay_price and pay_status=20)"

    orders_refuse_money = sob.select_mysql_record(sob_handle,cmd)
    orders_refuse_money = orders_refuse_money[0]['residue_money'] if orders_refuse_money[0]['residue_money'] else 0

    # 套餐包退款
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {refund_strs} and pay_type=20 and pay_status=20 and order_status=40"
    recharge_package_order_refuse = sob.select_mysql_record(sob_handle,cmd)
    recharge_package_order_refuse = recharge_package_order_refuse[0]['pay_price'] if recharge_package_order_refuse[0]['pay_price'] else 0
    # 续费包退款
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {refund_strs} and pay_status=20 and pay_type=20 and order_status=40"
    recharge_package_order_renew_refuse = sob.select_mysql_record(sob_handle,cmd)
    recharge_package_order_renew_refuse = recharge_package_order_renew_refuse[0]['pay_price'] if recharge_package_order_renew_refuse[0]['pay_price'] else 0
    #门禁微信退款
    cmd = f"select sum(money) as money from wxapp_user_door_log where {refund_strs} and pay_status=3 and pay_type=4"
    pod_door_log_refund = sob.select_mysql_record(sob_handle,cmd)
    pod_door_log_refund = pod_door_log_refund[0]['money'] if pod_door_log_refund[0]['money'] else 0
    count_refund = orders_refuse + orders_refuse_money + recharge_package_order_refuse + recharge_package_order_renew_refuse + recharge_price_refund + pod_door_log_refund  # 退款金额
    count_income = count_income - count_refund  # 减去退款

    # 充电余额支付
    cmd = f"select sum(pay_price) as pay_price from wxapp_order where {strs} and pay_type=10 and pay_status=20"
    order_wallet = sob.select_mysql_record(sob_handle,cmd)
    order_wallet = order_wallet[0]['pay_price'] if order_wallet[0]['pay_price'] else 0
    # 充电包余额支付
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {strs} and pay_status=20 and pay_type=10 and order_status=20"
    ev_recharge_package_order_wallet = sob.select_mysql_record(sob_handle,cmd)
    ev_recharge_package_order_wallet = ev_recharge_package_order_wallet[0]['pay_price'] if ev_recharge_package_order_wallet[0]['pay_price'] else 0
    # 续费包余额支付
    cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {strs} and pay_status=20 and pay_type=10 and order_status=20"
    recharge_package_order_renew_wallet = sob.select_mysql_record(sob_handle,cmd)
    recharge_package_order_renew_wallet = recharge_package_order_renew_wallet[0]['pay_price'] if recharge_package_order_renew_wallet[0]['pay_price'] else 0
    # 门禁余额支付
    cmd = f"select sum(money) as money from wxapp_user_door_log where {strs} and pay_status=4"
    day_pod_door_log_income_num_wallet = sob.select_mysql_record(sob_handle,cmd)
    day_pod_door_log_income_num_wallet = day_pod_door_log_income_num_wallet[0]['money'] if day_pod_door_log_income_num_wallet[0]['money'] else 0
    # 余额已消费
    count_wallet = order_wallet + ev_recharge_package_order_wallet + recharge_package_order_renew_wallet + day_pod_door_log_income_num_wallet

    cmd = f"select count(*) as total from wxapp_pod_pileport where mini_id={request_data.mini_id}"
    port_total = sob.select_mysql_record(sob_handle, cmd)
    port_total = port_total[0]['total']
    # try:
    order_income = count_income - day_pod_door_log_income_num_wx + pod_door_log_refund
    print(end_time)
    print(type(end_time))
    print(start_time)
    count_day = (timer.time2timestamp(str(end_time)) - timer.time2timestamp(str(start_time))) / 86400
    apru = order_income / (port_total * count_day)
    use_rate = int(order_num * 100 / (port_total * count_day))
    apru = '%.2f' % apru
    count_income = '%.2f' % count_income
    count_refund = '%.2f' % count_refund
    # except:
    #     apru = 0
    #     use_rate = 0
    sob.sql_close(sob_handle)
    data = {'count_income': count_income, 'order_num': order_num,
            'day_pod_door_log_income_num': day_pod_door_log_income_num, 'order_user_num': order_user_num,
            'ev_recharge_price': ev_recharge_price, 'count_wallet': count_wallet,
            'ordewr_recharge_time': ordewr_recharge_time,
            'day_pod_door_log_income_num_wx': day_pod_door_log_income_num_wx, 'apru': apru, 'use_rate': use_rate,
            'count_refund': count_refund}
    return {'data': data}



#【全国数据汇总】
def country_data_report_total(request_data: ReportFilterFormat):
    # try:
        res = _country_data_report_total(request_data)
        response = format_response_data(res)
        return response
    # except Exception as exc:
    #     return {"status": 400, "msg": exc.__str__()}



def _province_data_report_total(request_data: ReportFilterFormat):
    sob_handle = sob.sql_open(db_config)
    start_time = request_data.start_time
    end_time = request_data.end_time
    strs0 = refund_strs0 = f"mini_id={request_data.mini_id}"
    if start_time:
        strs0 += ' and pay_time>="{}" and pay_time<"{}"'.format(start_time, end_time)
        refund_strs0 += ' and refund_time>="{}" and refund_time<"{}"'.format(start_time, end_time)  # 退款时间
    cmd = f"select province_id from wxapp_note where mini_id={request_data.mini_id} group by province_id"
    ev_notes_provinc = sob.select_mysql_record(sob_handle,cmd)
    data = []
    for provinc in ev_notes_provinc:
        cmd = f"select name from wxapp_region where id={provinc['province_id']}"
        region = sob.select_mysql_record(sob_handle,cmd)
        region = region[0]
        cmd = f"select id from wxapp_note where mini_id={request_data.mini_id} and province_id={provinc['province_id']}"
        notes = sob.select_mysql_record(sob_handle,cmd)
        note_ids = ', '.join([str(i['id']) for i in notes])
        print(note_ids)
        strs = strs0 + f' and note_id in ({note_ids})'
        refund_strs = refund_strs0 + f' and note_id in ("{note_ids}")'
        print(strs)

        # # 充电支付
        cmd = f"select sum(total_price) as total_price from wxapp_order where {strs} and (pay_type=10 or pay_type=20) and pay_status!=10"
        order_wx = sob.select_mysql_record(sob_handle,cmd)
        order_wx = order_wx[0]['total_price'] if order_wx[0]['total_price'] else 0
        # 充电包支付
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {strs} and pay_status=20 and pay_type!=40"
        ev_recharge_package_order_wx = sob.select_mysql_record(sob_handle, cmd)
        ev_recharge_package_order_wx = ev_recharge_package_order_wx[0]['pay_price'] if ev_recharge_package_order_wx[0]['pay_price'] else 0
        # 续费包支付
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {strs} and pay_status=20"
        recharge_package_order_renew_wx = sob.select_mysql_record(sob_handle, cmd)
        recharge_package_order_renew_wx = recharge_package_order_renew_wx[0]['pay_price'] if recharge_package_order_renew_wx[0]['pay_price'] else 0
        # 门禁支付
        cmd = f"select sum(money) as total_price from wxapp_user_door_log where {strs} and pay_status=2 and (pay_type=3 or pay_type=4)"
        day_pod_door_log_income_num_wx = sob.select_mysql_record(sob_handle, cmd)
        day_pod_door_log_income_num_wx = day_pod_door_log_income_num_wx[0]['total_price'] if day_pod_door_log_income_num_wx[0]['total_price'] else 0
        # 总营收(包括退款)
        count_income = order_wx + ev_recharge_package_order_wx + recharge_package_order_renew_wx + day_pod_door_log_income_num_wx
        # 总订单（充电)
        cmd = f"select count(*) as total from wxapp_order where {strs} and pay_status!=10"
        order_num = sob.select_mysql_record(sob_handle,cmd)
        order_num = order_num[0]['total']
        # 总订单（门禁）
        cmd = f"select count(*) as total from wxapp_user_door_log where {strs} and pay_status!=1"
        day_pod_door_log_income_num = sob.select_mysql_record(sob_handle,cmd)
        day_pod_door_log_income_num = day_pod_door_log_income_num[0]['total']
        # 用户数
        cmd = f"select count(*) as total from (select user_id total from wxapp_order where {strs} and pay_status=20 group by user_id) a"
        order_user_num = sob.select_mysql_record(sob_handle,cmd)
        order_user_num = order_user_num[0]['total'] if order_user_num else 0
        # 总充电时长
        cmd = f"select sum(recharge_time) as recharge_time from wxapp_order where {strs} and pay_status=20"
        ordewr_recharge_time = sob.select_mysql_record(sob_handle,cmd)
        ordewr_recharge_time = ordewr_recharge_time[0]['recharge_time'] if ordewr_recharge_time[0]['recharge_time'] else 0
        # 充电退款
        cmd = f"select sum(pay_price) as pay_price from wxapp_order where {refund_strs} and pay_status=30 and (pay_price=residue_money or residue_money=0) and (pay_type=10 or pay_type=20)"
        orders_refuse = sob.select_mysql_record(sob_handle,cmd)
        orders_refuse = orders_refuse[0]['pay_price'] if orders_refuse[0]['pay_price'] else 0
        #充电退款(手动)
        cmd = f"select sum(residue_money) as residue_money from wxapp_order where {refund_strs} and residue_money!=0 and (pay_status=30 and pay_price>residue_money or total_price>pay_price and pay_status=20) and (pay_type=10 or pay_type=20)"
        orders_refuse_money = sob.select_mysql_record(sob_handle,cmd)
        orders_refuse_money = orders_refuse_money[0]['residue_money'] if orders_refuse_money[0]['residue_money'] else 0

        # 套餐包退款
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {refund_strs} and pay_status=20 and order_status=40"
        recharge_package_order_refuse = sob.select_mysql_record(sob_handle,cmd)
        recharge_package_order_refuse = recharge_package_order_refuse[0]['pay_price'] if recharge_package_order_refuse[0]['pay_price'] else 0
        # 续费包退款
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {refund_strs} and pay_status=20 and order_status=40"
        recharge_package_order_renew_refuse = sob.select_mysql_record(sob_handle,cmd)
        recharge_package_order_renew_refuse = recharge_package_order_renew_refuse[0]['pay_price'] if recharge_package_order_renew_refuse[0]['pay_price'] else 0
        #门禁微信退款
        cmd = f"select sum(money) as money from wxapp_user_door_log where {refund_strs} and pay_status=3 and (pay_type=3 or pay_type=4)"
        pod_door_log_refund = sob.select_mysql_record(sob_handle,cmd)
        pod_door_log_refund = pod_door_log_refund[0]['money'] if pod_door_log_refund[0]['money'] else 0
        count_refund = orders_refuse + orders_refuse_money + recharge_package_order_refuse + recharge_package_order_renew_refuse  + pod_door_log_refund  # 退款金额
        count_income = count_income - count_refund  # 减去退款

        cmd = f"select count(*) as total from wxapp_pod_pileport where mini_id={request_data.mini_id} and note_id in ({note_ids})"
        port_total = sob.select_mysql_record(sob_handle, cmd)
        port_total = port_total[0]['total']
        try:
            order_income = count_income - day_pod_door_log_income_num_wx + pod_door_log_refund
            count_day = (timer.time2timestamp(str(end_time)) - timer.time2timestamp(str(start_time))) / 86400
            apru = order_income / (port_total * count_day)
            use_rate = int(order_num * 100 / (port_total * count_day))
            apru = '%.2f' % apru
            count_income = '%.2f' % count_income
        except:
            apru = 0
            use_rate = 0
        data.append(
            {'region': region['name'], 'note_num': len(notes), 'ev_pod_pile': port_total, 'count_income': count_income,
             'count_num': order_num, 'order_user_num': order_user_num, 'ordewr_recharge_time': ordewr_recharge_time,
             'day_pod_door_log_income_num_wx': day_pod_door_log_income_num_wx, 'apru': apru, 'use_rate': use_rate,
             'count_refund': count_refund})
    sob.sql_close(sob_handle)
    return {'data': data}


#【各省份数据汇总】
def province_data_report_total(request_data: ReportFilterFormat):
    try:
        res = _province_data_report_total(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


def _note_data_report_total(request_data: ReportFilterFormat):
    sob_handle = sob.sql_open(db_config)
    start_time = request_data.start_time
    end_time = request_data.end_time
    strs0 = refund_strs0 = f"mini_id={request_data.mini_id}"
    if start_time:
        strs0 += ' and pay_time>="{}" and pay_time<"{}"'.format(start_time, end_time)
        refund_strs0 += ' and refund_time>="{}" and refund_time<"{}"'.format(start_time, end_time)  # 退款时间
    if request_data.note_id:
        cmd = f"select * from wxapp_note where id={request_data.note_id}"
    else:
        cmd = f"select * from wxapp_note where mini_id={request_data.mini_id}"
    notes = sob.select_mysql_record(sob_handle, cmd)
    data = []
    for note in notes:
        # cmd = f"select name from wxapp_region where id={note['province_id']}"
        # region = sob.select_mysql_record(sob_handle, cmd)
        # region = region[0]
        strs = strs0 + f" and note_id in ({note['id']})"
        refund_strs = refund_strs0 + f" and note_id in ({note['id']})"

        # cmd = f"select sum(balance) as balance from wxapp_user where mini_id={request_data.mini_id} and is_manage=0 and note_id={note['id']}"
        # user_balances = sob.select_mysql_record(sob_handle,cmd)
        # user_balances = user_balances[0]['balance'] if user_balances[0]['balance'] else 0
        # # 充电支付
        cmd = f"select sum(total_price) as total_price from wxapp_order where {strs} and (pay_type=10 or pay_type=20) and pay_status!=10"
        order_income = sob.select_mysql_record(sob_handle,cmd)
        order_income = order_income[0]['total_price'] if order_income[0]['total_price'] else 0
        # 充电包支付
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {strs} and pay_status=20 and pay_type!=40"
        ev_recharge_package_order_income = sob.select_mysql_record(sob_handle, cmd)
        ev_recharge_package_order_income = ev_recharge_package_order_income[0]['pay_price'] if ev_recharge_package_order_income[0]['pay_price'] else 0
        # 续费包支付
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {strs} and pay_status=20"
        recharge_package_order_renew_income = sob.select_mysql_record(sob_handle, cmd)
        recharge_package_order_renew_income = recharge_package_order_renew_income[0]['pay_price'] if recharge_package_order_renew_income[0]['pay_price'] else 0
        # 门禁支付
        cmd = f"select sum(money) as total_price from wxapp_user_door_log where {strs} and pay_status=2 and (pay_type=3 or pay_type=4)"
        day_pod_door_log_income_income = sob.select_mysql_record(sob_handle, cmd)
        day_pod_door_log_income_income = day_pod_door_log_income_income[0]['total_price'] if day_pod_door_log_income_income[0]['total_price'] else 0
        # 总营收(包括退款)
        count_income = order_income + ev_recharge_package_order_income + recharge_package_order_renew_income + day_pod_door_log_income_income  # 总营收(包含退款)

        # 停车包（不包含退款）
        # cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {strs} and pay_status=20 and (order_status=20 or order_status=30) and type=1"
        # recharge_package_order_stop = sob.select_mysql_record(sob_handle,cmd)
        # recharge_package_order_stop = recharge_package_order_stop[0]['pay_price'] if recharge_package_order_stop[0]['pay_price'] else 0

        # # 充电微信支付(含退款)
        # cmd = f"select sum(total_price) as total_price from wxapp_order where {strs} and pay_type=20 and pay_status!=10"
        # order_wx = sob.select_mysql_record(sob_handle, cmd)
        # order_wx = order_wx[0]['total_price'] if order_wx[0]['total_price'] else 0
        # # 充电包微信支付（含退款）
        # cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {strs} and pay_status=20 and pay_type=20"
        # ev_recharge_package_order_wx = sob.select_mysql_record(sob_handle, cmd)
        # ev_recharge_package_order_wx = ev_recharge_package_order_wx[0]['pay_price'] if ev_recharge_package_order_wx[0]['pay_price'] else 0
        # # 续费包微信支付（含退款）
        # cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {strs} and pay_status=20 and pay_type=20"
        # recharge_package_order_renew_wx = sob.select_mysql_record(sob_handle, cmd)
        # recharge_package_order_renew_wx = recharge_package_order_renew_wx[0]['pay_price'] if recharge_package_order_renew_wx[0]['pay_price'] else 0
        # # 微信门禁支付
        # cmd = f"select sum(money) as total_price from wxapp_user_door_log where {strs} and pay_status=2 and pay_type=4"
        # day_pod_door_log_income_num_wx = sob.select_mysql_record(sob_handle, cmd)
        # day_pod_door_log_income_num_wx = day_pod_door_log_income_num_wx[0]['total_price'] if day_pod_door_log_income_num_wx[0]['total_price'] else 0
        # count_income_wx = order_wx + ev_recharge_package_order_wx + recharge_package_order_renew_wx + day_pod_door_log_income_num_wx  # 微信支付收入

        # 充电退款
        # cmd = f"select sum(pay_price) as pay_price from wxapp_order where {refund_strs} and pay_status=30 and pay_type=20 and (pay_price=residue_money or residue_money=0) and refund_id!=''"
        # orders_refuse_wx = sob.select_mysql_record(sob_handle,cmd)
        # orders_refuse_wx = orders_refuse_wx[0]['pay_price'] if orders_refuse_wx[0]['pay_price'] else 0
        # #充电退款(手动)
        # cmd = f"select sum(residue_money) as residue_money from wxapp_order where {refund_strs} and residue_money!=0 and (pay_status=30 and pay_price>residue_money and refund_id!='' or total_price>pay_price and pay_status=20) and pay_type=20"
        # orders_refuse_money_wx = sob.select_mysql_record(sob_handle,cmd)
        # orders_refuse_money_wx = orders_refuse_money_wx[0]['residue_money'] if orders_refuse_money_wx[0]['residue_money'] else 0

        # 套餐包退款
        # cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {refund_strs} and pay_status=20 and pay_type=20 and order_status=40"
        # recharge_package_order_refuse_wx = sob.select_mysql_record(sob_handle,cmd)
        # recharge_package_order_refuse_wx = recharge_package_order_refuse_wx[0]['pay_price'] if recharge_package_order_refuse_wx[0]['pay_price'] else 0
        # # 续费包退款
        # cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {refund_strs} and pay_status=20 and pay_type=20 and order_status=40"
        # recharge_package_order_renew_refuse_wx = sob.select_mysql_record(sob_handle,cmd)
        # recharge_package_order_renew_refuse_wx = recharge_package_order_renew_refuse_wx[0]['pay_price'] if recharge_package_order_renew_refuse_wx[0]['pay_price'] else 0
        # #门禁微信退款
        # cmd = f"select sum(money) as money from wxapp_user_door_log where {refund_strs} and pay_status=3 and pay_type=4"
        # pod_door_log_refund_wx = sob.select_mysql_record(sob_handle,cmd)
        # pod_door_log_refund_wx = pod_door_log_refund_wx[0]['money'] if pod_door_log_refund_wx[0]['money'] else 0
        # count_refund_wx = orders_refuse_wx + orders_refuse_money_wx + recharge_package_order_refuse_wx + recharge_package_order_renew_refuse_wx + pod_door_log_refund_wx  # 退款金额
        # count_income_wx = count_income_wx - count_refund_wx  # 减去退款 (微信支付收入)

        # 总订单（充电)
        cmd = f"select count(*) as total from wxapp_order where {strs} and pay_status=20"
        order_num = sob.select_mysql_record(sob_handle, cmd)
        order_num = order_num[0]['total']
        # 总订单（门禁）
        cmd = f"select count(*) as total from wxapp_user_door_log where {strs} and pay_status!=1"
        day_pod_door_log_num = sob.select_mysql_record(sob_handle, cmd)
        day_pod_door_log_num = day_pod_door_log_num[0]['total']
        # 充电包
        cmd = f"select count(*) as total from wxapp_recharge_package_order where {strs} and pay_status=20 and (order_status=20 or order_status=30)"
        ev_recharge_package_order_num = sob.select_mysql_record(sob_handle,cmd)
        ev_recharge_package_order_num = ev_recharge_package_order_num[0]['total']
        #续费包
        cmd = f"select count(*) as total from wxapp_recharge_package_order_renew where {strs} and pay_status=20 and (order_status=20 or order_status=30)"
        recharge_package_order_renew_num = sob.select_mysql_record(sob_handle,cmd)
        recharge_package_order_renew_num = recharge_package_order_renew_num[0]['total']
        count_num = order_num + day_pod_door_log_num + ev_recharge_package_order_num + recharge_package_order_renew_num  # 总订单

        # 用户数
        cmd = f"select count(*) as total from (select user_id from wxapp_order where {strs} and pay_status=20 group by user_id) a"
        order_user_num = sob.select_mysql_record(sob_handle, cmd)
        order_user_num = order_user_num[0]['total'] if order_user_num else 0
        # 总充电时长
        # cmd = f"select sum(recharge_time) as recharge_time from wxapp_order where {strs} and pay_status=20"
        # ordewr_recharge_time = sob.select_mysql_record(sob_handle, cmd)
        # ordewr_recharge_time = ordewr_recharge_time[0]['recharge_time'] if ordewr_recharge_time[0]['recharge_time'] else 0

        # 充电退款
        cmd = f"select sum(pay_price) as pay_price from wxapp_order where {refund_strs} and pay_status=30 and (pay_price=residue_money or residue_money=0) and (pay_type=10 or pay_type=20)"
        orders_refuse = sob.select_mysql_record(sob_handle, cmd)
        orders_refuse = orders_refuse[0]['pay_price'] if orders_refuse[0]['pay_price'] else 0
        # 充电退款(手动)
        cmd = f"select sum(residue_money) as residue_money from wxapp_order where {refund_strs} and residue_money!=0 and (pay_status=30 and pay_price>residue_money or total_price>pay_price and pay_status=20) and (pay_type=10 or pay_type=20)"
        orders_refuse_money = sob.select_mysql_record(sob_handle, cmd)
        orders_refuse_money = orders_refuse_money[0]['residue_money'] if orders_refuse_money[0]['residue_money'] else 0

        # 套餐包退款
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order where {refund_strs} and pay_status=20 and order_status=40"
        recharge_package_order_refuse = sob.select_mysql_record(sob_handle, cmd)
        recharge_package_order_refuse = recharge_package_order_refuse[0]['pay_price'] if recharge_package_order_refuse[0]['pay_price'] else 0
        # 续费包退款
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where {refund_strs} and pay_status=20 and order_status=40"
        recharge_package_order_renew_refuse = sob.select_mysql_record(sob_handle, cmd)
        recharge_package_order_renew_refuse = recharge_package_order_renew_refuse[0]['pay_price'] if recharge_package_order_renew_refuse[0]['pay_price'] else 0
        # 门禁微信退款
        cmd = f"select sum(money) as money from wxapp_user_door_log where {refund_strs} and pay_status=3 and (pay_type=3 or pay_type=4)"
        pod_door_log_refund = sob.select_mysql_record(sob_handle, cmd)
        pod_door_log_refund = pod_door_log_refund[0]['money'] if pod_door_log_refund[0]['money'] else 0
        count_refund = orders_refuse + recharge_package_order_refuse + recharge_package_order_renew_refuse + orders_refuse_money + pod_door_log_refund  # 退款金额
        count_income = count_income - count_refund

        # ev_recharge_package_order_income = ev_recharge_package_order_income + recharge_package_order_renew_income - recharge_package_order_refuse - recharge_package_order_renew_refuse  # 套餐营收（不包含退款）
        cmd = f"select count(*) as total from wxapp_pod_pile a left join wxapp_pod_pileport b on a.id=b.pile_id where a.mini_id={request_data.mini_id} and a.note_id={note['id']}"
        port_total = sob.select_mysql_record(sob_handle, cmd)
        port_total = port_total[0]['total']
        cmd = f"select count(*) as total from wxapp_pod_pile a left join wxapp_pod_pileport b on a.id=b.pile_id where a.mini_id={request_data.mini_id} and isonline=1 and a.note_id={note['id']}"
        online_port = sob.select_mysql_record(sob_handle, cmd)
        online_port = online_port[0]['total']
        # try:
        #     order_income = count_income - day_pod_door_log_income_num_wx + pod_door_log_refund
        #     count_day = (timer.time2timestamp(str(end_time)) - timer.time2timestamp(str(start_time))) / 86400
        #     apru = order_income / (port_total * count_day)
        #     use_rate = int(order_num * 100 / (port_total * count_day))
        #     apru = '%.2f' % apru
        #     count_refund = '%.2f' % count_refund
        #     count_income = '%.2f' % count_income
        # except:
        #     apru = 0
        #     use_rate = 0
        # data.append({'region': region['name'], 'note_name': note['note_name'], 'ev_pod_pile': port_total,
        #              'ev_pod_pile_isonline': online_port,
        #              'count_income': count_income, 'day_pod_door_log_income_income': day_pod_door_log_income_income,
        #              'ev_recharge_package_order_income':
        #                  ev_recharge_package_order_income, 'recharge_package_order_stop': recharge_package_order_stop,
        #              'count_income_wx': count_income_wx,
        #              'count_num': count_num, 'order_user_num': order_user_num,
        #              'ordewr_recharge_time': ordewr_recharge_time, 'apru': apru,
        #              'use_rate': use_rate, 'count_refund': count_refund, 'user_balances': user_balances})

        data.append({'note_name': note['note_name'], 'ev_pod_pile': port_total,
                     'ev_pod_pile_isonline': online_port,
                     'count_income': count_income,'count_refund': count_refund,
                     'count_num': count_num, 'order_user_num': order_user_num,
                     })
    sob.sql_close(sob_handle)
    return {'data': data}

#【各场地数据汇总】
def note_data_report_total(request_data: ReportFilterFormat):
    # try:
        res = _note_data_report_total(request_data)
        response = format_response_data(res)
        return response
    # except Exception as exc:
    #     return {"status": 400, "msg": exc.__str__()}

def _pile_data_report_total(request_data: ReportFilterFormat):
    sob_handle = sob.sql_open(db_config)
    start_time = request_data.start_time
    end_time = request_data.end_time
    strs = refund_strs = f"mini_id={request_data.mini_id} and pile_id={request_data.pile_id}"
    if start_time:
        strs += ' and pay_time>="{}" and pay_time<"{}"'.format(start_time, end_time)
        refund_strs += ' and refund_time>="{}" and refund_time<"{}"'.format(start_time, end_time)  # 退款时间
    # # 充电支付
    cmd = f"select sum(total_price) as total_price from wxapp_order where {strs} and (pay_type=10 or pay_type=20) and pay_status!=10"
    order_income = sob.select_mysql_record(sob_handle, cmd)
    order_income = order_income[0]['total_price'] if order_income[0]['total_price'] else 0
    # 总订单（充电)
    cmd = f"select count(*) as total from wxapp_order where {strs} and pay_status!=10"
    order_num = sob.select_mysql_record(sob_handle, cmd)
    order_num = order_num[0]['total']
    # 充电退款
    cmd = f"select sum(pay_price) as pay_price from wxapp_order where {refund_strs} and pay_status=30 and (pay_price=residue_money or residue_money=0) and (pay_type=10 or pay_type=20)"
    orders_refuse = sob.select_mysql_record(sob_handle, cmd)
    orders_refuse = orders_refuse[0]['pay_price'] if orders_refuse[0]['pay_price'] else 0
    # 充电退款(手动)
    cmd = f"select sum(residue_money) as residue_money from wxapp_order where {refund_strs} and residue_money!=0 and (pay_status=30 and pay_price>residue_money or total_price>pay_price and pay_status=20) and (pay_type=10 or pay_type=20)"
    orders_refuse_money = sob.select_mysql_record(sob_handle, cmd)
    orders_refuse_money = orders_refuse_money[0]['residue_money'] if orders_refuse_money[0]['residue_money'] else 0
    order_refund = orders_refuse + orders_refuse_money
    order_income = order_income - order_refund
    order_income = '%.2f' % order_income
    order_refund = '%.2f' % order_refund
    data = {
        'order_num':order_num,
        'order_income':order_income,
        'order_refund':order_refund,
    }
    return {'data':data}


#【各设备数据汇总】
def pile_data_report_total(request_data: ReportFilterFormat):
    try:
        res = _pile_data_report_total(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}
