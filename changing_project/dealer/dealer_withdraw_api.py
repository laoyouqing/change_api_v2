from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.normal_func import get_settings
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()


class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    note_id: int = Field(None, description="社区id")
    user_id: int = Field(None, description="用户id")
    id: int = Field(None, description="提现id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")

def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    user_id = request_data['user_id']
    note_id = request_data['note_id']
    keyword = request_data['keyword']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if note_id:
        where_lst.append(f"a.note_id={note_id}")
    if user_id:
        where_lst.append(f"account_id={user_id}")
    if keyword:
        where_lst.append(f"(nickname like '%{sob.escape(keyword)}%' or note_name like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _dealer_withdraw_list(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
               a.*,
               nickname,avatar,note_name,
               count(*) over() as total
            from
               wxapp_dealer_withdraw a
            left join wxapp_user b
            on a.account_id=b.id
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



#【申请提现列表】
def dealer_withdraw_list(request_data: QueryFilterFormat):
    try:
        res = _dealer_withdraw_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class ApplyFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    user_id: int = Field(None, description="用户id")
    pay_type: int = Field(None, description="提现方式 20支付宝 30银行卡")
    money: float = Field(None, description="提现金额")
    account_name: str = Field(None, description="账户名字")
    account: str = Field(None, description="账号")


def _dealer_withdraw_apply(request_data: ApplyFilterFormat):
    sob_handle = sob.sql_open(db_config)
    values_json = get_settings(request_data.mini_id, 'settlement')
    min_money = values_json['min_money']  # 最低提现金额
    if float(request_data.money) < float(min_money):
        raise ValueError('最低提现佣金%s元' % min_money)
    service_charge_ratio = values_json['service_charge_ratio']  # 手续费比例 千分之几
    cmd = f"select * from wxapp_dealer_note where mini_id={request_data.mini_id} and account_id={request_data.user_id}"
    dealer_note = sob.select_mysql_record(sob_handle, cmd)
    dealer_note = dealer_note[0]
    if dealer_note['money'] < float(request_data.money):
        raise ValueError('超出可提现金额')
    reality_money = float(request_data.money) - float(request_data.money) * int(service_charge_ratio) / 1000
    value_info = {
        "mini_id":request_data.mini_id,
        "note_id":dealer_note['note_id'],
        "account_id":request_data.user_id,
        "money":request_data.money,
        "reality_money":reality_money,
        "pay_type":request_data.pay_type,
        "account_name":request_data.account_name,
        "account":request_data.account,
        "add_time":timer.get_now(),
        "update_time":timer.get_now()
    }
    flag = sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_dealer_withdraw', [value_info])
    cmd = f"update wxapp_dealer_note set money=money-{request_data.money},total_money=total_money+{request_data.money} where id={dealer_note['id']}"
    sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return

#【申请提现】
def dealer_withdraw_apply(request_data: ApplyFilterFormat):
    try:
        res = _dealer_withdraw_apply(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class AuditFilterFormat(BaseModel):
    id: int = Field(..., description="id")
    apply_status: int = Field(..., description="申请状态 (10待审核 20审核通过 30驳回 40已打款)")
    reject_reason: str = Field(None, description="驳回原因")


def _dealer_withdraw_audit(request_data: AuditFilterFormat):
    sob_handle = sob.sql_open(db_config)
    apply_status = request_data.apply_status
    reject_reason = request_data.reject_reason
    cmd = f"select * from wxapp_dealer_withdraw where id={request_data.id}"
    dealer_withdraw = sob.select_mysql_record(sob_handle,cmd)
    dealer_withdraw = dealer_withdraw[0]
    if apply_status == 30:
        cmd = f"update wxapp_dealer_note set money=money+{dealer_withdraw['money']},total_money=total_money-{dealer_withdraw['money']} where mini_id={dealer_withdraw['mini_id']} and account_id={dealer_withdraw['account_id']}"
        sob.update_mysql_record(sob_handle, cmd)
    cmd = f"update wxapp_dealer_withdraw set apply_status={apply_status},reject_reason='{reject_reason}',audit_time='{timer.get_now()}' where id={request_data.id}"
    sob.select_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    return ''



#【申请提现审核】
def dealer_withdraw_audit(request_data: AuditFilterFormat):
    try:
        res = _dealer_withdraw_audit(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}