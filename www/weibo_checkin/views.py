from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.forms.models import model_to_dict
from .models import Area, POITask
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


def _execute_task(taskid):
    """ 执行任务，在开始或继续任务时进行 """
    # 1. 更新MySQL，poi_task，status为2：进行中，last_error清空。
    poi_task = POITask.objects.get(pk=taskid)
    poi_task.status = 2
    poi_task.last_error = ""
    poi_task.save()
    # 2. 更新Redis，更新poi_task_todo_list。
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.rpush("poi_task_todo_list", taskid)
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
    # task_worker = POITaskWorker(task=new_task,
    #                             worker=1,
    #                             min_lat=area.min_lat,
    #                             max_lat=area.max_lat,
    #                             min_lon=area.min_lon,
    #                             max_lon=area.max_lon,
    #                             )
    # task_worker.save()

    # poi_task，status为1：已分配。
    new_task.status = 1
    new_task.save()

    # 2.2 更新Redis。
    # poi_task_*_worker_list
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.rpush("poi_task_" + str(new_task.id) + "_worker_list", 1)
    # poi_task_*_worker_*。
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "min_lat", area.min_lat)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "max_lat", area.max_lat)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "min_lon", area.min_lon)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "max_lon", area.max_lon)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "cur_lat", area.min_lat)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "cur_lon", area.min_lon)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "progress", 0)
    r.hset("poi_task_" + str(new_task.id) + "_worker_1", "errormsg", "")

    # 3. 执行任务。
    _execute_task(new_task.id)

    return JsonResponse(APIResult(is_success=True, message="新建更新任务成功，请等待后台处理。"))


def pause_area(request):
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    area = Area.objects.get(pk=request.POST['id'])
    task = POITask.objects.filter(area=area).filter(status=2).order_by('created_at').reverse()[:1]
    if task.count() == 0:
        return JsonResponse(APIResult(is_success=False, message="操作失败，没有进行中的任务。"))
    task = task[0]
    r.set("poi_" + str(task.id) + "_to_pause", 1)
    return JsonResponse(APIResult(is_success=True, message="任务暂停成功，请等待后台处理。"))


def continue_area(request):
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    area = Area.objects.get(pk=request.POST['id'])
    task = POITask.objects.filter(area=area).filter(status=3).order_by('created_at').reverse()[:1]
    if task.count() == 0:
        return JsonResponse(APIResult(is_success=False, message="操作失败，没有进行中的任务。"))
    task = task[0]
    _execute_task(task.id)
    return JsonResponse(APIResult(is_success=True, message="任务将继续执行，请等待后台处理。"))


def get_pois_task(request):
    areas = Area.objects.all()
    res = []
    for area in areas:
        item = {"id": area.id, "last_poi_count": area.poi_count}
        task = POITask.objects.filter(area=area).order_by('created_at').reverse()
        if task.count() == 0:
            item["last_update"] = ""
            item["show_button"] = "update"
        else:
            item["last_update"] = task[0].created_at.strftime('%Y-%m-%d %H:%M:%S')
            if task[0].status == 3:
                item["show_button"] = "continue"
            elif task[0].status == 4:
                item["show_button"] = "update"
            else:
                item["show_button"] = "pause"
            item["progress"] = task[0].progress
            item["poi_count"] = task[0].poi_count
            item["poi_add_count"] = task[0].poi_add_count
            item["last_error"] = task[0].last_error
        res.append(item)

    return JsonResponse(APIResult(is_success=True, data=res))


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
