from pydantic import BaseModel, Field

from config import db_config
from tool.format_data import format_response_data
from tool.logger import MyLogger
from tool.wf_mysql import wf_mysql_class
from tool.wf_time_new import wf_time_new

prolog = MyLogger("main", level=20).logger
sob = wf_mysql_class(cursor_type=True)
timer = wf_time_new()


class BindFilterFormat(BaseModel):
    note_id: int = Field(..., description="社区id")
    mini_id: int = Field(..., description="小程序id")
    user_id: int = Field(..., description="用户id")
    type: int = Field(..., description="1:IC卡 2:RFID")
    cardid: str = Field(..., description="卡号")


def _bind_door_cards(request_data: BindFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select * from wxapp_door_cards where type={request_data.type} and cardid='{request_data.cardid}'"
    door_cards = sob.select_mysql_record(sob_handle,cmd)
    if not door_cards:
        raise ValueError('无效卡')
    cmd = f"select * from wxapp_door_idno where user_id={request_data.user_id}"
    door_idno = sob.select_mysql_record(sob_handle,cmd)
    if door_idno:
        door_idno = door_idno[0]
        if request_data.type == 1:
            if request_data.cardid != door_idno['idno']:
                cmd = f"select * from wxapp_door_idno where idno='{request_data.cardid}'"
                exist = sob.select_mysql_record(sob_handle,cmd)
                if exist:
                    raise ValueError('充电卡已被绑定')
            cmd = f"update wxapp_door_idno set idno='{request_data.cardid}',note_id={request_data.note_id} where user_id={request_data.user_id}"
            sob.update_mysql_record(sob_handle,cmd)
        else:
            if request_data.cardid != door_idno['rfid']:
                cmd = f"select * from wxapp_door_idno where rfid='{request_data.cardid}'"
                exist = sob.select_mysql_record(sob_handle,cmd)
                if exist:
                    raise ValueError('门禁卡已被绑定')
            cmd = f"update wxapp_door_idno set rfid='{request_data.cardid}',note_id={request_data.note_id} where user_id={request_data.user_id}"
            sob.update_mysql_record(sob_handle,cmd)
    else:
        value_info = {
            'mini_id': request_data.mini_id,
            'user_id': request_data.user_id,
            'note_id': request_data.note_id,
            'add_time': timer.get_now(),
            'update_time': timer.get_now()
        }
        if request_data.type == 1:
            cmd = f"select * from wxapp_door_idno where idno='{request_data.cardid}'"
            exist = sob.select_mysql_record(sob_handle, cmd)
            if exist:
                raise ValueError('充电卡已被绑定')
            value_info.update({'idno':request_data.cardid})
        else:
            cmd = f"select * from wxapp_door_idno where rfid='{request_data.cardid}'"
            exist = sob.select_mysql_record(sob_handle, cmd)
            if exist:
                raise ValueError('门禁卡已被绑定')
            value_info.update({'rfid': request_data.cardid})
        sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_door_idno',[value_info])
    sob.sql_close(sob_handle)
    return ''




#【小程序绑定充电/门禁卡】
def bind_door_cards(request_data: BindFilterFormat):
    try:
        res = _bind_door_cards(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}




class CardFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")


def _get_user_door_cards(request_data: CardFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"select note_name,a.* from wxapp_door_idno a left join wxapp_note b on a.note_id=b.id where user_id='{request_data.user_id}'"
    door_idno = sob.select_mysql_record(sob_handle,cmd)
    door_idno = door_idno[0] if door_idno else ''
    sob.sql_close(sob_handle)
    return {'door_idno':door_idno}



#【小程序获取用户充电/门禁卡】
def get_user_door_cards(request_data: CardFilterFormat):
    try:
        res = _get_user_door_cards(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}



class UnBindFilterFormat(BaseModel):
    user_id: int = Field(..., description="用户id")
    type: int = Field(..., description="1:IC卡 2:RFID")


def _unbind_door_cards(request_data: UnBindFilterFormat):
    sob_handle = sob.sql_open(db_config)
    if request_data.type == 1:
        cardid = 'idno'
    else:
        cardid = 'rfid'
    cmd = f"update wxapp_door_idno set {cardid}='' where user_id={request_data.user_id}"
    sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)

# 【小程序解绑充电/门禁卡】
def unbind_door_cards(request_data: UnBindFilterFormat):
    try:
        res = _unbind_door_cards(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}