#!/usr/bin/env python

from   copy                import  deepcopy
from   path                import  path as Path
from   namespace           import  NameSpace


class UiItem(object):
    """
    Base class for UiNameSpace data
    Used as values of NameSpace members that have metadata that helps build UIs
    Subclassed for use in storing and presenting in a UI types such as float, int, filepath etc.
    """
    NAME = "ERROR" # must be implemented in subclass
    def __init__(self,kv={},**kw):
        self._args = dict(kv.items()+kw.items())
    def __repr__(self):
        def _niceRepr(v):
            return "%g" % v if isinstance(v,float) else repr(v)
        if self.NAME in ('Vector',):
            vr = "value=(%g,%g,%g)" % tuple([self.value[i] for i in range(3)])
        else:
            vr = "value=%s" % repr(self.value)
        s = "%s(%s)" % (self.NAME, ", ".join([vr]+["%s=%s" % (n,_niceRepr(v)) for n,v in self._args.items() if n != 'value']))
        return s
    def __contains__(self,key):
        return key in self._args
    def __getitem__(self,key):
        return self._args[key]
    def setValue(self,value):
        self._args['value'] = value
    @property
    def value(self):
        if 'value' not in self._args:
            raise KeyError("UiItem subclass '%s' has no value() method" % self.__class__.__name__)
        return self._args['value']


class UiFloat(UiItem):
    NAME = 'Float'
    def valid(self,value):
        return isinstance(value,float)
    def coerce(self,value,force=False):
        if isinstance(value,float):
            coercedValue = value
        elif isinstance(value,int):
            coercedValue = float(value)
        elif isinstance(value,(unicode,str)):
            try:
                coercedValue = float(value)
            except Exception, desc:
                if force:
                    coercedValue = 0.0
                else:
                    raise ValueError("cannot coerce '%s' to Float, error: '%s'" % (value,desc))
        else:
            if force:
                coercedValue = 0.0
            else:
                raise ValueError("cannot coerce '%s' to Float" % value)
        return coercedValue

class UiVector(UiItem):
    NAME = 'Vector'
    def valid(self,value):
        return ( isinstance(value,(tuple,list)) and isinstance(value[0],float) ) or ( isinstance(value,vec3) )
    def coerce(self,value,force=False):
        if isinstance(value,float):
            coercedValue = vec3(value,value,value)
        elif isinstance(value,(tuple,list)):
            if len(value) == 0:
                coercedValue = vec3(0,0,0)
            elif len(value) == 1:
                coercedValue = vec3(value[0],value[0],value[0])
            elif len(value) == 2:
                coercedValue = vec3(value[0],value[1],0)
            elif len(value) == 3:
                coercedValue = vec3(value[0],value[1],value[2])
            else:
                coercedValue = vec3(value[0],value[1],value[2])
        elif isinstance(value,(unicode,str)):
            try:
                x = eval(value)
                coercedValue = vec3(value[0],value[1],value[2])
            except Exception, desc:
                if force:
                    coercedValue = vec3(0,0,0)
                else:
                    raise ValueError("cannot coerce '%s' to Vector, error: '%s'" % (value,desc))
        else:
            if force:
                coercedValue = vec3(0,0,0)
            else:
                raise ValueError("cannot coerce '%s' to Vector" % value)
        return coercedValue

class UiInt(UiItem):
    NAME = 'Int'
    def valid(self,value):
        return isinstance(value,int)
    def coerce(self,value,force=False):
        if isinstance(value,int):
            coercedValue = value
        elif isinstance(value,float):
            coercedValue = int(value)
        elif isinstance(value,(unicode,str)):
            try:
                coercedValue = int(value)
            except Exception, desc:
                if force:
                    coercedValue = 0
                else:
                    raise ValueError("cannot coerce '%s' to Int, error: '%s'" % (value,desc))
        else:
            if force:
                coercedValue = 0
            else:
                raise ValueError("cannot coerce '%s' to Int" % value)
        return coercedValue

class UiString(UiItem):
    NAME = 'String'
    def valid(self,value):
        return isinstance(value,(unicode,str))
    def coerce(self,value,force=False):
        if isinstance(value,(int,float)):
            coercedValue = "%g" % value
        elif isinstance(value,(unicode,str)):
            coercedValue = value
        else:
            if force:
                if hasattr(value,"__str__"):
                    coercedValue = str(value)
                else:
                    coercedValue = repr(value)
            else:
                raise ValueError("cannot coerce '%s' to String, only int or float are supported" % value)
        return coercedValue

class UiBoolean(UiItem):
    NAME = 'Boolean'
    def valid(self,value):
        return value in (False,True)
    def coerce(self,value,force=False):
        if isinstance(value,int):
            coercedValue = value != 0
        elif isinstance(value,float):
            coercedValue = (abs(value) > 0.0001)
        elif isinstance(value,(unicode,str)):
            coercedValue = str(value) not in ('',"None","False","0")
        else:
            if force:
                coercedValue = False
            else:
                raise ValueError("cannot coerce '%s' to Boolean" % value)
        return coercedValue

class UiFile(UiItem):
    NAME = 'File'
    def valid(self,value):
        return isinstance(value,(Path,unicode,str))
    def coerce(self,value,force=False):
        if isinstance(value,(unicode,str,Path)):
            coercedValue = str(value)
        else:
            if force:
                if hasattr(value,"__str__"):
                    coercedValue = str(value)
                else:
                    coercedValue = ''
            else:
                raise ValueError("cannot coerce '%s' to File" % value)
        return coercedValue

class UiDate(UiItem):
    NAME = 'Date'
    def valid(self,value):
        return isinstance(value,(unicode,str))
    def coerce(self,value,force=False):
        if isinstance(value,(unicode,str,Path)):
            coercedValue = str(value)
        else:
            if force:
                if hasattr(value,"__str__"):
                    coercedValue = str(value)
                else:
                    coercedValue = ''
            else:
                raise ValueError("cannot coerce '%s' to File" % value)
        return coercedValue


class UiNameSpace(NameSpace):
    """
    A NameSpace superclass that supports data values that are UiItem objects.
    Example:
        render.xres      = Int(value=640,default=1024,min=1,max=4096,choices=[320,640,1024,2048])
        render.order     = String(value="spiral",default="spiral",choices=['horizontal', 'vertical', 'spiral'])
        light.key.gain   = Float(value=0.75,map="log",min=0.0,hintmax=10.0,default=1.0)
        light.key.rtshad = Boolean(value=False,default=False)
        camera.position  = Vector(value=(0,0,-100),rubber=True)
    """
    
    LocalFuncTable = {
        'Float'       : UiFloat,
        'Int'         : UiInt,
        'String'      : UiString,
        'Boolean'     : UiBoolean,
        'File'        : UiFile,
        'Vector'      : UiVector,
        'Date'        : UiDate,
    }
    
    def __init__(self):
        super(UiNameSpace,self).__init__()
    
    def parse(self,text):
        super(UiNameSpace,self).parse(text,self.LocalFuncTable)

    def getValue(self,key):
        uiItem = self.get(key)
        if not isinstance(uiItem,tuple(self.LocalFuncTable.values())):
            raise Exception("Cannot get value of key '%s' since it is not a uiItem, it's a '%s'" % (key,type(uiItem)))
        return uiItem.value()

    @staticmethod
    def load(filePath):
        uiNS = UiNameSpace()
        uiNS.read(filePath, UiNameSpace.LocalFuncTable)
        return uiNS


# --- TEST ----------------------------------------------------------------------

if __name__ == '__main__':

    uns = UiNameSpace()
    uns.parse("""
    junk.floo        = Float(value=1.1)
    junk.bar         = Int(value=1,min=0,max=100,default=50,choices=[10,25,50,99])
    render.xres      = Int(value=640,min=1,max=4096,choices=[640,1024,2048])
    render.order     = String(value="spiral",choices=['horizontal', 'vertical', 'spiral'])
    light.key.gain   = Float(value=0.75,map="log",min=0.0,hintmax=10.0)
    material.difftex = File(value='/usr/tmp/foo.mtl',default='output.mtl',extensions=['mtl','mbws'],dirs=['/usr/tmp/','/tmp'])
    camera.position  = Vector(value=(0,0,-100),rubber=True)
    goop.date        = Date(value="20110430")
    """)

    uns.write("test.ns", "myspace")
    uns['junk'].write("test2.ns")
    
    uns2 = UiNameSpace.load("test.ns")
    uns2['myspace'].dump("hello")

