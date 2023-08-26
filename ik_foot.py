import maya.cmds as cmds
import functools
from create_group import makeGrpFunc

# create_group is NOT a lecturer script, and is also available in this repository. This script should work with both downloaded. :)

def footGUI():
    '''GUI window for IK foot setup.'''
    
    myWin = cmds.window(title="IK Foot Setup", width = 355, height = 70)
    cmds.rowColumnLayout(nc=3, cw=[(1, 125), (2, 300), (3, 70)],  columnAttach=[(1, "left", 5), (2, "both", 5)], cs=(5, 5))
    
    cmds.text(label = "Ankle Joint:")
    cmds.textField("ankleJoint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "ankleJoint"))
    
    cmds.text(label = "Ball Joint:")
    cmds.textField("ballJoint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "ballJoint"))
    
    cmds.text(label = "Toe Joint:")
    cmds.textField("toeJoint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "toeJoint"))
    
    cmds.separator(visible=False)
    cmds.separator(visible=False)
    cmds.separator(visible=False)
    
    cmds.text(label = "Heel Locator:")
    cmds.textField("heelLoc")
    cmds.button(label="Select", command=functools.partial(updateTexField, "heelLoc"))
    
    cmds.text(label = "Ball Locator:")
    cmds.textField("ballLoc")
    cmds.button(label="Select", command=functools.partial(updateTexField, "ballLoc"))
    
    cmds.text(label = "Toe Locator:")
    cmds.textField("toeLoc")
    cmds.button(label="Select", command=functools.partial(updateTexField, "toeLoc"))
    
    cmds.text(label = "Inside Locator:")
    cmds.textField("insideLoc")
    cmds.button(label="Select", command=functools.partial(updateTexField, "insideLoc"))
    
    cmds.text(label = "Outside Locator:")
    cmds.textField("outsideLoc")
    cmds.button(label="Select", command=functools.partial(updateTexField, "outsideLoc"))
    
    cmds.separator(visible=False)
    cmds.separator(visible=False)
    cmds.separator(visible=False)
    
    cmds.text(label = "IK Foot Control:")
    cmds.textField("footCtrl")
    cmds.button(label="Select", command=functools.partial(updateTexField, "footCtrl"))

    
    cmds.text(label = "Left/Right Prefix:")
    cmds.textField("leftrightPrefix")
    cmds.optionMenu("leftrightPresets", changeCommand = copyDropDown)
    cmds.menuItem(label = "")
    cmds.menuItem(label = "r_")
    cmds.menuItem(label = "l_")
    
    cmds.separator(visible=False, h=20)
    cmds.separator(visible=False, h=20)
    cmds.separator(visible=False, h=20)
    
    cmds.separator(visible=False)
    cmds.checkBox("ikHandleCheckbox", l="Place Leg ikHandle in foot hierarchy", onc = "cmds.textField(\"legIKLoc\",edit=True, en=True)", ofc="cmds.textField(\"legIKLoc\", edit=True, en=False)")
    cmds.separator(visible=False)
    
    cmds.text(label = "Leg IKHandle Locator:")
    cmds.textField("legIKLoc", en=False)
    cmds.button(label="Select", command=functools.partial(updateTexField, "legIKLoc"))
    
    cmds.separator(visible=False)
    cmds.checkBox("kneeCheckbox", l="Parent knee ctrl to ik foot", onc = "cmds.textField(\"kneeCtrl\",edit=True, en=True)", ofc="cmds.textField(\"kneeCtrl\", edit=True, en=False)")
    cmds.separator(visible=False)
    
    cmds.text(label = "Knee Control:")
    cmds.textField("kneeCtrl", en=False)
    cmds.button(label="Select", command=functools.partial(updateTexField, "kneeCtrl"))
    
    cmds.separator(h=20)
    cmds.separator(h=20)
    cmds.separator(h=20)
    
    cmds.button(label="Close", command=functools.partial(closeWindow,myWin))
    cmds.separator(visible = False)
    cmds.button(label="Apply", command=functools.partial(createIKFoot, "ankleJoint", "ballJoint", "toeJoint",
                                                                        "heelLoc", "ballLoc", "toeLoc",
                                                                        "insideLoc", "outsideLoc",
                                                                        "footCtrl", "legIKLoc", "kneeCtrl", "leftrightPrefix", "ikHandleCheckbox", "kneeCheckbox"))
    
    cmds.showWindow(myWin)
   
    
def createIKFoot(ankleJoint, ballJoint, toeJoint, heelLoc, ballLoc, toeLoc, insideLoc, outsideLoc, footCtrl, legIKLoc, kneeCtrl, leftrightPrefix, ikHandleCheckbox, kneeCheckbox, *pArgs):
    
    ''' Main function and processing block, call to all other functions within this block
    
        ankleJoint         : string, name of ankle joint in IK footroll setup.
        ballJoint          : string, name of ball joint in IK footroll setup.
        toeJoint           : string, name of toe (end) joint in IK footroll setup.
        heelLoc            : string, name of heel locator in IK footroll setup.
        ballLoc            : string, name of ball locator in IK footroll setup.
        toeLoc             : string, name of toe locator in IK footroll setup.
        insideLoc          : string, name of inside locator in IK footroll setup.
        outsideLoc         : string, name of outside locator in IK footroll setup.
        footCtrl           : string, name of control intended to control the IK foot.
        legIKLoc           : string, name of locator controlling the end of the (PRE-EXISTING) leg IK chain.
        kneeCtrl           : string, name of object intended to be pole-vector knee/elbow control.
        leftrightPrefix    : string, custom or pre-set prefixes to label created nodes with. (e.g. l_leg_)
        ikHandleCheckbox   : bool, option to integrate legIKLoc into IK foot hierarchy. (Foot will affect leg, otherwise manual integration needed)
        kneeCheckbox       : bool, option to parent pole-vector control to foot control.
        
        
        On Exit:
            Node-based IK Footroll is setup on specified controls. Options allow integration into existing IK leg systems, but these are not required.
            Must use a 3-joint and 5-locator footroll setup, with an ankle-ball-toe joint setup, and locators for the heel, ball, toe, outside and inside of the mesh.
            '''
    # Query all entered information.
    ankleJString = cmds.textField("ankleJoint", q=True, text=True)
    ballJString = cmds.textField("ballJoint", q=True, text=True)
    toeJString = cmds.textField("toeJoint", q=True, text=True)
    heelAttrLoc = cmds.textField("heelLoc", q=True, text=True)
    ballAttrLoc = cmds.textField("ballLoc", q=True, text=True)
    toeAttrLoc = cmds.textField("toeLoc", q=True, text=True)
    insideAttrLoc = cmds.textField("insideLoc", q=True, text=True)
    outsideAttrLoc = cmds.textField("outsideLoc", q=True, text=True)
    footCtrl = cmds.textField("footCtrl", q=True, text=True)
    kneeCtrl = cmds.textField("kneeCtrl", q=True, text=True)
    legIK = cmds.textField("legIKLoc", q=True, text=True)
    leftright = cmds.textField("leftrightPrefix", q=True, text=True)
    
    ikCheckState = cmds.checkBox("ikHandleCheckbox", q=True, value=True)
    kneeCheckState = cmds.checkBox("kneeCheckbox", q=True, value=True)
    
    # Remove children from foot control, change it's pivot to match the ankle joint, return the children afterwards.  
    # PERSONAL NOTE: Disable the children removal and returning steps when adapting the human footroll for animal paws.
    childList = cmds.listRelatives(footCtrl, type="transform")
    if cmds.listRelatives(footCtrl, p=True) != None:
        for i in range(len(childList)):
            
            cmds.parent(childList[0], world=True)
    cmds.matchTransform(footCtrl, ankleJString, piv=True, pos=False, rot=False, scl=False)
    
    if cmds.listRelatives(footCtrl, p=True) != None:
        for i in range(len(childList)):
            cmds.parent(childList[i], footCtrl)                            
    
    # For the various IK Foot sliders, we need specific duplicates of the 5 specified locators.
    # Create and format those specific duplicates.
    ballPivotLoc = dupeLocator(leftright, ballAttrLoc, "ball_pivot_loc")
    toeWiggleLoc = dupeLocator(leftright, ballAttrLoc, "toe_wiggle_loc")
    heelFootRollLoc = dupeLocator(leftright, heelAttrLoc, "heel_footRoll_loc")
    ballFootRollLoc = dupeLocator(leftright, ballAttrLoc, "ball_footRoll_loc")
    toeFootRollLoc = dupeLocator(leftright, toeAttrLoc, "toe_footRoll_loc")

    heelAttrLoc = cmds.rename(heelAttrLoc, "%sheel_attr_loc" % leftright)
    ballAttrLoc = cmds.rename(ballAttrLoc, "%sball_attr_loc" % leftright)
    toeAttrLoc = cmds.rename(toeAttrLoc, "%stoe_attr_loc" % leftright)
    insideAttrLoc = cmds.rename(insideAttrLoc, "%sinside_attr_loc" % leftright)
    outsideAttrLoc = cmds.rename(outsideAttrLoc, "%soutside_attr_loc" % leftright)
    
    # List of all the above.
    locList = [heelAttrLoc, ballAttrLoc, toeAttrLoc, insideAttrLoc, outsideAttrLoc, ballPivotLoc, toeWiggleLoc, heelFootRollLoc, ballFootRollLoc, toeFootRollLoc]
    
    # Assemble locators into a specific hierarchy to create the IK Foot behaviour we're aiming for.
    setupParent(ballFootRollLoc, ballAttrLoc)    
    setupParent(ballAttrLoc, insideAttrLoc)
    setupParent(toeWiggleLoc, insideAttrLoc)
   
    setupParent(insideAttrLoc, outsideAttrLoc)
    setupParent(outsideAttrLoc, ballPivotLoc)
    setupParent(ballPivotLoc, toeFootRollLoc)
    setupParent(toeFootRollLoc, toeAttrLoc)
    setupParent(toeAttrLoc, heelFootRollLoc)
    setupParent(heelFootRollLoc, heelAttrLoc)
    setupParent(heelAttrLoc, footCtrl)
    
    # For each locator, create an offsetGrp.
    for i in range(len(locList)):
        cmds.select(locList[i])
        makeGrpFunc()
    
    # PERSONAL NOTE: freezeLocs caused issues when reusing this script to adapt human footroll setup for animal paws. Disable if needed.
    # Calling processing functions.   
    freezeLocs(heelAttrLoc, ballAttrLoc, toeAttrLoc, insideAttrLoc, outsideAttrLoc, toeWiggleLoc, heelFootRollLoc, ballFootRollLoc, toeFootRollLoc)   
    setupAttrs(footCtrl, heelAttrLoc, ballAttrLoc, toeAttrLoc, insideAttrLoc, outsideAttrLoc, toeWiggleLoc, ballPivotLoc)
    
    footRollNodes(footCtrl, leftright, heelFootRollLoc, ballFootRollLoc, toeFootRollLoc)
    sideSideNodes(footCtrl, leftright, outsideAttrLoc, insideAttrLoc)
    
    # If option to have the pole-vector knee control follow the IK Foot control is enabled, create the constraint.
    if kneeCheckState == 1:
        cmds.parentConstraint(footCtrl, kneeCtrl, maintainOffset = True)
    

    # IK Handles are added last to the setup due to issues occurring if added earlier.
    setupIKHandles(ankleJString, ballJString, toeJString, leftright)         # If ikHandles are parented before attr/roll/sideside setup, they tend to be offset.
                                                                             # So will handle ikHandles last of all things.
    setupParent("%s" % leftright + "ballToe_ikHandle", toeWiggleLoc)         # Direct naming needs to be used or ikHandles will not parent.
    setupParent("%s" % leftright + "ankleBall_ikHandle", insideAttrLoc)      # Can't abstract to "ballToe" for this, for example.
    
    # If option to have existing IK leg affected by the IK Foot enabled, create the connection.
    if ikCheckState == 1:
        setupParent(legIK, ballFootRollLoc)
        
    cmds.select(footCtrl) 
    
     
def setupAttrs(footCtrl, heelAttrLoc, ballAttrLoc, toeAttrLoc, insideAttrLoc, outsideAttrLoc, toeWiggleLoc, ballPivotLoc, *pArgs):
    
    ''' The IK Foot has various sliders ('attrs') for manipulating the foot. Wiggle, side-to-side, etc. This function sets those up on the foot control and connects
        them to the relevant locators.
    
        footCtrl           : string, name of control intended to control the IK foot.
        heelAttrLoc        : string, name of locator used for heel-positioned sliders.
        ballAttrLoc        : string, name of locator used for ball-positioned sliders.
        toeAttrLoc         : string, name of locator used for toe-positioned sliders.
        insideAttrLoc      : string, name of locator used for side-to-side sliders.
        outsideAttrLoc     : string, name of locator used for side-to-side sliders.
        toeWiggleLoc       : string, name of separate locator used for toe wiggling sliders. 
        ballPivotLoc       : string, name of locator marking the position of the ball's pivot point.
        
        
        On Exit:
            Foot control has attributes/sliders for all supported foot transformations, which have been connected to the relevant locators and the required transformation channels.
            '''
    # If any custom attributes have been added to the footControl - remove them. Prevents duplicates.
    cmds.select(footCtrl)
    userAttrs = cmds.listAttr(ud=True)
    if userAttrs != None:
        for i in range(len(userAttrs)):
            cmds.deleteAttr("%s" % footCtrl + ".%s" % userAttrs[i])

    # Create attributes on the footcontrol.. Multiplier amplifies the strength of all other sliders.
    cmds.addAttr(footCtrl, longName = "Multiplier", attributeType = "float", keyable=True, defaultValue = 3, niceName = " Multiplier") 
     
    cmds.addAttr(footCtrl, longName = "ROLL", attributeType = "enum", enumName = "---", keyable=True) 
    cmds.addAttr(footCtrl, longName = "Roll", attributeType = "float", keyable=True)
    cmds.addAttr(footCtrl, longName = "BreakLimit", attributeType = "float", keyable=True, defaultValue = 30)
    cmds.addAttr(footCtrl, longName = "StraightenLimit", attributeType = "float", keyable=True, defaultValue = 50)
    
    cmds.addAttr(footCtrl, longName = "FOOT", attributeType = "enum", enumName = "---", keyable=True) 
    cmds.addAttr(footCtrl, longName = "H_FootSwivel", attributeType = "float", keyable=True, niceName = "Heel Foot Swivel")
    cmds.addAttr(footCtrl, longName = "B_FootSwivel", attributeType = "float", keyable=True, niceName = "Ball Foot Swivel")
    cmds.addAttr(footCtrl, longName = "T_FootSwivel", attributeType = "float", keyable=True, niceName = "Toe Foot Swivel")
    cmds.addAttr(footCtrl, longName = "H_FootLift", attributeType = "float", keyable=True, niceName = "Heel Foot Lift")
    cmds.addAttr(footCtrl, longName = "T_FootLift", attributeType = "float", keyable=True, niceName = "Toe Foot Lift")
    cmds.addAttr(footCtrl, longName = "SideSide", attributeType = "float", keyable=True, niceName = "Side to Side")
        
    cmds.addAttr(footCtrl, longName = "HEEL", attributeType = "enum", enumName = "---", keyable=True) 
    cmds.addAttr(footCtrl, longName = "H_Lift", attributeType = "float", keyable=True, niceName = "Lift")
    cmds.addAttr(footCtrl, longName = "H_Swivel", attributeType = "float", keyable=True, niceName = "Swivel")
    cmds.addAttr(footCtrl, longName = "H_Lean", attributeType = "float", keyable=True, niceName = "Lean")
    
    cmds.addAttr(footCtrl, longName = "TOE", attributeType = "enum", enumName = "---", keyable=True) 
    cmds.addAttr(footCtrl, longName = "T_Lift", attributeType = "float", keyable=True, niceName = "Lift")
    cmds.addAttr(footCtrl, longName = "T_Swivel", attributeType = "float", keyable=True, niceName = "Swivel")
    cmds.addAttr(footCtrl, longName = "T_Lean", attributeType = "float", keyable=True, niceName = "Lean")

    # Create 4 lists, where item [n] in each list are to be connected to item [n] in other lists.   
    sourceAttrs = ["H_FootSwivel", "B_FootSwivel", "T_FootSwivel", "H_FootLift", "T_FootLift",
                    "H_Lift", "H_Swivel", "H_Lean",
                    "T_Lift", "T_Swivel", "T_Lean"]
    
    multiDivs = []
    
    destinations = [heelAttrLoc, ballPivotLoc, toeAttrLoc, heelAttrLoc, toeAttrLoc,
                    ballAttrLoc, ballAttrLoc, ballAttrLoc,
                    toeWiggleLoc, toeWiggleLoc, toeWiggleLoc]
    
    destAttrs = ["rotateY", "rotateY", "rotateY", "rotateX", "rotateX",
                "rotateX", "rotateY", "rotateZ",
                "rotateX", "rotateY", "rotateZ"]
    
    # For all the sliders we've created, cleanup any pre-existing scale nodes. (For the multiplier option.
    for i in range(len(sourceAttrs)):                                                       
        if cmds.objExists("%s" % footCtrl + "_" + sourceAttrs[i] + "_Scale"):
            cmds.delete("%s" % footCtrl + "_" + sourceAttrs[i] + "_Scale")
        
        # Create mutiply/divide nodes to handle the calculation of the multiplier's effect on other attributes/sliders. Append these to the empty multiDiv list.   
        multiDivs.append(cmds.createNode("multiplyDivide", n = "%s" % footCtrl + "_%s" % sourceAttrs[i] + "_Scale"))
            
        # Connect the footCtrl attributes to their individual multiply/divide nodes, connect the multiplier value, and connect the output to the required channel on the 
        # relevant locator.
        # For example H_FootSwivel and the Multiplier's values are connected to a H_FootSwivel_Scale multiplyDivide node. The output is connected to heelAttrLoc's rotateY channel.
        cmds.connectAttr("%s" % footCtrl + ".%s" % sourceAttrs[i], multiDivs[i] + ".input1.input1X")
        cmds.connectAttr("%s" % footCtrl + ".Multiplier"         , multiDivs[i] + ".input2.input2X")
        cmds.connectAttr(multiDivs[i] + ".output.outputX"              , destinations[i] + ".%s" % destAttrs[i])
   
    
def footRollNodes(footCtrl, leftright, heelLoc, ballLoc, toeLoc, *pArgs):

    ''' The expression to control the actual footRoll needs to be created. For performance and evaluation speed - this is created through a node network.
    
        footCtrl            : string, name of control intended to control the IK foot.
        leftright           : string, custom or pre-set prefixes to label created nodes with. (e.g. l_leg_)
        heelLoc             : string, name of heel locator in IK footroll setup.
        ballLoc             : string, name of ball locator in IK footroll setup.
        toeLoc              : string, name of toe locator in IK footroll setup.

        On Exit:
            Node equivelant of expression to control footRoll is established with tweakable performance parameters. Foot can be rolled without clipping through the ground plane
            - but an IK leg will not be affected unless the leg ikHandle option was checked.
            '''
         
    # If expression was created, clean it up.   
    if cmds.objExists("%s" % leftright + "footik_roll_expr"):
        cmds.delete("%s" % leftright + "footik_roll_expr")
        
    # Holder values for variables we'll need a lot
    cmds.createNode("floatConstant", n="%sroll_const" % leftright)
    cmds.createNode("floatConstant", n="%sbreak_const" % leftright)
    cmds.createNode("floatConstant", n="%sstraighten_const" % leftright)
    
    cmds.connectAttr("%s.Roll" % footCtrl, "%sroll_const.inFloat" % leftright)
    cmds.connectAttr("%s.BreakLimit" % footCtrl, "%sbreak_const.inFloat" % leftright)
    cmds.connectAttr("%s.StraightenLimit" % footCtrl, "%sstraighten_const.inFloat" % leftright)
    
    # Roll setup
    cmds.createNode("condition", n="%smin_roll" % leftright)
    cmds.setAttr("%smin_roll.operation" % leftright, 5)
    cmds.connectAttr("%sroll_const.outFloat" % leftright, "%smin_roll.secondTerm" % leftright)
    cmds.connectAttr("%sroll_const.outFloat" % leftright, "%smin_roll.colorIfFalse.colorIfFalseR" % leftright)
    
    cmds.createNode("floatConstant", n="%sroll_value" % leftright)
    cmds.connectAttr("%smin_roll.outColor.outColorR" % leftright, "%sroll_value.inFloat" % leftright)
    
    # Break setup
    
    #Linstep 1
    cmds.createNode("setRange", n="%sball_linstep_1" % leftright)
    cmds.setAttr("%sball_linstep_1.maxX" % leftright, 1) 
    cmds.connectAttr("%sbreak_const.outFloat" % leftright, "%sball_linstep_1.oldMaxX" % leftright)
    cmds.connectAttr("%sroll_const.outFloat" % leftright, "%sball_linstep_1.valueX" % leftright)
    
    #Linstep 2
    cmds.createNode("setRange", n="%sball_linstep_2" % leftright)
    cmds.setAttr("%sball_linstep_2.maxX" % leftright, 1) 
    cmds.connectAttr("%sbreak_const.outFloat" % leftright, "%sball_linstep_2.oldMinX" % leftright)
    cmds.connectAttr("%sstraighten_const.outFloat" % leftright, "%sball_linstep_2.oldMaxX" % leftright)
    cmds.connectAttr("%sroll_const.outFloat" % leftright, "%sball_linstep_2.valueX" % leftright)
    
    #One minus Linstep 2
    cmds.createNode("floatMath", n="%sone_minus_ball_linstep_2" % leftright)
    cmds.setAttr("%sone_minus_ball_linstep_2.operation" % leftright, 1)
    cmds.setAttr("%sone_minus_ball_linstep_2.floatA" % leftright, 1)
    cmds.connectAttr("%sball_linstep_2.outValueX" % leftright, "%sone_minus_ball_linstep_2.floatB" % leftright)
    
    #Multiply linstep 1 2
    cmds.createNode("multiplyDivide", n="%smultiply_linstep_1_2" % leftright)
    cmds.connectAttr("%sball_linstep_1.outValueX" % leftright, "%smultiply_linstep_1_2.input1X" % leftright)
    cmds.connectAttr("%sone_minus_ball_linstep_2.outFloat" % leftright, "%smultiply_linstep_1_2.input2X" % leftright)
    
    
    #Multiply ball by roll
    cmds.createNode("multiplyDivide", n="%smultiply_ball_by_roll" % leftright)
    cmds.connectAttr("%smultiply_linstep_1_2.outputX" % leftright, "%smultiply_ball_by_roll.input1X" % leftright)
    cmds.connectAttr("%sroll_const.outFloat" % leftright, "%smultiply_ball_by_roll.input2X" % leftright)
    
    cmds.createNode("floatConstant", n="%sball_value" % leftright)
    cmds.connectAttr("%smultiply_ball_by_roll.outputX" % leftright, "%sball_value.inFloat" % leftright)
    
    #Straighten Setup
    #Linstep1
    cmds.createNode("setRange", n="%stoe_linstep_1" % leftright)
    cmds.setAttr("%stoe_linstep_1.maxX" % leftright, 1)
    cmds.connectAttr("%sbreak_const.outFloat" % leftright, "%stoe_linstep_1.oldMinX" % leftright)
    cmds.connectAttr("%sstraighten_const.outFloat" % leftright, "%stoe_linstep_1.oldMaxX" % leftright)
    cmds.connectAttr("%sroll_const.outFloat" % leftright, "%stoe_linstep_1.valueX" % leftright)
    
    #Multiply toe by roll
    cmds.createNode("multiplyDivide", n="%smultiply_toe_by_roll" % leftright)
    cmds.connectAttr("%stoe_linstep_1.outValueX" % leftright, "%smultiply_toe_by_roll.input1X" % leftright)
    cmds.connectAttr("%sroll_const.outFloat" % leftright, "%smultiply_toe_by_roll.input2X" % leftright)
    
    cmds.createNode("floatConstant", n="%stoe_value" % leftright)
    cmds.connectAttr("%smultiply_toe_by_roll.outputX" % leftright, "%stoe_value.inFloat" % leftright)
    
    cmds.connectAttr("%sroll_value.outFloat" % leftright, "%s.rotateX" % heelLoc)
    cmds.connectAttr("%sball_value.outFloat" % leftright, "%s.rotateX" % ballLoc)
    cmds.connectAttr("%stoe_value.outFloat" % leftright, "%s.rotateX" % toeLoc)


    
def sideSideNodes(footCtrl, leftright, outsideLoc, insideLoc, *pArgs):
    
    ''' The expression to control the rocking side-to-side roll needs to be created. For performance and evaluation speed - this is created through a node network.
    
        footCtrl            : string, name of control intended to control the IK foot.
        leftright           : string, custom or pre-set prefixes to label created nodes with. (e.g. l_leg_)
        outsideLoc          : string, name of outside locator in IK footroll setup.
        insideLoc           : string, name of inside locator in IK footroll setup.

        On Exit:
            Node equivelant of expression to control side-to-side roll is established. Foot can be rolled side to side without clipping through the ground plane
            - but an IK leg will not be affected unless the leg ikHandle option was checked.
            '''
    
    # Cleanup old expression if it's accidentally created.
    if cmds.objExists("%s" % leftright + "footik_sideside_expr"):
        cmds.delete("%s" % leftright + "footik_sideside_expr")
        
    # Get value from IK foot Ctrl
    cmds.createNode("floatConstant", n="%sside_const" % leftright)
    cmds.connectAttr("%s.SideSide" % footCtrl, "%sside_const.inFloat" % leftright)
    
    # Min condition
    cmds.createNode("condition", n="%smin_side" % leftright)
    cmds.setAttr("%smin_side.operation" % leftright, 5)
    cmds.setAttr("%smin_side.colorIfFalse.colorIfFalseR" % leftright, 0)
    cmds.connectAttr("%sside_const.outFloat" % leftright, "%smin_side.firstTerm" % leftright)
    cmds.connectAttr("%sside_const.outFloat" % leftright, "%smin_side.colorIfTrue.colorIfTrueR" % leftright)
    
    # Max condition
    cmds.createNode("condition", n="%smax_side" % leftright)
    cmds.setAttr("%smax_side.operation" % leftright, 3)
    cmds.setAttr("%smax_side.colorIfFalse.colorIfFalseR" % leftright, 0)
    cmds.connectAttr("%sside_const.outFloat" % leftright, "%smax_side.firstTerm" % leftright)
    cmds.connectAttr("%sside_const.outFloat" % leftright, "%smax_side.colorIfTrue.colorIfTrueR" % leftright)
    
    # Values    
    cmds.createNode("floatConstant", n="%sside_min_value" % leftright)
    cmds.connectAttr("%smin_side.outColor.outColorR" % leftright, "%sside_min_value.inFloat" % leftright)
    
    cmds.createNode("floatConstant", n="%sside_max_value" % leftright)
    cmds.connectAttr("%smax_side.outColor.outColorR" % leftright, "%sside_max_value.inFloat" % leftright)
    
    #Connect in the scaling node
    
    cmds.createNode("multiplyDivide", n="%s_sideside_min_scale_factor" % leftright)
    cmds.connectAttr("%sside_min_value.outFloat" % leftright, "%s_sideside_min_scale_factor.input1X" % leftright)
    cmds.connectAttr("%s.Multiplier" % footCtrl, "%s_sideside_min_scale_factor.input2X" % leftright)
    
    cmds.createNode("multiplyDivide", n="%s_sideside_max_scale_factor" % leftright)
    cmds.connectAttr("%sside_max_value.outFloat" % leftright, "%s_sideside_max_scale_factor.input1X" % leftright)
    cmds.connectAttr("%s.Multiplier" % footCtrl, "%s_sideside_max_scale_factor.input2X" % leftright)
    
    
    # Connect to destination.
    cmds.connectAttr("%s_sideside_min_scale_factor.outputX" % leftright, "%s.rotateZ" % outsideLoc)
    cmds.connectAttr("%s_sideside_max_scale_factor.outputX" % leftright, "%s.rotateZ" % insideLoc)
    
    
                                        
def freezeLocs(heelAttrLoc, ballAttrLoc, toeAttrLoc, insideAttrLoc, outsideAttrLoc, toeWiggleLoc, heelFootRollLoc, ballFootRollLoc, toeFootRollLoc, *pArgs):
    '''Function to freeze the transformations of all the required locs. Isolated to separate function to compartmentalize script for easier reading.
        Admittedly I cannot remember why there are numerous locators included that are not frozen, but I don't dare question why I did it months ago.
        
        heelAttrLoc        : string, name of locator used for heel-positioned sliders.
        ballAttrLoc        : string, name of locator used for ball-positioned sliders.
        toeAttrLoc         : string, name of locator used for toe-positioned sliders.
        insideAttrLoc      : string, name of locator used for side-to-side sliders.
        outsideAttrLoc     : string, name of locator used for side-to-side sliders.
        toeWiggleLoc       : string, name of separate locator used for toe wiggling sliders.
        heelFootRollLoc    : string, name of locator used for enacting heel footRoll transformations.
        ballFootRollLoc    : string, name of locator used for enacting ball footRoll transformations.
        toeFootRollLoc     : string, name of locator used for enacting toe footRoll transformations.
        '''
    
    # Attempt to freeze locator's transformations if they are not connected.
    locList = [heelAttrLoc, ballAttrLoc, toeAttrLoc, insideAttrLoc, outsideAttrLoc, toeWiggleLoc]
    for i in range(len(locList)):
        try:
            cmds.makeIdentity(locList[i], apply=True)
        except RuntimeError:
            print "Freeze transform for %s skipped because it has incoming connections." % locList[i]
            
     
def dupeLocator(leftright, target, name, *pArgs):
    ''' Custom duplication function for creating and naming duplicates of the locators used in the IK Foot from the 5 initially provided.
    
        leftright        : string, custom or pre-set prefixes to label created nodes with. (e.g. l_leg_)
        target           : string, name of 1 of the 5 original locators to match new locator's transforms to.
        name             : string, name to be used for the newly created locator.
        '''

    # If locator with the name the locator is trying to use exists, delete it.   
    if cmds.objExists("%s" % leftright + "%s" % name):
        cmds.delete("%s" % leftright + "%s" % name)
    
    # Create locator with new name and prefix. Match it's transformations to that of the target, and return it.
    cmds.spaceLocator(name = "%s" % leftright + "%s" % name)
    newLoc = "%s" % leftright + "%s" % name
    cmds.matchTransform(newLoc, target, piv=True, pos=True, rot=True, scl=True)
    return newLoc
                 

def setupIKHandles(ankle, ball, toe, leftright, *pArgs):
    ''' Create the IKHandles on the foot joints required for footRoll to work.
    
        ankle        : string, name of the IK ankle joint.
        ball         : string, name of the IK ball joint.
        toe          : string, name of the IK toe joint.
        leftright    : string, custom or pre-set prefixes to label created nodes with. (e.g. l_leg_)
        '''
    
    # Clear existing ikHandles created by script if they exist.
    if cmds.objExists("%s" % leftright + "ankleBall_ikHandle"):
        cmds.delete("%s" % leftright + "ankleBall_ikHandle")
        
    if cmds.objExists("%s" % leftright + "ballToe_ikHandle"):
        cmds.delete("%s" % leftright + "ballToe_ikHandle")
        
    # Create ikHandles.
    cmds.ikHandle(sj = ankle, ee = ball, n = leftright + "ankleBall_ikHandle")
    cmds.ikHandle(sj = ball, ee = toe, n = leftright + "ballToe_ikHandle")
        
                                                 
def setupParent(child, destination, *pArgs):
    ''' Small function to parent things to other objects, and handle hierarchy or parenting issues automatically.
    
        child          : string, name of the object to be parented 
        destination    : string, name of the object child should be parented to
    '''
    
    # If intended child objected is already parented to something, parent it to the world (same as unparenting)
    if cmds.listRelatives(child, p=True) != None:        
        cmds.parent(child, world = True)
        
    # Then, parent normally.
    cmds.parent(child, destination)
   
   
def updateTexField(currentTextField, *pArgs):
    ''' Fills GUI text field with name of currently selected object
    
        currentTextField : string, the name of the text field to be filled'''
    
    # If nothing currently selected, do nothing. Otherwise, edit text field with currently selected object's name.
    list = cmds.ls(selection = True)
    if len(list) == 0:
        print "Error: No object selected"
    else:    
        cmds.textField("%s" % currentTextField, edit=True, tx="%s" % list[0])
        
        
def closeWindow(myWin, *pArgs ):
    ''' Close gui window
    
        myWin : string, the name of this instance of the foot GUI window'''
    
    if cmds.window(myWin, exists=True):
        cmds.deleteUI(myWin) 
        
        
def copyDropDown(dropdown, *pArgs):
    ''' Used to fill text field with an option from a dropdown menu if it's selected.
        
        dropdown    : string, string of the option selected from the dropdown menu.'''
    # When an option from the dropdown menu is selected, fill the leftrightprefix text field. (This is the only dropdown in the GUI, it only affects this field).
    cmds.textField("leftrightPrefix", edit=True, tx="%s" % dropdown)
    
footGUI()