import maya.cmds as cmds
import functools

# This script simply wraps Maya's default transformation/pivot matching functions into a single window.
# Just a little more user-friendly than a pinned drop-down list, at least for me!

def matchObjAll(*args):
    '''Match obj position, rotation, scale.'''
    cmds.matchTransform(pos=True, rot=True, scl=True)
    
def matchObjPos(*args):
    '''Match obj position.'''
    cmds.matchTransform(pos=True, rot=False, scl=False)
    
def matchObjRot(*args):
    '''Match obj rotation.'''
    cmds.matchTransform(pos=False, rot=True, scl=False)
    
def matchObjScale(*args):
    '''Match obj scale.'''
    cmds.matchTransform(pos=False, rot=False, scl=True)
    
def matchPivAll(*args):
    '''Match piv position, rotation, scale.'''
    cmds.matchTransform(piv=True)
    
def matchPivRot(*args):
    ''' Match piv position, rotation. The two are linked and cannot be separated.
    
    Get destObj's pivot's world coordinates and apply them to srcObj'''
    selection = cmds.ls(sl=True)
    srcObj = selection[0]
    destObj = selection[1]
    
    pivPos = cmds.xform (destObj, q = True, ws = True, rotatePivot = True)
    cmds.xform (srcObj, ws = True, rp = pivPos)
    
def matchPivScale(*args):
    ''' Match piv scale.'''
    selection = cmds.ls(sl=True)
    srcObj = selection[0]
    destObj = selection[1]
    
    pivPos = cmds.xform (destObj, q = True, ws = True, rotatePivot = True)
    cmds.xform (srcObj, ws = True, sp = pivPos)    
    
     
def createMatchGUI():

    '''GUI window to interact with matching functions'''

    myWin = cmds.window(title="Match Window", width = 300, height = 70)
    cmds.gridLayout(nc=2, cwh=[150,30])
    
    cmds.text("Object:", al="left")
    cmds.text("Pivot:", al="left")
    
    cmds.button(label = "All", command = matchObjAll)
    cmds.button(label = "All", command = matchPivAll)
    cmds.text(" ")
    cmds.text(" ")
    cmds.button(label = "Position", command = matchObjPos)
    cmds.text("N/A")
    cmds.button(label = "Rotation", command = matchObjRot)
    cmds.button(label = "Rotation", command = matchPivRot)
    cmds.button(label = "Scale", command = matchObjScale)
    cmds.button(label = "Scale", command = matchPivScale)

    
    cmds.showWindow(myWin)
    
    
createMatchGUI()