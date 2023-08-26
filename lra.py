import maya.cmds as cmds

def toggleLRA(*pArgs):
    list = cmds.ls(selection = True)                        # Get a list of selected objs.
    allList = cmds.ls(transforms = True, type="joint")      # If nothing selected, list everything.
           
    if len(list) == 0:                                              # Nothing selected, use allList
        if cmds.getAttr(allList[0] + ".displayLocalAxis") == 0:     # Toggle LRA visibility all On/Off
            for i in range(len(allList)):
                cmds.setAttr(allList[i] + ".displayLocalAxis", 1)
        else:
            for i in range(len(allList)):
                cmds.setAttr(allList[i] + ".displayLocalAxis", 0) 
                  
    elif cmds.getAttr(list[0] + ".displayLocalAxis") == 0:    # Turn visibility for selected on.
        for i in range(len(list)):
            cmds.setAttr(list[i] + ".displayLocalAxis", 1)
                    
    else:                                                    # Turn visibility for selected off.
        for i in range(len(list)):
            cmds.setAttr(list[i] + ".displayLocalAxis", 0)