daemon=False #是否守护
bind='0.0.0.0:9088'#绑定
worker_class='uvicorn.workers.UvicornWorker'
workers=2
loglevel='debug' # 日志级别
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
accesslog = "gunicorn_access.log"
errorlog = "gunicorn_error.log"



