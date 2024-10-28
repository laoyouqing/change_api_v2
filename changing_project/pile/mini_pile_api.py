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
    city_id: int = Field(None, description="城市id")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")


class PileDetailFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    user_id: int = Field(None, description="用户id")
    snum: str = Field(None, description="设备SN编码")


def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    city_id = request_data['city_id']
    keyword = request_data['keyword']
    if mini_id:
        where_lst.append(f"mini_id={mini_id}")
    if city_id:
        where_lst.append(f"city_id={city_id}")
    if keyword:
        where_lst.append(f"note_name like '%{sob.escape(keyword)}%'")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _mini_get_note(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              id,
              note_name, province_id,city_id,region_id,
              address,longitude,latitude,
              count(*) over() as total
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
        total_port = 0
        free_total = 0
        del _["total"]
        cmd = f"select count(*) as total from wxapp_pod_pileport where note_id={_['id']}"
        count_port = sob.select_mysql_record(sob_handle,cmd)
        if count_port:
            total_port = count_port[0]['total']
            cmd = f"select count(*) as free_total from wxapp_pod_pileport where note_id={_['id']} and portstatus=0"
            free_port = sob.select_mysql_record(sob_handle, cmd)
            if free_port:
                free_total = free_port[0]['free_total']
        _['total_port'] = total_port
        _['free_total'] = free_total
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "info": info
    }


#【小程序充电社区节点列表】
def mini_get_note(request_data: QueryFilterFormat):
    try:
        res = _mini_get_note(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

def _mini_pile_detail(request_data: PileDetailFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select id,note_id,snum,isonline,lastip from wxapp_pod_pile where mini_id={request_data.mini_id} and snum='{request_data.snum}'"
    pod_pile = sob.select_mysql_record(sob_handle,cmd)
    if pod_pile:
        pod_pile = pod_pile[0]
        if pod_pile['isonline'] == 0:
            raise ValueError('充电桩是离线状态')
        cmd = f"select note_name,address from wxapp_note where id={pod_pile['note_id']}"
        note = sob.select_mysql_record(sob_handle,cmd)
        note = note[0] if note else ''
        cmd = f"select id,portnum,portstatus,trouble_status from wxapp_pod_pileport where pile_id={pod_pile['id']}"
        pile_port = sob.select_mysql_record(sob_handle,cmd)
        pile_port = pile_port if pile_port else []
        cmd = f"select id,title,billtype,duration from wxapp_bill where note_id={pod_pile['note_id']}"
        bill = sob.select_mysql_record(sob_handle,cmd)
        bill = bill if bill else []
        cmd = f"select id,balance from wxapp_user where id={request_data.user_id}"
        user = sob.select_mysql_record(sob_handle,cmd)
        user = user[0] if user else ''
        return {'pod_pile':pod_pile,'note':note,'pile_port':pile_port,'bill':bill,'user':user}
    else:
        raise ValueError('充电编码不存在')



#【小程序插座详情】
def mini_pile_detail(request_data: PileDetailFilterFormat):
    try:
        res = _mini_pile_detail(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}
