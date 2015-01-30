strings = {
    app_desc_missing : [
//                        '<div class="alert alert-dismissable alert-info">',
//                        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>',
                        '<div class="row clearfix">',
                        '    <div class="col-sm-4 column">',
                        '<strong>The application description missing!</strong>',
                        '<br/>',
                        '<br/>',
                        '<p>Add file __init__.py in the application root directory and provide your ',
                        '   application description over there as the first statement in the file</p>',
                        '<br/>',
                        '<p><strong>Example:</strong> Let the application folder name is "MyApp"',
                        '<br/>Then in MyApp/__init__.py file, prepend the following lines</p><br/>',
                        '</div>',
                        '    <div class="col-sm-6 column"><pre>',
                        '#!/usr/bin/python',
                        '',
                        '#',
                        '#The license  description',
                        '#',
                        '',
                        '"""Your documention should go here"""',
                        '</pre>',
                        '    </div>',
                        '</div>'//,
//                        '</div>'
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
}

_applications = null;
_current_module = null;
_current_app_id = 0;

function initialize_applications(callback) {
    ret = {}
    $.getJSON("/dwm/applications", function (data){
        status = data.status;

        if(status == 0) {
            _applications = data.data;

            if (ret.success) {
                ret.success();
            }
        } else {
            if (ret.failure) {
                ret.failure();
            }
        }
    });
    return ret;
}

function load() {
    future = initialize_applications();
    future.success = function () {
        load_topmenu();
        load_description();
        load_modules();
    };

    future.failure = function () {
        error("Error initializing","We are facing challenge in access the server. Check your network connectivity");
    }
}
function load_topmenu() {
    var applist = $('#applications-list-tmpl').html();
    var apps = []
    for(i = 0; i < _applications.length; i++) {
        apps.push({
            "id" : i,
            "name" : _applications[i].name
        })
    }
    apps[0].active = true;
    var rendered = Mustache.render(applist, {"data" :apps});
    $("#topmenu-apps").html(rendered);
}

function load_description(id) {
    id = typeof id !== 'undefined' ? id : 0;
    desc_tmpl = $("#applications-desc-tmpl").html();
    if(_applications[id].description) {
        var rendered = Mustache.render(desc_tmpl, {"desc" :
                                        _applications[id].description});
        $("#description-app").html(rendered);
    } else {
        $("#description-app").html(strings.app_desc_missing);
    }

    $("#handlers-count").html(_applications[id].handlers.length);
    $("#preprocessors-count").html(_applications[id].preprocessors.length);
    $("#posthandlers-count").html(_applications[id].posthandlers.length);

}

function load_modules(id) {
    id = typeof id !== 'undefined' ? id : 0;
    var modlist = $('#modules-list-tmpl').html();
    var modules = []
    for(i = 0; i < _applications[id].modules.length; i++) {
        modules.push({
            "id" : i,
            "location" : _applications[id].modules[i]
        })
    }
    if(modules.length > 0) {
        modules[0].active = true;
        url = modules[0].location;
        var rendered = Mustache.render(modlist, {"data" :modules});
        $("#modules-list").html(rendered);
        load_signature(url);
        $("#modules-count").html(modules.length);
    } else {
        $("#modules-list").html(strings.modules_missing);
    }
}

function openapp(id, object) {
    $(".application-list-item").removeClass("active");
    $(object).parent().addClass("active");
    load_description(id);
    load_modules(id);
    _current_app_id = id;
}

function openmodule(url, object) {
    $(".module-list-item").removeClass("active");
    $(object).addClass("active");

    //$("#modules-panel").click();
    //$("#modules-details-panel").click();
    load_signature(url);
}

function load_signature(url) {
    //$("#module-details-selected").html(url);
    $.getJSON("/dwm/signature?url=" + url , function (data){
            if (data.data.desc) {
                $("#description-module").html(data.data.desc)
            } else {
                $("#description-module").html(strings.module_desc_missing)
            }
            load_testsets(data.data.testsets);
            generate_form_elements(data.data.signature);
            _current_module=url;
    });
}

function load_testsets(testsets) {
    tmpl = $("#testset-tmpl").html();

    if(testsets.length > 0) {
        var rendered = "";
        for(i=0;i<testsets.length;i++) {
             rendered += Mustache.render(tmpl, testsets[i]);
        }
        $("#testsets-container").html(rendered);
        $("#testcase-execute-all-btn").prop( "disabled", false);
    } else {
        $("#testcase-execute-all-btn").prop( "disabled", true);
        $("#testsets-container").html("No testsets defined");
    }
}

function generate_form_elements(args) {
    //clearing the output
    $("#output-box").html('<pre style="min-height:200px"></pre>');
    $("#output-panel").removeClass();
    $("#output-panel").addClass("panel panel-default");
    input_tmpl = $("#form-input-item-tmpl").html();

    form_inputs = []
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
            arg.htmltype = "File";
        } else {
            arg.htmltype = "Text";
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
    output_tmpl = $("#output-tmpl").html();
    $(".execute_btn").prop( "disabled", true );
    $("#output-box").html('<pre style="min-height:200px"><div class="spinner"> <div class="bounce1"></div> <div class="bounce2"></div> <div class="bounce3"></div> </div></pre>');
    $.post( _current_module, $('#invoke-form').serialize(), function(data) {

         if(data.status == 0) {
            $("#output-panel").removeClass();
            $("#output-panel").addClass("panel panel-success");
         } else {
            $("#output-panel").removeClass();
            $("#output-panel").addClass("panel panel-danger");
         }
         var rendered = Mustache.render(output_tmpl, {"output" :JSON.stringify(data, null, 4)});
         $("#output-box").html(rendered);
        $(".execute_btn").prop( "disabled", false);
       },
       'json' // I expect a JSON response
    ).always(function() {
            $(".execute_btn").prop( "disabled", false);
        });
}

function display_handlers() {
    tmpl = $("#list-tmpl").html()
    if(_applications[_current_app_id].handlers.length>0) {
        var rendered = Mustache.render(tmpl, {"data" :_applications[_current_app_id].handlers});
        msg("Deployed handlers", rendered);
    } else {
        msg("Deployed handlers", "No handlers deployed");
    }
}
function display_preprocessors() {
    tmpl = $("#list-tmpl").html()
    if(_applications[_current_app_id].preprocessors.length>0) {
        var rendered = Mustache.render(tmpl, {"data" :_applications[_current_app_id].preprocessors});
        msg("Deployed preprocessors", rendered);
    } else {
        msg("Deployed preprocessors", "No preprocessors deployed");
    }
}
function display_posthandlers() {
    tmpl = $("#list-tmpl").html()
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
    $(".execute_btn").prop( "disabled", true );
    $("#output-box").html('<pre style="min-height:200px"><div class="spinner"> ' +
    '<div class="spinner-container container1"> <div class="circle1"></div> <div class="circle2"></div> ' +
    '<div class="circle3"></div> <div class="circle4"></div> </div> <div class="spinner-container container2"> ' +
    '<div class="circle1"></div> <div class="circle2"></div> <div class="circle3"></div> <div class="circle4"></div> ' +
    '</div> <div class="spinner-container container3"> <div class="circle1"></div> <div class="circle2"></div> ' +
    '<div class="circle3"></div> <div class="circle4"></div> </div></div></pre>');
    if (testset) {
        url = "/dwm/testing/run?url=" + _current_module +"&name=" + testset;
    } else {
        url = "/dwm/testing/run_all?url=" + _current_module;
    }

    $.get(url, function(data) {

         if(data.status == 0) {
            $("#output-panel").removeClass();
            $("#output-panel").addClass("panel panel-success");
         } else {
            $("#output-panel").removeClass();
            $("#output-panel").addClass("panel panel-danger");
         }
         var rendered = Mustache.render(output_tmpl, {"output" :JSON.stringify(data, null, 4)});
         $("#output-box").html(rendered);
       },
       'json' // I expect a JSON response
    ).always(function() {
            $(".execute_btn").prop( "disabled", false);
        });
}
function form_option_cb(object, id, id_view) {
    $('#'+id).val($(object).html());
    $('#'+ id_view).html($(object).html());
}

function msg(title, msg) {
    $("#modal-type").removeClass();
    $("#modal-type").addClass("modal-content panel-info");
    $("#ModalMsg-title").html(title);
    $("#ModalMsg-body").html(msg);
    $("#ModalMsg").click();
}

function warning(title, msg) {
    $("#modal-type").removeClass();
    $("#modal-type").addClass("modal-content panel-warning");
    $("#ModalMsg-title").html(title);
    $("#ModalMsg-body").html(msg);
    $("#ModalMsg").click();
}

function error(title, msg) {
    $("#modal-type").removeClass();
    $("#modal-type").addClass("modal-content panel-danger");
    $("#ModalMsg-title").html(title);
    $("#ModalMsg-body").html(msg);
    $("#ModalMsg").click();
}
