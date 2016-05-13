import sys, os
import datetime
from datetime import datetime
sys.path.append("scripts/exportVRML")
import exportPartToVRML as expVRML
import shaderColors

dstDir = '../packages3d'+libName+'.3dshapes/'
srcDir = 'feeds/'+libName+'/'
tmplDir = 'template/'

from collections import namedtuple
import FreeCAD, FreeCADGui
import random
import ImportGui
import importDXF

