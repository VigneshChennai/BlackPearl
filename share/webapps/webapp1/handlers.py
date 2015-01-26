from BlackPearl.core.decorators import weblocation
from BlackPearl.core import datatype

@weblocation("/index")
def hello():
    return "Vignesh is here"

@weblocation('/sess')
class SESS:
    def index(self, new_name:datatype.Float()):
        try:
            name = self.session.name
            self.session.name = new_name
            return "Session status :  %s,previous value : %s;" \
                    " current value : %s" % (self.session.__status__,name, new_name)
        except:
            self.session.name = new_name
            return "Session status :  %s, New name: %s" % (self.session.__status__,
                                                            new_name)
