from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()


class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    user_id: int = Field(None, description="用户id")
    id: int = Field(None, description="社区节点id (mini_id,id二选一)")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(50, description="页面大小")


class CreateFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    id: int = Field(None, description="id")
    note_name: str = Field(..., description="救援note名称")
    province_id: int = Field(..., description="所在省份id")
    city_id: int = Field(..., description="所在城市id")
    region_id: int = Field(..., description="所在辖区id")
    address: str = Field(..., description="详细地址")
    longitude: str = Field(..., description="经度")
    latitude: str = Field(..., description="纬度")
    summary: str = Field(None, description="NOTE简介")
    status: int = Field(1, description="状态(0停止 1正常)")
    is_ind_dealer: int = Field(0, description="是否开启单独分成(0关闭 1开启)")
    bill_type: int = Field(0, description="计费类型(0按时 1分档)")
    predict_price: float = Field(0, description="预扣金额")
    first_proportion: float = Field(0, description="一级分成比例(代理商)")
    second_proportion: float = Field(0, description="二级分成比例(社区)")
    free_time: int = Field(0, description="免费停放时长（分钟）")
    money: float = Field(0, description="门禁费用单次")
    is_refund: int = Field(0, description="是否开启充电时长不足退款(1是 0否)")
    is_temporary_site: int = Field(0, description="是否是临停场地(1是 0否)")
    step: int = Field(0, description="步长/小时")
    refund_price: float = Field(0, description="步长/退款单价")


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="社区节点id")


class AgentFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    is_manage: int = Field(..., description="账号类型 5:代理商 6:物业")


def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    keyword = request_data['keyword']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if keyword:
        where_lst.append(f"note_name like '%{sob.escape(keyword)}%'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_note(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd =f"select * from wxapp_user where id={request_data.user_id}"
    user = sob.select_mysql_record(sob_handle,cmd)
    if user and user[0]['is_manage'] in [3,5,6]:
        cmd = f"""
            select 
              *, count(*) over() as total
            from
               wxapp_note
            {where_sql}
                and id in ({user['note_id']})
            limit {request_data.size} offset {request_data.offset}
        """
    else:
        cmd = f"""
                select 
                  *, count(*) over() as total
                from
                   wxapp_note
                {where_sql}
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


def _create_note(request_data: CreateFilterFormat):
    request_dict = request_data.dict()
    request_dict.update({"add_time":timer.get_now(),"update_time":timer.get_now()})
    hope_lst = list(request_dict.keys())
    hope_lst.remove('add_time')
    sob_handle = sob.sql_open(db_config)
    flag = sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_note',[request_dict],hope_lst)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return

def _delete_note(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"delete from wxapp_note where id={request_data.id}"
    flag = sob.delete_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【获取社区节点】
def get_note(request_data: QueryFilterFormat):
    try:
        res = _get_note(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【创建修改社区节点】
def create_note(request_data: CreateFilterFormat):
    try:
        res = _create_note(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【删除社区节点】
def delete_note(request_data: DeleteFilterFormat):
    try:
        res = _delete_note(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class PileFilterFormat(BaseModel):
    note_id: int = Field(None, description="社区id")


def _note_pile_list(request_data: PileFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"SELECT note_name,snum,serialnum,iccid,b.id from wxapp_note a left join wxapp_pod_pile b on a.id=b.note_id where a.id={request_data.note_id}"
    pile_info = sob.select_mysql_record(sob_handle,cmd)
    cmd = f"SELECT pile_num,count(*) as online_num,pile_num-count(*) as notonlinepile_num from " \
          f"(SELECT isonline,count(*) over() as pile_num from wxapp_pod_pile where note_id=1) aa where isonline=1"
    num_info = sob.select_mysql_record(sob_handle,cmd)
    cmd = f"SELECT pileports_num,count(*) as notfreepileports_num,pileports_num-count(*) as freepileports_num from (" \
          f"SELECT portstatus,count(*) over() as pileports_num from wxapp_pod_pileport where note_id=1) aa where portstatus=1"
    portnum_info = sob.select_mysql_record(sob_handle,cmd)
    for pile in pile_info:
        cmd = f"select serialnum,portnum,portstatus from wxapp_pod_pileport where pile_id={pile['id']}"
        port_info = sob.select_mysql_record(sob_handle,cmd)
        pile['port_info'] = port_info
    return {'pile_info':pile_info,'num_info':num_info,'portnum_info':portnum_info}



#【社区充电桩详情】
def note_pile_list(request_data: PileFilterFormat):
    try:
        res = _note_pile_list(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}





def _note_isagent(request_data:AgentFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select id,note_name from wxapp_note where mini_id={request_data.mini_id}"
    note_info = sob.select_mysql_record(sob_handle,cmd)
    for note in note_info:
        cmd = f"select * from wxapp_dealer_note where FIND_IN_SET({note['id']},note_id) and type={request_data.is_manage}"
        info = sob.select_mysql_record(sob_handle,cmd)
        if info:
            note['is_agent'] = 1  # 已被代理
        else:
            note['is_agent'] = 0
    return note_info

#社区是否已被代理
def note_isagent(request_data:AgentFilterFormat):
    try:
        res = _note_isagent(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}