import os

from celery import Celery

# 1. 创建示例对象
app = Celery("changing_project")


import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. 加载配置
app.config_from_object("celery_task.config")
# 3. 注册任务[自动搜索并加载任务]
# 参数必须必须是一个列表，里面的每一个任务都是任务的路径名称
# app.autodiscover_tasks(["任务1","任务2"])
# app.autodiscover_tasks(["celery_task.tasks"])
app.autodiscover_tasks(["celery_task"])

# 4. 在终端下面运行celery命令启动celery
# celery -A 主程序 worker --loglevel=info
# celery -A celery_tasks.main worker --loglevel=info