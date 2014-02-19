#!/usr/bin/env python

from   copy                import  deepcopy
from   path                import  path as Path

#import pyImath

#mat4 = pyImath.M44f
#vec3 = pyImath.V3f

from cgkit.cgtypes import mat4, vec3

class RLSpan:
    """
    The tuple (lo,hi) where lo, hi are positive int's, lo < hi, or hi == None if lo == hi
    """
    def __init__(self,lo,hi=None):
        if hi == None:
            if isinstance(lo,(list,tuple)):
                assert len(lo) == 2, "sequence must be len(2) '%s'" % lo
                lo, hi = lo
        assert isinstance(hi,int) or hi == None, "arg must be int '%s'" % hi
        assert isinstance(lo,int), "arg must be int '%s'" % lo
        if lo == hi:
            self.hi = None
        else:
            self.hi = hi
        self.lo = lo
    def __iter__(self):
        "Yield all the integer values for this span"
        if self.hi == None:
            yield self.lo
        else:
            for i in range(self.lo,self.hi+1):
                yield i
    def __contains__(self,a):
        "Test if the integer is within this span"
        assert isinstance(a,int), "arg must be int '%s'" % a
        if self.hi:
            return a >= self.lo and a <= self.hi
        else:
            return a == self.lo
    def adjacent(self,other):
        "Are these two spans consecutive?"
        if isinstance(other,int):
            other = RLSpan(other)
        assert isinstance(other,RLSpan), "expecting RLSpan '%s'" % other
        if self.hi == None:
            if other.hi == None:
                return self.lo in (other.lo-1,other.lo+1)
            else:
                return self.lo in (other.lo-1,other.hi+1)
        else:
            if other.hi == None:
                return other.lo in (self.lo-1,self.hi+1)
            else:
                return other.lo == self.hi+1 or other.hi == self.lo-1
    def overlaps(self,other):
        assert isinstance(other,RLSpan), "expecting RLSpan '%s'" % other
        if self.hi == None:
            return self.lo in other
        elif other.hi == None:
            return other.lo in self
        else:
            if self.lo > other.hi:
                return False
            elif self.hi < other.lo:
                return False
            else:
                return True
    def mergable(self,other):
        "Are these two spans adjacent or overlapping?"
        return self.overlaps(other) or self.adjacent(other)
    def add(self, other):
        "Merge other span into this one, return self; other may be an integer"
        if isinstance(other,int):
            other = RLSpan(other)
        assert isinstance(other,RLSpan), "expecting RLSpan '%s'" % other
        if self.hi == None:
            if other.hi == None:
                if self.lo == other.lo:
                    return
                self.lo = min(self.lo,other.lo)
                self.hi = max(self.lo,other.lo)
            else:
                self.lo = min(self.lo,other.lo)
                self.hi = max(self.lo,other.hi)
        else:
            if other.hi == None:
                self.lo = min(self.lo,other.lo)
                self.hi = max(self.hi,other.lo)
            else:
                self.lo = min(self.lo,other.lo)
                self.hi = max(self.hi,other.hi)
        if self.lo == self.hi:
            self.hi = None
        return self
    def __eq__(self,other):
        if isinstance(other,int):
            other = RLSpan(other)
        assert isinstance(other,RLSpan), "expecting RLSpan '%s'" % other
        return self.lo == other.lo and self.hi == other.hi
    def __str__(self):
        if self.hi == None:
            return "%d" % self.lo
        else:
            return "%d-%d" % (self.lo,self.hi)
    __repr__ = __str__
    def dump(self):
        print "   %s -- %s" % (self.lo,self.hi)
    def asTuple(self):
        return (self.lo,self.hi)

class RunLength:
    """
    Class for handling sequences of positive integers with run-length compression
    A set of RLSpans
    
    eg.
        >>> rl = RunLength()
        >>> rl.add((1,12))
        >>> print rl
        1-12
        >>> rl.add(17)
        >>> print rl
        1-12 17
        >>> rl.add((9,16))
        >>> print rl
        1-17
        >>> rl.addList(range(20,25))
        >>> print rl
        1-17 20-24
    """
    def __init__(self,*args):
        self.spans = list()
        for a in args:
            self.add(a)
    def __iter__(self):
        "Yield all spans"
        for span in self.spans:
            yield span
    def expand(self):
        "Yield all the integer values"
        for s in self:
            for i in s:
                yield i
    def extend(self,spansOrInts):
        "Add all spans or integers from the given arg to this"
        for a in spansOrInts:
            self += a
    def __contains__(self,other):
        if isinstance(other,(RunLength,RLSpan)):
            for span in self:
                if span == other:
                    return True
            return False
        elif isinstance(other,int):
            for span in self:
                if other in span:
                    return True
            return False
        else:
            raise TypeError, type(other)
    def clean(self):
        if len(self.spans) < 2: return
        self.spans.sort(lambda a,b: cmp(a.lo,b.lo))
        cont = True
        i = len(self.spans) - 2
        while i >= 0:
            if self.spans[i].mergable(self.spans[i+1]):
                self.spans[i].add(self.spans[i+1])
                del self.spans[i+1]
            i -= 1
    def addList(self,other):
        "Compress other (a list of integers) and add it"
        o = RLcompress(other)
        for span in o.spans:
            self.add(span)
    def add(self,other):
        "Add another int, tuple or RLSpan to the current"
        if isinstance(other,(list,tuple)):
            assert len(other) == 2, "sequence must be len(2) '%s'" % other
            assert isinstance(other[0],int) and isinstance(other[1],int), "both args must be int '%s'" % other
            new = RLSpan(other)
        elif isinstance(other,RLSpan):
            new = other
        elif isinstance(other,RunLength):
            for span in other:
                self.add(span)
            new = None
        else:
            assert isinstance(other,int), "arg must be int '%s'" % other
            new = RLSpan(other)
        if not self.spans:
            if new:
                self.spans.append(new)
        else:
            if new and new not in self: 
                inserted = False
                for i in range(len(self.spans)):
                    if self.spans[i].mergable(new):
                        self.spans[i].add(new)
                        inserted = True
                        break
                if not inserted:
                    self.spans.append(new)
        self.clean()
        return self
    __iadd__ = add
    def __add__(self,other):
        new = RunLength()
        new += self
        new += other
        return new
    def dump(self):
        print len(self.spans),self.spans
        for span in self.spans:
            span.dump() 
    def __str__(self):
        return ", ".join([str(i) for i in self])
    __repr__ = __str__
    def asTuples(self):
        "Return a list of 2-tuples"
        return [s.asTuple() for s in self.spans]
    def parse(self,s):
        """
        Parse a string that may have been generated by printing itself.
            - Replace all commas with spaces
            - split on spaces, remove null strings
            - parse each span
        New spans are added to any that existed.
        It is illegal to have spaces between numbers and hyphens (for now)
        eg.
            Okay:      1 3-6 43, 17-18, 5 13
            Not okay:  1 3 -6 
        """
        for spanStr in [ s1 for s1 in s.replace(',',' ').split() if s1 ]:
            n = [ int(x) for x in spanStr.split('-',1)]
            if len(n) == 1:
                self.add(n[0])
            elif len(n) == 2:
                self.add(n)
            else:
                raise Exception("bad span '%s'" % spanStr)
        self.clean()

def RLcompress(numbers):
    "Given a list of integers, return an RunLength object"
    rl = RunLength()
    for i in sorted(numbers):
        rl.add(i)
    return rl


def _testRl():
    from random import randint

    r = RunLength()
    r.add((1,12))
    print "r.add((1,12)):  ", r
    r.add(17)
    print "r.add(17):      ", r
    r.add((9,16))
    print "r.add((9,16)):  ", r
    r.addList(range(20,25))
    print "r.addList(range(20,25)):  ", r

    print "asTuples():  ",r.asTuples()

    r = RunLength()
    print "r = RunLength()"
    r.add((1,12))
    print "r.add((1,12)):  ", r
    for i in range(30):
        print "  before:    ",r,
        i = randint(1,25)
        r.add(i)
        print "  after %-2d:  " % i,r

    print "asTuples():  ",r.asTuples()

    r = RunLength()
    print "r = RunLength()"
    r.add((1,12))
    print "r.add((1,12)):  ", r
    r.parse('5,7,16-17')
    print "r.parse('5,7,16-17'):  ", r

    print "Expanding",r,"yields:"
    for i in r.expand():
        print "   ",i
    
    print "Overloading '+'"
    print "r -->",r
    print "r + 99 -->",r + 99
    print "r + (100,103) -->",r + (100,103)

    print "Overloading '+='"
    print "r -->",r
    r += 99
    print "r += 99; r -->",r
    r += (100,103)
    print "r += (100,103); r -->",r

    print "101 in r?", 101 in r
    print "1011 in r?", 1011 in r

# --- NameSpaces ----------------------------------------------------------------------


class NameSpace(object):

    def __init__(self,kv={},**kw):
        self._data = dict()
        self.update(kv)
        self.update(kw)

    def set(self,key,value):
        if isinstance(key,(tuple,list)):
            if len(key) == 1:
                self._data[key[0]] = value
            elif len(key) > 1:
                if key[0] in self._data:
                    ns = self._data[key[0]]
                    if not isinstance(ns,self.__class__):
                        raise ValueError, ns
                else:
                    ns = self._data[key[0]] = self.__class__()
                ns.set(key[1:],value)
            else:
                raise KeyError, key
        elif isinstance(key,(str,unicode)):
            self.set(str(key).split('.'),value)
        else:
            raise ValueError, key

    def updateValue(self,paramName,value):
        p = self.get(paramName)
        p.setValue(value)

    def __contains__(self,key):
        try:
            self.get(key)
        except:
            return False
        return True

    def get(self,key):
        if isinstance(key,(tuple,list)):
            if len(key) == 1:
                #print "Len(1)",self._data, key[0]
                #print "-->",self._data[key[0]]
                return self._data[key[0]]
            elif len(key) > 1:
                if key[0] in self._data:
                    ns = self._data[key[0]]
                    if not isinstance(ns,self.__class__):
                        raise ValueError, ns
                else:
                    raise KeyError, key
                return ns.get(key[1:])
            else:
                raise KeyError, key
        elif isinstance(key,(str,unicode)):
            k = str(key).split('.')
            #print "K",k
            return self.get(k)
        else:
            raise ValueError, key

    __getitem__ = get
    __setitem__ = set
    
    def __iter__(self):
        for k in self._data.keys():
            yield k

    def items(self):
        for i in self._data.items():
            yield i

    def has_key(self,key):
        return self._data.has_key(key)

    def update(self,kv={},**kw):
        kv.update(kw)
        for k,v in kv.items():
            self.set(k,v)

    def dump(self,prefix=''):
        for k,v in self._data.items():
            name = "%s.%s" % (prefix,k) if prefix else k
            if isinstance(v,self.__class__):
                v.dump(name)
            else:
                print "%s = %s" % (name, repr(v))
    
    def __str__(self):
        return repr(self.dict)
    
    @property
    def hdict(self):
        "Hierarchial dictionary"
        d = dict()
        for k,v in self._data.items():
            #name = "%s.%s" % (prefix,k) if prefix else k
            if isinstance(v,self.__class__):
                d.update([(k,v.hdict)])
            else:
                d.update([(k,v)])
        return d

    @property
    def dict(self):
        "Flattended dictionary where keys are dot-separated"
        d = dict()
        for k,v in self._data.items():
            #name = "%s.%s" % (prefix,k) if prefix else k
            if isinstance(v,self.__class__):
                for kk,vv in v.dict.items():
                    d.update([("%s.%s" % (k,kk),vv)])
            else:
                d.update([(k,v)])
        return d

    def read(self,file,localFuncDict={}):
        p = Path(file)
        for line in p.lines(retain=False):
            if line.strip() == '' or line.strip().startswith('#'):  continue
            if '=' not in line:
                raise SyntaxError, line
            lhs, rhs = line.split('=',1)
            key = lhs.strip()
            value = eval(rhs,localFuncDict,globals())
            self.set(key,value)

    def parse(self,text,localFuncDict={}):
        lineNum = 1
        for line in text.split('\n'):
            if line.strip() == '' or line.strip().startswith('#'):  continue
            if '=' not in line:
                raise SyntaxError, line
            lhs, rhs = line.split('=',1)
            key = lhs.strip()
            try:
                value = eval(rhs,localFuncDict,globals())
            except Exception, desc:
                raise Exception("%s parsing '%s' (at line %d)" % (desc,rhs,lineNum))
            self.set(key,value)
            lineNum += 1

    def write(self,file,prefix='',append=False):
        p = Path(file)
        if not append:
            p.write_text('')
        for k,v in self._data.items():
            name = "%s.%s" % (prefix,k) if prefix else k
            if isinstance(v,self.__class__):
                v.write(file,name,append=True)
            else:
                try:
                    r = repr(v)
                except:
                    print '***',k
                p.write_lines(["%s = %s" % (name, repr(v))],append=True)

    def dupe(self):
        return deepcopy(self)

    def __add__(self,other):
        new = self.dupe()
        if not hasattr(other,"items"):
            raise ValueError("__add__ needs '%s' to have 'items' method" % repr(other))
        for k,v in other.items():
            new.set(k,v)
        return new
    
    def __iadd__(self,other):
        if not hasattr(other,"items"):
            raise ValueError("__iadd__ needs '%s' to have 'items' method" % repr(other))
        for k,v in other.items():
            self.set(k,v)
        return self


# --- UiNameSpaces ----------------------------------------------------------------------


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

def loadUiNameSpace(filePath):
    uiNS = UiNameSpace()
    uiNS.read(filePath, UiNameSpace.LocalFuncTable)
    return uiNS


# --- TEST ----------------------------------------------------------------------

def _testUiNameSpace():
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
    
    uns2 = loadUiNameSpace("test.ns")
    uns2['myspace'].dump("hello")



def _testNameSpace():
    
    from pprint import  pprint

    builtin = NameSpace(
                   
        material = NameSpace(
            default  = '/imd/dept/surfacing/materials/Global_default.mtl', #'${REACTORTREE}/defaults/materials/genericGrey.mtl',
        ),
    
        aperature = NameSpace( {
            '185':      20.95,
        } ),
        
    
        camera = NameSpace(
            persp       = "perspective",
        ),
        
        render = NameSpace(
            orderchoices = ['horizontal', 'vertical', 'zigzag-x', 'zigzag-y', 'spacefill', 'spiral', 'random', ],
        ),
        
        object = NameSpace(
            truck       = 0.0, 
            globalMtx   = [1, 0, 0, 0,  0, 1, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1],
        ),
        
        lights = NameSpace(
            rtshad      = True,
            radius      = 1.0,
        ),
    )

    print "Before"
    print builtin['render.orderchoices']
    args = builtin.dupe()
    print "After duplicate"
    args.set('render.orderchoices','foobie')
    print args['render.orderchoices']

    print "write to file"
    builtin.write("temp.ns")
    builtin.dump()
    new = NameSpace()
    print "read back"
    new.read("temp.ns")
    new.dump()

    print "parse"
    new = NameSpace()
    text = """
    # testing
    aperature.185 = 20.949999999999999
    object.globalMtx = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    render.orderchoices = ['horizontal', 'vertical', 'zigzag-x', 'zigzag-y', 'spacefill', 'spiral', 'random']
    material.default = '/imd/dept/surfacing/materials/Global_default.mtl'
    """
    print "original:"
    print text
    new.parse(text)
    print "parsed:"
    new.dump()
    
    print "get sub-namespace 'object':"
    pprint(builtin['object'])
    
    print "as dict"
    pprint(builtin.dict)
    
    print "as hierarchial dict"
    pprint(builtin.hdict)
    





if __name__ == '__main__':
    #_testRl()
    _testNameSpace()
    _testUiNameSpace()
