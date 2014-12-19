#!/usr/bin/python

url_map_stage = {}
        
def add_url(details):
    '''this function must not to be used by the webapplication'''
    url = details["url"]
    func = details["handler"]
    signature = details["signature"]
    module_ns = details["module_ns"]
    module_loc = details["module_loc"]
    
    url_seg = []
    for segment in url.split('/'):
        segment = segment.strip()
        if len(segment) != 0:
            url_seg.append(segment)
    url = "/" + "/".join(url_seg)
    url_map_stage[(url, module_loc)] = [func, signature, module_ns]
