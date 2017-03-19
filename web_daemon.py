import logging
import sys
import os
import time
import redis
import MySQLdb

from daemon import Daemon


class WebDaemon(Daemon):
    def __init__(self, pidfile, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        super().__init__(pidfile, stdin, stdout, stderr)
        self.mysql_conn = MySQLdb.connect(host="localhost", user="root",
                                          passwd="admin", db="weibo_checkin")
        self.redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        logging.info("web daemon init.")

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

    def redis_lfind(self, key, value):
        if not self.redis_conn.exists(key):
            return -1
        length = self.redis_conn.llen(key)
        for i in range[0:length - 1]:
            if value == self.redis_conn.lindex(key, i):
                return i
        return -1

    def run(self):
        while True:
            sys.stdout.write('%s:WebDaemon looping\n' % (time.ctime(),))
            sys.stdout.flush()

            # 对于要继续进行的任务：
            task_todo = self.redis_conn.lpop("poi_task_todo_list")
            if (task_todo):
                self.redis_conn.rpush("poi_task_doing_list", task_todo)
                self.redis_conn.rpush("poi_worker_1_todo_list", task_todo)
                self.redis_conn.hset("poi_task_" + task_todo + "_worker_1", "errormsg", "")

            # 监视所有poi_worker_1_doing_list：
            tasks_doing = self.redis_conn.lrange("poi_task_doing_list", 0, -1)
            for task_doing in tasks_doing:
                workers_count = self.redis_conn.llen("poi_task_" + task_doing + "_worker_list")
                workers = self.redis_conn.lrange("poi_task_" + task_doing + "_worker_list", 0, -1)
                # 任务1：更新progress
                avg_progress = 0
                for worker in workers:
                    progress = self.redis_conn.hget("poi_task_" + task_doing + "_worker_" + worker, "progress")
                    avg_progress += int(progress)
                avg_progress /= workers_count
                avg_progress = int(avg_progress)
                self.mysql_execute("update `weibo_checkin_poitask` set `progress`= ? where id = ?",
                                   (avg_progress, task_doing))

                # 任务2：监控worker
                is_done = 0
                error_found = False
                error_list = []
                for worker in workers:
                    if -1 != self.redis_lfind("poi_worker_" + worker + "_todo_list", task_doing):
                        continue
                    if -1 != self.redis_lfind("poi_worker_" + worker + "_doing_list", task_doing):
                        continue
                    errormsg = self.redis_conn.hget("poi_task_" + task_doing + "_worker_" + worker, "errormsg")
                    if not errormsg:
                        error_found = True
                        error_list.append("Worker #%s error: %s" % (worker, errormsg))
                    is_done += 1
                if is_done != workers_count:
                    continue
                if error_found:
                    self.mysql_execute("update `weibo_checkin_poitask` set `status` = 3 where id = ?", (task_doing,))
                else:
                    self.mysql_execute("update `weibo_checkin_poitask` set `status` = 4 where id = ?", (task_doing,))

            time.sleep(2)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)s[line:%(lineno)d]\n\t%(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename='web_deamon_%s.log' % (time.ctime(),)
    )

    # 守护进程
    daemon = WebDaemon('/tmp/watch_process.pid', stdout="/dev/stdout")
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
