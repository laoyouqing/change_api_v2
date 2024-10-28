from pydantic import BaseModel

from tool.wf_mysql import wf_mysql_class

sob = wf_mysql_class(cursor_type=True)

def _range_field_cmd(request_dict:dict,param,field):
    where_list = []
    value = request_dict[param]
    if value:
        where_list.append(f"{field}" + " in %s" % '(%s)' % ','.join(
            "\'%s\'" % sob.escape(rec) for rec in value))
    return where_list



def _mm_field_cmd(request_dict:dict,param,field):
    where_list = []
    value_dict = request_dict[param]
    if value_dict:
        for m_type in ("min","max"):
            value = value_dict[m_type]
            if value:
                if m_type == "min":
                    symbol = '>='
                else:
                    symbol = '<='
                where_list.append(f"{field}{symbol}'{value}'")
    return where_list



def format_response_data(res):
    """
    格式化返回体
    """
    return {
        "status":200,
        "msg":"success",
        "data":res,
    }