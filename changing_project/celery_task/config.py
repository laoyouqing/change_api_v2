# 任务队列的链接地址
from datetime import timedelta

broker_url = 'redis://:1234560@123.60.187.198:6379/5'
# 结果队列的链接地址
result_backend = 'redis://:1234560@123.60.187.198:6379/6'

from celery.schedules import crontab
from .main import app
# 定时任务的调度列表，用于注册定时任务
app.conf.beat_schedule = {
    'check_order_settled_outtime': {
                # 结算
                'task': 'check_order_settled',
                'schedule': crontab(minute=0, hour=0),   # 每天0点0分时刻执行任务
            },
    'create_table_time_electric': {
                # 创建表
                'task': 'create_table_time',
                'schedule': crontab(minute=0, hour=0),   # 每天0点0分时刻执行任务
            },
    'check_pile_online_outtime': {
        # 查看设备是否在线
        'task': 'check_pile_online',
        'schedule': crontab(minute='*/5'),   # 每5分钟执行一次任务

    },
    'check_package_time_outtime': {
            # 充电套餐到期前三天消息提醒
            'task': 'check_package_time',
            'schedule': crontab(minute=0, hour=10),   # 每天10点0分时刻执行任务
            # 'schedule': crontab(),   # 每分时刻执行一次任务
        },
    'check_order_recharges_outtimes': {
                # 检测充电超时-自动下发结束指令
                'task': 'check_order_recharge_outtime',
                'schedule': crontab(minute='*/10'),  # 每10分执行一次任务
                # 'schedule': crontab(),   # 每分时刻执行一次任务
            },
    'check_order_status_outtime': {
                    # 检测异常订单退款
                    'task': 'check_order_status',
                    'schedule': crontab(minute='*/5'),  # 每5分钟执行一次任务
                    # 'schedule': crontab(),   # 每分时刻执行一次任务
                },
    'check_order_fail_refund_outtime': {
                        # 检查启动中订单--退款
                        'task': 'check_order_fail_refund',
                        'schedule': crontab(),   # 每分时刻执行一次任务
                    },
    'check_order_fefund_update_log': {
                        # 检查订单退款记录更新是否成功
                        'task': 'check_order_fefund_update',
                        'schedule': crontab(minute=0, hour=0),   # 每天0点0分时刻执行任务
                    },
    'auto_recharge_package_order_outtime': {
                        # 自动续期
                        'task': 'auto_recharge_package_order',
                        'schedule': crontab(minute=10, hour=0),   # 每天0点10分时刻执行任务
                    },
    'check_package_order_expird_outtime': {
                        # 检测套餐包是否到期
                        'task': 'check_package_order_expird',
                        'schedule': crontab(minute=30, hour=0),   # 每天0点30分时刻执行任务
                    },
    'create_table_day_time_electric': {
                # 创建表
                'task': 'create_day_table_time',
                'schedule': crontab(minute='*/5',hour=15),  # 每5分钟执行一次任务
            },
    # 'order_restart_rechage_outtime': {
    #                     # 重启订单
    #                     'task': 'order_restart_rechage',
    #                     'schedule': 10,   # 每十秒钟一次
    #                 },
    # 'order_over_rechage_outtime': {
    #                     # 结束订单
    #                     'task': 'order_over_rechage',
    #                     'schedule': 30,   # 每十秒钟一次
    #                 }
}

# CELERY_TIMEZONE = "Asia/Shanghai"
# CELERY_ENABLE_UTC = False

app.conf.timezone = "Asia/Shanghai"