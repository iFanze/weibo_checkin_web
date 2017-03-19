import logging
from daemon import Daemon

from weibo import APIClient
from weibo_login import WeiboLogin, WeiboLoginError

import sys
import os
import time
import redis
from worker_config import config
# import aiomysql
import MySQLdb


class WorkerDaemon(Daemon):
    def __init__(self, pidfile, workerid, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        super().__init__(pidfile, stdin, stdout, stderr)
        self.worker_id = workerid
        self.weibo_apps = []
        self.mysql_conn = MySQLdb.connect(host="localhost", user="root",
                                          passwd="admin", db="weibo_checkin")
        self.redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        logging.info("Worker init. workerid: %s" % workerid)

    def mysql_select(self, sql, args, size=None):
        cur = self.mysql_conn.cursor()
        try:
            cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                if size == 1:
                    rs = cur.fetchone()
                else:
                    rs = cur.fetchmany(size)
            else:
                rs = cur.fetchall()
        except BaseException as e:
            raise
        finally:
            cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

    def mysql_execute(self, sql, args):
        cur = self.mysql_conn.cursor()
        try:
            cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
        except BaseException as e:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        finally:
            cur.close()
        logging.info('rows affected: %s' % affected)
        return affected

    def run(self):
        """ 运行worker """
        while True:
            sys.stdout.write('%s:working\n' % (time.ctime(),))
            sys.stdout.flush()
            # 弹出poi_worker_1_todo_list。
            todo = self.redis_conn.lpop("poi_worker_" + str(self.worker_id) + "_todo_list")
            if todo:
                self.redis_conn.rpush("poi_worker_" + str(self.worker_id) + "_doing_list")
                self.execute_poi_task(todo)
            time.sleep(2)

    def read_weibo_apps(self, _config):
        self.weibo_apps = _config

    def execute_poi_task(self, taskid):
        """ 开始/继续一个任务 """
        logging.info("poi task to do. poiid: %s" % taskid)

        # 放进working队列，代表正在进行
        self.redis_conn.rpush("poi_task_" + str(self.worker_id) + "_working", taskid)

        try:
            pid = os.fork()
            if pid == 0:        # 在子进程中进行任务。
                # 得到当前任务进行的信息。
                try:
                    # 只要没有检测到暂停指令，就继续进行任务。
                    while not self.redis_conn.exists("poi_" + str(taskid) + "_to_pause"):
                        time.sleep(5)   # 进行一次兴趣点的下载和插入数据库的操作。
                        # 任务完成
                        if True:
                            logging.info("poi task finish. poiid: %s" % taskid)
                except BaseException as e:
                    # 任务出错。
                    logging.info("poi task error. poiid: %s" % poiid)
                sys.exit()
        except OSError as err:
            sys.stderr.write('fork failed: {0}\n'.format(err))
            sys.exit(1)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)s[line:%(lineno)d]\n\t%(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename='example.log'
    )

    # 守护进程
    daemon = WorkerDaemon('/tmp/watch_process.pid', workerid=config["worker_id"], stdout="/dev/stdout")
    daemon.read_weibo_apps(config["weibo_apps"])

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print('unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        print('usage: %s start|stop|restart' % sys.argv[0])
        sys.exit(2)
#
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s %(filename)s[line:%(lineno)d]\n\t%(levelname)s %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     filename='example.log'
#
# )
#
# APP_KEY = "3226611318"
# APP_SECRET = "4f94b19d1d30c6bce2505e69d22cd62e"
# CALLBACK_URL = "https://api.weibo.com/oauth2/default.html"
#
# print("start login...")
#
# client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
#
# code = ''
# try:
#     code = WeiboLogin("ichen0201@sina.com", "s2013h1cfr", APP_KEY, CALLBACK_URL).get_code()
# except WeiboLoginError as e:
#     print("Login Fail [%s]: %s" % (e.error_code, e.error))
#     exit(1)
#
# print("code: %s" % code)
#
# # client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK_URL)
#
# r = client.request_access_token(code)
#
# access_token = r.access_token
# expires_in = r.expires_in
#
# print("token: %s" % access_token)
# print("expires in %s" % expires_in)
#
# client.set_access_token(access_token, expires_in)
#
# # print(client.statuses.user_timeline.get())
# # print(client.statuses.update.post(status=u'测试OAuth 2.0发微博'))
# # print(client.statuses.upload.post(status=u'测试OAuth 2.0带图片发微博', pic=open('/Users/Fanze/Pictures/Wallpapers/4yzPVohNuVI.jpg')))
#
# print(client.place.nearby.pois.get(lat=30.525985500492297, long=114.36581559753414))
# # print(client.place.poi_timeline.get(poiid="B2094750D26FA1FD4999"))
#
#
# # r = client.statuses.user_timeline.get(uid="1689924681")
# # for st in r.statuses:
# #     print(st.text)
