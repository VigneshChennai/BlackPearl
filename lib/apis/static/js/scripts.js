strings = {
    app_desc_missing : ['#!/usr/bin/python',
                        '',
                        '#',
                        '#The license  description',
                        '#',
                        '',
                        '"""Your documention should go here"""',
                        ''
                        ].join('\n'),
                        
    module_desc_mission : [
                    '<strong>The module description missing!</strong>',
                    '<br/>',
                    '<br/>',
                    '<p>Add string as first statement in the function definition',
                    '</p>',
                    '<br/>',
                    "<p><strong>Example:</strong></p>",
                    '<br/>',
                    '<div class="row clearfix">',
	                '<div class="col-md-4 column">',
                    '<pre>',
                    '',
                    '@weblocation("/web/path/")',
                    'def func(arg1, arg2):',
                    '    """Your documentation goes here"""',
                    '',
                    '</pre>',
                    '</div>',
                    '</div>'].join('\n')
}

