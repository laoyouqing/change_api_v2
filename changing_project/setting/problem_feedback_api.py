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
    id: int = Field(None, description="问题反馈id (mini_id,id二选一)")
    user_id: int = Field(None, description="用户id")
    offset: int = Field(0, description="偏移量")
    size: int = Field(20, description="页面大小")


class CreateFilterFormat(BaseModel):
    mini_id: int = Field(..., description="小程序id")
    id: int = Field(None, description="id")
    type_id: int = Field(..., description="问题类型id")
    note_id: int = Field(..., description="社区id")
    user_id: int = Field(..., description="用户id")
    problem_detail: str = Field(..., description="问题描述")


class DealFilterFormat(BaseModel):
    id: int = Field(..., description="问题反馈id")
    is_status: int = Field(..., description="维修状态 (10待处理 20已处理)")


def _generate_where_sql(request_data):
    where_lst = []
    mini_id = request_data['mini_id']
    id = request_data['id']
    user_id = request_data['user_id']
    if not any([mini_id, id]):
        raise ValueError("mini_id、id二选一")
    if mini_id:
        where_lst.append(f"mini_id={mini_id}")
    if id:
        where_lst.append(f"id={id}")
    if user_id:
        where_lst.append(f"user_id={user_id}")
    where_sql = (" where " if where_lst else "") + " and ".join('%s' % rec for rec in where_lst)
    return where_sql


def _get_problem_feedback(request_data: QueryFilterFormat):
    request_dict = request_data.dict()
    where_sql = _generate_where_sql(request_dict)
    sob_handle = sob.sql_open(db_config)
    cmd = f"""
            select 
              *, count(*) over() as total
            from
               wxapp_problem_feedback
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


def _create_problem_feedback(request_data: CreateFilterFormat):
    request_dict = request_data.dict()
    request_dict.update({"add_time":timer.get_now()})
    hope_lst = list(request_dict.keys())
    hope_lst.remove('add_time')
    sob_handle = sob.sql_open(db_config)
    flag = sob.insert_Or_update_mysql_record_many_new(sob_handle,'wxapp_problem_feedback',[request_dict],hope_lst)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return

def _deal_problem_feedback(request_data: DealFilterFormat):
    sob_handle = sob.sql_open(db_config)
    cmd = f"update wxapp_problem_feedback set is_status={request_data.is_status} where id={request_data.id}"
    flag = sob.update_mysql_record(sob_handle,cmd)
    sob.sql_close(sob_handle)
    if flag == -1:
        raise
    else:
        return


#【获取问题反馈】
def get_problem_feedback(request_data: QueryFilterFormat):
    try:
        res = _get_problem_feedback(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【创建修改问题反馈】
def create_problem_feedback(request_data: CreateFilterFormat):
    try:
        res = _create_problem_feedback(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


#【删除问题反馈】
def deal_problem_feedback(request_data: DealFilterFormat):
    try:
        res = _deal_problem_feedback(request_data)
        response = format_response_data(res)
        return response
    except Exception as exc:
        return {"status": 400, "msg": exc.__str__()}


