import io

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
    note_id: int = Field(None, description="社区id")
    user_id: int = Field(None, description="用户id")
    order_status: int = Field(None, description="订单状态(0未开始充电 1启动中 10充电中 11结束中 20充电结束 30充电失败)")
    pay_status: int = Field(None, description="支付状态(10待支付 20已支付 30已退款 40退款异常)")
    snum: str = Field(None, description="设备SN编码")
    portnum: int = Field(None, description="端口编号")
    keyword: str = Field(None, description="关键字搜索")
    start_time: str = Field(None, description="开始时间")
    end_time: str = Field(None, description="结束时间")



def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    note_id = request_data['note_id']
    user_id = request_data['user_id']
    order_status = request_data['order_status']
    snum = request_data['snum']
    portnum = request_data['portnum']
    pay_status = request_data['pay_status']
    keyword = request_data['keyword']
    start_time = request_data['start_time']
    end_time = request_data['end_time']
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
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
    if end_time and start_time:
        where_lst.append(f"pay_time>='{start_time}' and pay_time<'{end_time}'")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or mobile like '%{sob.escape(keyword)}%' or snum like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql





def export_order_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.id as 'ID',
               nickname as '用户',
               note_name as '社区',
               a.snum as '设备编码',
               a.portnum as '端口号',
               a.start_time as '开始时间',
               a.end_time as '结束时间',
               a.recharge_time as '充电时长',
               a.pay_price as '实际付款金额',
               a.pay_type as '支付方式(10余额支付 20微信支付 30套餐扣款 40刷卡充电 50白名单用户 60虚拟金额支付)',
               a.order_status as '订单状态(0未开始充电 1启动中 10充电中 11结束中 20充电结束 30充电失败)',
               a.pay_status as '支付状态(10待支付 20已支付 30已退款 40退款异常)',
               a.is_settled as '是否已结算(0未结算 1已结算)',
               a.add_time as '创建时间',
               a.pay_time as '支付时间',
               a.total_price as '原支付金额',
               a.residue_money as '退款金额'
            from
               wxapp_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_note c
            on a.note_id=c.id
            {where_sql}
        """
    prolog.info(cmd)
    info = sob.select_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    # 将数据转换为 pandas 的 DataFrame
    df = pd.DataFrame(info)
    # 将 DataFrame 导出到 Excel 文件
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    output.seek(0)
    # 返回 Excel 文件作为流式响应
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename="order.xlsx"'})



def _refund_generate_where_sql(request_data):
    where_lst = ['(pay_type=10 or pay_type=20) and pay_status!=10']
    mini_id = request_data['mini_id']
    note_id = request_data['note_id']
    user_id = request_data['user_id']
    order_status = request_data['order_status']
    snum = request_data['snum']
    portnum = request_data['portnum']
    pay_status = request_data['pay_status']
    keyword = request_data['keyword']
    start_time = request_data['start_time']
    end_time = request_data['end_time']
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
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
    if end_time and start_time:
        where_lst.append(f"refund_time>='{start_time}' and refund_time<'{end_time}'")
    if keyword:
        where_lst.append(f"nickname like '%{sob.escape(keyword)}%'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql



def export_fefund_order_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _refund_generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.id as 'ID',
               nickname as '用户',
               note_name as '社区',
               a.snum as '设备编码',
               a.portnum as '端口号',
               a.start_time as '开始时间',
               a.end_time as '结束时间',
               a.recharge_time as '充电时长',
               a.pay_price as '实际付款金额',
               a.pay_type as '支付方式(10余额支付 20微信支付 30套餐扣款 40刷卡充电 50白名单用户 60虚拟金额支付)',
               a.order_status as '订单状态(0未开始充电 1启动中 10充电中 11结束中 20充电结束 30充电失败)',
               a.pay_status as '支付状态(10待支付 20已支付 30已退款 40退款异常)',
               a.is_settled as '是否已结算(0未结算 1已结算)',
               a.pay_time as '支付时间',
               a.total_price as '原支付金额',
               a.residue_money as '退款金额'
            from
               wxapp_order a
            left join wxapp_user b
            on a.user_id=b.id
            left join wxapp_note c
            on a.note_id=c.id
            {where_sql}
        """
    prolog.info(cmd)
    info = sob.select_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    # 将数据转换为 pandas 的 DataFrame
    df = pd.DataFrame(info)
    # 将 DataFrame 导出到 Excel 文件
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    output.seek(0)
    # 返回 Excel 文件作为流式响应
    return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename="refund_order.xlsx"'})