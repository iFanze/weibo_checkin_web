from django.conf.urls import url

from . import views

urlpatterns = [
    # 主页
    url(r'^$', views.index, name='index'),

    # Area相关
    url(r'^api/area/add/$', views.add_area_api),
    url(r'^api/area/all/$', views.get_areas_api),
    url(r'^api/area/delete/$', views.delete_area_api),
    url(r'^area/all/$', views.get_areas),

    # POI相关
    url(r'^api/area/update/', views.update_area),
    url(r'^api/area/pause/', views.pause_area),
    url(r'^api/area/continue/', views.continue_area),
    url(r'^api/area/(?P<area_id>[0-9]+)/pois/$', views.get_pois),

    # 任务相关
    url(r'^api/task/pois/', views.get_pois_task),

    # 测试
    url(r'test/', views.test),
]