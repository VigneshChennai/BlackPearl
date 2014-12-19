import inspect

from BlackPearl.core.decorators import weblocation, webname
from BlackPearl.core import datatype
from BlackPearl.core import webapps
from BlackPearl.core.exceptions import RequestInvalid
from BlackPearl.core import datatype

@weblocation('/trial/')
class Trial:
    @webname('/dummy')
    def funny(self, s:datatype.Float()):
        return s
    
    def __call__(self):
        return "object call"

@weblocation('/applications')
def applications():
    ret = []
    for app in webapps.deployed_apps:
        urls = [url for url in app.web_modules.keys()]
        ret.append({
            "name" : app.name,
            "description" : app.desc,
            "modules" : urls
        })
    
    return ret
    
@weblocation('/signature')
def signature(url):
    ret = []
    
    try:
        webapp = webapps.modules[url]
    except:
        raise RequestInvalid("The URL <%s> not found" % url)
    
    signature = webapp.web_modules[url]['signature']
    
    for arg, value in signature.parameters.items():
        v = {
            "arg" : arg,
            "type" : repr(value.annotation),
            "type_def" : None
        }
        
        annotation = value.annotation
        
        if annotation is inspect.Signature.empty:
            v['type'] = None
            
        if (isinstance(annotation, datatype.Format)
            or isinstance(annotation, datatype.FormatList)):
            v["type_def"] = annotation.data_format
        
        elif (isinstance(annotation, datatype.Options)
            or isinstance(annotation, datatype.OptionsList)):
            v["type_def"] = annotation.values
        
        ret.append(v)
    
    return ret
        
