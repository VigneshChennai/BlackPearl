strings = {
    app_desc_missing : [
                        '<strong>The application description missing!</strong>',
                        'You can add the same in the config.yaml file of this webapp '
                        ].join('\n'),

    module_desc_missing : [
                    '<strong>The module description missing!</strong>',
                    '<br/>',
                    '<br/>',
                    '<p>Add string as first statement in the function definition',
                    '</p>',
                    '<br/>',
                    "<p><strong>Example:</strong></p>",
                    '<br/>',
                    '<div class="row clearfix">',
	                '<div class="col-md-12 column">',
                    '<pre>',
                    '',
                    '@weblocation("/web/path/")',
                    'def func(arg1, arg2):',
                    '    """Your documentation goes here"""',
                    '',
                    '</pre>',
                    '</div>',
                    '</div>'].join('\n'),

    modules_missing: [
                    "<p>No modules defined in this application.</p>",
                    "<p>If it has, try checking the server log to see why they failed to load"
                    ].join('\n'),
    no_inputs: [
                '<p class="help-block">',
                '    The module accepts no inputs.',
                '</p>'
                ].join('\n'),
    no_handlers: 'No handlers deployed',
    no_preprocessors : 'No preprocessors deployed',
    no_posthandlers: 'No posthandlers deployed'
};

var _applications = [];
var _current_module = null;
var _current_app_id = 0;
var _current_module_type = null;

function getCurrentWebAppURL() {
    return _applications[_current_app_id].url_prefix;
}

function load() {
    var future = initialize_applications();
    future.success = function () {
        load_topmenu();
        load_description();
        load_modules();
    };

    future.failure = function () {
        error("Error initializing","We are facing challenge in access the server. Check your network connectivity");
    }
}

function initialize_applications() {
    var ret = {};
    $.getJSON("applications", function (data){
        var status = data.status;
        if(status == 0) {
            _applications = data.data;
            for(var i = 0; i < _applications[0].url_prefix.length; i++) {
                if (_applications[i].url_prefix.length == 1) {
                   _applications[i].url_prefix = ""
                }
            }
            $.getJSON(_applications[0].url_prefix + "/__application__", function (data){
                var status = data.status;
                if(status == 0) {
                    _applications[0] = data.data;
                    if (ret.success) {
                        ret.success();
                    }
                }else {
                    if (ret.failure) {
                        ret.failure();
                    }
                }
            });
        } else {
            if (ret.failure) {
                ret.failure();
            }
        }
    });
    return ret;
}

function load_topmenu() {
    var app_list = $('#applications-list-tmpl').html();
    var apps = [];
    for(var i = 0; i < _applications.length; i++) {
        apps.push({
            "id" : i,
            "name" : typeof _applications[i].name !== 'undefined' ? _applications[i].name : _applications[i][0]
        })
    }
    apps[0].active = true;
    var rendered = Mustache.render(app_list, {"data" :apps});
    $("#topmenu-apps").html(rendered);
}

function load_description(id) {
    id = typeof id !== 'undefined' ? id : 0;

    var desc_tmpl = $("#applications-desc-tmpl").html();
    if(_applications[id].description) {
        var rendered = Mustache.render(desc_tmpl, {"desc" :
                                        _applications[id].description,
                                        "url": getCurrentWebAppURL()});
        $("#application-details").html(rendered);
    } else {
        var rendered = Mustache.render(desc_tmpl, {"desc" :
                                        strings.app_desc_missing,
                                        "url": getCurrentWebAppURL()});
        $("#application-details").html(rendered);
    }

    $("#handlers-count").html(_applications[id].handlers.length);
    $("#preprocessors-count").html(_applications[id].preprocessors.length);
    $("#posthandlers-count").html(_applications[id].posthandlers.length);

}

function load_modules(id) {
    id = typeof id !== 'undefined' ? id : 0;

    var mod_list = $('#modules-list-tmpl').html();
    var modules = [];
    for(i = 0; i < _applications[id].modules.length; i++) {
        modules.push({
            "id" : i,
            "location" : _applications[id].modules[i]
        })
    }
    if(modules.length > 0) {
        modules[0].active = true;
        var url = modules[0].location;
        var rendered = Mustache.render(mod_list, {"data" :modules});
        $("#modules-list").html(rendered);
        load_signature(url);
        $("#modules-count").html(modules.length);
    } else {
        $("#modules-list").html(strings.modules_missing);
    }
}

function load_signature(url) {
    //$("#module-details-selected").html(url);
    $.getJSON(_applications[_current_app_id].url_prefix + "/__signature__?url=" + url , function (data){
            if (data.data.desc) {
                $("#description-module").html(data.data.desc)
            } else {
                $("#description-module").html(strings.module_desc_missing)
            }
            load_testsets(data.data.testsets);
            generate_form_elements(data.data.signature);
            _current_module=url;
            _current_module_type = data.data.type;
            $("#invoke-form").attr("action", url);

            if (data.data.type == "file") {
                $("#module-output-panel").hide();
                $("#module_invoke_btn").html("Get File")
            } else {
                $("#module-output-panel").show();
                $("#module_invoke_btn").html("Invoke")
            }
    });
}

function load_testsets(testsets) {
    var tmpl = $("#testset-tmpl").html();

    if(testsets.length > 0) {
        var rendered = "";
        for(var i=0;i<testsets.length;i++) {
             rendered += Mustache.render(tmpl, testsets[i]);
        }
        $("#testsets-container").html(rendered);
        $("#testcase-execute-all-btn").prop( "disabled", false);
    } else {
        $("#testcase-execute-all-btn").prop( "disabled", true);
        $("#testsets-container").html("No testsets defined");
    }
}

function openapp(id, object) {
    $(".application-list-item").removeClass("active");
    $(object).parent().addClass("active");

    if (Object.keys(_applications[id]).length == 2) {
        $.getJSON(_applications[id].url_prefix + "/__application__", function (data){
            var status = data.status;
            if(status == 0) {
                _current_app_id = id;
                _applications[id] = data.data;
                load_description(id);
                load_modules(id);
            }else {
                error("Error Opening Webapp","We are facing challenge in access the server. Check your network connectivity");
            }
        });
    } else {
        _current_app_id = id;
        load_description(id);
        load_modules(id);
    }
}

function openmodule(url, object) {
    $(".module-list-item").removeClass("active");
    $(object).addClass("active");

    //$("#modules-panel").click();
    //$("#modules-details-panel").click();
    load_signature(url);

}

function generate_form_elements(args) {
    //clearing the output
    var output_body = $("#module-output-body");
    output_body.html('<pre style="min-height:200px"></pre>');
    var output_panel = $("module-output-panel");
    output_panel.removeClass();
    output_panel.addClass("panel panel-default top20");
    var input_tmpl = $("#form-input-item-tmpl").html();

    var form_inputs = [];
    args.forEach(function (arg, index) {
        arg.name = arg.arg.charAt(0).toUpperCase() + arg.arg.slice(1);
        if (arg.type == "Float datatype") {
            arg.placeholder = "Float value. Example : 234.123";
        } else if (arg.type == "Integer datatype") {
            arg.placeholder = "Integer value. Example : 234";
        } else if (arg.type == "Regex datatype") {
            arg.placeholder = "Custom Text : " + arg.type_def;
        } else if (arg.type == "Option datatype") {
            arg.placeholder = arg.type_def;
            arg.option_type = true;
        } else {
            arg.placeholder = "";
        }

        if(arg.type == "File datatype") {
            arg.htmltype = "file";
            arg.file_type = true;
        } else {
            arg.htmltype = "text";
        }
        form_inputs.push(Mustache.render(input_tmpl, arg));
    });
    if (form_inputs.length > 0) {
        $("#invoke-form-inputs").html(form_inputs.join(''));
    } else {
        $("#invoke-form-inputs").html(strings.no_inputs);
    }
}

function invoke() {
    if (_current_module_type == "json") {
        var output_tmpl = $("#output-tmpl").html();
        var execute_all = $("#testcase-execute-all-btn").prop( "disabled");
        $(".execute_btn").prop( "disabled", true );
        $("#module-output-body").html('<pre style="min-height:200px"><div class="spinner"> ' +
        '<div class="spinner-container container1"> <div class="circle1"></div> <div class="circle2"></div> ' +
        '<div class="circle3"></div> <div class="circle4"></div> </div> <div class="spinner-container container2"> ' +
        '<div class="circle1"></div> <div class="circle2"></div> <div class="circle3"></div> <div class="circle4"></div> ' +
        '</div> <div class="spinner-container container3"> <div class="circle1"></div> <div class="circle2"></div> ' +
        '<div class="circle3"></div> <div class="circle4"></div> </div></div></pre>');

        var hasFile = false;
        formData = new FormData(document.getElementById("invoke-form"));
        $('#invoke-form').find(':input').each(function() {
            if($(this).attr("name")) {
                if ($(this).attr("type") == 'file') {
                    hasFile = true;
                }
            }
        });
        previous = $("#module_invoke_btn").html()
        if(hasFile) {
            $("#module_invoke_btn").html("Uploading...");
        }
        $.ajax({
            url: _current_module,
            data: formData,
            processData: false,
            type: 'POST',
            contentType: false,
            success: function ( data ) {
                var output_panel = $("#module-output-panel");
                if(data.status == 0) {
                   output_panel.removeClass();
                   output_panel.addClass("panel panel-success top20");
                } else {
                   output_panel.removeClass();
                   output_panel.addClass("panel panel-danger top20");
                }
                var rendered = Mustache.render(output_tmpl, {"output" :JSON.stringify(data, null, 4)});
                $("#module-output-body").html(rendered);
                $(".execute_btn").prop( "disabled", false);
            },
            dataType: 'json'
        }).always(function() {
                if(hasFile) {
                    $("#module_invoke_btn").html(previous);
                }
                $(".execute_btn").prop( "disabled", false);
                $("#testcase-execute-all-btn").prop( "disabled", execute_all);
        });
        /*
        $.post(_current_module, $('#invoke-form').serialize(), function(data) {

            var output_panel = $("#module-output-panel");
             if(data.status == 0) {
                output_panel.removeClass();
                output_panel.addClass("panel panel-success top20");
             } else {
                output_panel.removeClass();
                output_panel.addClass("panel panel-danger top20");
             }
             var rendered = Mustache.render(output_tmpl, {"output" :JSON.stringify(data, null, 4)});
             $("#module-output-body").html(rendered);
            $(".execute_btn").prop( "disabled", false);
           },
           'json' // I expect a JSON response
        ).always(function() {
                $(".execute_btn").prop( "disabled", false);
                $("#testcase-execute-all-btn").prop( "disabled", execute_all);
            });*/
        return false;
    } else {
        return true;
    }
}

function display_handlers() {
    var tmpl = $("#list-tmpl").html();
    if(_applications[_current_app_id].handlers.length>0) {
        var rendered = Mustache.render(tmpl, {"data" :_applications[_current_app_id].handlers});
        msg("Deployed handlers", rendered);
    } else {
        msg("Deployed handlers", "No handlers deployed");
    }
}
function display_preprocessors() {
    var tmpl = $("#list-tmpl").html();
    if(_applications[_current_app_id].preprocessors.length>0) {
        var rendered = Mustache.render(tmpl, {"data" :_applications[_current_app_id].preprocessors});
        msg("Deployed preprocessors", rendered);
    } else {
        msg("Deployed preprocessors", "No preprocessors deployed");
    }
}
function display_posthandlers() {
    var tmpl = $("#list-tmpl").html();
    if(_applications[_current_app_id].posthandlers.length>0) {
        var rendered = Mustache.render(tmpl, {"data" :_applications[_current_app_id].posthandlers});
        msg("Deployed posthandlers", rendered);
    } else {
        msg("Deployed posthandlers", "No posthandler deployed");
    }
}

function execute_testset(testset) {
    var output_tmpl = $("#output-tmpl").html();

    var url = "";
    var execute_all = $("#testcase-execute-all-btn").prop( "disabled");
    $(".execute_btn").prop( "disabled", true );
    $("#module-output-body").html('<pre style="min-height:200px"><div class="spinner"> ' +
    '<div class="spinner-container container1"> <div class="circle1"></div> <div class="circle2"></div> ' +
    '<div class="circle3"></div> <div class="circle4"></div> </div> <div class="spinner-container container2"> ' +
    '<div class="circle1"></div> <div class="circle2"></div> <div class="circle3"></div> <div class="circle4"></div> ' +
    '</div> <div class="spinner-container container3"> <div class="circle1"></div> <div class="circle2"></div> ' +
    '<div class="circle3"></div> <div class="circle4"></div> </div></div></pre>');
    if (testset) {
        url = _applications[_current_app_id].url_prefix + "/__test_run__?url=" + _current_module +"&name=" + testset;
    } else {
        url = _applications[_current_app_id].url_prefix + "/__test_run_all__?url=" + _current_module;
    }

    $.get(url, function(data) {
         var output_panel = $("#module-output-panel");
         if(data.status == 0) {
            output_panel.removeClass();
            output_panel.addClass("panel panel-success");
         } else {
            output_panel.removeClass();
            output_panel.addClass("panel panel-danger");
         }
         var rendered = Mustache.render(output_tmpl, {"output" :JSON.stringify(data, null, 4)});
         $("#module-output-body").html(rendered);
       },
       'json' // I expect a JSON response
    ).always(function() {
            $(".execute_btn").prop( "disabled", false);
            $("#testcase-execute-all-btn").prop( "disabled", execute_all);
        });
}
function form_option_cb(object, id, id_view) {
    $('#'+id).val($(object).html());
    $('#'+ id_view).html($(object).html());
}

function msg(title, msg) {
    var modal_type = $("#modal-type");
    modal_type.removeClass();
    modal_type.addClass("modal-content panel-info");
    $("#ModalMsg-title").html(title);
    $("#ModalMsg-body").html(msg);
    $("#ModalMsg").click();
}

function warning(title, msg) {
    var modal_type = $("#modal-type");
    modal_type.removeClass();
    modal_type.addClass("modal-content panel-warning");
    $("#ModalMsg-title").html(title);
    $("#ModalMsg-body").html(msg);
    $("#ModalMsg").click();
}

function error(title, msg) {
    var modal_type = $("#modal-type");
    modal_type.removeClass();
    modal_type.addClass("modal-content panel-danger");
    $("#ModalMsg-title").html(title);
    $("#ModalMsg-body").html(msg);
    $("#ModalMsg").click();
}
