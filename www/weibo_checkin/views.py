from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.forms.models import model_to_dict
from .models import Area, POITask, POITaskWorker
import json
from django.core.serializers.json import DjangoJSONEncoder

from django.conf import settings
from django.core.cache import cache
import redis


# Create your views here.


class APIResult(dict):
    def __init__(self, is_success, message="", data=None, request=None):
        self.is_success = is_success
        self.message = message
        self.data = data
        self.request = request

    def __str__(self):
        return 'APIResult: %s: %s, request: %s' % ("Success" if self.is_success else "failed",
                                                   self.message, self.request)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(r"'APIResult' object has no attribute '%s'" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value


class APIError(BaseException):
    """ raise APIError if receiving json message indicating failure. """

    def __init__(self, error_code, error, request):
        self.error_code = error_code
        self.error = error
        self.request = request
        BaseException.__init__(self, error)

    def __str__(self):
        return 'APIError: %s: %s, request: %s' % (self.error_code, self.error, self.request)


def index(request):
    # return HttpResponse("Hello, world. You're at the polls index.")
    return render(request, 'weibo_checkin/index_uikit.html')


def add_area_api(request):
    """post: name, minlat, maxlat, minlon, maxlon"""
    name = request.POST['name']
    minlat = request.POST['minlat']
    maxlat = request.POST['maxlat']
    minlon = request.POST['minlon']
    maxlon = request.POST['maxlon']
    area = Area(name=name,
                min_lat=minlat,
                max_lat=maxlat,
                min_lon=minlon,
                max_lon=maxlon)

    area.save()
    return JsonResponse(APIResult(is_success=True))
    # except BaseException as e:


def get_areas_api(request):
    areas = Area.objects.all()

    # areas = serializers.serialize("json", areas)
    # areas_json = json.dumps(list(areas), cls=DjangoJSONEncoder)
    # areas_json = areas.values()
    areas_json = map(model_to_dict, areas)
    return JsonResponse(APIResult(is_success=True, data=list(areas_json)))


def get_areas(request):
    areas = Area.objects.all()
    context = {
        'areas': areas
    }
    return render(request, 'weibo_checkin/nav-areas.html', context)


def delete_area_api(request):
    result = None
    try:
        area = Area.objects.get(pk=request.POST['id'])
        area.delete()
        result = APIResult(is_success=True)
    except Area.DoesNotExist:
        result = APIResult(is_success=False, message=("id为%s的Area不存在" % request.POST['id']))
    return JsonResponse(result)


def _execute_worker(workerid):
    """ 执行任务，在开始或继续任务时进行 """
    # 1. 更新MySQL，poi_task，status为2：进行中，last_error清空。
    poi_task = POITask.objects.get(pk=workerid)
    poi_task.status = 2
    poi_task.last_error = ""
    poi_task.save()
    # 2. 更新Redis，更新poi_task_todo_list。
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.lpush("poi_task_todo_list", workerid)
    # 接下来的工作交给 WebDeamon 和 WorkerDaemon 。


def update_area(request):
    area = Area.objects.get(pk=request.POST['id'])

    # 0. 确定poi_task中是否有未完成的记录。
    poi_tasks = POITask.objects.filter(area=area.id)
    for task in poi_tasks:
        if task.status != 4:
            return JsonResponse(APIResult(is_success=False, message="操作失败。有任务还在进行中，不能再次新建。"))

    # 1. 创建poi_task记录。status为0：未开始。
    new_task = POITask(area=area)
    new_task.save()

    # 2. 分配协作机。
    # 2.1 更新MySQL。
    # poi_task_worker
    task_worker = POITaskWorker(task=new_task,
                                worker=1,
                                min_lat=area.min_lat,
                                max_lat=area.max_lat,
                                min_lon=area.min_lon,
                                max_lon=area.max_lon,
                                )
    task_worker.save()

    # poi_task，status为1：已分配。
    new_task.status = 1
    new_task.save()

    # 2.2 更新Redis。
    # poi_task_*_worker_list
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.rpush("poi_task_1_worker_list", 1)
    # poi_task_*_worker_*。
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "min_lat", task_worker.min_lat)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "max_lat", task_worker.max_lat)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "min_lon", task_worker.min_lon)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "max_lon", task_worker.max_lon)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "cur_lat", task_worker.cur_lat)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "cur_lon", task_worker.cur_lon)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "progress", 0)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "errormsg", "")

    # 3. 执行任务。

    return JsonResponse(APIResult(is_success=True, message="新建更新任务成功，请等待后台处理。"))


def pause_area(request):
    pass


def continue_area(request):
    pass


def get_pois_task(request):
    tasks = POITask.objects.all()
    tasks_json = map(model_to_dict, tasks)
    return JsonResponse(APIResult(is_success=True, data=list(tasks_json)))


def test(request):
    res = APIResult(is_success=True)
    cache.set('b', res)

    cache.lpush('b', 'b')
    # create
    # task = POITask()
    # task.area_id = 1
    # task.save()

    # delete
    # task = POITask.get_by_areaid(1)

    # update

    # query

    return HttpResponse("%s %s" % (cache.get('a'), cache.get('b')))
