import io
from datetime import datetime

from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from config import db_config
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new
import pandas as pd
prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()



class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    id: int = Field(None, description="id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    start_time: datetime = Field(None, description='开始时间')
    end_time: datetime = Field(None, description='结束时间')



def _generate_where_sql(request_data):
    where_lst = ["pay_status=20"]
    mini_id = request_data['mini_id']
    keyword = request_data['keyword']
    end_time = request_data['end_time']
    start_time = request_data['start_time']
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if keyword:
        where_lst.append(f"nickname like '%{sob.escape(keyword)}%'")
    if start_time and end_time:
        where_lst.append(f"pay_time>='{start_time}' and pay_time<='{end_time}'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def export_recharge_order_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.id as '订单号',
               nickname as '用户',
               plan_name as '套餐名',
               a.pay_price as '用户支付金额',
               a.gift_money as '赠送金额',
               a.actual_money as '实际到账金额',
               a.pay_status as '支付状态(10待支付 20已支付)',
               a.pay_time as '付款时间',
               a.add_time as '创建时间'
            from
               wxapp_recharge_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_recharge_plan c
            on a.plan_id=c.id
            {where_sql}
        """
    prolog.info(cmd)
    info = sob.select_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    print(info)
    # for _ in info:
    #     pass
    # 将数据转换为 pandas 的 DataFrame
    df = pd.DataFrame(info)
    # 将 DataFrame 导出到 Excel 文件
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    output.seek(0)
    # 返回 Excel 文件作为流式响应
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': 'attachment; filename="recharge_order.xlsx"'})




class QFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    note_id: int = Field(None, description="社区id")
    user_id: int = Field(None, description="用户id")
    package_id: int = Field(None, description="套餐包id")
    keyword: str = Field(None, description="关键字搜索")
    start_time :datetime = Field(None,description='开始时间')
    end_time :datetime = Field(None,description='结束时间')





def _package_generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    user_id = request_data['user_id']
    note_id = request_data['note_id']
    package_id = request_data['package_id']
    keyword = request_data['keyword']
    start_time = request_data['start_time']
    end_time = request_data['end_time']
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if note_id:
        where_lst.append(f"a.note_id={note_id}")
    if user_id:
        where_lst.append(f"a.user_id={user_id}")
    if package_id:
        where_lst.append(f"a.package_id={package_id}")
    if start_time and end_time:
        where_lst.append(f"pay_time>='{start_time}' and pay_time<='{end_time}'")
    if keyword:
        where_lst.append(f"nickname like '%{sob.escape(keyword)}%'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def export_recharge_package_order_list(request_data: QFilterFormat):
    request_dict = request_data.dict()
    where_sql = _package_generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.id,
               nickname,
               note_name,
               a.type,
               days,
               a.plan_name,
               a.recharge_time,
               a.pay_price,
               a.pay_type,
               a.order_status,
               a.pay_time,
               a.residue_time,
               a.is_use,
               a.is_renew,
               a.end_time,
               a.add_time
            from
               wxapp_recharge_package_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_recharge_package c
            on a.package_id=c.id
            left join wxapp_note d
            on a.note_id=d.id
            {where_sql}
        """
    prolog.info(cmd)
    info = sob.select_mysql_record(sob_handle, cmd)
    id_ls = []
    nickname_ls = []
    note_name_ls = []
    type_ls = []
    days_ls = []
    plan_name_ls = []
    recharge_time_ls = []
    pay_price_ls = []
    pay_type_ls = []
    order_status_ls = []
    pay_time_ls = []
    residue_time_ls = []
    is_use_ls = []
    is_renew_ls = []
    end_time_ls = []
    add_time_ls = []
    renew_price_ls = []
    for _ in info:
        id_ls.append(_['id'])
        nickname_ls.append(_['nickname'])
        note_name_ls.append(_['note_name'])
        type_ls.append(_['type'])
        days_ls.append(_['days'])
        plan_name_ls.append(_['plan_name'])
        recharge_time_ls.append(_['recharge_time'])
        pay_price_ls.append(_['pay_price'])
        pay_type_ls.append(_['pay_type'])
        order_status_ls.append(_['order_status'])
        pay_time_ls.append(_['pay_time'])
        residue_time_ls.append(_['residue_time'])
        is_use_ls.append(_['is_use'])
        is_renew_ls.append(_['is_renew'])
        end_time_ls.append(_['end_time'])
        add_time_ls.append(_['add_time'])
        cmd = f"select sum(pay_price) as pay_price from wxapp_recharge_package_order_renew where packageorder_id={_['id']} and order_status=20 and pay_status=20"
        renew_info = sob.select_mysql_record(sob_handle,cmd)
        renew_price = renew_info[0]['pay_price'] if renew_info[0]['pay_price'] else 0
        renew_price_ls.append(renew_price)
    sob.sql_close(sob_handle)
    # 将数据转换为 pandas 的 DataFrame
    data = {
        '订单号':id_ls,
        '用户':nickname_ls,
        '社区':note_name_ls,
        '套餐类型(1:停车包 2:停车加充电包)':type_ls,
        '套餐天数':days_ls,
        '套餐名称':plan_name_ls,
        '充电时间':recharge_time_ls,
        '支付金额':pay_price_ls,
        '支付方式(10余额支付 20微信支付)':pay_type_ls,
        '订单状态(10未完成 20已完成 30退款中 40已退款 50退款被拒绝 60退款异常)':order_status_ls,
        '付款时间':pay_time_ls,
        '剩余充电时间':residue_time_ls,
        '是否有效(0否 1是)':is_use_ls,
        '是否续费(0否 1是)':is_renew_ls,
        '金额续费':renew_price_ls,
        '到期时间':end_time_ls,
        '创建时间':add_time_ls,
    }
    df = pd.DataFrame(data)
    # 将 DataFrame 导出到 Excel 文件
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    output.seek(0)
    # 返回 Excel 文件作为流式响应
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': 'attachment; filename="package_order.xlsx"'})

def _ex_package_generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    user_id = request_data['user_id']
    note_id = request_data['note_id']
    package_id = request_data['package_id']
    keyword = request_data['keyword']
    start_time = request_data['start_time']
    end_time = request_data['end_time']
    if mini_id:
        where_lst.append(f"mini_id={mini_id}")
    if note_id:
        where_lst.append(f"note_id={note_id}")
    if user_id:
        where_lst.append(f"user_id={user_id}")
    if package_id:
        where_lst.append(f"package_id={package_id}")
    if start_time and end_time:
        where_lst.append(f"pay_time>='{start_time}' and pay_time<='{end_time}'")
    if keyword:
        where_lst.append(f"nickname like '%{sob.escape(keyword)}%'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql



#【充电包数据统计】
def export_package_data(request_data: QFilterFormat):
    sob_handle = sob.sql_open(db_config)
    request_dict = request_data.dict()
    where_sql = _ex_package_generate_where_sql(request_dict)
    note_id = request_data.note_id
    if note_id:
        cmd = f"select * from wxapp_note where id={request_data.note_id}"
    else:
        cmd = f"select * from wxapp_note where mini_id={request_data.mini_id}"
    notes = sob.select_mysql_record(sob_handle,cmd)
    data = []
    for note in notes:
        cmd = f"select count(*) as total from wxapp_pod_pileport where mini_id={request_data.mini_id} and note_id={note['id']}"
        pileport = sob.select_mysql_record(sob_handle,cmd)
        pileport = pileport[0]['total']
        cmd = f"select sum(pay_price) as pay_price,count(*) as total from wxapp_recharge_package_order {where_sql} and note_id={note['id']} and pay_status=20 and order_status=20"
        recharge_package_order_incomes = sob.select_mysql_record(sob_handle,cmd)
        print(recharge_package_order_incomes)
        recharge_package_order_income = recharge_package_order_incomes[0]['pay_price'] if recharge_package_order_incomes[0]['pay_price'] else 0
        recharge_package_order_num = recharge_package_order_incomes[0]['total']
        cmd = f"select count(*) as total from (select user_id from wxapp_recharge_package_order {where_sql} and note_id={note['id']} and pay_status=20 and order_status=20 group by user_id) a"
        recharge_package_order_user_num = sob.select_mysql_record(sob_handle,cmd)
        recharge_package_order_user_num = recharge_package_order_user_num[0]['total'] if recharge_package_order_user_num[0]['total'] else 0
        cmd = f"select sum(pay_price) as pay_price,count(*) as total from wxapp_recharge_package_order_renew {where_sql} and note_id={note['id']} and pay_status=20 and order_status=20"
        recharge_package_order_renew_incomes = sob.select_mysql_record(sob_handle,cmd)
        recharge_package_order_renew_income = recharge_package_order_renew_incomes[0]['pay_price'] if recharge_package_order_renew_incomes[0]['pay_price'] else 0
        recharge_package_order_renew_num = recharge_package_order_renew_incomes[0]['total']
        cmd = f"select count(*) as total from (select user_id from wxapp_recharge_package_order_renew {where_sql} and note_id={note['id']} and pay_status=20 and order_status=20 group by user_id) a"
        recharge_package_order_renew_user_num = sob.select_mysql_record(sob_handle, cmd)
        recharge_package_order_renew_user_num = recharge_package_order_renew_user_num[0]['total'] if recharge_package_order_renew_user_num[0]['total'] else 0
        user_num = recharge_package_order_user_num + recharge_package_order_renew_user_num
        recharge_package_order_income = recharge_package_order_income+recharge_package_order_renew_income
        recharge_package_order_num = recharge_package_order_num + recharge_package_order_renew_num
        data.append({
            '社区':note['note_name'],
            '端口数':pileport,
            '充电包总营收':recharge_package_order_income,
            '购买充电包用户数':user_num,
            '购买订单数':recharge_package_order_num,
        })
    sob.sql_close(sob_handle)
    # 将数据转换为 pandas 的 DataFrame
    df = pd.DataFrame(data)
    # 将 DataFrame 导出到 Excel 文件
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    output.seek(0)
    # 返回 Excel 文件作为流式响应
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': 'attachment; filename="package_data.xlsx"'})



