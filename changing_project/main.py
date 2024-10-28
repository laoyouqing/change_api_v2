#!encoding:utf-8
import datetime, time, os, sys, re, json
from fastapi.routing import APIRoute
from jose.constants import ALGORITHMS

from authority.authority_api import get_authority_log, create_authority_log, update_authority_log
from config import SECRET_KEY
from dealer.dealer_note_api import dealer_note_list
from dealer.dealer_order_api import dealer_order_list
from dealer.dealer_withdraw_api import dealer_withdraw_list, dealer_withdraw_apply, dealer_withdraw_audit
from door.door_api import get_pod_door, create_pod_door, delete_pod_door, mini_udp_req
from door.door_cards_api import get_door_cards, create_door_cards, delete_door_cards
from door.mini_door_cards_api import bind_door_cards, get_user_door_cards, unbind_door_cards
from door.mini_user_door_api import wx_door_scancode_payback, tl_door_scancode_payback, wx_door_fefunds_payback, \
    user_door_refund
from door.user_door_idno_api import get_door_idno, create_door_idno, delete_door_idno
from door.user_door_log_api import user_door_log
from node.bill_api import get_bill, create_bill, delete_bill
from node.bill_tranche_api import get_bill_tranche, create_bill_tranche, delete_bill_tranche
from node.note_api import get_note, create_note, delete_note, note_pile_list, note_isagent
from node.note_elecdata_api import get_note_elecdata, create_note_elecdata, delete_note_elecdata
from node.rescue_note_api import get_rescue_note, create_rescue_note, delete_rescue_note
from order.mini_order_api import mini_recharge_emergency, mini_order_fail, mini_user_order_list, mini_order_topay, \
    wx_order_payback, tl_order_payback, wx_order_fefunds_payback
from order.order_api import order_list, delete_order, order_over, order_refunds, order_electric
from order.order_export_api import export_order_list, export_fefund_order_list
from order.refund_order_api import refund_orders_list
from package.mini_recharge_package_api import get_note_recharge_package, recharge_package_buy, recharge_package_due, \
    recharge_package_renew, wx_recharge_package_payback, tl_recharge_package_payback, wx_recharge_package_renew_payback, \
    tl_recharge_package_renew_payback, wx_renew_order_fefunds_payback, wx_package_order_fefunds_payback, \
    is_user_recharge_buy
from package.mini_recharge_plan_api import user_balance, recharge_plan_buy, wx_recharge_plan_buy_payback, \
    tl_recharge_plan_buy_payback, represent_user_balance, wx_recharge_fefunds_payback
from package.package_export_api import export_recharge_order_list, export_recharge_package_order_list, \
    export_package_data
from package.recharge_order_api import recharge_order_list, recharge_order_fefund, delete_recharge_order
from package.recharge_package_api import get_recharge_package, create_recharge_package, delete_recharge_package
from package.recharge_package_order_api import recharge_package_order_list, package_refunds_apply, package_refunds, \
    cancal_package_refunds_apply
from package.recharge_package_order_refund_api import recharge_package_order_refund
from package.recharge_package_order_renew_api import recharge_package_order_renew_list, package_renew_refunds
from package.recharge_plan_api import get_recharge_plan, create_recharge_plan, delete_recharge_plan
from package.recharge_refund_api import get_recharge_refund_log, create_recharge_refund_log, delete_recharge_refund_log
from pile.mini_pile_api import mini_get_note, mini_pile_detail
from pile.pod_pile_api import get_pod_pile, create_pod_pile, delete_pod_pile, update_pod_pile, ota_upgrade, \
    set_pile_param, restart_pile, networknode_pile, batch_delete_pod_pile, data_otas_upgrade, get_pile_param
from pile.pod_pile_trouble import get_pile_trouble, update_pile_trouble
from report.report_api import data_report_total, note_data_report_total, province_data_report_total, \
    country_data_report_total, pile_data_report_total
from report.report_export_api import export_to_excel, export_country_data_report, export_province_data_report, \
    export_note_data_report, export_pile_data_report
from setting.color_api import create_color, delete_color, get_color
from setting.mini_api import get_mini
from setting.operate_record_api import get_operate_record, create_operate_record
from setting.payinfo_api import get_payinfo, create_payinfo
from setting.picture_api import get_pictures, create_pictures, delete_pictures, upload_file
from setting.guide_api import get_guide, create_guide, delete_guide
from setting.problem_feedback_api import deal_problem_feedback, get_problem_feedback, create_problem_feedback
from setting.problem_type_api import get_problem_type, create_problem_type, delete_problem_type
from setting.region_api import get_region
from setting.setting_api import get_setting, create_setting, delete_setting
from tool.logger import MyLogger
from user.authority_api import get_authority, create_authority, delete_authority, set_user_authority
from user.mini_user_api import authorize_login_user, bind_mobile_user, update_user_info
from user.mini_user_balance_log_api import user_balance_log
from user.user_api import register_user, login_user, modify_user, get_user, delete_user, freeze_user, recharge_user
from user.white_list_api import get_white_list, create_white_list, delete_white_list

logger = MyLogger("gross_log", level=20)
track_log = logger.logger
sys.path.append("../")
import uvicorn
from fastapi import FastAPI
import MiddlewareJwtAuth as Tk






routes = [
    #用户
    APIRoute("/api/register_user",endpoint=register_user,methods=['post'],name='账户注册'),
    APIRoute("/api/login_user",endpoint=login_user,methods=['post'],name='账户登录'),
    APIRoute("/api/modify_user",endpoint=modify_user,methods=['post'],name='修改账户信息'),
    APIRoute("/api/get_user",endpoint=get_user,methods=['post'],name='获取用户'),
    APIRoute("/api/delete_user",endpoint=delete_user,methods=['post'],name='删除用户'),
    APIRoute("/api/freeze_user",endpoint=freeze_user,methods=['post'],name='冻结用户'),
    APIRoute("/api/recharge_user",endpoint=recharge_user,methods=['post'],name='用户充值虚拟金额'),
    # 图片
    APIRoute("/api/upload",endpoint=upload_file,methods=['post'],name='上传图片'),
    APIRoute("/api/get_pictures",endpoint=get_pictures,methods=['post'],name='获取图片'),
    APIRoute("/api/create_pictures",endpoint=create_pictures,methods=['post'],name='创建编辑图片'),
    APIRoute("/api/delete_picture",endpoint=delete_pictures,methods=['delete'],name='删除图片'),
    #设置
    APIRoute("/api/get_setting", endpoint=get_setting, methods=['post'], name='获取设置'),
    APIRoute("/api/create_setting", endpoint=create_setting, methods=['post'], name='创建编辑设置'),
    APIRoute("/api/delete_setting", endpoint=delete_setting, methods=['delete'], name='删除设置'),
    #配套颜色
    APIRoute("/api/get_color", endpoint=get_color, methods=['post'], name='获取配套颜色'),
    APIRoute("/api/create_color", endpoint=create_color, methods=['post'], name='创建编辑配套颜色'),
    APIRoute("/api/delete_color", endpoint=delete_color, methods=['delete'], name='删除配套颜色'),
    #用户指南
    APIRoute("/api/get_guide", endpoint=get_guide, methods=['post'], name='获取用户指南'),
    APIRoute("/api/create_guide", endpoint=create_guide, methods=['post'], name='创建编辑用户指南'),
    APIRoute("/api/delete_guide", endpoint=delete_guide, methods=['delete'], name='删除用户指南'),
    #权限
    APIRoute("/api/get_authority", endpoint=get_authority, methods=['post'], name='获取权限'),
    APIRoute("/api/create_authority", endpoint=create_authority, methods=['post'], name='创建编辑权限'),
    APIRoute("/api/delete_authority", endpoint=delete_authority, methods=['delete'], name='删除权限'),
    APIRoute("/api/set_user_authority", endpoint=set_user_authority, methods=['post'], name='设置用户权限'),
    #操作记录
    APIRoute("/api/get_operate_record", endpoint=get_operate_record, methods=['post'], name='获取操作记录'),
    APIRoute("/api/create_operate_record", endpoint=create_operate_record, methods=['post'], name='创建编辑操作记录'),
    #支付信息
    APIRoute("/api/get_payinfo", endpoint=get_payinfo, methods=['post'], name='获取支付信息'),
    APIRoute("/api/create_payinfo", endpoint=create_payinfo, methods=['post'], name='创建编辑支付信息'),
    #所有门禁卡
    APIRoute("/api/get_door_cards", endpoint=get_door_cards, methods=['post'], name='获取门禁卡'),
    APIRoute("/api/create_door_cards", endpoint=create_door_cards, methods=['post'], name='创建编辑门禁卡'),
    APIRoute("/api/delete_door_cards", endpoint=delete_door_cards, methods=['delete'], name='删除门禁卡'),
    # 用户门禁卡
    APIRoute("/api/get_door_idno", endpoint=get_door_idno, methods=['post'], name='获取用户门禁卡'),
    APIRoute("/api/create_door_idno", endpoint=create_door_idno, methods=['post'], name='创建编辑用户门禁卡'),
    APIRoute("/api/delete_door_idno", endpoint=delete_door_idno, methods=['delete'], name='删除用户门禁卡'),
    APIRoute("/api/user_door_log", endpoint=user_door_log, methods=['post'], name='门禁刷卡记录'),
    #问题类型
    APIRoute("/api/get_problem_type", endpoint=get_problem_type, methods=['post'], name='获取问题类型'),
    APIRoute("/api/create_problem_type", endpoint=create_problem_type, methods=['post'], name='创建编辑问题类型'),
    APIRoute("/api/delete_problem_type", endpoint=delete_problem_type, methods=['delete'], name='删除问题类型'),
    #问题反馈
    APIRoute("/api/get_problem_feedback", endpoint=get_problem_feedback, methods=['post'], name='获取问题反馈'),
    APIRoute("/api/create_problem_feedback", endpoint=create_problem_feedback, methods=['post'], name='创建编辑问题反馈'),
    APIRoute("/api/deal_problem_feedback", endpoint=deal_problem_feedback, methods=['delete'], name='处理问题反馈'),
    # 钱包充值套餐
    APIRoute("/api/get_recharge_plan", endpoint=get_recharge_plan, methods=['post'], name='获取钱包充值套餐'),
    APIRoute("/api/create_recharge_plan", endpoint=create_recharge_plan, methods=['post'], name='创建编辑钱包充值套餐'),
    APIRoute("/api/delete_recharge_plan", endpoint=delete_recharge_plan, methods=['delete'], name='删除钱包充值套餐'),
    APIRoute("/api/recharge_order_list", endpoint=recharge_order_list, methods=['post'], name='余额充值记录'),
    # 充电套餐包
    APIRoute("/api/get_recharge_package", endpoint=get_recharge_package, methods=['post'], name='获取充电套餐包'),
    APIRoute("/api/create_recharge_package", endpoint=create_recharge_package, methods=['post'], name='创建编辑充电套餐包'),
    APIRoute("/api/delete_recharge_package", endpoint=delete_recharge_package, methods=['delete'], name='删除充电套餐包'),
    APIRoute("/api/recharge_package_order_list", endpoint=recharge_package_order_list, methods=['post'], name='充电包充值记录'),
    APIRoute("/api/recharge_package_order_refund", endpoint=recharge_package_order_refund, methods=['post'], name='套餐包退款记录'),
    # 救援节点
    APIRoute("/api/get_rescue_note", endpoint=get_rescue_note, methods=['post'], name='获取救援节点'),
    APIRoute("/api/create_rescue_note", endpoint=create_rescue_note, methods=['post'], name='创建编辑救援节点'),
    APIRoute("/api/delete_rescue_note", endpoint=delete_rescue_note, methods=['delete'], name='删除救援节点'),
    # 社区节点
    APIRoute("/api/get_note", endpoint=get_note, methods=['post'], name='获取社区节点'),
    APIRoute("/api/create_note", endpoint=create_note, methods=['post'], name='创建编辑社区节点'),
    APIRoute("/api/delete_note", endpoint=delete_note, methods=['delete'], name='删除社区节点'),
    APIRoute("/api/note_pile_list", endpoint=note_pile_list, methods=['post'], name='社区充电桩详情'),
    APIRoute("/api/note_isagent", endpoint=note_isagent, methods=['post'], name='社区是否已被代理'),
    # 社区电表数据
    APIRoute("/api/get_note_elecdata", endpoint=get_note_elecdata, methods=['post'], name='获取社区电表数据'),
    APIRoute("/api/create_note_elecdata", endpoint=create_note_elecdata, methods=['post'], name='创建编辑社区电表数据'),
    APIRoute("/api/delete_note_elecdata", endpoint=delete_note_elecdata, methods=['delete'], name='删除社区电表数据'),
    # 社区计费
    APIRoute("/api/get_bill", endpoint=get_bill, methods=['post'], name='获取社区计费'),
    APIRoute("/api/create_bill", endpoint=create_bill, methods=['post'], name='创建编辑社区计费'),
    APIRoute("/api/delete_bill", endpoint=delete_bill, methods=['delete'], name='删除社区计费'),
    # 分档计费
    APIRoute("/api/get_bill_tranche", endpoint=get_bill_tranche, methods=['post'], name='获取分档计费'),
    APIRoute("/api/create_bill_tranche", endpoint=create_bill_tranche, methods=['post'], name='创建编辑分档计费'),
    APIRoute("/api/delete_bill_tranche", endpoint=delete_bill_tranche, methods=['delete'], name='删除分档计费'),
    # # 充电桩
    APIRoute("/api/get_pod_pile", endpoint=get_pod_pile, methods=['post'], name='获取充电桩'),
    APIRoute("/api/create_pod_pile", endpoint=create_pod_pile, methods=['post'], name='创建充电桩'),
    APIRoute("/api/update_pod_pile", endpoint=update_pod_pile, methods=['post'], name='编辑充电桩'),
    APIRoute("/api/delete_pod_pile", endpoint=delete_pod_pile, methods=['delete'], name='删除充电桩'),
    APIRoute("/api/batch_delete_pod_pile", endpoint=batch_delete_pod_pile, methods=['delete'], name='批量解绑充电桩'),
    APIRoute("/api/data_otas_upgrade", endpoint=data_otas_upgrade, methods=['post'],name='ota升级 data'),
    APIRoute("/api/ota_upgrade", endpoint=ota_upgrade, methods=['post'], name='ota升级'),
    APIRoute("/api/get_pile_param", endpoint=get_pile_param, methods=['post'], name='获取插座默认参数'),
    APIRoute("/api/set_pile_param", endpoint=set_pile_param, methods=['post'], name='设置插座默认参数'),
    APIRoute("/api/restart_pile", endpoint=restart_pile, methods=['post'], name='充电桩重启'),
    APIRoute("/api/networknode_pile", endpoint=networknode_pile, methods=['post'], name='充电桩组网'),
    APIRoute("/api/get_pile_trouble", endpoint=get_pile_trouble, methods=['post'], name='故障处理列表'),
    APIRoute("/api/update_pile_trouble", endpoint=update_pile_trouble, methods=['post'], name='故障恢复'),
    # # 所有门禁信息
    APIRoute("/api/get_pod_door", endpoint=get_pod_door, methods=['post'], name='获取门禁信息'),
    APIRoute("/api/create_pod_door", endpoint=create_pod_door, methods=['post'], name='创建编辑门禁信息'),
    APIRoute("/api/delete_pod_door", endpoint=delete_pod_door, methods=['delete'], name='删除门禁信息'),
    # 白名单
    APIRoute("/api/get_white_list", endpoint=get_white_list, methods=['post'], name='获取白名单'),
    APIRoute("/api/create_white_list", endpoint=create_white_list, methods=['post'], name='创建编辑白名单'),
    APIRoute("/api/delete_white_list", endpoint=delete_white_list, methods=['delete'], name='删除白名单'),
    # #社区收益
    APIRoute("/api/dealer_withdraw_list", endpoint=dealer_withdraw_list, methods=['post'], name='申请提现列表'),
    APIRoute("/api/dealer_note_list", endpoint=dealer_note_list, methods=['post'], name='社区首页记录列表'),
    APIRoute("/api/dealer_order_list", endpoint=dealer_order_list, methods=['post'], name='分成订单列表'),
    #订单
    APIRoute("/api/order_list", endpoint=order_list, methods=['post'], name='订单列表'),
    APIRoute("/api/export_order_list", endpoint=export_order_list, methods=['post'], name='订单列表导出'),
    APIRoute("/api/export_fefund_order_list", endpoint=export_fefund_order_list, methods=['post'], name='退款订单列表导出'),
]

mini_routes = [
    APIRoute("/api/authorize_login_user",endpoint=authorize_login_user,methods=['post'],name='小程序授权登录'),
    APIRoute("/api/update_user_info",endpoint=update_user_info,methods=['post'],name='小程序设置昵称头像'),
    APIRoute("/api/bind_mobile_user",endpoint=bind_mobile_user,methods=['post'],name='小程序绑定手机号'),
    APIRoute("/api/mini_get_note",endpoint=mini_get_note,methods=['post'],name='小程序充电社区节点列表(城市节点)'),
    APIRoute("/api/mini_pile_detail",endpoint=mini_pile_detail,methods=['post'],name='小程序插座详情'),
    APIRoute("/api/mini_recharge_emergency",endpoint=mini_recharge_emergency,methods=['post'],name='小程序应急充电'),
    APIRoute("/api/mini_order_fail",endpoint=mini_order_fail,methods=['post'],name='小程序充电失败'),
    APIRoute("/api/mini_user_order_list",endpoint=mini_user_order_list,methods=['post'],name='小程序充电记录'),
    APIRoute("/api/get_region",endpoint=get_region,methods=['post'],name='小程序获取城市'),
    APIRoute("/api/get_note_recharge_package",endpoint=get_note_recharge_package,methods=['post'],name='小程序获取社区充电套餐包'),
    APIRoute("/api/recharge_package_buy",endpoint=recharge_package_buy,methods=['post'],name='小程序充电包立即购买/代他充值'),
    APIRoute("/api/recharge_package_due",endpoint=recharge_package_due,methods=['post'],name='小程序充电包即将到期判断'),
    APIRoute("/api/user_balance",endpoint=user_balance,methods=['post'],name='小程序-钱包'),
    APIRoute("/api/recharge_plan_buy",endpoint=recharge_plan_buy,methods=['post'],name='小程序余额充值/代他充值'),
    APIRoute("/api/wx_recharge_plan_buy_payback/{orgid}",endpoint=wx_recharge_plan_buy_payback,methods=['post'],name='小程序余额充值-微信回调'),
    APIRoute("/api/tl_recharge_plan_buy_payback",endpoint=tl_recharge_plan_buy_payback,methods=['post'],name='小程序余额充值-通联回调'),
    APIRoute("/api/wx_order_payback/{orgid}",endpoint=wx_order_payback,methods=['post'],name='小程序充电支付-微信回调'),
    APIRoute("/api/tl_order_payback",endpoint=tl_order_payback,methods=['post'],name='小程序充电支付-通联回调'),
    APIRoute("/api/user_balance_log",endpoint=user_balance_log,methods=['post'],name='小程序-充值/消费记录'),
    APIRoute("/api/represent_user_balance",endpoint=represent_user_balance,methods=['post'],name='小程序-代他充值钱包'),
    APIRoute("/api/recharge_package_renew",endpoint=recharge_package_renew,methods=['post'],name='小程序充电包续费'),
    APIRoute("/api/bind_door_cards",endpoint=bind_door_cards,methods=['post'],name='小程序绑定充电/门禁卡'),
    APIRoute("/api/get_user_door_cards",endpoint=get_user_door_cards,methods=['post'],name='小程序获取用户充电/门禁卡'),
    APIRoute("/api/unbind_door_cards",endpoint=unbind_door_cards,methods=['post'],name='小程序解绑充电/门禁卡'),
    APIRoute("/api/mini_order_topay",endpoint=mini_order_topay,methods=['post'],name='小程序消息订阅-付款'),
    APIRoute("/api/wx_recharge_package_payback/{orgid}",endpoint=wx_recharge_package_payback,methods=['post'],name='小程序套餐包-微信回调'),
    APIRoute("/api/tl_recharge_package_payback",endpoint=tl_recharge_package_payback,methods=['post'],name='小程序套餐包-通联回调'),
    APIRoute("/api/wx_recharge_package_renew_payback/{orgid}/{log_id}",endpoint=wx_recharge_package_renew_payback,methods=['post'],name='小程序套餐包续费-微信回调'),
    APIRoute("/api/tl_recharge_package_renew_payback/{log_id}",endpoint=tl_recharge_package_renew_payback,methods=['post'],name='小程序套餐包续费-通联回调'),
    APIRoute("/api/wx_door_scancode_payback/{orgid}",endpoint=wx_door_scancode_payback,methods=['post'],name='小程序门禁扫码-微信回调'),
    APIRoute("/api/tl_door_scancode_payback",endpoint=tl_door_scancode_payback,methods=['post'],name='小程序门禁扫码-通联回调'),
    APIRoute("/api/wx_order_fefunds_payback/{orgid}",endpoint=wx_order_fefunds_payback,methods=['post'],name='小程序充电退款-微信回调'),
    APIRoute("/api/wx_package_order_fefunds_payback/{orgid}",endpoint=wx_package_order_fefunds_payback,methods=['post'],name='小程序套餐包退款-微信回调'),
    APIRoute("/api/wx_renew_order_fefunds_payback/{orgid}",endpoint=wx_renew_order_fefunds_payback,methods=['post'],name='小程序套餐包续费退款-微信回调'),
    APIRoute("/api/wx_recharge_fefunds_payback/{orgid}",endpoint=wx_recharge_fefunds_payback,methods=['post'],name='小程序余额退款-微信回调'),
    APIRoute("/api/wx_door_fefunds_payback/{orgid}",endpoint=wx_door_fefunds_payback,methods=['post'],name='小程序门禁退款-微信回调'),
    APIRoute("/api/user_door_refund",endpoint=user_door_refund,methods=['post'],name='小程序门禁退款'),
    APIRoute("/api/is_user_recharge_buy",endpoint=is_user_recharge_buy,methods=['post'],name='小程序套餐-判断是否已购买此套餐'),
    APIRoute("/api/cancal_package_refunds_apply",endpoint=cancal_package_refunds_apply,methods=['post'],name='小程序套餐-充电包取消退款申请'),
    APIRoute("/api/recharge_order_fefund",endpoint=recharge_order_fefund,methods=['post'],name='钱包充值套餐退款'),
]

end_routes = [
    APIRoute("/api/data_report_total", endpoint=data_report_total, methods=['post'], name='数据报表'),
    APIRoute("/api/country_data_report_total", endpoint=country_data_report_total, methods=['post'], name='全国数据汇总'),
    APIRoute("/api/export_country_data_report", endpoint=export_country_data_report, methods=['post'], name='全国数据汇总导出'),
    APIRoute("/api/province_data_report_total", endpoint=province_data_report_total, methods=['post'], name='各省份数据汇总'),
    APIRoute("/api/export_province_data_report", endpoint=export_province_data_report, methods=['post'], name='各省份数据汇总导出'),
    APIRoute("/api/note_data_report_total", endpoint=note_data_report_total, methods=['post'], name='各场地数据汇总'),
    APIRoute("/api/export_note_data_report", endpoint=export_note_data_report, methods=['post'], name='各场地数据汇总导出'),
    APIRoute("/api/pile_data_report_total", endpoint=pile_data_report_total, methods=['post'], name='各设备数据汇总'),
    APIRoute("/api/export_pile_data_report", endpoint=export_pile_data_report, methods=['post'], name='各设备数据汇总导出'),
    APIRoute("/api/delete_order", endpoint=delete_order, methods=['post'], name='删除订单'),
    APIRoute("/api/order_over", endpoint=order_over, methods=['post'], name='结束充电'),
    APIRoute("/api/order_refunds", endpoint=order_refunds, methods=['post'], name='充电时长不足-退款'),
    APIRoute("/api/order_electric", endpoint=order_electric, methods=['post'], name='电流图'),
    APIRoute("/api/refund_orders_list", endpoint=refund_orders_list, methods=['post'], name='退款订单列表'),
    APIRoute("/api/dealer_withdraw_apply", endpoint=dealer_withdraw_apply, methods=['post'], name='申请提现'),
    APIRoute("/api/dealer_withdraw_audit", endpoint=dealer_withdraw_audit, methods=['post'], name='申请提现审核'),
    APIRoute("/api/package_refunds_apply", endpoint=package_refunds_apply, methods=['post'], name='充电包退款申请'),
    APIRoute("/api/package_refunds", endpoint=package_refunds, methods=['post'], name='充电包退款'),
    APIRoute("/api/recharge_package_order_renew_list", endpoint=recharge_package_order_renew_list, methods=['post'], name='充电包续费详情'),
    APIRoute("/api/package_renew_refunds", endpoint=package_renew_refunds, methods=['post'], name='充电包续费退款'),
    APIRoute("/api/export_recharge_order_list", endpoint=export_recharge_order_list, methods=['post'], name='充值记录导出'),
    APIRoute("/api/export_recharge_package_order_list", endpoint=export_recharge_package_order_list, methods=['post'], name='充电包充值记录导出'),
    APIRoute("/api/export_package_data", endpoint=export_package_data, methods=['post'], name='充电包数据统计'),
    APIRoute("/api/get_authority_log", endpoint=get_authority_log, methods=['post'], name='获取权限操作记录'),
    APIRoute("/api/create_authority_log", endpoint=create_authority_log, methods=['post'], name='创建权限操作记录'),
    APIRoute("/api/update_authority_log", endpoint=update_authority_log, methods=['post'], name='审核权限操作记录'),
    APIRoute("/api/get_mini", endpoint=get_mini, methods=['post'], name='获取小程序列表'),
    APIRoute("/api/mini_udp_req", endpoint=mini_udp_req, methods=['post'], name='udp操作请求'),
    APIRoute("/api/delete_recharge_order", endpoint=delete_recharge_order, methods=['post'], name='删除充值记录'),
    APIRoute("/api/get_recharge_refund_log", endpoint=get_recharge_refund_log, methods=['post'], name='获取钱包退款记录'),
    APIRoute("/api/create_recharge_refund_log", endpoint=create_recharge_refund_log, methods=['post'], name='创建修改钱包退款记录'),
    APIRoute("/api/delete_recharge_refund_log", endpoint=delete_recharge_refund_log, methods=['delete'], name='删除钱包退款记录'),
]

app = FastAPI(routes=routes+mini_routes+end_routes)

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 关闭Oauth2验证
# app.add_middleware(Tk.AuthenticationMiddlewareMd,
#                    backend=Tk.JWTAuthenticationBackendMd(secret_key=SECRET_KEY, prefix="Bearer",
#                                                          algorithm=ALGORITHMS.HS256))

api_project_name = "充电桩"



if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=9001, log_level="info")
