import maya.cmds as cmds
import functools
from splitJoint import splitJoints

# splitJoint is a script written by lecturer, Ari Sarafopoulos. It is not uploaded, so the FK creation options will not work.

def spineGUI():
    '''GUI window for spine setup.'''
    
    myWin = cmds.window(title="IK Spine Setup", width = 355, height = 70)
    cmds.rowColumnLayout(nc=3, cw=[(1, 125), (2, 200), (3, 70)],  columnAttach=[(1, "left", 5), (2, "both", 5)], cs=(5, 5))

    cmds.text(label="Spine Joint - Root:")
    cmds.textField("spine_root_joint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "spine_root_joint"))
    
    cmds.text(label="Spine Joint - End:")
    cmds.textField("spine_end_joint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "spine_end_joint"))
    
    cmds.text(label="IK Ctrl - Root:")
    cmds.textField("spine_root_ctrl")
    cmds.button(label="Select", command=functools.partial(updateTexField, "spine_root_ctrl"))
    
    cmds.text(label="IK Ctrl - End:")
    cmds.textField("spine_end_ctrl")
    cmds.button(label="Select", command=functools.partial(updateTexField, "spine_end_ctrl"))
    
    cmds.text(label="Prefix for new Nodes:")
    cmds.textField("prefix", tx = "ik_spine_")
    cmds.button(label="Select", command=functools.partial(updateTexField, "prefix"))
    
    cmds.separator(visible=False)
    cmds.checkBox("stretch_checkbox", label="Create Spine Stretch", value=True)
    cmds.separator(visible=False)
    
    cmds.separator(visible=False)
    cmds.checkBox("fk_checkbox", label="Create FK Controls", value=True, onc="cmds.intField(\"num_fk_ctrls\",edit=True, en=True) \ncmds.checkBox(\"fk_limit\", edit=True, en=True)", ofc="cmds.intField(\"num_fk_ctrls\", edit=True, en=False) \ncmds.checkBox(\"fk_limit\", edit=True, en=False)")
    cmds.separator(visible=False)
    
    cmds.separator(visible=False)
    cmds.checkBox("fk_limit", label="Restrict FK Controls From Chest", value=False)
    cmds.separator(visible=False)
    
    cmds.text(label="No. of FK Controls:")
    cmds.intField("num_fk_ctrls", value=2)
    cmds.separator(visible=False)

    cmds.button(label="Close", command=functools.partial(closeWindow,myWin))
    cmds.separator(visible = False)
    cmds.button(label="Apply", command=functools.partial(mainFunc, "spine_root_joint", "spine_end_joint", "spine_root_ctrl", "spine_end_ctrl", "stretch_checkbox", "fk_checkbox", "fk_limit", "num_fk_ctrls", "prefix"))

    cmds.showWindow(myWin)


def mainFunc(spine_root_joint, spine_end_joint, spine_root_ctrl, spine_end_ctrl, stretch_checkbox, fk_enabled, fk_limit, fk_ctrls_num, prefix, *pArgs):
    
    ''' Main function and processing block, call to all other functions within this block
    
        spine_root_joint        : string, name of joint to use as root of spine
        spine_end_joint         : string, name of joint to use as end of spine
        spine_root_ctrl         : string, name of control to manipulate spine_root_joint
        spine_end_ctrl          : string, name of control to manipulate spine_end_joint
        stretch_checkbox        : bool, toggle for whether IK spine should be able to stretch
        fk_enabled              : bool, toggle for whether to create any FK controls
        fk_limit                : bool, toggle for whether to limit FK controls from "chest area" of spine (upper 50% of chain)
        fk_ctrls_num            : int, number of desired FK controls
        prefix                  : string, user-defined prefix for created nodes. Defaults to 'ik_spine_'
    
        On Exit:
            Hybrid IK/FK spine created from chain of joints. Behaviour varies based on user settings.
            Integration into rig is not handled by script. Script only creates.
            '''
    
    # Query text and check status for all the GUI text fields. 
    
    spine_root_joint = cmds.textField("spine_root_joint", q=True, text=True)
    spine_end_joint  = cmds.textField("spine_end_joint", q=True, text=True)
    spine_root_ctrl  = cmds.textField("spine_root_ctrl", q=True, text=True)
    spine_end_ctrl   = cmds.textField("spine_end_ctrl", q=True, text=True)
    prefix           = cmds.textField("prefix", q=True, text=True)
    stretch_enabled  = cmds.checkBox("stretch_checkbox", q=True, value=True)
    fk_enabled       = cmds.checkBox("fk_checkbox", q=True, value=True)
    fk_limit         = cmds.checkBox("fk_limit", q=True, value=True)
    fk_ctrls_num     = cmds.intField("num_fk_ctrls", q=True, value=True)

    # Ensure final joint in chain is alligned w/ rest of chain.
    cmds.setAttr("%s.jointOrientX" % spine_end_joint, 0)        
    cmds.setAttr("%s.jointOrientY" % spine_end_joint, 0)
    cmds.setAttr("%s.jointOrientZ" % spine_end_joint, 0)
    
    # Main creation function called
    ik_curve = spineIKFunc(spine_root_joint, spine_end_joint, spine_root_ctrl, spine_end_ctrl, prefix)
    
    # If FK controls desired and number specified is above 0, call FK creation function.
    if (fk_enabled == True) and (fk_ctrls_num > 0):
        fkCtrlFunc(spine_root_joint, spine_end_joint, spine_end_ctrl, fk_ctrls_num, fk_limit, prefix)
    
    # Call stretch function if setting enabled.
    if stretch_enabled == True:
        createStretch(spine_root_joint, spine_end_joint, ik_curve, prefix)
    
    
def spineIKFunc(spine_root, spine_end, spine_root_ctrl, spine_end_ctrl, prefix, *pArgs):
    
    ''' Creates basic IK Spine on a user-specified joint-chain and controls.
    
        spine_root         : string, name of joint to use as root of spine
        spine_end          : string, name of joint to use as end of spine
        spine_root_ctrl    : string, name of control to manipulate spine_root
        spine_end_ctrl     : string, name of control to manipulate spine_end
        prefix             : string, user-defined prefix for created nodes. Defaults to 'ik_spine_'
        
        On Exit:
            Basic IK Spline setup between spine_root and spine_end, controlled by spine_root_ctrl and spine_end_ctrl.'''
    
    # Create duplicate joints of spine_root and spine_end, parented to controls, for later use in skinning spline curve. createDupeJoints detailed below.
    ik_hip = createDupeJoints(spine_root)
    ik_hip = cmds.rename(ik_hip, "%ship_joint" % prefix)
    cmds.parent(ik_hip, spine_root_ctrl)
    
    ik_shoulders = createDupeJoints(spine_end)
    ik_shoulders = cmds.rename(ik_shoulders, "%sshoulder_joint" % prefix)
    cmds.parent(ik_shoulders, spine_end_ctrl)
    
    # Build IK handle, generate and rename spline curve.
    spineikHandle = cmds.ikHandle(n = "%sikHandle" % prefix, sj = spine_root, ee = spine_end, sol="ikSplineSolver", rootOnCurve=True, parentCurve=True,  createCurve=True, simplifyCurve=True, numSpans=3, twistType="linear")
    newCurve = cmds.listConnections(spineikHandle, source=True, type="nurbsCurve")
    newCurve = cmds.rename(newCurve, "%scurve" % prefix)

    # Skin curve to duplicate joints
    cmds.skinCluster(ik_hip, ik_shoulders, newCurve)
    
    # Return curve to mainFunc for use in subsequent functions.
    return newCurve
    
    
def fkCtrlFunc(spine_root_joint, spine_end_joint, spine_end_ctrl, fk_ctrls_num, fk_limit, prefix, *pArgs):
    
    ''' Creates FK controls for a hybrid setup if settings enabled.
    
        spine_root_joint   : string, name of joint to use as root of spine
        spine_end_joint    : string, name of joint to use as end of spine
        spine_end_ctrl     : string, name of control to manipulate spine_end
        fk_ctrls_num       : int, number of desired fk controls. Default 2.
        fk_limit           : bool, option to restrict fk controls to only the "lower" 50% of spine - avoids having FK controls in the chest area.
        prefix             : string, user-defined prefix for created nodes. Defaults to 'ik_spine_'
        
        On Exit:
            Basic IK Spine has FK controls based on the number and positioning desired by the user.'''

    segment_num = (fk_ctrls_num + 1)
    fk_prefix = prefix + "fk_"
    
    # Build FK controls restricted to lower half of the joint chain
    if fk_limit == True:
        # splitJoints script creates a chain of joints between two specified joints. Used to "split" chains into more/less joints.
        # Used here to find the halfway point between the spine_root_joint and spine_end_joint by creating a 3 joint chain.
        temp_joints = splitJoints(spine_root_joint, spine_end_joint, 2, "construct_joint_01", 2, 0.5)
        
        # FK joint chain created between root and half-point of chain, with mid-chain joints equal to number of desired controls.
        fk_joints = splitJoints(temp_joints[0], temp_joints[1], fk_ctrls_num, fk_prefix, 2, 0.5)
        
        # Find end joint of FK chain, and extend to original spine_end_joint position, and parent to preceding FK chain joint.
        fk_end_joint = cmds.joint(n="%send" % fk_prefix)
        cmds.matchTransform(fk_end_joint, spine_end_joint)
        cmds.FreezeTransformations(fk_end_joint)
        cmds.parent(fk_end_joint, fk_joints[-1])
        
        # Cleanup
        cmds.delete(temp_joints)
    
    # Build FK controls distributed equally across the joint chain  
    else:
        # Creates a chain of joints between two specified joints. Lecturer script.
        fk_joints = splitJoints(spine_root_joint, spine_end_joint, segment_num, fk_prefix, 2, 0.5)
    
    # Set orientation of FK joints.
    cmds.joint("%s" % fk_joints[0], edit=True, oj="xyz", sao= "yup" , zso=True, ch=True)
    
    # Create and orient FK controls. Setup of offsetGroups.
    for i in range(fk_ctrls_num):
        circleCtrl = cmds.circle()
        cmds.matchTransform(circleCtrl, fk_joints[i+1])
        
        cmds.select("%s.cv[0:7]" % circleCtrl[0])        # Orient assuming X axis is the primary.
        cmds.rotate(0,90,0)
        cmds.FreezeTransformations(circleCtrl)
        
        newGrp = cmds.group(n="%s_offsetGrp" % circleCtrl[0], w=True, em=True)
        cmds.matchTransform(newGrp, circleCtrl[0])
        cmds.parent(circleCtrl[0], newGrp)
        
        cmds.parent(newGrp, fk_joints[i])
        cmds.parent(fk_joints[i+1], circleCtrl[0])
        
    # Create offset group for spine_end_ctrl, constrain to penultimate FK joint. (Last one with a control).    
    newGrp = cmds.group(n="%s_offsetGrp" % spine_end_ctrl, w=True, em=True)
    cmds.matchTransform(newGrp, spine_end_ctrl)
    cmds.parent(spine_end_ctrl, newGrp)
    cmds.parentConstraint(fk_joints[-1], newGrp, maintainOffset=True)
            
   

def createStretch(spine_root_joint, spine_end_joint, ik_curve, prefix, *pArgs):

    ''' Build the systems to allow spine to stretch beyond default length.
    
        spine_root_joint   : string, name of joint to use as root of spine
        spine_end_joint    : string, name of joint to use as end of spine
        ik_curve           : string, name of ik curve of the spine
        prefix             : string, user-defined prefix for created nodes. Defaults to 'ik_spine_'
        
        On Exit: Node-based stretch/scaling applied to spine's ik joints, if setting enabled.
        '''
    
    # Get list of all IK joints in the spine from start to end. Function further down.        
    joint_list = getJointList(spine_root_joint, spine_end_joint)
    stretch_list = joint_list
    # Remove root joint from list, as it doesn't need stretch applied to it.
    stretch_list.pop(0)
    
    # Create info node and get resting length of curve (curve_length).
    curve_info_node = cmds.arclen(ik_curve, ch=True)
    curve_length = cmds.getAttr("%s.arcLength" % curve_info_node)
    
    # Clear previous stretch nodes using the same prefix.
    if cmds.objExists("%sstretch_multiDiv" % prefix) == True:
        multiDivList = cmds.listConnections("%sstretch_multiDiv" % prefix, type="multiplyDivide")
        if multiDivList != None:
            for i in range(len(multiDivList)):
                cmds.delete("%s" % multiDivList[i])
        cmds.delete("%sstretch_multiDiv" % prefix, hierarchy="below")

    # Create node to calculate stretch multipliation factor; (current curve length / resting curve length)
    cmds.createNode("multiplyDivide", n="%sstretch_multiDiv" % prefix)
    cmds.setAttr("%sstretch_multiDiv.operation" % prefix, 2)
    cmds.setAttr("%sstretch_multiDiv.input2X" % prefix, curve_length)
    cmds.connectAttr("%s.arcLength" % curve_info_node, "%sstretch_multiDiv.input1X" % prefix)
    
    # Connect each joint's x translation value to the scale factor.
    for i in range(len(stretch_list)):
        cmds.createNode("multiplyDivide", n="%s_stretch_multiDiv" % stretch_list[i])        # Create multidiv for each joint
        xTranslate = cmds.getAttr("%s.translateX" % stretch_list[i])                        # Get resting length of joint
        cmds.setAttr("%s_stretch_multiDiv.input1X" % stretch_list[i], xTranslate)           # Set 1x of joint multidiv to default
        cmds.connectAttr("%sstretch_multiDiv.outputX" % prefix, "%s_stretch_multiDiv.input2X" % stretch_list[i]) # Connect scale to multiDiv node.
        cmds.connectAttr("%s_stretch_multiDiv.outputX" % stretch_list[i], "%s.translateX" % stretch_list[i])
        

def getJointList(start_joint, end_joint, *pArgs):

    ''' Get list of all joints in chain from end to start joint.
    
        start_joint      : string, name of joint to use as root of spine
        end_joint        : string, name of joint to use as end of spine
        
        On Exit: A list of all joints in a chain leading to end_joint from start_joint.
                Needed in order to isolate chain of spine joints from clavicle or breast 
                joints that may be children of spine joints.
                NOTE: List is "backwards". end_joint is the first entry, start_joint is the last.
        '''

    # The root joint is selected as a target. 
    cmds.select(start_joint)
    target_joint = cmds.ls(sl=True)
    # Temp joint created beneath end joint so that the true end joint is included in the list.                
    temp_joint = cmds.joint("%s" % end_joint)
    
    # Current joint initialized to temporary end joint.
    current_joint = cmds.ls(sl=True)
    cmds.select(clear=True)
    
    jList = []
    
    # Cycle through each joint's parent, adding the parent to the list until current and target joint match.
    while current_joint != target_joint:
        current_joint = cmds.listRelatives(current_joint, parent=True, type="joint")
        jList.insert(0, current_joint)
        
    # Cleanup
    cmds.delete(temp_joint)
    
    # Get object only version of the list and return it.
    for i in range(len(jList)):
        cmds.select(jList[i], add=True)  
    jList = cmds.ls(sl=True, o=True) 
    return jList
    
    
    
def createDupeJoints(origin_joint, *pArgs):
    ''' Duplicate specified joint, removing any children it may have.
    
        origin_joint : string, the name of the joint to duplicate and isolate'''
        
    # Duplicate Root Spine Joint and isolate by deleting all children
    newRoot = cmds.duplicate(origin_joint)                
    children = cmds.listRelatives(newRoot[0])
    # If statement to handle cases with no children.
    if children != None:                                    
        for i in range(len(children)):
            cmds.delete("%s|%s" % (newRoot[0], children[i]))
        
    return newRoot[0]
    
    
def closeWindow(myWin, *pArgs ):
    ''' Close gui window
    
        myWin : string, the name of this instance of the spine GUI window'''
        
    if cmds.window(myWin, exists=True):
        cmds.deleteUI(myWin)    
        
        
def updateTexField(currentTextField, *pArgs):
    ''' Fills GUI text field with name of currently selected object
    
        currentTextField : string, the name of the text field to be filled'''
      
    # If nothing currently selected, do nothing. Otherwise, edit text field with currently selected object's name.  
    list = cmds.ls(selection = True)
    if len(list) == 0:
        print "Error: No object selected"
    else:    
        cmds.textField("%s" % currentTextField, edit=True, tx="%s" % list[0])


spineGUI()