#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os


class MyLogger:
    def __init__(self, moudle_name, level=20,
                 log_format="%(asctime)s,%(msecs)d %(name)s:%(levelname)s: [%(module)s(%(lineno)d)] %(message)s",
                 date_format="%Y-%m-%d %H:%M:%S", console_print=True, log_file=None,
                 tr_flag: bool = False, when='MIDNIGHT', backupCount: int = 3, interval: int = 1,
                 robot_key: str = None):
        """
        日志模块
        :param moudle_name:
        :param level: 10 #NOTSET 0 < DEBUG 10 < INFO 20 < WARNING 30 < ERROR 40 < CRITICAL 50
        :param log_format:
        :param date_format:
        :param console_print: 终端输出，开启时，文件日志相关参数失效
        :param log_file: 日志文件路径全称
        :param tr_flag: 是否开启TimedRotatingFileHandler，默认False关闭
        # tr_flag=True时以下参数生效(默认每日0点分割日志文件，并保留3个备份文件数）
        :param when: 日志切分的间隔时间单位
            "S"：Second 秒
            "M"：Minutes 分钟
            "H"：Hour 小时
            "D"：Days 天
            "W"：Week day（0 = Monday）
            "midnight"：Roll over at midnight
        :param backupCount: 保留日志的文件个数
        :param interval: 间隔时间单位的个数
        """
        # 防止产生多个logger，解决重复打印问题
        if str(moudle_name) not in logging.Logger.manager.loggerDict:
            handle_flg = True
        else:
            handle_flg = False

        if console_print is False and log_file is None:
            print("Error: Save log in file, but input not log file!")
            return
        # create logger
        self.logger = logging.getLogger(str(moudle_name))
        self.logger.setLevel(level)
        formatter = logging.Formatter(log_format, date_format)
        if handle_flg is True:
            if console_print is True:
                # create handler，output log to console
                ch = logging.StreamHandler()
                ch.setFormatter(formatter)
                # logger add handler
                self.logger.addHandler(ch)
            else:
                if tr_flag:
                    th = logging.handlers.TimedRotatingFileHandler(filename=log_file, when=when,
                                                                   interval=interval, backupCount=backupCount,
                                                                   encoding='utf-8')
                    th.setFormatter(formatter)
                    self.logger.addHandler(th)
                else:
                    fh = logging.FileHandler(log_file)
                    fh.setFormatter(formatter)
                    # logger add handler
                    self.logger.addHandler(fh)


