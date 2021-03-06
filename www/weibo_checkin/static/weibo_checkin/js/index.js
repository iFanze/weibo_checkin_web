var selected_area = -1;

var map = null;

var draw_mode = false;
var draw_layers = [];
var drawing_manager = null;

var new_area_name = "";

var all_areas = [];

var show_poi = true;
var show_heatmap = true;
var show_cluster = true;

var draw_style = {
    strokeColor: "#0f89f5", //边线颜色。
    fillColor: "#0f89f5", //填充颜色。当参数为空时，圆形将没有填充效果。
    strokeWeight: 2, //边线的宽度，以像素为单位。
    strokeOpacity: 0.8, //边线透明度，取值范围0 - 1。
    fillOpacity: 0.2, //填充的透明度，取值范围0 - 1。
    strokeStyle: 'solid' //边线的样式，solid或dashed。
};

// =============== 常用 =================
function show_message(msg, type = "primary") {
    UIkit.notification({
        message: msg,
        status: type,
        pos: 'top-right',
        timeout: 1000
    });
}

function addDate(dd, dadd) {
    var a = new Date(dd)
    a = a.valueOf()
    a = a + dadd * 24 * 60 * 60 * 1000
    a = new Date(a)
    zero1 = ""
    if (a.getUTCMonth() < 10)
        zero1 = "0"
    zero2 = ""
    if (a.getUTCDate() < 10)
        zero2 = "0"
    return a.getFullYear() + "-" + zero1 + (a.getUTCMonth() + 1) + "-" + zero2 + a.getUTCDate();
}
// =============== 初始化 =================
function init_map() {
    // 初始化百度地图
    map = new BMap.Map("map"); // 创建地图实例
    //var point = new BMap.Point(116.404, 39.915); // 创建点坐标
    map.centerAndZoom("武汉", 13); // 初始化地图，设置中心点坐标和地图级别
    map.addControl(new BMap.NavigationControl());
    map.addControl(new BMap.ScaleControl());
    map.addControl(new BMap.OverviewMapControl());
    map.addControl(new BMap.MapTypeControl());
    map.enableScrollWheelZoom();
    init_draw_mode();
}

function init_control() {
    // 双向拖动条
    $('.nstSlider').nstSlider({
        "left_grip_selector": ".leftGrip",
        "right_grip_selector": ".rightGrip",
        "value_bar_selector": ".bar",
        "highlight": {
            "grip_class": "gripHighlighted",
            "panel_selector": ".highlightPanel"
        },
        "value_changed_callback": function(cause, leftValue, rightValue) {
            $('.leftLabel').text(leftValue);
            $('.rightLabel').text(rightValue);
        },
    });

    time = ["2016-3-30", "2016-4-5", "2016-4-9", "2016-4-13", "2016-4-17", "2016-4-21", "2016-4-25", "2016-4-29"];
    short_time = [];
    for (i in time) {
        x = time[i].slice(5);
        short_time.push(x);
    }
    $(".slider").slider({
        min: 0,
        max: time.length - 1
    }).slider("pips", {
        rest: "label",
        labels: short_time
    });
}

function init_event() {
    $("#add-area-btn").click(function(event) {
        new_area_name = $("#add-area-name").val();
        if (!new_area_name) {
            alert("请输入区域名。");
            return;
        }
        $("#nav-menu-area").hide();
        select_area(-1);
        show_message('请在地图上绘制一个矩形。');
        draw_mode = true;
        open_draw_mode();
    });

    $("#show_poi").click(function(event) {
        if ($("#show_poi").prop("checked"))
            show_poi = true;
        else
            show_poi = false;
        refresh_overlays();
    });

    $("#show_heatmap").click(function(event) {
        if ($("#show_heatmap").prop("checked"))
            show_heatmap = true;
        else
            show_heatmap = false;
        refresh_overlays();
    });

    $("#show_cluster").click(function(event) {
        if ($("#show_cluster").prop("checked"))
            show_cluster = true;
        else
            show_cluster = false;
        refresh_overlays();
    });

    // 为页面添加消息响应函数，在键盘上有按键被按下时触发
    document.onkeydown = chang_page;

    function chang_page() {
        // 如果是左方向键
        if (event.keyCode == 37) {
            var tempDate = new Date();
            tempDate.setFullYear(from_date.substring(0, 4),
                from_date.substring(5, 7),
                from_date.substring(8, 10));
            from_date = addDate(from_date, -1);

            tempDate.setFullYear(to_date.substring(0, 4),
                to_date.substring(5, 7),
                to_date.substring(8, 10));
            to_date = addDate(to_date, -1);

            $("#from-date").val(from_date);
            $("#to-date").val(to_date);
        }
        // 如果是右方向键
        if (event.keyCode == 39) {
            var tempDate = new Date();
            tempDate.setFullYear(from_date.substring(0, 4),
                from_date.substring(5, 7),
                from_date.substring(8, 10));
            from_date = addDate(from_date, 1);

            tempDate.setFullYear(to_date.substring(0, 4),
                to_date.substring(5, 7),
                to_date.substring(8, 10));
            to_date = addDate(to_date, 1);

            $("#from-date").val(from_date);
            $("#to-date").val(to_date);
        }
        // 改变日期后重新获取签到数据、刷新地图
        if (selected_area != -1)
            get_checkins(selected_area, from_date, to_date);
    }
}

// =============== 绘图 =================
function init_draw_mode() {
    //实例化鼠标绘制工具
    drawing_manager = new BMapLib.DrawingManager(map, {
        isOpen: false, //是否开启绘制模式
        enableDrawingTool: false, //是否显示工具栏
        rectangleOptions: draw_style //矩形的样式
    });

    //添加鼠标绘制工具监听事件，用于获取绘制结果
    drawing_manager.addEventListener('overlaycomplete', draw_complete);
}

function draw_complete(e) {
    draw_layers.push(e.overlay);

    sw = e.overlay.getBounds().getSouthWest();
    ne = e.overlay.getBounds().getNorthEast();

    var minlat = sw.lat;
    var maxlat = ne.lat;
    var minlon = sw.lng;
    var maxlon = ne.lng;

    drawing_manager.close();
    if (confirm("确定添加区域『" + new_area_name + "』？")) {
        add_area(new_area_name, minlat, maxlat, minlon, maxlon);
    } else {
        clear_draw();
    }
};

function open_draw_mode() {
    drawing_manager.open();
    drawing_manager.setDrawingMode(BMAP_DRAWING_RECTANGLE);
}

function clear_draw() {
    for (var i = 0; i < draw_layers.length; i++) {
        map.removeOverlay(draw_layers[i]);
    }
    draw_layers.length = 0
}

// =============== Area =================
function add_area(name, minlat, maxlat, minlon, maxlon) {
    $.post('/api/area/add/', {
        name: name,
        minlat: minlat,
        maxlat: maxlat,
        minlon: minlon,
        maxlon: maxlon
    }, function(data, textStatus, xhr) {
        if (data.is_success) {
            show_message('成功添加了一个区域。');
            $("#add-area-name").val("");
            new_area_name = "";
            reload_areas();
        } else
            show_message('区域添加失败，原因：' + data.message, "danger");
    });
}

function reload_areas() {
    select_area(-1);
    $("#area-list li").remove(".area-item");
    $.get('/area/all/', function(data, textStatus, xhr) {
        $("#area-list").append(data);
    });
}

function show_area(minlat, minlon, maxlat, maxlon) {
    var area = new BMap.Polygon([
        new BMap.Point(minlon, minlat),
        new BMap.Point(maxlon, minlat),
        new BMap.Point(maxlon, maxlat),
        new BMap.Point(minlon, maxlat),
    ], draw_style);
    map.addOverlay(area);
    draw_layers.push(area);
}

var poi_infowindows = [];
var poi_markers = [];
var poi_points = [];

var cluster_markers = [];

var MAX = 10000;
var pt = null;

var myIcon = new BMap.Icon("http://api.map.baidu.com/img/markers.png", new BMap.Size(23, 25), {
    offset: new BMap.Size(10, 25), // 指定定位位置  
    imageOffset: new BMap.Size(0, 0 - 10 * 25) // 设置图片偏移  
});

var poi_markers = [];
var poi_titles = [];

var from_date = "2017-04-09";
var to_date = "2017-04-10";

function select_area(id) {
    selected_area = id;
    if (id == -1) {
        $(".cur_area").html("未选择");
        clear_draw();
    } else {
        $(".cur_area").html($("#name_of_" + id).val());
        minlat = parseFloat($("#minlat_of_" + id).val());
        minlon = parseFloat($("#minlon_of_" + id).val());
        maxlat = parseFloat($("#maxlat_of_" + id).val());
        maxlon = parseFloat($("#maxlon_of_" + id).val());
        clear_draw();
        show_area(minlat, minlon, maxlat, maxlon);
        $("#nav-menu-area").hide();
        var point = new BMap.Point((minlon + maxlon) / 2, (minlat + maxlat) / 2); // 创建点坐标
        map.panTo(point);
        $.get('/api/area/' + id + '/pois/', function(data) {
            for (i in data.data) {

                var point = new BMap.Point(data.data[i].lon_baidu, data.data[i].lat_baidu);
                var marker = new BMap.Marker(point, {
                    offset: new BMap.Size(width = 6, height = 15)
                });
                var title = data.data[i].title;

                poi_markers.push(marker);
                poi_titles.push(title);
                // map.addOverlay(marker);
                // addClickHandler(title, marker);
            }
            get_checkins(id, from_date, to_date);
        });
    }
}

function addClickHandler(content, marker) {
    marker.addEventListener("click", function(e) {
        openInfo(content, e)
    });
}

function openInfo(content, e) {
    var p = e.target;
    var point = new BMap.Point(p.getPosition().lng, p.getPosition().lat);
    var opts = {
        width: 250, // 信息窗口宽度    
        height: 100, // 信息窗口高度    
        title: "POI" // 信息窗口标题   
    };
    var infoWindow = new BMap.InfoWindow(content, opts); // 创建信息窗口对象 
    map.openInfoWindow(infoWindow, point); //开启信息窗口
}

function delete_area(id) {
    if (confirm('确定删除区域？')) {
        $.post('/api/area/delete/', {
            id: id
        }, function(data, textStatus, xhr) {
            if (data.is_success) {
                show_message('成功删除了一个区域。');
                oldid = selected_area;
                reload_areas();
            } else
                show_message('区域删除失败，原因：' + data.message, "danger");
        });
    }
}

// =============== POI =================
function toggle_update_area(id, opera) {
    $("#disabled-area-" + id).hide();
    if (opera == "on" || opera == "continue") {
        // 显示pause
        $("#update-area-" + id).hide();
        $("#continue-area-" + id).hide();
        $("#pause-area-" + id).fadeIn();
        $("#area-progress-" + id).fadeIn();
        $("#area-label-" + id).show();
    } else if (opera == "pause") {
        // 显示continue
        $("#pause-area-" + id).hide();
        $("#update-area-" + id).hide();
        $("#continue-area-" + id).fadeIn();
        $("#area-progress-" + id).fadeIn();
        $("#area-label-" + id).hide();
    } else if (opera == "finish") {
        // 显示update
        $("#continue-area-" + id).hide();
        $("#update-area-" + id).fadeIn();
        $("#pause-area-" + id).hide();
        $("#area-progress-" + id).fadeOut();
        $("#area-label-" + id).hide();
    }
}

function disable_area(id) {
    $("#update-area-" + id).hide();
    $("#continue-area-" + id).hide();
    $("#pause-area-" + id).hide();
    $("#disabled-area-" + id).show();
}

function update_area(id) {
    disable_area(id);
    $.post("/api/area/update/", {
        id: id
    }, function(data) {
        if (data.is_success) {
            show_message(data.message)
        } else {
            show_message(data.message, "error")
        }
    })
}

function pause_area(id) {
    disable_area(id);
    $.post("/api/area/pause/", {
        id: id
    }, function(data) {
        if (data.is_success) {
            show_message(data.message)
        } else {
            show_message(data.message, "error")
        }
    })
}

function continue_area(id) {
    disable_area(id);
    $.post("/api/area/continue/", {
        id: id
    }, function(data) {
        if (data.is_success) {
            show_message(data.message)
        } else {
            show_message(data.message, "error")
        }
    })
}

function get_pois_task() {
    $.get("/api/task/pois/", function(data) {
        if (data.is_success) {
            for (var area in data.data) {
                area = data.data[area]
                switch (area.show_button) {
                    case "update":
                        toggle_update_area(area.id, "finish");
                        break;
                    case "pause":
                        toggle_update_area(area.id, "continue");
                        $("#area-" + area.id + "-update-progress").val(area.progress);
                        $("#progress-value-" + area.id).html(area.progress)
                        $("#last-error-value-" + area.id).html(area.last_error)
                        break;
                    case "continue":
                        toggle_update_area(area.id, "pause");
                        $("#area-" + area.id + "-update-progress").val(area.progress);
                        $("#progress-value-" + area.id).html(area.progress)
                        $("#last-error-value-" + area.id).html(area.last_error)
                        break;
                    default:
                        disable_area(area.id);
                }
            }
        } else {
            show_message(data.message, "error")
        }
    });
}

var allHeatmapPoints = [];
var allClusterMarkers = [];
// =============== 可视化 =================

function show_cluster_markers(from, to) {

}

var heatmapOverlay;
var markerClusterer;

function get_checkins(areaid, from, to) {
    show_message(from_date);
    $.get("/api/checkins/", {
        area_id: areaid,
        from_date: from,
        to_date: to
    }, function(data) {
        if (data.is_success) {
            allHeatmapPoints = [];
            allClusterMarkers = [];
            for (i in data.data) {
                checkin = data.data[i];
                heatmapPoint = {
                    "lng": checkin.lon,
                    "lat": checkin.lat,
                    "count": checkin.checkin_count
                };
                allHeatmapPoints.push(heatmapPoint);
                var j = 0;
                for (j = 0; j < heatmapPoint.count; j++)
                    allClusterMarkers.push(new BMap.Marker(new BMap.Point(heatmapPoint.lng, heatmapPoint.lat)));
            }


            heatmapOverlay = new BMapLib.HeatmapOverlay({ "radius": 80 });
            // map.addOverlay(heatmapOverlay);
            // heatmapOverlay.setDataSet({ data: allHeatmapPoints, max: 50 });
            // heatmapOverlay.show();

            //markerClusterer = new BMapLib.MarkerClusterer(map, {markers:allClusterMarkers});
            refresh_overlays();

        }

    });
}

function refresh_overlays() {
    map.clearOverlays();
    if (show_poi) {
        var counts = poi_markers.length;
        for (var i = 0; i < counts; i++) {
            map.addOverlay(poi_markers[i]);
            addClickHandler(poi_titles[i], poi_markers[i]);
        }
    }
    if (show_heatmap) {
        map.addOverlay(heatmapOverlay);
        heatmapOverlay.setDataSet({ data: allHeatmapPoints, max: 10 });
        heatmapOverlay.show();
    }
    if (show_cluster) {
        markerClusterer = new BMapLib.MarkerClusterer(map, { markers: allClusterMarkers });
    }
    minlat = parseFloat($("#minlat_of_" + selected_area).val());
    minlon = parseFloat($("#minlon_of_" + selected_area).val());
    maxlat = parseFloat($("#maxlat_of_" + selected_area).val());
    maxlon = parseFloat($("#maxlon_of_" + selected_area).val());
    show_area(minlat, minlon, maxlat, maxlon);
}


$(function() {
    init_map();
    init_control();
    init_event();
    //show_area(39.91951, 116.397676, 39.929193, 116.409174);
    //var point = new BMap.Point(116.381003, 39.91262); // 创建点坐标
    //map.centerAndZoom(point, 15); // 初始化地图，设置中心点坐标和地图级别
    reload_areas();
    refresh_poi_job = self.setInterval("get_pois_task()", 5000)
})


// Call methods and such...
// $('.nstSlider').nstSlider('highlight_range', 20, 50);

// $('.nstSlider').nstSlider('highlight_range', 60, 70);

var marker = new BMap.Marker(point);        // 创建标注    
map.addOverlay(marker);                     // 将标注添加到地图中

BMap.Point(116.404, 39.915)



