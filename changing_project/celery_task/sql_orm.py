from pymysql import *
import pymysql

class MysqlHelp(object):
    """mysql常用方法的封装"""
    myql_params = {
        "host": "60.204.222.113",
        "user": "root",
        "password": "Qf123456",
        "port": 3306,
        "database": "qf_change",
        "charset": "utf8mb4",
    }

    # myql_params = {
    #         'host': 'gz-cdb-7nx563pl.sql.tencentcdb.com',
    #         'port': 57041,
    #         'user': 'evqf',
    #         'password': 'zx973956',
    #         'database': 'evqf_ygg_com_cn',
    #          'charset': 'utf8'
    # }

    # myql_params = {
    #     'host': '182.254.162.40',
    #     'port': 3306,
    #     'user': 'root',
    #     'password': '973956',
    #     'database': 'zxcloud_unzstar_com',
    #     'charset': 'utf8'
    # }

    @classmethod
    def getall(cls, field, table_name,where=None):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象
        sql = "select %s from %s" % (field, table_name)
        if where:
            sql = "select %s from %s where %s" % (field, table_name,where)
        print(sql)
        cr_obj.execute(sql)
        resp = cr_obj.fetchall()
        index = cr_obj.description
        result = []
        for res in resp:
            row = {}
            for i in range(len(index)):
                row[index[i][0]] = res[i]
            result.append(row)
        cr_obj.close()
        return result

    @classmethod
    def getnum(cls, field, table_name, where=None):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象
        sql = "select %s _num_ from %s" % (field, table_name)
        if where:
            sql = "select %s from %s where %s" % (field, table_name, where)
        cr_obj.execute(sql)
        resp = cr_obj.fetchall()
        index = cr_obj.description
        result = []
        for res in resp:
            row = {}
            for i in range(len(index)):
                row[index[i][0]] = res[i]
            result.append(row)
            result = result[0]['_num_']
        cr_obj.close()
        return result



    @classmethod
    def get(cls, field, table_name, where=None):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象
        sql = "select %s from %s" % (field, table_name)
        if where:
            sql = "select %s from %s where %s" % (field, table_name,where)
            # print(sql)
        cr_obj.execute(sql)
        # return cls.cr_obj.fetchone()  # 获取一数据
        res = cr_obj.fetchone()
        index = cr_obj.description
        row = {}
        for i in range(len(index)):
            row[index[i][0]] = res[i]
        cr_obj.close()
        return row


    @classmethod
    def group(cls, field, table_name, where=None,group=None):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象
        sql = "select %s from %s" % (field, table_name)
        if where and group:
            sql = "select %s from %s where %s group by %s" % (field, table_name, where,group)
        else:
            if where:
                sql = "select %s from %s where %s" % (field, table_name, where)
            if group:
                sql = "select %s from %s group by %s" % (field, table_name, group)
        print(sql)
        cr_obj.execute(sql)
        resp = cr_obj.fetchall()
        index = cr_obj.description
        result = []
        for res in resp:
            row = {}
            for i in range(len(index)):
                row[index[i][0]] = res[i]
            result.append(row)
        cr_obj.close()
        return result


    @classmethod
    def insert(cls, table_name, field_name, field_value):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象
        sql = "insert into {} ({}) values ({})".format(table_name, field_name, field_value)
        # print(sql)
        ret = cr_obj.execute(sql)
        # print(ret)
        conn.commit()
        cr_obj.close()

    @classmethod
    def update(cls, table_name, field,where):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象
        sql =  "update {} set {} where {}".format(table_name, field, where)
        ret = cr_obj.execute(sql)
        conn.commit()
        cr_obj.close()

    @classmethod
    def delete(cls, table_name, field):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象
        # field_value = "'"+field_value+"'"
        ret = cr_obj.execute("delete from %s where %s" % (table_name, field))
        conn.commit()
        cr_obj.close()

    @classmethod
    def create(cls,table_name,sql):
        mysql_params = MysqlHelp.myql_params
        conn = Connection(**mysql_params)  # 获取连接对象
        cr_obj = conn.cursor()  # 获取cursor对象

        # 如果存在student表，则删除
        # cr_obj.execute("DROP TABLE IF EXISTS {}".format(table_name))

        # 创建student表
        sql = """
               create table IF NOT EXISTS {}(
               {})
           """.format(table_name,sql)
        try:
            # 执行SQL语句
            cr_obj.execute(sql)
        except Exception as e:
            print("创建数据库失败：case%s" % e)
        finally:
            # 关闭游标连接
            cr_obj.close()



if __name__ == '__main__':
    # ret = MysqlHelp.get("*", "students", 4)
    # print(ret)
    # ret1 = MysqlHelp.insert("students",("name","age","high"),("老王","10","190"))
    #
    # ret1 = MysqlHelp.update("students",{"field_name":"high","field_value":"178","c_field":"id","f_field":15})
    # print(ret1)
    ret2 = MysqlHelp.delete("students","name","老王")

    MysqlHelp.close()