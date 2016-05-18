libName = 'Connectors_Molex'

import sys, os
import datetime
from datetime import datetime
sys.path.append("scripts/exportVRML")
import exportPartToVRML as expVRML
import shaderColors

dstDir = '../packages3d/'+libName+'.3dshapes/'
srcDir = 'feeds/'+libName+'/'
tmplDir = 'template/'

from collections import namedtuple
import FreeCAD, FreeCADGui
import random
import ImportGui
import importDXF

bodyName = 'SOLID'
fpName = 'COMPOUND'

def export(variant, fuse=False, overwrite=False, saveFCStd=False, exportDXF=False):
    partPrefix = variant[:-4]
    partPostfix = variant[5:]
    pinCount = int(variant[5:7])

    srcName = srcDir+variant+'.stp'
    if not os.path.isfile(srcName):
        FreeCAD.Console.PrintMessage('missing ' + variant + '.stp\n')
        return

    if not os.path.exists(dstDir):
        os.makedirs(dstDir)

    bodyCutName = 'body-' + partPrefix + '#'

    bodyCut = None
    try:
        tmpl = App.getDocument(libName)
    except:
        tmpl = App.openDocument(tmplDir+libName+'.FCStd')
    for obj in tmpl.Objects:
        if obj.Label.startswith(bodyCutName):
            bodyCut = obj
            break

    if bodyCut == None:
        FreeCAD.Console.PrintMessage('missing template for ' + partPrefix + '\n')
        return

    FreeCAD.Console.PrintMessage('cehcking  ' + variant + '\n')

    names = [x for x in obj.Label.split('#')]
    pitch = float(names[2])
    dstName = dstDir+names[3]\
            .replace('%e',partPrefix)\
            .replace('%o',partPostfix)\
            .replace('%c','%02d'%pinCount)\
            .replace('%p','%.2f'%pitch)

    settings = { 'align':'' }

    if len(names) > 4:
        for i in range(4,len(names)):
            if names[i] == '': continue
            option = [x for x in names[i].split(':')]
            if not option[0] in settings:
                FreeCAD.Console.PrintWarning('unknown setting : ' + option[0] + '\n')
            else:
                settings[option[0]] = option[1]

    if os.path.isfile(dstName+'.stp'):
        if not overwrite:
            FreeCAD.Console.PrintMessage(dstName + ' already exists, skip!\n')
            return

    FreeCAD.Console.PrintMessage('exporting ' + dstName + '\n')

    newDoc = App.newDocument(variant+'_'+str(random.randrange(10000,99999)))
    guiDoc = Gui.getDocument(newDoc.Name)

    bodyCut = newDoc.copyObject(bodyCut,True)
    FreeCAD.Console.PrintMessage(bodyCut.Name +  '\n')
    guiDoc.getObject(bodyCut.Name).Visibility = False;

    ImportGui.insert(srcName,newDoc.Name)

    objs = newDoc.getObjectsByLabel(bodyName)
    if not objs:
        FreeCAD.Console.PrintMessage('missing body for ' + partPrefix + '\n')
        return
    part = objs[0]
    guiDoc.getObject(part.Name).Visibility = False;

    objs = newDoc.getObjectsByLabel(fpName)
    if not objs:
        FreeCAD.Console.PrintMessage('missing footprint for ' + partPrefix + '\n')
        return
    footprint = objs[0]

    # NOTE!!! If we don't use Placement.copy here, we will be getting a surprise
    # from FreeCAD. Even if we reset the bodyCut.Placement below, whenever we change
    # the non-copied placement, bodyCut.Placement will get an update, too! Spooky!!
    # There seems to be some dangling internal reference bug here.
    placement = bodyCut.Placement.copy()
    bodyCut.Placement = App.Placement()

    offset = (pinCount-2)*pitch/2

    if settings['align'] == 'pin':
        placement.Base.x += offset

    footprint.Placement = placement.copy()

    for obj in bodyCut.Shapes:
        # any better way to id array object?
        if 'ArrayType' in obj.PropertiesList:
            # TODO, we assum interval x sets the pitch, add more check later
            obj.IntervalX.x = pitch
            obj.NumberX = pinCount
            obj.Placement.Base.x -= offset
        else:
            for sobj in obj.Shapes:
                if sobj.TypeId == 'Part::Mirroring':
                    sobj.Source.Placement.Base.x -= offset

    newDoc.recompute()

    colors = []
    objs = []
    shapes = []

    def make_part(obj,isCut):
        names = [x for x in obj.Label.split('#')]
        newObj = newDoc.addObject("Part::Feature", names[0])
        if isCut:
            newObj.Shape = part.Shape.cut(obj.Shape).removeSplitter()
        else:
            newObj.Shape = part.Shape.common(obj.Shape).removeSplitter()
        color = names[1]
        if not color in shaderColors.named_colors:
            FreeCAD.Console.PrintWarning('unknown color : ' + color + '\n')
            color = None
        else:
            newObj.ViewObject.ShapeColor = shaderColors.named_colors[color].getDiffuseFloat()
            if not color in colors:
                colors.append(color)
        newObj.Placement = placement.copy()
        shapes.append(newObj)
        objs.append(expVRML.exportObject(freecad_object = newObj, shape_color=color, face_colors=None))

    make_part(bodyCut,True)

    for obj in bodyCut.Shapes:
        make_part(obj,False)

    if fuse:
        newObj = newDoc.addObject("Part::MultiFuse", 'part')
        newObj.Shapes = shapes
        shapes = [newObj]

    newDoc.recompute()

    ImportGui.export(shapes,dstName+'.stp')

    if exportDXF:
        shapes = []
        shapes.append(footprint)
        importDXF.export(shapes,dstName+'.dxf')

    scale=1/2.54
    colored_meshes = expVRML.getColoredMesh(Gui, objs , scale)
    expVRML.writeVRMLFile(colored_meshes, dstName+'.wrl', colors)

    if saveFCStd:
        newDoc.saveAs(dstName+'.FCStd')
    App.closeDocument(newDoc.Name)

if __name__ == "__main__":

    if len(sys.argv) < 3:
        for subdirs,dirs,files in os.walk(srcDir):
            for f in files:
                fname = os.path.splitext(f)
                if fname[1] == '.stp':
                    export(fname[0])
    else:
        export(sys.argv[2])
