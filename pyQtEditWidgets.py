#!/bin/env python

import sys
import os
import re
from collections import defaultdict

try:
    import pyCrashCatcher
except ImportError:
    pass

from PyQt4.QtCore import *
from PyQt4.QtGui import *

mapTypeTxInfo = {}
from    path                             import    path as Path
import  utils

from cgkit.cgtypes import mat4, vec3

DECIMALS    = 4

versionRE = re.compile(r'(.*)_[vV](\d+)\.(\w+)')

def makeQtFilter(*args): return ''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Plastique')



iconDirectory = dict(
    # Generic UI
    lookdev    = "ui/icons/lookdev.png",
    check      = "ui/icons/checkbox.png",
    checkChe   = "ui/icons/checkboxChecked.png",
    checkUn    = "ui/icons/checkboxUnChecked.png",
    checkExc   = "ui/icons/checkboxExclaim.png",
    checkQ     = "ui/icons/checkboxQuestion.png",
    checkX     = "ui/icons/checkboxX.png",
    notPerm    = "ui/icons/notPermitted.png",
    collapse   = "ui/icons/collapse.png",
    expand     = "ui/icons/expand.png",
    splitv     = "ui/icons/splitv.png",
    splith     = "ui/icons/splith.png",
    folder     = "ui/icons/folder.png",
    open       = "ui/icons/open.png",
    save       = "ui/icons/save.png",
    email      = "ui/icons/airmail.png",
    clipboard  = "ui/icons/clipboard.png",
    find       = "ui/icons/find.png",
    settings   = "ui/icons/gear.png",
    printout   = "ui/icons/print.png",
    light      = "ui/icons/flashlight.png",
    incrfile   = "ui/icons/incrfile.png",

    # Maya-style
    Model      = "ui/icons/asset.png",
    Mesh       = "ui/icons/mesh.png",
    Transform  = "ui/icons/xform.png",

    # Ingestion
    GtoFile    = "ui/icons/gtofile.png",
    Camera     = "ui/icons/camera.png",

    # Texture
    Faceset      = "ui/icons/faceset.png",
    FacesetGrp   = "ui/icons/facesetSet.png",
    texture      = "ui/icons/texture.png",
    TextureAsset = "ui/icons/textureasset.png",
    notexture    = "ui/icons/notexture.png",
    TIF          = "ui/icons/textureMap.png",
    TEX          = "ui/icons/textureMip.png",
    paint        = "ui/icons/paint.png",

    # Inheritance
    local        = "ui/icons/local.png",
    inherit0     = "ui/icons/inheritRank0.png",
    inherit1     = "ui/icons/inheritRank1.png",
    inherit2     = "ui/icons/inheritRank2.png",
    inherit3     = "ui/icons/inheritRank3.png",
    inherit4     = "ui/icons/inheritRank4.png",

    # Materials
    ArchetypeSet = "ui/icons/archetypeSet.png",
    Material     = "ui/icons/material.png",
    MaterialFile = "ui/icons/mtlfile.png",
    InheritedMtl = "ui/icons/inheritedMtl.png",
    LibraryMtl   = "ui/icons/libraryMtl.png",
    Shader       = "ui/icons/shader.png",
    ParamGroup   = "ui/icons/paramGroup.png",
    Param        = "ui/icons/param.png",
    ParamInherit = "ui/icons/paramInherited.png",
    ParamLocal   = "ui/icons/paramLocal.png",
    ParamDefault = "ui/icons/paramDefault.png",
    Global       = "ui/icons/global.png",

    # Mtl Builder
    target          = "ui/icons/target.png",
    newTarget       = "ui/icons/newTarget.png",
    compile         = "ui/icons/compile.png",
    wkspace         = "ui/icons/wkspace.png",
    slo             = "ui/icons/slo.png",
    
    # Loco
    loco            = "ui/icons/loco.png",
    locopub         = "ui/icons/locopub.png",
    checkin         = "ui/icons/db3_add.png",
)

iconSynonyms = dict(
    ATMtl             = "Material",
    ATParameter       = "Param",
    ATParameterGroup  = "ParamGroup",
    ATShader          = "Shader",
    Shape             = "Mesh",
    MtlBuildWorkspace = "wkspace",
)
iconSynonyms[''] = 'check'
iconDirectory[''] = "ui/icons/checkboxUnChecked.png"

def getTagIcon(tag):
    if tag in iconDirectory:
        p = iconDirectory[tag]
    elif tag in iconSynonyms:
        tag2 = iconSynonyms[tag]
        assert tag2 in iconDirectory, "iconSynonyms mapping incomplete"
        p = iconDirectory[tag2]
    else: 
        p = iconDirectory[iconSynonyms['']]
        return QIcon(p)
    if isinstance(p,str):
        iconDirectory[tag] = QIcon(p)
    return iconDirectory[tag]


class BaseEditWidget(QWidget):

    """
    Base for all editing widgets
    
    Has an Icon, a Name and the actual edit widgets (eg. slider etc).
    
    Has feature for storing individual "recent values" that are proposed by 
    a value which stays for at least a few seconds 
    """
    
    def __init__(self,parent=None):
        super(BaseEditWidget,self).__init__(parent)

        self._editWidgets = list()

        #  Main layout: name frame and edit frame
        self._mainlayout  = QHBoxLayout()
        self._mainlayout.setMargin(2)
        self.setLayout(self._mainlayout)
        self.nameF = QFrame(self)
        self.frame = QFrame(self)
        self._mainlayout.addWidget(self.nameF)
        self._mainlayout.addWidget(self.frame)

        # Name frame: name label and icon label
        self._namelayout  = QHBoxLayout()
        self._namelayout.setMargin(0)
        self.nameF.setLayout(self._namelayout)

        self.iconL = QLabel(self.nameF)
        self.iconL.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.iconL.setMinimumWidth(30)
        self.iconL.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed))
        self._namelayout.addWidget(self.iconL)

        self.nameL = QLabel(self.nameF)
        self.nameL.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.nameL.setMinimumWidth(180)
        self.nameL.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed))
        font = QFont()
        font.setLetterSpacing(QFont.PercentageSpacing,90.0)
        font.setFixedPitch(False)
        font.setPointSize(12)
        self.nameL.setFont(font)
        self._namelayout.addWidget(self.nameL)

        # Edit frame: sub widgets added to this:
        self.layout  = QHBoxLayout()
        self.layout.setMargin(0)
        self.frame.setLayout(self.layout)

        # Enabled
        self.groupEnabled = True

        # Stack of the most recent values
        self._recent    = list()
        self._saveTimer = QTimer()
        self._saveTimer.setSingleShot(True)
        self._proposedValue = None

        self.connect(self._saveTimer,SIGNAL("timeout()"),self._saveRecentTimerCB)

    def setEditEnabled(self,bool):
        self.groupEnabled = bool
        for w in self._editWidgets:
            w.setEnabled(bool)
        font = QFont()
        if bool:
            font.setWeight(99)
            font.setBold(True)
        else:
            font.setWeight(0)
            font.setBold(False)
        self.nameL.setFont(font)

    def setName(self,name,iconType=''):
        "Set the name in the label and optionally set an icon type"
        icon = getTagIcon(iconType).pixmap(24,24)
        self.iconL.setPixmap(icon)
        self.nameL.setText(name)

    def setSource(self,sourceText):
        self.nameL.setToolTip(sourceText)

    def getName(self):
        return str(self.nameL.text())

    def saveRecentValue(self,value):
        if value not in self._recent:
            #print "SAVED VALUE",value,self._recent
            self._recent.append(value)
        #else:
        #    print "SAVED (already had that.)"

    def recentValue(self):
        if len(self._recent):
            return self._recent[-1]
        else:
            return None

    def recentValues(self,maxValues=0):
        if maxValues and maxValues < len(self._recent):
            return self._recent[:maxValues]
        else:
            return self._recent

    def clearRecentValues(self):
        self._recent = list()

    def _saveRecentTimerCB(self):
        if self._proposedValue != None:
            self.saveRecentValue(self._proposedValue)

    def proposeSaveCandidate(self,value):
        self._proposedValue = value
        self._saveTimer.start(2000)

# --- Widgets without inheritance ---

class DirComboBox(QComboBox):
    """
    Choose a directory
    
    Instantiate with either:
        nothing (or None)
        a path to a directory or
        a list of paths
    
    If a list is given, the chooser will present the basenames as choices,
    or if a path is given (string or path object) then the
    subdirectories that match pattern will be choosable.
    
    If no directory is given, the cwd is used.
    
    Will emit signal 'directoryChanged(QString)' when a choice is made with
    the string set to the full path to the chosen subdirectory.
    
    the combo box's 'files' and 'dirs' properties will be updated
    with lists of path objects to all the dirs and files in the 
    chosen subdirectory.
    
    The current chosen subdirectory is available as its 
    'directory' property as a path object.
    """

    def __init__(self, directoryOrPaths=None, pattern="*", parent=None):
        super(DirComboBox, self).__init__(parent)
        self.setup(directoryOrPaths,pattern)
        self.connect(self, SIGNAL('currentIndexChanged(int)'), self.updateUiCB)

    def setup(self,directoryOrPaths,pattern='*'):
        self.pattern = pattern
        self.subDirs = dict()
        if isinstance(directoryOrPaths,(list,tuple)):
            self.subDirs = dict( [ (Path(d).basename(), Path(d)) for d in directoryOrPaths ] )
            choices = [ Path(d).basename() for d in directoryOrPaths ]
        elif isinstance(directoryOrPaths,(str,unicode,Path)):
            self.subDirs = dict( [ (s.basename(),s) for s in directoryOrPaths.dirs(self.pattern)] )
            choices = self.subDirs.keys()
        else:
            self.subdirs = dict( [ (s.basename(),s) for s in Path().getcwd().dirs(self.pattern)] )
            choices = self.subDirs.keys()
        self.addItems(sorted(choices))
        self.setCurrentIndex(0)
        QTimer.singleShot(200, self.updateUiCB)
        
    def updateUiCB(self, choice=0):
        current = self.directory
        if current != None:
            self.emit(SIGNAL('directoryChanged(QString)'), QString(current))

    @property
    def dirs(self):
        return self.directory.dirs() if self.directory else []

    @property
    def files(self):
        return self.directory.files() if self.directory else []

    @property
    def directory(self):
        return self.subDirs.get(str(self.currentText()), None)






# --- Widgets that have inheritance controls ---

INHERITANCE_RANK = {0: "Local", 1: "Inherit", 2: "Default"}


class InheritControlWidget(BaseEditWidget):


    def __init__(self,parent=None):
        super(InheritControlWidget,self).__init__(parent)
        #self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self,SIGNAL("customContextMenuRequested (const QPoint&)"),self.contextMenuCB)
        self._defaultValues = []
        self._deleteAllowed = False

    def addDefaultValue(self,v):
        self._defaultValues.append(v)

    def setAllowDelete(self,onOff):
        if onOff:
            self._deleteAllowed = True
        else:
            self._deleteAllowed = False

    def contextMenuCB(self,pos):
        menu = QMenu(self)
        
        if self._deleteAllowed:
            menu.addAction( QAction("Delete",self) )
        
        inheritMenu = QMenu("Inheritance",menu)
        inheritMenu.addAction( QAction(INHERITANCE_RANK[0],self) )
        inheritMenu.addAction( QAction(INHERITANCE_RANK[1],self) )
        inheritMenu.addAction( QAction(INHERITANCE_RANK[2],self) )
        menu.addMenu(inheritMenu)

        # Set values
        if self._defaultValues:
            menu.addSeparator()
            rangesMenu = QMenu("Default",menu)
            for a in self._defaultValues:
                rangesMenu.addAction( QAction(str(a),self) )
            menu.addMenu(rangesMenu)

        # Recent values
        recentValues = self.recentValues()
        if recentValues:
            menu.addSeparator()
            recentMenu = QMenu("Recent",menu)
            for v in recentValues:
                recentMenu.addAction( QAction(str(v),self) )
            menu.addMenu(recentMenu)

        gpos = self.mapToGlobal(pos)
        action = menu.exec_(gpos)
        if action:
            if action.text() == INHERITANCE_RANK[0]:
                self.setInheritanceRank(0)
                self.emit(SIGNAL("inheritanceChanged(int)"),0)
            elif action.text() == INHERITANCE_RANK[1]:
                self.setInheritanceRank(1)
                self.emit(SIGNAL("inheritanceChanged(int)"),1)
            elif action.text() == INHERITANCE_RANK[2]:
                self.setInheritanceRank(2)
                self.emit(SIGNAL("inheritanceChanged(int)"),2)
            elif action.text() == "Delete":
                self.emit(SIGNAL("delete()"))
            else:
                self.setValue( str(action.text()) )

    def mouseDoubleClickEvent(self, event):
        self.setInheritanceRank(0)


    def setInheritanceRank(self,rank):
        assert rank in INHERITANCE_RANK, "rank not in %s: '%s'" % (repr(INHERITANCE_RANK.keys()),rank)
        iconLocal     = getTagIcon("ParamLocal").pixmap(24,24)
        iconInherited = getTagIcon("ParamInherit").pixmap(24,24)
        iconDefault   = getTagIcon("ParamDefault").pixmap(24,24)
        font = QFont()
        #font.setLetterSpacing(QFont.PercentageSpacing,90.0)
        #font.setFixedPitch(False)
        if rank == 0: 
            self.setEditEnabled(True)
            self.iconL.setPixmap(iconLocal)
            font.setPointSize(12)
            font.setWeight(99)
            font.setBold(True)
        elif rank == 1: 
            self.setEditEnabled(False)
            self.iconL.setPixmap(iconInherited)
            font.setPointSize(10)
            font.setWeight(0)
            font.setBold(False)
        elif rank == 2: 
            self.setEditEnabled(False)
            self.iconL.setPixmap(iconDefault)
            font.setPointSize(10)
            font.setWeight(0)
            font.setBold(False)
            font.setItalic(True)
        self.nameL.setFont(font)


class SwitchEditWidget(InheritControlWidget):

    def __init__(self,parent=None):
        super(SwitchEditWidget,self).__init__(parent)

        self.checkbox = QCheckBox(self.frame)
        self.checkbox.setMinimumWidth(40)
        self.checkbox.setMaximumWidth(40)
        self.checkbox.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed))
        self.layout.addWidget(self.checkbox)
        self.checkbox.setCheckState(Qt.Checked)
        self.layout.addStretch(1)

        def stateChangedCB(v):
            v = self.checkbox.checkState() == Qt.Checked
            self.emit(SIGNAL("valueChanged(QVariant)"),QVariant(v))
        self.connect(self.checkbox, SIGNAL("stateChanged(int)"),stateChangedCB)
        self._editWidgets = [self.checkbox]

    def getValue(self):
        return 1.0 if self.checkbox.isChecked() else 0.0

    def setValue(self,v):
        if v in (True, False):
            i = v
        elif isinstance(v,int):
            i = i != 0
        elif isinstance(v,float):
            i = int(v) != 0
        elif isinstance(v,(str,unicode,QString)):
            try:
                i = int(eval(str(v))) != 0
            except:
                i = 0
        elif isinstance(v,(tuple,list)):
            i = int(v[0]) != 0
        else:
            print "XXX weird type",v, type(v)
            i = 0
        self.setCheckState( i )

    def setCheckState(self,bool):
        if bool:
            checkState = Qt.Checked
        else:
            checkState = Qt.Unchecked
        self.checkbox.setCheckState(checkState)


class FloatEditWidget(InheritControlWidget):

    def __init__(self,parent=None):
        super(FloatEditWidget,self).__init__(parent)

        self.valueLE = QLineEdit(self.frame)
        self.valueLE.setMaximumWidth(150)
        self.valueLE.setMinimumHeight(20)
        self.valueLE.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed))
        self.validator = QDoubleValidator(-1e38,1e38,4,self.valueLE)
        self.valueLE.setValidator(self.validator)

        self.valueLE.setText("0.000")

        def textChangedCB(s):
            state, i = self.validator.validate(s,0)
            self.setFont(state)

        def textEditedCB(s):
            state, i = self.validator.validate(s,0)
            self.setFont(state)
            if state == QValidator.Acceptable:
                v = float(s)
                self.emit(SIGNAL("valueChanged(QVariant)"),QVariant(v))
                self.proposeSaveCandidate(v)

        def editingFinishedCB():
            s = str( self.valueLE.text() )
            state, i = self.validator.validate(s,0)
            self.setFont(state)
            if state == QValidator.Acceptable:
                v = float(s)
                self.emit(SIGNAL("valueChanged(QVariant)"),QVariant(v))
                self.proposeSaveCandidate(v)

        self.connect(self.valueLE, SIGNAL("textChanged(const QString&)"),textChangedCB)
        self.connect(self.valueLE, SIGNAL("textEdited (const QString&)"),textEditedCB)
        self.connect(self.valueLE, SIGNAL("editingFinished()"),editingFinishedCB)

        self.layout.addWidget(self.valueLE)
        self.layout.addStretch(0.1)
        self._editWidgets = [self.valueLE,]

    def setFont(self,style=QValidator.Acceptable):
        font = QFont()
        font.setPointSize(9)
        if style == QValidator.Acceptable:
            font.setWeight(75)
            font.setBold(True)
        else:
            font.setWeight(0)
            font.setItalic(True)
        self.valueLE.setFont(font)

    def getValue(self):
        return float( self.valueLE.text() )

    def setValue(self,v):
        if isinstance(v,(list,tuple)):
            if len(v) == 1: #workaround hack for when it has a list of one float.
                v = v[0]
        if isinstance(v,(str,unicode)):
            s = v
            try:
                v = float(s)
            except:
                print "XXX failed setValue() not float",v,type(v)
                return
        else:
            try:
                s = "%g" % v
            except:
                print "XXX failed setValue() not stringable",v,type(v)
                return
        #print "XXX setValue() s='%s'  v='%s'"%(s,v)
        self.valueLE.setText(s)

def clamp(x,lo,hi): return min(hi,max(lo,x))

class ColorEditWidget(InheritControlWidget):

    def __init__(self,parent=None):
        super(ColorEditWidget,self).__init__(parent)

        self.fontValid = QFont()
        self.fontValid.setPointSize(10)
        self.fontValid.setWeight(50)
        self.fontIntermediate = QFont()
        self.fontIntermediate.setWeight(50)
        self.fontIntermediate.setPointSize(10)
        self.fontIntermediate.setItalic(True)
        self.fontInvalid = QFont()
        self.fontInvalid.setPointSize(10)
        self.fontInvalid.setWeight(0)
        self.fontInvalid.setItalic(True)

        self.dial = dict()
        self.edit = dict()
        for c in ('R', 'G', 'B'):#, 'H', 'S', 'V'):
            self.edit[c] = QLineEdit(self.frame)
            if c == 'H':
                self.edit[c].setText("0")
            else:
                self.edit[c].setText("1.000")
            self.edit[c].setToolTip(c)
            self.edit[c].setMinimumHeight(24)
            self.edit[c].setMinimumWidth(40)
            self.edit[c].setMaximumWidth(60)
            self.edit[c].setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed))
            self.edit[c].setAlignment(Qt.AlignLeft|Qt.AlignTrailing|Qt.AlignVCenter)
            self.edit[c].validator = QDoubleValidator(0.0,100.0,DECIMALS,self.edit[c])
            self.edit[c].setValidator(self.edit[c].validator)
            self.layout.addWidget(self.edit[c])

            def textChangedCB(s,channel=c):
                edit = self.edit[channel]
                dial = self.dial[channel]
                if channel == 'H':
                    range = 3590
                else:
                    range = 2550
                state, i = edit.validator.validate(s,0)
                if state == QValidator.Intermediate:
                    edit.setFont(self.fontIntermediate)
                    return
                elif state == QValidator.Acceptable:
                    edit.setFont(self.fontValid)
                    #dial.setValue(int(range*float(s)))
                    self.update()
                    self.emitRGB()
                elif state == QValidator.Invalid:
                    edit.setFont(self.fontInvalid)
                    return
            self.connect(self.edit[c], SIGNAL("textChanged(const QString&)"),textChangedCB)

            self.dial[c] = QDial(self.frame)
            self.dial[c].setToolTip(c)
            self.dial[c].setBaseSize(24,24)
            self.dial[c].setMaximumWidth(24)
            self.dial[c].setMinimumHeight(24)
            sizePolicy = QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            self.dial[c].setSizePolicy(sizePolicy)
            if c == 'H':
                self.dial[c].setMaximum(3590)
                self.dial[c].setValue(0)
            else:
                self.dial[c].setMaximum(2550)
                self.dial[c].setValue(2550)
            self.layout.addWidget(self.dial[c])

            def valueChangedCB(n,channel=c):
                edit = self.edit[channel]
                if channel == 'H':
                    v = float(n)
                    edit.setText("%d" % n)
                else:
                    v = float(n) / 2550.0
                    edit.setText("%5.4f" % v)
                self.update(channel)
            self.connect(self.dial[c], SIGNAL("valueChanged(int)"),valueChangedCB)

        self.swatchPB = QPushButton(self.frame)
        self.swatchPB.setBaseSize(48,24)
        self.swatchPB.setMaximumWidth(48)
        self.swatchPB.setMinimumHeight(24)
        self.swatchPB.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed))
        palette = QPalette()
        brush = QBrush(QColor(0,0,0))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active,QPalette.Button,brush)
        palette.setBrush(QPalette.Inactive,QPalette.Button,brush)
        palette.setBrush(QPalette.Disabled,QPalette.Button,brush)
        self.swatchPB.setPalette(palette)
        self.swatchPB.setCursor(Qt.ArrowCursor)
        self.swatchPB.setAcceptDrops(True)
        self.swatchPB.setAutoFillBackground(False)
        self.layout.addWidget(self.swatchPB)

        self.lutCheckBox = QCheckBox(self.frame)
        font = QFont()
        font.setPointSize(8)
        self.lutCheckBox.setFont(font)
        self.lutCheckBox.setChecked(True)
        self.lutCheckBox.setText("LINEAR")
        def lutChangedCB(n):
            self.update()
        self.connect(self.lutCheckBox, SIGNAL("stateChanged(int)"),lutChangedCB)
        self.layout.addWidget(self.lutCheckBox)
        self.update()
        self.layout.addStretch(0.1)
        self._editWidgets = self.dial.values()+self.edit.values()+[self.lutCheckBox,self.swatchPB,]
        
        self.lutCheckBox.hide()


    def update(self,channel=None):
        r,g,b = self.getValue()
        if channel in ('H', 'S', 'V'):
            hsv = QColor(r,g,b).toHsv()
        if self.lutCheckBox.checkState() == Qt.Checked:
            r  = linearToSrgb(r)
            g  = linearToSrgb(g)
            b  = linearToSrgb(b)
        rI = int(255.0*clamp(r,0.0,1.0))
        gI = int(255.0*clamp(g,0.0,1.0))
        bI = int(255.0*clamp(b,0.0,1.0))
        palette = QPalette()
        brush = QBrush(QColor(rI,gI,bI))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active,QPalette.Button,brush)
        palette.setBrush(QPalette.Inactive,QPalette.Button,brush)
        palette.setBrush(QPalette.Disabled,QPalette.Button,brush)
        self.swatchPB.setPalette(palette)
        if hasattr(self,"rgbColorL"):
            self.rgbColorL.setText("%s   %s   %s" % (r,g,b))

    def getValue(self):
        rS = self.edit['R'].text() or '1'
        gS = self.edit['G'].text() or '1'
        bS = self.edit['B'].text() or '1'
        r  = float(rS)
        g  = float(gS)
        b  = float(bS)
        return (r,g,b)
        #return ( float(self.dial['R'].value()) / 2550.0, float(self.dial['G'].value()) / 2550.0,  float(self.dial['B'].value()) / 2550.0 )

    def setValue(self,r,g=None,b=None,setText=True):
        if isinstance(r,(str,unicode)) and g == None and b == None:
            try:
                r, g, b = eval(r)
            except:
                return
        if isinstance(r,(tuple,list)) and len(r) == 3 and g == None and b == None:
            r, g, b = r
        if setText:
            for c, v in ( ('R',r), ('G',g), ('B',b) ):
                fmt = "%%%d.%df" % (DECIMALS+1,DECIMALS)
                try:
                    s = fmt % v
                except TypeError:
                    pass
                else:
                    self.edit[c].setText(s)
        self.update()

    def rgb(self):
        rS = self.edit['R'].text() or '1'
        gS = self.edit['G'].text() or '1'
        bS = self.edit['B'].text() or '1'
        r  = float(rS)
        g  = float(gS)
        b  = float(bS)
        return (r,g,b)

    def emitRGB(self):
        r, g, b = self.rgb()
        self.emit(SIGNAL("valueChanged(QVariant)"),QVariant((r,g,b)))
        self.proposeSaveCandidate((r,g,b))

def srgbToLinear(v):
    if v <= 0.04045: 
        L = v / 12.92
    else:
        L = pow((v+0.055)/1.055, 2.4)
    return L

def linearToSrgb(v):
    if v > 0.00313:
        L = (pow(v,1.0/2.4) * 1.055) - 0.055
    else:
        L = 12.92 * v
    return L

class MaptypeEditWidget(InheritControlWidget):

    def __init__(self,parent=None):
        super(MaptypeEditWidget,self).__init__(parent)
        
        self.texTags = list()

        self.maptypeC = QComboBox(self.frame)
        self.maptypeC.setMinimumWidth(80)
        self.maptypeC.setMaximumWidth(120)
        self.maptypeC.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed))

        self.textagLE = QLineEdit(self.frame)
        self.textagLE.setMinimumWidth(180)
        self.textagLE.setMaximumWidth(280)
        self.textagLE.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed))
        self.textagLE.setToolTip("Texture tag override\nUse an existing texture tag from GTO or 'global'")

        self._index = dict()
        self._reverseIndex = dict()
        self.maptypeC.addItem('')
        self._index[''] = 0
        self._reverseIndex[0] = ''
        for i,t in enumerate(sorted(mapTypeTxInfo)):
            self.maptypeC.addItem(t)
            self._index[t] = i+1
            self._reverseIndex[i+1] = t

        #TODO: list of texTags. Now just blank or 'global'.
        self.textagLE.setText('')
        #self.textagC.addItem('global')
        #self.textagC.addSeparator()
        #for i,t in enumerate(sorted(self.texTags)):
        #    self.textagC.addItem(t)

        def indexChangedCB(ignored):
            mapType = str(self.maptypeC.currentText())
            texTag  = str(self.textagLE.text()).strip()
            if texTag:
                mapType = "%s:%s" % (mapType,texTag)
            self.emit(SIGNAL("valueChanged(QVariant)"),QVariant(mapType))
            self.proposeSaveCandidate(mapType)
        self.connect(self.maptypeC, SIGNAL("currentIndexChanged (const QString&)"),indexChangedCB)
        self.connect(self.textagLE, SIGNAL("textChanged (const QString&)"),indexChangedCB)

        self.layout.addWidget(self.maptypeC)
        self.layout.addWidget(QLabel(":"))
        self.layout.addWidget(self.textagLE)
        self.layout.addStretch(1)
        self._editWidgets = [self.maptypeC,self.textagLE, ]

    def setMaptype(self,mapType):
        if ':' in mapType:
            mt, texTag = mapType.split(":",1)
        else:
            mt, texTag = mapType, ''
        if not mt or (mt not in self._index):
            i = 0
            #raise Exception("maptype '%s' not in database" %(mt,))
        else:
            i = self._index[mt]
        self.maptypeC.setCurrentIndex(i)
        #TODO: list of texTags.
        self.textagLE.setText(texTag)
    setValue = setMaptype

    def getValue(self):
        mapType = str(self.maptypeC.currentText())
        texTag  = str(self.textagLE.text()).strip()
        if texTag:
            mapType = "%s:%s" % (mapType,texTag)
        return mapType




class StringEditWidget(InheritControlWidget):

    def __init__(self,parent=None):
        super(StringEditWidget,self).__init__(parent)

        self.lineedit = QLineEdit(self.frame)
        self.lineedit.setMinimumWidth(80)
        self.lineedit.setMaximumWidth(520)
        self.lineedit.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed))
        self._editWidgets = [self.lineedit,]

        def textChangedCB(s):
            self.emit(SIGNAL("valueChanged(QVariant)"),QVariant(str(s)))
            self.proposeSaveCandidate(str(s))
        self.connect(self.lineedit, SIGNAL("textChanged (const QString&)"),textChangedCB)

        self.layout.addWidget(self.lineedit)
        self.layout.addStretch(0.1)

    def getValue(self):
        return str(self.lineedit.text())

    def setValue(self,v):
        self.lineedit.setText(str(v))


class RibAttrEditWidget(StringEditWidget):
    def __init__(self,parent=None):
        super(RibAttrEditWidget,self).__init__(parent)
        self.setAllowDelete(True)

# ------------------------------------------------------------------

class PolishingSlider(QSlider):
    """Slider with mouseRelease callback and logarithmic feature"""
    def __init__(self,parent=None):
        super(PolishingSlider,self).__init__(parent)
        self.setRange(0,1000)
        self.setOrientation(Qt.Horizontal)
        self.mouseReleaseCallback = None
        self.mouseMoveCallback = None
    def setFloatRange(self,lo,hi,log=False):
        self.loFloat = lo
        self.hiFloat = hi
        self.log     = log
    def setFloatValue(self,floatValue):
        self.setValue(self.fToI(floatValue))
    def iToF(self,intValue):
        return self.loFloat + (self.hiFloat-self.loFloat) * pow(float(intValue) / 1000.0, 2.2 if self.log else 1.0)
    def fToI(self,floatValue):
        nF = pow( (floatValue - self.loFloat) / (self.hiFloat-self.loFloat), 1.0/2.2 if self.log else 1.0)
        i = max(0,min(1000,int(nF*1000.0)))
        #print nF,i
        return i
    def setMouseReleaseCallback(self,callback):
        self.mouseReleaseCallback = callback
    def setMouseMoveCallback(self,callback):
        self.mouseMoveCallback = callback
    def mouseReleaseEvent(self,event):
        QSlider.mouseReleaseEvent(self,event)
        if self.mouseReleaseCallback:
            self.mouseReleaseCallback(self)
    def mouseMoveEvent(self,event):
        QSlider.mouseMoveEvent(self,event)
        if self.mouseMoveCallback:
            self.mouseMoveCallback(self)



class WidgetSet(QWidget):
    
    """Vertical list of control widgets"""
    
    def __init__(self,parent):
        super(WidgetSet,self).__init__(parent)
        self.setLayout(QVBoxLayout())
        self.gridLayout = QGridLayout()
        self.gridLayout.setColumnStretch(0,0.0)
        self.gridLayout.setColumnStretch(2,0.8)
        self.gridLayout.setColumnMinimumWidth(0,100)
        self.gridLayout.setColumnMinimumWidth(1, 70)
        self.layout().addLayout(self.gridLayout)
        self.layout().addStretch()
        self.rowIndex = 0
        self._rowLabel = dict()
        self._rowWidget = dict()
        self.floatValidator = QDoubleValidator(-1e38,1e38,4,self)

    def getRowLabel(self,index):
        return self._rowLabel.get(index,None)

    def getRowWidget(self,index):
        return self._rowWidget.get(index,None)

    def addSlider(self,name,callback,initValue=None,loValue=0.0,hiValue=1.0,log=False,format="%g",rubber=False):
        if initValue == None: initValue = hiValue
        def cb0(valI):
            sW = self.sender()
            valF = sW.iToF(valI)
            sW.numberWidget.setText(format % valF)
        def cb1(valI):
            sW = self.sender()
            valF = sW.iToF(valI)
            try:
                callback(valF)
            except:
                pass
            sW.numberWidget.setText(format % valF)
            self.emit(SIGNAL("valueChanged()"))
        def cb2(sW):
            valI = sW.sliderPosition()
            valF = sW.iToF(valI)
            try:
                callback(valF)
            except:
                pass
            sW.numberWidget.setText(format % valF)
            self.emit(SIGNAL("valueChanged()"))
        sliderW = PolishingSlider(self)
        sliderW.setFloatRange(loValue,hiValue,log)
        numberW = QLabel()
        numberW.setText(format % (initValue or loValue))
        sliderW.numberWidget = numberW
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        class wrapSlider:
            def __init__(self,slider):
                self.slider = slider
            def setValue(self,value):
                sW = self.slider
                valI = sW.fToI(value)
                self.slider.setValue(valI)
                valF = sW.iToF(valI)
                sW.numberWidget.setText(format % valF)
        wrapper = wrapSlider(sliderW)
        self._rowWidget[self.rowIndex] = wrapper
        self.connect(sliderW,SIGNAL("valueChanged(int)"),cb0)
        if rubber:
            sliderW.setMouseMoveCallback(cb2)
        else:
            sliderW.setMouseReleaseCallback(cb2)
        self.gridLayout.addWidget(sliderW, self.rowIndex,2)
        self.gridLayout.addWidget(numberW,self.rowIndex,1)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        sliderW.setFloatValue(initValue)
        try:
            callback(initValue)
        except:
            pass
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addCheckbox(self,name,callback,initValue=False):
        def cb(val):
            sW = self.sender()
            callback(val not in (None,0,''))
            self.emit(SIGNAL("valueChanged()"))
        checkW = QCheckBox(self)
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = checkW
        checkW.setValue = lambda v: checkW.setCheckState( (Qt.Unchecked,Qt.Checked)[v!=False])
        self.connect(checkW,SIGNAL("stateChanged(int)"),cb)
        self.gridLayout.addWidget(checkW, self.rowIndex,1,Qt.AlignLeft)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        checkW.setCheckState((Qt.Unchecked,Qt.Checked)[int(initValue)!=0])
        try:
            callback(initValue)
        except:
            pass
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addInteger(self,name,callback,initValue=None,**kw):
        lo = None
        hi = None
        for k,v in kw.items():
            if k in ("min","minimum","lo"):
                lo = v
            elif k in ("max","maximum","hi"):
                hi = v
            else:
                raise ValueError("no such arg '%s'" % k)
        def cb(val):
            sW = self.sender()
            callback(val)
            self.emit(SIGNAL("valueChanged()"))
        spinW = QSpinBox(self)
        labelW = QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = spinW
        #spinW.setValue = lambda v: spinW.setValue(v)
        self.connect(spinW,SIGNAL("valueChanged(int)"),cb)
        self.gridLayout.addWidget(spinW, self.rowIndex,1,Qt.AlignLeft)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        if lo != None:
            spinW.setMinimum(lo)
        else:
            spinW.setMinimum(0)
        if hi != None:
            spinW.setMaximum(hi)
        else:
            spinW.setMaximum(9999)
        try:
            callback(initValue)
        except:
            pass
        spinW.setValue(int(initValue))
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addCombo(self,name,callback,choices,initChoice=None):
        def cb(val):
            sW = self.sender()
            callback(str(val))
            self.emit(SIGNAL("valueChanged()"))
        comboW = QComboBox(self)
        try:
            comboW.addItems(choices)
        except:
            print choices
            raise
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = comboW
        comboW.setValue = lambda v: comboW.setCurrentIndex(comboW.findText(QString(v)))
        self.connect(comboW,SIGNAL("currentIndexChanged (const QString&)"),cb)
        self.gridLayout.addWidget(comboW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        try:
            callback(initChoice or choices[0])
        except:
            pass
        else:
            for i,c in enumerate(choices):
                if c == initChoice:
                    comboW.setCurrentIndex(i)
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addIntegerCombo(self,name,callback,choices,initChoice=None):
        def cb(val):
            sW = self.sender()
            try:
                v = int(str(val))
            except:
                return
            callback(v)
            self.emit(SIGNAL("valueChanged()"))
        comboW = QComboBox(self)
        try:
            comboW.addItems([str(i) for i in choices])
        except:
            print choices
            raise
        labelW = QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = comboW
        comboW.setValue = lambda v: comboW.setCurrentIndex(comboW.findText(QString(v)))
        self.connect(comboW,SIGNAL("currentIndexChanged (const QString&)"),cb)
        self.gridLayout.addWidget(comboW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        try:
            callback(initChoice or choices[0])
        except:
            pass
        else:
            for i,c in enumerate(choices):
                if c == initChoice:
                    comboW.setCurrentIndex(i)
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addFloatCombo(self,name,callback,choices,initChoice=None):
        def cb(val):
            sW = self.sender()
            callback(float(str(val)))
            self.emit(SIGNAL("valueChanged()"))
        comboW = QComboBox(self)
        try:
            comboW.addItems(["%g"%i for i in choices])
        except:
            print choices
            raise
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = comboW
        comboW.setValue = lambda v: comboW.setCurrentIndex(comboW.findText(QString(v)))
        self.connect(comboW,SIGNAL("currentIndexChanged (const QString&)"),cb)
        self.gridLayout.addWidget(comboW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        try:
            callback(initChoice or choices[0])
        except:
            pass
        else:
            for i,c in enumerate(choices):
                if c == initChoice:
                    comboW.setCurrentIndex(i)
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addLineEdit(self,name,callback,text):
        def cb(val):
            sW = self.sender()
            callback(str(val))
            self.emit(SIGNAL("valueChanged()"))
        lineeditW = QLineEdit(self)
        try:
            lineeditW.setText(text)
        except:
            print text
            raise
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = lineeditW
        lineeditW.setValue = lambda v: lineeditW.setText(v)
        self.connect(lineeditW,SIGNAL("textChanged (const QString&)"),cb)
        self.gridLayout.addWidget(lineeditW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        try:
            callback(text)
        except:
            pass
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addDateEdit(self,name,callback,text):
        def cb(val):
            sW = self.sender()
            callback(str(val))
            self.emit(SIGNAL("valueChanged()"))
        dateeditW = QDateEdit(self)
        dateeditW.setCalendarPopup(True)
        dateeditW.setDisplayFormat("yyyyMMdd")
        try:
            dateeditW.setDateTime(dateeditW.dateTimeFromText(text))
        except:
            print text
            raise
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = dateeditW
        dateeditW.setValue = lambda v: dateeditW.setText(v)
        self.connect(dateeditW,SIGNAL("dateChanged (const QDate&)"),cb)
        self.gridLayout.addWidget(dateeditW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        try:
            callback(text)
        except:
            pass
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addFileChooser(self,name,callback,filePath):
        def cb(val):
            sW = self.sender()
            callback(str(val))
            self.emit(SIGNAL("valueChanged()"))
        lineeditW = QLineEdit(self)
        try:
            lineeditW.setText(filePath)
        except:
            print filePath
            raise
        labelW  =QLabel(name)
        
        def requestCB():
            s = str(lineeditW.text()).strip()
            if not s:
                directory = os.getcwd()
            else:
                directory = Path(s).dirname()
            filename = QFileDialog.getOpenFileName(
                None, # application modal
                QString("Choose file for %s" % name.strip()),
                QString(directory),
            )
            if filename:
                try:
                    callback(filename)
                    lineeditW.setText(filename)
                except:
                    pass
            else:
                pass

        browseB = QToolButton()
        browseB.setIcon(getTagIcon('open'))
        browseB.setToolTip("Browse for file")
        browseB.setAutoRaise(True)
        self.connect(browseB, SIGNAL("clicked()"),requestCB)

        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = lineeditW
        lineeditW.setValue = lambda v: lineeditW.setText(v)
        self.connect(lineeditW,SIGNAL("textChanged (const QString&)"),cb)
        self.gridLayout.addWidget(labelW, self.rowIndex, 0,1,1)
        self.gridLayout.addWidget(browseB, self.rowIndex,1,1,1)
        self.gridLayout.addWidget(lineeditW, self.rowIndex,2,1,1)
        try:
            callback(filePath)
        except:
            pass
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addFloatEdit(self,name,callback,value):
        def cb(val):
            sW = self.sender()
            state, i = self.floatValidator.validate(str(val),0)
            try:
                v = float(str(val))
            except:
                return
            if state == QValidator.Acceptable:
                callback(v)
                self.emit(SIGNAL("valueChanged()"))
        lineeditW = QLineEdit(self)
        if isinstance(value,(float,int)):
            text = "%g" % value
        else:
            text = str(value).strip()
        try:
            lineeditW.setText(text)
        except:
            print text
            raise
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = lineeditW
        lineeditW.setValue = lambda v: lineeditW.setText(str(v))
        self.connect(lineeditW,SIGNAL("textChanged (const QString&)"),cb)
        self.gridLayout.addWidget(lineeditW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        lineeditW.setValidator(self.floatValidator)
        try:
            callback(text)
        except:
            pass
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addVectorEdit(self,name,callback,value,fmt="%6.3f"):
        def cb(val):
            sW = self.sender()
            state, i = self.floatValidator.validate(str(val),0)
            try:
                v = float(str(val))
            except:
                return
            if state == QValidator.Acceptable:
                x,y,z = [float(str(w.text())) for w in sW.xyzWidgets]
                callback(vec3(x,y,z))
                self.emit(SIGNAL("valueChanged()"))
        mainW = QWidget(self)
        xEditW = QLineEdit(mainW)
        yEditW = QLineEdit(mainW)
        zEditW = QLineEdit(mainW)
        xEditW.xyzWidgets = (xEditW,yEditW,zEditW)
        yEditW.xyzWidgets = (xEditW,yEditW,zEditW)
        zEditW.xyzWidgets = (xEditW,yEditW,zEditW)
        xyzLayout = QGridLayout()
        mainW.setLayout(xyzLayout)
        xyzLayout.addWidget(xEditW,0,0)
        xyzLayout.addWidget(yEditW,0,1)
        xyzLayout.addWidget(zEditW,0,2)
        try:
            xEditW.setText(fmt % value[0])
            yEditW.setText(fmt % value[1])
            zEditW.setText(fmt % value[2])
        except:
            print value
            raise
        labelW  =QLabel(name)
        self._rowLabel[self.rowIndex] = labelW
        self._rowWidget[self.rowIndex] = mainW
        mainW.setValue = lambda v: (xEditW.setText(fmt % v[0]),yEditW.setText(fmt % v[1]),zEditW.setText(fmt % v[2]))
        self.connect(xEditW,SIGNAL("textChanged (const QString&)"),cb)
        self.connect(yEditW,SIGNAL("textChanged (const QString&)"),cb)
        self.connect(zEditW,SIGNAL("textChanged (const QString&)"),cb)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        self.gridLayout.addWidget(mainW, self.rowIndex,1,1,2)
        xEditW.setValidator(self.floatValidator)
        yEditW.setValidator(self.floatValidator)
        zEditW.setValidator(self.floatValidator)
        try:
            callback(value)
        except:
            pass
        index = self.rowIndex
        self.rowIndex += 1
        return index

    def addSeparator(self,name=''):
        if name:
            labelW = QLabel(self)
            self._rowLabel[self.rowIndex] = labelW
            labelW.setText('<b>%s</b>' % name)
            labelW.setTextFormat(Qt.RichText)
            labelW.setFrameStyle(QFrame.Box | QFrame.Raised)
            self.gridLayout.addWidget(labelW, self.rowIndex,0,1,1)
            #self.gridLayout.addWidget(sepW, self.rowIndex,1,1,2)
        else:
            sepW = QFrame(self)
            sepW.setFrameStyle(QFrame.HLine | QFrame.Raised)
            sepW.setLineWidth(2)
            self.gridLayout.addWidget(sepW, self.rowIndex,0,1,3)
        index = self.rowIndex
        self.rowIndex += 1
        return index


class WidgetSetToolBox(QToolBox):
    
    """A tool box with a tab for each widget set"""
    
    def __init__(self,parent):
        super(WidgetSetToolBox,self).__init__(parent)
        self.widgetIndex = dict() # maps paramName to values
        self.widgetSet = dict() # maps section names to a widgetSet

    def minimumSizeHint(self):
        return QSize(360, 120)

    def addUiItem(self,ws,name,item,callback):
        index = None
        if item.NAME == "Float":
            if "min" in item and "max" in item:
                isLog = "map" in item and item['map'] == 'log'
                isRubber = 'rubber' in item and item['rubber'] == True
                index = ws.addSlider(name,callback,initValue=item.value,loValue=item['min'],hiValue=item['max'],log=isLog,format="%7.3f",rubber=isRubber)
            elif "choices" in item:
                index = ws.addFloatCombo(name,callback,item['choices'],item.value)
            else:
                index = ws.addFloatEdit(name,callback,item.value)
        elif item.NAME == "String":
            if "choices" in item:
                index = ws.addCombo(name,callback,item['choices'],item.value)
            else:
                index = ws.addLineEdit(name,callback,item.value)
        elif item.NAME == "Int":
            if "choices" in item:
                index = ws.addIntegerCombo(name,callback,item['choices'],item.value)
            else:
                index = ws.addInteger(name,callback,item.value)
        elif item.NAME == "File":
            if "choices" in item:
                index = ws.addFileCombo(name,callback,item['choices'],item.value)
            else:
                index = ws.addFileChooser(name,callback,item.value)
        elif item.NAME == "Boolean":
            index = ws.addCheckbox(name,callback,item.value)
        elif item.NAME == "Vector":
            index = ws.addVectorEdit(name,callback,item.value)
        elif item.NAME == "Date":
            index = ws.addDateEdit(name,callback,item.value)
        else:
            pass
        if index == None:
            print "HUH",name,item
            return None
        if 'hint' in item:
            labelW = ws.getRowLabel(index)
            labelW.setToolTip(item['hint'].replace(';','\n'))
        return ws.getRowWidget(index)

    def addUiNameSpace(self,uiNameSpace,callbackFunc):
        assert isinstance(uiNameSpace,utils.UiNameSpace), "expecting UiNameSpace, got '%s'" % repr(uiNameSpace)
        for tabName in uiNameSpace.hdict.keys():
            ns = uiNameSpace[tabName]
            ws = self.getWidgetSet(tabName)
            if isinstance(ns,utils.UiNameSpace):
                for sectionName in ns.hdict.keys():
                    ns2 = ns[sectionName]
                    if isinstance(ns2,utils.UiNameSpace):
                        ws.addSeparator(sectionName)
                        for pName, p in ns2.items():
                            paramName = ".".join([tabName,sectionName,pName])
                            cb = lambda v,n=paramName: callbackFunc(n,v)
                            valueW = self.addUiItem(ws,"    "+pName,p,cb)
                            self.widgetIndex[paramName] = valueW
                            valueW.nameSpaceItem = p
                    else:
                        paramName = ".".join([tabName,sectionName])
                        cb = lambda v,n=paramName: callbackFunc(n,v)
                        valueW = self.addUiItem(ws,sectionName,ns2,cb)
                        self.widgetIndex[paramName] = valueW
                        valueW.nameSpaceItem = ns2
            else:
                raise Exception("bad %s"%tabName)
                #addItem(ws,tabName,ns)
            
    def updateParam(self,paramName):
        v = self.widgetIndex[paramName].nameSpaceItem.value
        self.widgetIndex[paramName].setValue(v)
        print "---- updateParam",paramName,v

    def getWidgetSet(self,tabName,iconName='settings'):
        if tabName in self.widgetSet:
            return self.widgetSet[tabName]
        self.widgetSet[tabName] = WidgetSet(self)
        self.addItem(self.widgetSet[tabName], getTagIcon(iconName), tabName)
        return self.widgetSet[tabName]

    def updateUiNameSpace(self,uiNameSpace,callbackFunc):
        uiNameSpace.write("updateUiNameSpace.uins")
        #from pprint import pprint
        #print "BEFORE:--------------------"
        #pprint(self.widgetIndex)
        #print "--------------------:BEFORE"
        for paramName in uiNameSpace.dict.keys():
            if paramName in self.widgetIndex:
                v = uiNameSpace.get(paramName).value
                print "XXX self.widgetIndex[%s].setValue(uiNameSpace.get(%s).value) = %s" % (paramName,paramName,v)
                self.widgetIndex[paramName].setValue(v)
                continue
            #print " NOT FOUND ",paramName
            for tabName in uiNameSpace.hdict.keys():
                ns = uiNameSpace[tabName]
                ws = self.getWidgetSet(tabName)
                if isinstance(ns,utils.UiNameSpace):
                    for sectionName in ns.hdict.keys():
                        ns2 = ns[sectionName]
                        if isinstance(ns2,utils.UiNameSpace):
                            ws.addSeparator(sectionName)
                            for pName, p in ns2.items():
                                paramName = ".".join([tabName,sectionName,pName])
                                cb = lambda v,n=paramName: callbackFunc(n,v)
                                valueW = self.addUiItem(ws,"    "+pName,p,cb)
                                self.widgetIndex[paramName] = valueW
                                valueW.nameSpaceItem = p
                        else:
                            paramName = ".".join([tabName,sectionName])
                            cb = lambda v,n=paramName: callbackFunc(n,v)
                            valueW = self.addUiItem(ws,sectionName,ns2,cb)
                            self.widgetIndex[paramName] = valueW
                            valueW.nameSpaceItem = ns2
                else:
                    raise Exception("bad %s"%tabName)
        #print "AFTER:--------------------"
        #pprint(self.widgetIndex)
        #print "--------------------:AFTER"
                


# ---------------------------------------------------------------------------
if __name__ == "__main__":

    NWIDGETS = 40

    from random import choice, randint
    randNames = [
        "ColorGain",
        "ColorTex",
        "ColorTint",
        "Color",
        "EdgeGain",
        "EdgeRoughness",
        "GainMaxValue",
        "GainMinValue",
        "GainTex",
        "MaxGain",
        "MinGain",
        "Roughness",
        "RoughnessMaxValue",
        "RoughnessMinValue",
        "RoughnessTex",
        "Switch",
        "Tex",
        "CompOp",
        "Bkm",
        "Ptc",
    ]

    BUILTINS2 = utils.UiNameSpace()
    BUILTINS2.parse("""
        shotplan.show              = String(value='')
        shotplan.shot              = String(value='')
        shotplan.date              = Date(value='20110430')
        shotplan.user              = String(value='')

        plate.frames      = Int(value=240)
        plate.notes       = String(value='')
        
        conversion.eye    = String(value='right',choices=['left','right','both',])
        conversion.notes  = String(value='')
        
        camera.match      = String(value='track',choices=["track", "manual", "lockoff",])
        camera.notes      = String(value='')
        
        set.lidar         = Boolean(value=False)
        set.notes         = String(value='')
        
        fx.has            = Boolean(value=False)
        fx.done           = Boolean(value=True)
        fx.notes          = String(value='')
        
        layer1.name       = String(value="Layer 1")
        layer1.geo.model  = String(value="primitives", choices=["primitives", "blob", "puppet", "hires"])
        layer1.geo.notes          = String(value='')

        layer1.roto.name       = String(value="Layer 1")
        layer1.roto.model  = String(value="primitives", choices=["primitives", "blob", "puppet", "hires"])
        layer1.roto.tight           = Boolean(value=True)
        layer1.roto.feather           = Boolean(value=False)
        layer1.roto.notes          = String(value='')
        
        layer1.osr.width     = Int(value=18)

    """)

    shotplanXml = """
    <shotplan show="xyz" shot="abc123" date="20110523" user="dougm">
        <plate frames="240"> plate notes </plate>
        <conversion eye="left">  # ["left", "right", "both"] 
            conversion overall notes
        </conversion>
        <camera match="track">  # ["track", "manual", "lockoff"] 
            camera notes
        </camera>
        <set lidar="false"> set notes </set>
        <fx has="true" done="false"> fx notes </fx>
        <volume index="1" name="background"> 
            volume note
        </volume>
        <volume index="2" name="rocks">
            <geo model="primitives">  # ["primitives", "blob", "puppet", "hires"] 
                geo notes
            </geo>
            <roto name="jaw" quality="tight" feather="false"> roto notes </roto>
            <osr width="18"> osr notes </osr>
        </volume>
    </shotplan>
    """
    
    BUILTINS = utils.UiNameSpace()
    BUILTINS.parse("""

        object.tilt          = Float(value=0.0,min=-90,max=90,hint="<b>rotation around X axis</b> at center of interest in degrees")
        object.turntable     = Float(value=0.0,min=-180,max=180,hint="<b>rotation of camera around Y axis</b> at center of interest in degrees")
        object.truck         = Float(value=100.0,hint="distance from eye to center of interest in cm")
        object.asset         = String(value='')
        object.file.mtl      = File(value='')
        object.file.gto      = File(value='')
        
        render.order         = String(value='spiral',choices = ['horizontal', 'vertical', 'zigzag-x', 'zigzag-y', 'spacefill', 'spiral', 'random'])
        render.tracebias     = Float(value=0.001,min=0.0,max=1.0,map='log')
        render.shadingrate   = Float(value=1.0,min=0.1,max=10,map='log')
        render.dispbounds    = Float(value=0.5,min=0)
        render.samples       = Int(value=1,min=1,max=16)
        render.sides         = Boolean(value=False)
        
        lights.radius        = Float(value=1.0,hint="scale automatic distance of light locations")
        lights.colored       = Boolean(value=False,hint="tint fill light orange, rim blue")
        lights.rtshad        = Boolean(value=True,hint="raytraced shadows")
        
        camera.fov           = Float(value=39.15)
        camera.clipNear      = Float(value=1.0,min=0.0)
        camera.clipFar       = Float(value=1000000.0,min=0.0)
        camera.persp         = String(value='perspective',choices=['ortho','perspective'])
        camera.crop.left     = Float(value=0.0,min=0.0,max=1.0)
        camera.crop.right    = Float(value=1.0,min=0.0,max=1.0)
        camera.crop.bottom   = Float(value=0.0,min=0.0,max=1.0)
        camera.crop.top      = Float(value=1.0,min=0.0,max=1.0)
        camera.aspect        = Float(value=1.3333,min=0.0,max=3.0,choices=[1.0,1.33333,1.66,1.85,2.35])
        camera.resolution.x  = Int(value=640,choices=[320,640,1024,2048,4096])
        camera.resolution.y  = Int(value=480,choices=[240,480,768,1556,3112])
        camera.aperature     = Float(value=21.94,choices=[21.94, 24.89, 37.72, 20.95],hint="<b>academy</b> 21.94;<b>fullap</b> 24.89;<b>vv</b> 37.72;<b>1.85</b> 20.95")
        camera.position.eye  = Vector(value=(0,0,-100))
  
        background.opacity   = Float(value=0.0,min=0.0,max=1.0)
        background.texture   = File(value='/imd/dept/surfacing/images/col/checkerboardA.tex')
        
        output.channels      = String(value='rgba',choices=['rgb','rgba','r','z'])
        output.outfile       = File(value='',default='render.exr')
        
        visibility.specular  = Boolean(value=True)
        
        hitmode.diffuse      = String(value="shader",choices=["shader","primitive"])
        hitmode.specular     = String(value="shader",choices=["shader","primitive"])
        hitmode.transmission = String(value="shader",choices=["shader","primitive"])
        hitmode.camera       = String(value="shader",choices=["shader","primitive"])
        
        
    """)

    CONSTANTS = utils.UiNameSpace()
    CONSTANTS.parse("""
        material.texture.default     = File(value='/imd/dept/surfacing/materials/Global_default.mtl')
        material.texture.mipmap      = File(value='/imd/dept/surfacing/materials/Global_debugMipMap.mtl')
        material.texture.st          = File(value='/imd/dept/surfacing/materials/debugST.mtl')
        material.texture.shadnorm    = File(value='/imd/dept/surfacing/materials/Global_debugShadingNormals.mtl')
        material.texture.grid        = File(value='/imd/dept/surfacing/materials/grid44.mtl')
        material.texture.norm        = File(value='/imd/dept/surfacing/materials/Global_debugNormals.mtl')

        gto.sphere           = File(value='/imd/dept/surfacing/gto/sphere.gto')
        gto.flange           = File(value='/imd/dept/surfacing/gto/flange.gto')

        environment.diffMap    = File(value='/imd/dept/surfacing/maya/resources/Lobby_Hdr_LatLong_Paint_Gamma_Illum.tex')
        environment.specMap    = File(value='/imd/dept/surfacing/maya/resources/Lobby_Hdr_LatLong_Paint_Gamma_Reflect.tex')
        environment.background = File(value='/imd/dept/surfacing/images/col/checkerboardA.tex')
    """)

    class MainWindow(QMainWindow):

        def __init__(self):
            QMainWindow.__init__(self)

            self.resize(1000, 1000)
            self.setWindowTitle('Edit Widgets Test Application')

            self.statusBar().showMessage('Ready',2000)

            exit = QAction('Exit', self)
            exit.setShortcut('Ctrl+Q')
            exit.setStatusTip('Exit application')
            self.connect(exit, SIGNAL('triggered()'), self.quitCB)

            menubar = self.menuBar()
            file = menubar.addMenu('&Application')
            file.addAction(exit)
  
            self.toolBox = WidgetSetToolBox(self)
            self.toolBox2 = WidgetSetToolBox(self)
            
            self.variables = BUILTINS.dupe()
            self.variables2 = BUILTINS2.dupe()

            def widgetSetCB(paramName,value):
                self.variables.set(paramName,value)
            def widgetSet2CB(paramName,value):
                self.variables2.set(paramName,value)

            self.toolBox.addUiNameSpace(self.variables, widgetSetCB)
            self.toolBox2.addUiNameSpace(self.variables2, widgetSet2CB)

            self.widgetSetDW  = QDockWidget("Render parameters", self)
            self.widgetSetDW.setWidget(self.toolBox)
            
            self.widgetSet2DW  = QDockWidget("Other parameters", self)
            self.widgetSet2DW.setWidget(self.toolBox2)
            
            self.widgetSetDW.setAllowedAreas(Qt.AllDockWidgetAreas)
            self.widgetSetDW.setFeatures(self.widgetSetDW.features() ^ QDockWidget.DockWidgetClosable)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.widgetSetDW)
            
            self.widgetSet2DW.setAllowedAreas(Qt.AllDockWidgetAreas)
            self.widgetSet2DW.setFeatures(self.widgetSet2DW.features() ^ QDockWidget.DockWidgetClosable)
            self.addDockWidget(Qt.RightDockWidgetArea, self.widgetSet2DW)
            
            treeW = QTreeWidget()
            self.setCentralWidget(treeW)
            treeW.setColumnCount(1)
            treeW.setHeaderLabels(["Widget",])

            self.lineW   = QLineEdit(self)
            self.lineDW  = QDockWidget("Set Value", self)
            self.lineDW.setWidget(self.lineW)
            self.lineDW.setAllowedAreas(Qt.AllDockWidgetAreas)
            self.lineDW.setFeatures(self.lineDW.features() ^ QDockWidget.DockWidgetClosable)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.lineDW)

            self.connect(self.lineW, SIGNAL("textChanged(const QString&)"), self.textChangedCB)

            # --- Simple Widget for test suite ---
            
            class NodeWidget(BaseEditWidget):
            
                def __init__(self,parent=None):
                    super(NodeWidget,self).__init__(parent)
                    # I don't know why but the name and icon don't display without this:
                    def anyCB(s): self.emit(SIGNAL("textChanged(const QString&)"),QString(s))
                    self.connect(self.nameL, SIGNAL("textChanged (const QString&)"),anyCB)


            iconsFolder = QTreeWidgetItem()
            iconsFolder.setText(0,"Icons")
            font = QFont()
            font.setLetterSpacing(QFont.PercentageSpacing,90.0)
            font.setFixedPitch(False)
            font.setPointSize(12)
            font.setWeight(99)
            font.setBold(True)
            iconsFolder.setFont(0,font)
            treeW.addTopLevelItem(iconsFolder)
            for name in sorted(iconDirectory.keys()):
                if not name: continue
                child = QTreeWidgetItem()
                iconsFolder.addChild(child)

                f = NodeWidget()
                f.setName(name,name)
                treeW.setItemWidget(child,0,f)

            child = QTreeWidgetItem()
            treeW.addTopLevelItem(child)
            self.shaderWidget = QWidget()
            treeW.setItemWidget(child,0,self.shaderWidget)

            self.widgets = [None] * NWIDGETS
            for i in range(NWIDGETS):
                child = QTreeWidgetItem()
                treeW.addTopLevelItem(child)

                name = choice(randNames)
                if not name: continue
                if name.endswith("Tex"):
                    W = MaptypeEditWidget
                elif name.endswith("Switch"):
                    W = SwitchEditWidget
                elif name.endswith("Color") or name.endswith("Tint"):
                    W = ColorEditWidget
                elif name in("Bkm", "CompOp", "Tint", "Type", ):
                    W = StringEditWidget
                else:
                    W = FloatEditWidget
                editWidget = W()
                self.widgets[i] = editWidget
                editWidget.setName(name)
                rank = randint(0,2)
                if i < 3: rank = i
                editWidget.setInheritanceRank(rank)
                treeW.setItemWidget(child,0,editWidget)

                self.connect(editWidget,SIGNAL("valueChanged(QVariant)"),self.changeCB)
                self.connect(editWidget,SIGNAL("inheritanceChanged(int)"),self.inheritCB)

        def quitCB(self):
            uins = Path("/usr/tmp/variables.uins")
            self.variables.write(uins)
            print "...saved to",uins

        def textChangedCB(self,qs):
            isFloat = False
            isColor = False
            s = str(qs)
            try:
                v = float(s)
                isFloat = True
            except:
                pass
            try:
                r,g,b = [float(i) for i in s.split()]
                isColor = True
                isFloat = False
            except:
                pass
            for i in range(NWIDGETS):
                val = None
                w = self.widgets[i]
                c = w.__class__.__name__
                if isFloat:
                    if c == "FloatEditWidget":
                        val = v
                    elif c == "SwitchEditWidget" and s in (0,1):
                        val = s != '0'
                elif isColor:
                    if c == "ColorEditWidget":
                        val = (r,g,b)
                else:
                    if c == "MaptypeEditWidget":
                        val = s
                    elif c == "StringEditWidget":
                        val = s
                if val != None:
                    w.setValue(val)
            
            if not (isFloat or isColor) and s:
                self.shaderWidget.setValue(s)

        def versChangeCB(self,newVersion):
            print "VERS CHANGE CALLBACK in main: ", self.sender(), newVersion#, self.sender().getValue()

        def changeCB(self,newValue):
            print "CHANGE CALLBACK in main: ", self.sender(), newValue.toPyObject()#, self.sender().getValue()

        def inheritCB(self,newValue):
            print self.sender(), newValue
            if newValue == 1:
                self.sender().setSource("foo")
            else:
                self.sender().setSource("bar")

    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
