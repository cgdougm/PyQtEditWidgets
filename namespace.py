#!/usr/bin/env python

from   copy                import  deepcopy
from   path                import  path as Path



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



 
if __name__ == '__main__':
   
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
    


