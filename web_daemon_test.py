import unittest
from web_daemon import WebDaemon


class WebDaemonTestCase(unittest.TestCase):
    def test_mysql_select(self):
        res = self.daemon.mysql_select("select * from `weibo_checkin_area`", None)
        print(res[0])
        res = self.daemon.mysql_select("select * from `weibo_checkin_area`", None, 1)
        res = self.daemon.mysql_select("select * from `weibo_checkin_area`", None, 2)

    def test_mysql_update(self):
        res = self.daemon.mysql_execute("update `weibo_checkin_poitask` set `progress`= ? where id = ?", (5, '12'))
    # def test_redis_lfind(self):
    #     self.assertEqual(self.daemon.redis_lfind("bbbb", "a"), -2)
    #     self.assertEqual(self.daemon.redis_lfind("bbb", "a"), -1)
    #     self.assertEqual(self.daemon.redis_lfind("bbb", "2"), 1)

    def setUp(self):
        self.daemon = WebDaemon('/tmp/watch_process.pid', stdout="/dev/stdout")
        # print('preparing data for testing...')
        # self.daemon.mysql_execute("""INSERT INTO `weibo_checkin_poitask`
        #                                     (`id`, `status`, `progress`, `created_at`, `start_time`, `end_time`,
        #                                     `poi_count`, `area_id`, `last_error`, `poi_add_count`)
        #                             VALUES ('0', '1', '0', '2017-03-09 16:34:14.998110', NULL, NULL,
        #                             '0', '5', '', '0')""", None)
        # self.daemon.mysql_conn.commit()

    def tearDown(self):
        # print('tearDown...')
        pass


if __name__ == '__main__':
    unittest.main()
