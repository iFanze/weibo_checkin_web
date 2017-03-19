var selected_area = -1;

var map = null;

var draw_mode = false;
var draw_layers = [];
var drawing_manager = null;

var new_area_name = "";

var all_areas = [];

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
    //lat
    var de = e.overlay.Nu.De;
    var ie = e.overlay.Nu.Ie;
    //lon
    var ee = e.overlay.Nu.Ee;
    var je = e.overlay.Nu.Je;

    var minlat = (de > ie) ? ie : de;
    var maxlat = (de < ie) ? ie : de;
    var minlon = (ee > je) ? je : ee;
    var maxlon = (ee < je) ? je : ee;

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
    }
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
    if (opera == "on") {
        $("#update-area-" + id).hide();
        $("#continue-area-" + id).hide();
        $("#pause-area-" + id).fadeIn();
        $("#area-progress-" + id).fadeIn();
        $("#area-label-" + id).show();
    } else if (opera == "pause") {
        $("#pause-area-" + id).hide();
        $("#update-area-" + id).hide();
        $("#continue-area-" + id).fadeIn();
        $("#area-progress-" + id).fadeIn();
        $("#area-label-" + id).hide();
    } else if (opera == "continue") {
        $("#continue-area-" + id).hide();
        $("#update-area-" + id).hide();
        $("#pause-area-" + id).fadeIn();
        $("#area-progress-" + id).fadeIn();    
        $("#area-label-" + id).show();    
    } else if (opera == "finish"){
        $("#continue-area-" + id).hide();
        $("#update-area-" + id).fadeIn();
        $("#pause-area-" + id).hide();
        $("#area-progress-" + id).fadeOut();    
        $("#area-label-" + id).hide();         
    }
}

function update_area(id) {
    $("#update-area-" + id).hide();
    $("#continue-area-" + id).hide();
    $("#pause-area-" + id).hide();
    $("#disabled-area-" + id).show();
    $.post("/api/area/update/",{
        id: id
    }, function(data){
        if(data.is_success){
            show_message(data.message)
            toggle_update_area(id, "on");
        }else{
            show_message(data.message, "error")
        }
    })
}

function pause_area(id) {
    $("#update-area-" + id).hide();
    $("#continue-area-" + id).hide();
    $("#pause-area-" + id).hide();
    $("#disabled-area-" + id).show();
    $.post("/api/area/pause/",{
        id: id
    }, function(data){
        if(data.is_success){
            show_message(data.message)
            toggle_update_area(id, "pause");
        }else{
            show_message(data.message, "error")
        }
    })
}

function continue_area(id) {
    $("#update-area-" + id).hide();
    $("#continue-area-" + id).hide();
    $("#pause-area-" + id).hide();
    $("#disabled-area-" + id).show();
        $.post("/api/area/pause/",{
        id: id
    }, function(data){
        if(data.is_success){
            show_message(data.message)
            toggle_update_area(id, "continue");
        }else{
            show_message(data.message, "error")
        }
    })
}


function get_pois_task(){
    $.get("/api/task/pois/", function(data){
        if(data.is_success){

        }else{
            show_message(data.message, "error")
        }
    });
}

$(function() {
    init_map();
    init_control();
    init_event();
    //show_area(39.91951, 116.397676, 39.929193, 116.409174);
    //var point = new BMap.Point(116.381003, 39.91262); // 创建点坐标
    //map.centerAndZoom(point, 15); // 初始化地图，设置中心点坐标和地图级别
    reload_areas();
    refresh_poi_job = self.setInterval("get_pois_task()",5000)
})


// Call methods and such...
// $('.nstSlider').nstSlider('highlight_range', 20, 50);

// $('.nstSlider').nstSlider('highlight_range', 60, 70);