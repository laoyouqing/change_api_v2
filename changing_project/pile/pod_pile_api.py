import json
from typing import List

from pydantic import BaseModel, Field

from config import db_config, TCP_PORT
from tool.format_data import format_response_data, _range_field_cmd
from tool.logger import MyLogger
from tool.tcpc import TCPClient
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()



class QueryFilterFormat(BaseModel):
    mini_id: int = Field(None, description="小程序id")
    id: int = Field(None, description="充电桩id (mini_id,id二选一)")
    note_id: int = Field(None, description="社区id")
    isonline: int = Field(None, description="是否在线 1是 0否")
    keyword: str = Field(None, description="关键字搜索")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")


class CreateFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    note_id: int = Field(..., description="社区id")
    type: int = Field(..., description="充电桩类型  1：新网 2：柏莱(二孔) 3：柏莱(十二孔) 4:柏莱(子母机) 5网关 6:柏莱（十口）")
    serialnum: List = Field(None, description="充电桩串号")
    gateway_id: str = Field(None, description="网关id")
    pilelist: List = Field(None, description='插座号、mac[{"pile":"","mac":""}]')
    macuid_list: List = Field(None, description='mac、uid[{"mac":"","uid":""}]')


class UpdateFilterFormat(BaseModel):
    id: int = Field(..., description="充电桩id")
    mini_id: int = Field(..., description="小程序id")
    note_id: int = Field(..., description="社区id")
    gateway_id: str = Field(None, description="网关id")
    type: int = Field(..., description="充电桩类型  1：新网 2：柏莱(二孔) 3：柏莱(十二孔) 4:柏莱(子母机) 5网关")
    title: str = Field(None, description="标题")
    snum: str = Field(None, description="设备SN编码")
    serialnum: str = Field(None, description="充电桩串号")
    pileport: int = Field(None, description='充电桩端口数量')
    pileversion: str = Field(None, description='充电桩版本')
    iccid: str = Field(None, description='ICCID号码')
    xhqd: str = Field(None, description='信号强度')
    isonline: int = Field(None, description='是否在线')
    lastip: str = Field(None, description='最后上线IP')
    pod_pileports: List = Field(None, description='端口信息')


class DeleteFilterFormat(BaseModel):
    id: int = Field(..., description="充电桩id")
    is_force_delete: bool = Field(False, description="是否强制删除true/false")


def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    note_id = request_data['note_id']
    keyword = request_data['keyword']
    isonline = request_data['isonline']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"a.mini_id={mini_id}")
    if id:
        where_lst.append(f"a.id={id}")
    if note_id:
        where_lst.append(f"a.note_id={note_id}")
    if isonline:
        where_lst.append(f"a.isonline={isonline}")
    if keyword:
        where_lst.append(f"(title like '%{sob.escape(keyword)}%' or a.snum like '%{sob.escape(keyword)}%' or a.serialnum like '%{sob.escape(keyword)}%')")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_pod_pile(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              a.*, 
              c.note_name,
              count(*) over() as total
            from
               wxapp_pod_pile a
            left join wxapp_note c on a.note_id=c.id
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
        if request_data.id:
            cmd = f"select * from wxapp_pod_pileport where pile_id={request_data.id}"
            pod_pileport = sob.select_mysql_record(sob_handle,cmd)
            _['pod_pileport'] = pod_pileport
    sob.sql_close(sob_handle)
    return {
        "total": total,
        "info": info
    }


def _create_pod_pile(request_data: CreateFilterFormat):
    where_lst = [f"mini_id={request_data.mini_id}"]
    sob_handle = sob.sql_open(db_config)
    request_dict = request_data.dict()
    type = request_data.type
    if type == 1:
        range_filed = {
            "serialnum":"serialnum"
        }
        for param,field in range_filed.items():
            where_lst += _range_field_cmd(request_dict,param,field)
        where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
        cmd = f"select serialnum from wxapp_pod_pile {where_sql}"
        prolog.info(cmd)
        info = sob.select_mysql_record(sob_handle, cmd)
        if info:
            raise ValueError(f'{info}充电桩已存在')
        value_list = []
        for serialnum in request_data.serialnum:
            value_info = {
                "mini_id":request_data.mini_id,
                "note_id":request_data.note_id,
                "serialnum":serialnum,
                "snum":serialnum,
                "type":1,
                "add_time":timer.get_now(),
                "update_time":timer.get_now(),
            }
            value_list.append(value_info)
        sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_pod_pile',value_list)
    elif type == 2 or type == 4:
        gateway_id = request_data.gateway_id
        cmd = f"select * from wxapp_pod_pile where gateway_id='{gateway_id}'"
        print(cmd)
        info = sob.select_mysql_record(sob_handle,cmd)
        print(info)
        if not info:
            raise ValueError('网关不存在')
        data = {}
        data['token'] = 'qfevserver'
        data['cmd'] = 'add'
        data['mini_id'] = request_data.mini_id
        data['note_id'] = request_data.note_id
        data['pilelist'] = request_data.pilelist
        data['onlytag'] = gateway_id
        data['type'] = type
        data['command'] = 'add_pile'
        data['ip'] = info[0]['lastip']
        sock_data = 'evapi|{}'.format(json.dumps(data))

        server1 = TCPClient(TCP_PORT)
        server1.send_msg(sock_data)
        try:
            resp = server1.recv_msg()
            resp = json.loads(resp)
            server1.close()
            return resp
        except:
            server1.close()
            raise ValueError('创建失败')
    elif type == 5:
        gateway_id = request_data.gateway_id
        cmd = f"select * from wxapp_pod_pile where gateway_id='{gateway_id}'"
        info = sob.select_mysql_record(sob_handle, cmd)
        if info:
            raise ValueError('网关已存在')
        value_info = {
            "mini_id": request_data.mini_id,
            "note_id": request_data.note_id,
            "gateway_id": gateway_id,
            "type": 5,
            "add_time": timer.get_now(),
            "update_time": timer.get_now(),
        }
        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_pod_pile', [value_info])
    else:
        macuid_list = request_data.macuid_list
        value_list = []
        for macuid in macuid_list:
            cmd = f"select * from wxapp_pod_pile where snum='{macuid['snum']}' and serialnum='{macuid['serialnum']}'"
            info = sob.select_mysql_record(sob_handle,cmd)
            if info:
                raise ValueError(f'{macuid} 已存在')
            value_info = {
                "mini_id": request_data.mini_id,
                "note_id": request_data.note_id,
                "serialnum": macuid['serialnum'],
                "snum": macuid['snum'],
                "type": type,
                "add_time": timer.get_now(),
                "update_time": timer.get_now(),
            }
            value_list.append(value_info)
        sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_pod_pile', value_list)
    sob.sql_close(sob_handle)
    return



def _delete_pod_pile(request_data: DeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    if request_data.is_force_delete == False:
        cmd = f"select * from wxapp_pod_pile where id={request_data.id}"
        info = sob.select_mysql_record(sob_handle,cmd)
        if info:
            pod_pile = info[0]
            if pod_pile.type == 2 or pod_pile.type == 4:
                data = {}
                data['token'] = 'qfevserver'
                data['id'] = request_data.id
                data['ip'] = pod_pile.lastip
                data['command'] = 'delete_pile'
                sock_data = 'evapi|{}'.format(json.dumps(data))
                server1 = TCPClient(TCP_PORT)
                server1.send_msg(sock_data)
                try:
                    resp = server1.recv_msg()
                    server1.close()
                    resp = json.loads(resp)
                    return resp
                except:
                    server1.close()
                    print('接收数据失败')
                    raise ValueError('删除失败')
    cmd = f"delete from wxapp_pod_pile where id={request_data.id}"
    sob.delete_mysql_record(sob_handle,cmd)
    cmd = f"delete from wxapp_pod_pileport where pile_id={request_data.id}"
    sob.delete_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    return


def _update_pod_pile(request_data: UpdateFilterFormat):
    request_dict = request_data.dict()
    request_dict.update({"add_time": timer.get_now(), "update_time": timer.get_now()})
    del request_dict['pod_pileports']
    hope_lst = list(request_dict.keys())
    hope_lst.remove('add_time')
    sob_handle = sob.sql_open(db_config)
    sob.insert_Or_update_mysql_record_many_new(sob_handle, 'wxapp_pod_pile', [request_dict], hope_lst)
    cmd = f"delete from wxapp_pod_pileport where pile_id={request_data.id}"
    sob.delete_mysql_record(sob_handle, cmd)
    value_list = []
    for pileport in request_data.pod_pileports:
        value_info = {
            "mini_id":request_data.mini_id,
            "note_id":request_data.note_id,
            "pile_id":request_data.id,
            "serialnum":request_data.serialnum,
            "portnum":pileport['portnum'],
            "portvoltage":pileport['portvoltage'],
            "portelectric":pileport['portelectric'],
            "portpulse":pileport['portpulse'],
            "portstatus":pileport['portstatus'],
            "trouble_status":pileport['trouble_status'],
        }
        value_list.append(value_info)
    sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_pod_pileport',value_list)
    sob.sql_close(sob_handle)
    return




#【获取充电桩】
def get_pod_pile(request_data: QueryFilterFormat):
    try:
        res = _get_pod_pile(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【创建充电桩】
def create_pod_pile(request_data: CreateFilterFormat):
    try:
        res = _create_pod_pile(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}




#【编辑充电桩】
def update_pod_pile(request_data: UpdateFilterFormat):
    try:
        res = _update_pod_pile(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

#【删除充电桩】
def delete_pod_pile(request_data: DeleteFilterFormat):
    try:
        res = _delete_pod_pile(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class BatchDeleteFilterFormat(BaseModel):
    note_id: int = Field(..., description="社区id")
def _batch_delete_pod_pile(request_data: BatchDeleteFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_pod_pile where note_id={request_data.note_id} and (type=2 or type=4)"
    piles_info = sob.select_mysql_record(sob_handle,cmd)
    if piles_info:
        pile_info = piles_info[0]
        data = {}
        data['token'] = 'qfevserver'
        data['mini_id'] = pile_info['mini_id']
        data['note_id'] = request_data.note_id
        data['command'] = 'delete_batch_pile'
        data['ip'] = pile_info['lastip']
        sock_data = 'evapi|{}'.format(json.dumps(data))

        server1 = TCPClient(TCP_PORT)
        server1.send_msg(sock_data)
        server1.close()

    cmd = f"select * from wxapp_pod_pile where note_id={request_data.note_id} and (type=1 or type=3)"
    piles_info = sob.select_mysql_record(sob_handle, cmd)
    for pile in piles_info:
        cmd = f"delete from wxapp_pod_pile where id={pile['id']}"
        sob.delete_mysql_record(sob_handle,cmd)
        cmd = f"delete from wxapp_pod_pileport where pile_id={pile['id']}"
        sob.delete_mysql_record(sob_handle, cmd)
    sob.sql_close(sob_handle)
    return
#【批量删除充电桩】
def batch_delete_pod_pile(request_data: BatchDeleteFilterFormat):
    try:
        res = _batch_delete_pod_pile(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class OtaFilterFormat(BaseModel):
    gateway_id: str = Field(..., description="充电桩id")
    type: int = Field(..., description="1:网关 2:十二口")

def _ota_upgrade(request_data:OtaFilterFormat):
    sob_handle = sob.sql_open(db_config)
    if request_data.type == 1:
        cmd = f"select * from wxapp_pod_pile where gateway_id='{request_data.gateway_id}'"
    else:
        cmd = f"select * from wxapp_pod_pile where snum='{request_data.gateway_id}'"
    info = sob.select_mysql_record(sob_handle,cmd)
    if info:
        pod_pile = info[0]
        data = {}
        data['token'] = 'qfevserver'
        data['command'] = 'ota_upgrade'
        data['snum'] = request_data.gateway_id
        data['ip'] = pod_pile.lastip
        sock_data = 'evapi|{}'.format(json.dumps(data))
        print(sock_data)
        server1 = TCPClient(TCP_PORT)
        server1.send_msg(sock_data)
        try:
            resp = server1.recv_msg()
            server1.close()
            resp = json.loads(resp)
            return resp
        except:
            server1.close()
            return
    else:
        raise ValueError('充电桩不存在')


#【ota升级】
def ota_upgrade(request_data:OtaFilterFormat):
    try:
        res = _ota_upgrade(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class DataFilterFormat(BaseModel):
    gateway_id: str = Field(..., description="充电桩id")
    type: int = Field(..., description="1:网关 2:十二口")
    data: str = Field(..., description="data")

def _data_otas_upgrade(request_data:DataFilterFormat):
    sob_handle = sob.sql_open(db_config)
    if request_data.type == 1:
        cmd = f"select * from wxapp_pod_pile where gateway_id='{request_data.gateway_id}'"
    else:
        cmd = f"select * from wxapp_pod_pile where snum='{request_data.gateway_id}'"
    info = sob.select_mysql_record(sob_handle, cmd)
    if info:
        data = {}
        data['token'] = 'qfevserver'
        data['command'] = 'upgrade'
        data['repmsg'] = request_data.data
        data['ip'] = info[0]['lastip']
        sock_data = 'evapi|{}'.format(json.dumps(data))
        server1 = TCPClient(TCP_PORT)
        server1.send_msg(sock_data)
        try:
            resp = server1.recv_msg()
            server1.close()
            resp = json.loads(resp)
            return resp
        except:
            server1.close()
            raise ValueError('升级失败')
    else:
        raise ValueError("充电桩不存在")



#【ota升级repmsg】
def data_otas_upgrade(request_data:DataFilterFormat):
    try:
        res = _data_otas_upgrade(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}





class ParamFilterFormat(BaseModel):
    pile_id: str = Field(..., description="充电桩id")
    null_charge_power: float = Field(..., description="空载功率阈值 w")
    null_charge_delay: int = Field(..., description="空载延时（秒）")
    full_charge_power: float = Field(..., description="充满功率阈值 w")
    full_charge_delay: int = Field(..., description="充满延时（秒）")
    high_temperature: int = Field(..., description="高温阈值 度")
    max_recharge_time: int = Field(..., description="最大充电时间 分钟")
    trickle_threshold: int = Field(..., description="涓流阈值 ma")
    threshold_p: float = Field(..., description="功率限值 w")
    threshold_i: float = Field(..., description="过流限值 mA")
    lastip: str = Field(..., description="最后更新ip")


def _set_pile_param(request_data:ParamFilterFormat):
    data = {}
    data['token'] = 'qfevserver'
    data['command'] = 'set_pile_param'
    data['ip'] = request_data.lastip
    data['id'] = request_data.pile_id
    data['null_charge_power'] = request_data.null_charge_power
    data['null_charge_delay'] = request_data.null_charge_delay
    data['full_charge_power'] = request_data.full_charge_power
    data['full_charge_delay'] = request_data.full_charge_delay
    data['high_temperature'] = request_data.high_temperature
    data['max_recharge_time'] = request_data.max_recharge_time # 最大充电时间
    data['trickle_threshold'] = request_data.trickle_threshold  # 涓流阈值
    data['threshold_p'] = request_data.threshold_p  # 功率限值
    data['threshold_i'] = request_data.threshold_i  # 过流限值
    sock_data = 'evapi|{}'.format(json.dumps(data))

    server1 = TCPClient(TCP_PORT)
    server1.send_msg(sock_data)
    try:
        resp = server1.recv_msg()
        server1.close()
        resp = json.loads(resp)
        return resp
    except:
        server1.close()
        raise ValueError('设置失败')


#【设置插座默认参数】
def set_pile_param(request_data:ParamFilterFormat):
    try:
        res = _set_pile_param(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

class GetParamFilterFormat(BaseModel):
    pile_id: int = Field(..., description="充电桩id")

def _get_pile_param(request_data: GetParamFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              *, count(*) over() as total
            from
               wxapp_default_param
            where pile_id={request_data.pile_id}
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

#【获取插座默认参数】
def get_pile_param(request_data:GetParamFilterFormat):
    try:
        res = _get_pile_param(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class RestartFilterFormat(BaseModel):
    ip: str = Field(..., description="ip")


def _restart_pile(request_data:RestartFilterFormat):
    ip = request_data.ip
    data = {}
    data['token'] = 'qfevserver'
    data['command'] = 'restart'
    data['ip'] = ip
    sock_data = 'evapi|{}'.format(json.dumps(data))
    server1 = TCPClient(TCP_PORT)
    server1.send_msg(sock_data)
    try:
        resp = server1.recv_msg()
        resp = json.loads(resp)
        server1.close()
        return resp
    except:
        server1.close()
        raise ValueError('重启失败')

#【充电桩重启】
def restart_pile(request_data:RestartFilterFormat):
    try:
        res = _restart_pile(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


class NetFilterFormat(BaseModel):
    gateway_id: str = Field(..., description="网关id")
    ip: str = Field(..., description="ip")

def _networknode_pile(request_data:NetFilterFormat):
    data = {}
    data['token'] = 'qfevserver'
    data['onlytag'] = request_data.gateway_id
    data['command'] = 'refresh_pile'
    data['ip'] = request_data.ip
    sock_data = 'evapi|{}'.format(json.dumps(data))
    server1 = TCPClient(TCP_PORT)
    server1.send_msg(sock_data)
    try:
        resp = server1.recv_msg()
        server1.close()
        resp = json.loads(resp)
        return resp
    except:
        raise ValueError('组网失败')


#【充电桩组网】
def networknode_pile(request_data:NetFilterFormat):
    try:
        res = _networknode_pile(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}

