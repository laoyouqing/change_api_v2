#!encoding:utf-8
from decimal import Decimal

import mysql.connector
from mysql.connector import errorcode
import time
import sys
from dbutils.pooled_db import PooledDB
from mysql.connector.custom_types import HexLiteral
from numpy import long

from tool.logger import MyLogger
logger = MyLogger("mysql_log", level=20)
mysql_log = logger.logger


class wf_mysql_class:

    # 构造函数
    def __init__(self, cursor_type=False,connect_pool_config={}):
        """
             :param cursor_type: 是否使用字段返回
             :param connect_pool_config: 连接池配置信息
             :return: 连接成功返回数据库句柄，失败返回None
             """
        self.cursor_type = cursor_type

        if(len(connect_pool_config)!=0):
            self.mysql_pool = PooledDB(mysql.connector, maxconnections=connect_pool_config['db_max_num'],blocking=True, **connect_pool_config['db_config'])


    # 打开数据库
    @staticmethod
    def sql_open(db_config, max_retry: int = 50, time_delay: int = 10):
        """
        :param db_config:
        :param max_retry: 最大重试连接次数50次
        :param time_delay: 每次链接延时10s
        :return: 连接成功返回数据库句柄，失败返回None
        """
        handle = None
        for rec in range(max_retry):
            try:
                handle = mysql.connector.connect(**db_config)
                break
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    mysql_log.info("something is wrong with you user name or password")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    mysql_log.info("database does not exist")
                else:
                    mysql_log.info("mysql init err=[{0}]".format(err))
            except Exception as err:
                mysql_log.error(f"unknown error when connecting to db, error: {err}")
            time.sleep(time_delay)
        return handle

    # 使用连接池打开数据库
    def sql_open_pool(self,max_retry: int = 50, time_delay: int = 10):
        """
        :param max_retry: 最大重试连接次数50次
        :param time_delay: 每次链接延时10s
        :return: 连接成功返回数据库句柄，失败返回None
        """
        handle = None
        for rec in range(max_retry):
            try:
                handle =  self.mysql_pool.connection()
                break
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    mysql_log.info("something is wrong with you user name or password")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    mysql_log.info("database does not exist")
                else:
                    mysql_log.info("mysql init err=[{0}]".format(err))
            except Exception as err:
                mysql_log.error(f"unknown error when connecting to db, error: {err}")
            time.sleep(time_delay)

        return handle

    # 关闭数据库
    @staticmethod
    def sql_close(handle):
        handle.close()

    # mysql转义函数
    @staticmethod
    def escape(value):
        """
        Escapes special characters as they are expected to by when MySQL
        receives them.
        As found in MySQL source mysys/charset.c

        Returns the value if not a string, or the escaped string.
        """
        PY2 = sys.version_info[0] == 2
        if PY2:
            NUMERIC_TYPES = (int, float, Decimal, HexLiteral, long)
        else:
            NUMERIC_TYPES = (int, float)
        if value is None:
            return value
        elif isinstance(value, NUMERIC_TYPES):
            return value
        if isinstance(value, (bytes, bytearray)):
            value = value.replace(b"\\", b"\\\\")
            value = value.replace(b"\n", b"\\n")
            value = value.replace(b"\r", b"\\r")
            value = value.replace(b"\047", b"\134\047")  # single quotes
            value = value.replace(b"\042", b"\134\042")  # double quotes
            value = value.replace(b"\032", b"\134\032")  # for Win32
        else:
            value = value.replace("\\", "\\\\")
            value = value.replace("\n", "\\n")
            value = value.replace("\r", "\\r")
            value = value.replace("\047", "\134\047")  # single quotes
            value = value.replace("\042", "\134\042")  # double quotes
            value = value.replace("\032", "\134\032")  # for Win32
        return value

    # 查询数据库命令。参考下面的select_test函数,推荐使用select_all_cmd命令即可
    def select_mysql_record(self, handle, select_all_cmd="", is_printf=False):
        cnt = 10
        while cnt > 0:
            cursor = handle.cursor(dictionary=self.cursor_type)
            info = 0
            if is_printf == True:
                mysql_log.info("select_cmd={0}".format(select_all_cmd))
            try:
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute(select_all_cmd)
                info = cursor.fetchall()
            except mysql.connector.Error as err:
                mysql_log.info("Something went wrong: {0}".format(err))
                mysql_log.info("mysql err select_cmd={0}".format(select_all_cmd))
                time.sleep(1)
                cnt -= 1
                continue
            break
        if cnt == 0:
            return -1
        else:
            return info

    # 插入表数据,如果存在相同主键，则更新，否则插入。参考下面的insert_update_test函数
    def insert_Or_update_mysql_record_many(
            self,
            handle,
            db_table,
            list_kye,
            list_values,
            hope_update_list,
            is_printf=False,
            hope_cmd="",
            is_ignore=0,
    ):

        cnt = 10
        num = 0
        while cnt > 0:
            cursor = handle.cursor()
            hope_update = ""
            str_key = ",".join(list_kye)
            str_temp = ""
            for line in list_values:
                str_temp += "("
                for value in line:
                    if not isinstance(value, int) and not isinstance(
                            value, float
                    ):  # : python3 not long type
                        if value == None:
                            value = ""
                        try:
                            value = value.encode("UTF-8")
                            value = self.escape(value)
                            value = str(value, "utf-8")  # python3的，byte类型转换为utf-8字符
                        except:
                            pass
                    str_temp += "'" + str(value) + "'" + ","
                str_temp = str_temp[:-1]
                str_temp += ")" + ","
            str_temp = str_temp[:-1]
            if hope_update_list != "":
                for key_tmp in hope_update_list:
                    hope_update += key_tmp + "=" + "VALUES({0})".format(key_tmp)
                    hope_update += ","
                hope_update = hope_update[:-1]
            if hope_cmd == "":
                if hope_update_list != "":
                    insert_cmd = "INSERT INTO {0} ({1}) VALUES {2} ON DUPLICATE KEY UPDATE {3}".format(
                        db_table, str_key, str_temp, hope_update
                    )
                else:
                    insert_cmd = "INSERT INTO {0} ({1}) VALUES {2}".format(
                        db_table, str_key, str_temp
                    )
            else:
                insert_cmd = "INSERT INTO {0} ({1}) VALUES {2} ON DUPLICATE KEY UPDATE {3}".format(
                    db_table, str_key, str_temp, hope_cmd
                )
            # 如果is_ignore=1,表示主键相同,不进行插入操作
            if is_ignore == 1:
                insert_cmd = "INSERT ignore INTO {0} ({1}) VALUES {2} ".format(
                    db_table, str_key, str_temp
                )
            if is_printf == True:
                mysql_log.info("str_value={0}".format(str_temp))
                mysql_log.info("insert_update_cmd={0}".format(insert_cmd))
            try:
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute(insert_cmd)
            except mysql.connector.Error as err:
                mysql_log.info("Something went wrong: {0}".format(err))
                mysql_log.info("mysql err insert_cmd={0}".format(insert_cmd))

                time.sleep(1)
                cnt -= 1
                continue
            break
        num = cursor.rowcount  #
        lastrowid = cursor.lastrowid
        handle.commit()
        if cnt == 0:
            return -1
        else:
            return lastrowid

    def sql_in_str(self, items: list, _char="'"):
        """构造sql , 链接格式"""
        return ", ".join(map(lambda x: f"{_char}{self.escape(x)}{_char}", items))

    def insert_Or_update_mysql_record_many_new(
            self,
            handle,
            db_table,
            list_values,
            hope_update_list="",
            hope_cmd="",
            is_printf=False,
            is_ignore=0
    ):
        """
        批量插入或批量更新数据库---字典形式
        :param handle: 句柄
        :param db_table: 表名
        :param list_values: 包含字段字典的列表
        :param hope_update_list: 主键冲突时，希望更新的字段列表
        :param hope_cmd: 希望执行命令,默认为空
        :param is_printf: 是否打印语句，默认False
        :param is_ignore: 等于1表示主键相同,不进行插入操作。 默认为0
        """
        num = 0
        cnt = 3
        while cnt > 0:
            cursor = handle.cursor()
            if not isinstance(list_values, list):
                raise ValueError("list_values must be a list!")

            str_temp = ""
            str_key = ""
            for values in list_values:
                if str_key == "":
                    str_key = self.sql_in_str([k for k in values.keys()], _char="")
                str_temp += "(" + self.sql_in_str([v for v in values.values()]) + ")" + " ,"
            str_temp = str_temp[:-1]  # 去最后一个逗号
            if hope_update_list != "":
                hope_update = ""
                for key_tmp in hope_update_list:
                    hope_update += key_tmp + "=" + "VALUES({0})".format(key_tmp)
                    hope_update += ","
                hope_update = hope_update[:-1]

            if hope_cmd == "":
                if hope_update_list != "":
                    insert_cmd = "INSERT INTO {0} ({1}) VALUES {2} ON DUPLICATE KEY UPDATE {3}".format(
                        db_table, str_key, str_temp, hope_update
                    )
                else:
                    insert_cmd = "INSERT INTO {0} ({1}) VALUES {2}".format(
                        db_table, str_key, str_temp
                    )
            else:
                insert_cmd = "INSERT INTO {0} ({1}) VALUES {2} ON DUPLICATE KEY UPDATE {3}".format(
                    db_table, str_key, str_temp, hope_cmd
                )
            # 如果is_ignore=1,表示主键相同,不进行插入操作
            if is_ignore == 1:
                insert_cmd = "INSERT ignore INTO {0} ({1}) VALUES {2} ".format(
                    db_table, str_key, str_temp
                )
            if is_printf is True:
                mysql_log.info("str_value={0}".format(str_temp))
                mysql_log.info("insert_update_cmd={0}".format(insert_cmd))
            try:
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute(insert_cmd)
            except mysql.connector.Error as err:
                mysql_log.info("Something went wrong: {0}".format(err))
                mysql_log.info("mysql err insert_cmd={0}".format(insert_cmd))

                time.sleep(1)
                cnt -= 1
                continue
            break
        num = cursor.rowcount
        lastrowid = cursor.lastrowid
        handle.commit()
        if cnt == 0:
            return -1
        else:
            return lastrowid

    # 删除表相关记录
    def delete_mysql_record(self, handle, delete_all_cmd="", is_printf=False):
        cnt = 10
        while cnt > 0:
            cursor = handle.cursor()
            info = 0
            if is_printf == True:
                mysql_log.info("select_cmd={0}".format(delete_all_cmd))
            try:
                cursor.execute(delete_all_cmd)
                handle.commit()
            except mysql.connector.Error as err:
                mysql_log.info("mysql err select_cmd={0}".format(delete_all_cmd))
                time.sleep(1)
                cnt -= 1
                continue
            break
        if cnt == 0:
            return -1
        else:
            return info

    # 更新表数据，推荐直接使用update_all_cmd，参考下面的update_test函数
    def update_mysql_record(self, handle, update_all_cmd="", is_printf=False):

        cnt = 10
        while cnt > 0:
            cursor = handle.cursor()
            if is_printf == True:
                mysql_log.info("update_cmd={0}".format(update_all_cmd))
            try:
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute(update_all_cmd)
            except mysql.connector.Error as err:
                mysql_log.info("Something went wrong: {0}".format(err))
                mysql_log.info("mysql err update_cmd={0}".format(update_all_cmd))
                time.sleep(1)
                cnt -= 1
                continue
            num = cursor.rowcount
            handle.commit()
            return num
        return 0


