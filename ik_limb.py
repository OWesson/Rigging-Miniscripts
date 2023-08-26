import maya.cmds as cmds
import functools
import ik_limb_ari_code as sj          # Script written by Anargyros Sarafopoulos.

# Script below is an interface and extension to lecturer's script above. Without access to ik_limb_ari_code, this will not work.
def limbGUI():
    '''GUI window for limb setup.'''

    myWin = cmds.window(title="IK Limb Setup", width = 355, height = 70)
    cmds.rowColumnLayout(nc=3, cw=[(1, 125), (2, 300), (3, 70)],  columnAttach=[(1, "left", 5), (2, "both", 5)], cs=(5, 5))

    cmds.text(label="Start IK Joint:")
    cmds.textField("startJoint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "startJoint"))
    
    cmds.text(label="End IK Joint:")
    cmds.textField("endJoint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "endJoint"))
    
    cmds.text(label="Knee/Elbow Control:")
    cmds.textField("kneeElbowControl")
    cmds.button(label="Select", command=functools.partial(updateTexField, "kneeElbowControl"))
    
    cmds.text(label="Global Scale Holder")
    cmds.textField("gScaleObj")
    cmds.button(label="Select", command=functools.partial(updateTexField, "gScaleObj"))
    
    cmds.text(label="Global Scale Attribute:")
    cmds.optionMenu("gScaleName")
    cmds.menuItem(label = "Update after entering Global Scale Holder")
    cmds.button(label="Update", command=functools.partial(updateDropDown, "gScaleObj", "gScaleName"))
    
    cmds.text(label="IK Handle Prefix:")
    cmds.textField("ikHandleName", text = "Example_")
    cmds.optionMenu("ikHandlePresets", changeCommand = copyDropDown)
    cmds.menuItem(label = "")
    cmds.menuItem(label = "l_Arm_")
    cmds.menuItem(label = "l_Leg_")
    cmds.menuItem(label = "r_Arm_")
    cmds.menuItem(label = "r_Leg_")
    
    cmds.text(label="Limb Settings Ctrl")
    cmds.textField("limbSettingsCtrl")
    cmds.button(label="Select", command=functools.partial(updateTexField, "limbSettingsCtrl"))
    
    cmds.text(label="Result Ankle Joint:")
    cmds.textField("resultJoint")
    cmds.button(label="Select", command=functools.partial(updateTexField, "resultJoint"))
            
    cmds.button(label="Close", command=functools.partial(closeWindow,myWin))
    cmds.separator(visible = False)
    cmds.button(label="Apply", command=functools.partial(toolFunction, "startJoint", "endJoint", "kneeElbowControl", "gScaleObj", "gScaleName", "ikHandName", "limbSettingsCtrl", "resultJoint"))
    
    cmds.showWindow(myWin)
     
    
def toolFunction(*pArgs):

    ''' main function block, call to all other functions within this block
    
        On Exit:
            3-joint stretchy pole vector IK setup created
            Locators will need to be placed into rig hierarchy correctly
            "Limb Setting Ctrl" will gain overall stretch toggle.
            '''
    
    currentlySelected = cmds.ls(selection = True)
    
    # Query text from all the GUI text windows. 

    sjString = cmds.textField("startJoint", q=True, text=True)
    ejString = cmds.textField("endJoint", q=True, text=True)
    kejString = cmds.textField("kneeElbowControl", q=True, text=True)
    gsoString = cmds.textField("gScaleObj", q=True, text=True)
    gsnString = cmds.optionMenu("gScaleName", q=True, v=True)
    ikhString = (cmds.textField("ikHandleName", q=True, text=True) + "ikHandle")
    limbSetString = cmds.textField("limbSettingsCtrl", q=True, text=True)
    resultString = cmds.textField("resultJoint", q=True, text=True)

    cmds.ikHandle(sj = sjString, ee = ejString, n=ikhString)

    # Lecturer script creates the ik setup for the limb, including elbow/knee lock.
    stretchIK = sj.stretchy_ik(ikhString, global_scale = gsoString + "." + gsnString, axis = "x")
    stretchIK.lock_joint(kejString)
    
    # Additional functionality added by me to add toggle to turn off ik stretching.
    stretchSwitch(resultString, limbSetString)
    
    # Re-select what was originally selected.
    cmds.select(currentlySelected)
    
def stretchSwitch(jointName, IKSettingCtrl, *pArgs):

    ''' In a stretchy IK limb setup, establish attribute to limit stretch function on IK control
    
        jointname : name of the end joint of the result chain that corresponds to the end of the IK chain.
        IKSettingCtrl : nurbsShape/Geometry used to hold IK toggle settings.
        
        On Exit:
            Additional attribute on IKSettingCtrl which allows toggling IK stretch on/off.'''

    # Stretch achieved with translation of latter 2 ik joints in 3 joint ik chain. 
    # To establish toggle, the corresponding joints in the result chain are needed.
    # Blend colour nodes used to hold the stretched and default lengths to swap between.     
    cmds.select("%s" % jointName)
    cmds.select(cmds.listRelatives(type="joint", parent=True), add=True)
    jList = cmds.ls(selection=True)                                            
    
    cmds.addAttr(IKSettingCtrl, longName = "ikStretchToggle", niceName = "IK Stretch Toggle", attributeType = "float", min = 0, max = 1, dv = 0, keyable=True)
    
    for i in range(len(jList)):
        
        # Cleanup if already exists
        if cmds.objExists("%s" % jList[i] + "_stretchToggle_blendColors"):            
            cmds.delete("%s" % jList[i] + "_stretchToggle_blendColors")
            

        # First 3 unitConversion nodes will be the translate X, Y, Z attrs. Next 3 are the rotate X, Y, Z. Only after Translate X.
        cmds.select(jList[i])
        connectList = cmds.listConnections(destination=False, plugs=True, type = "unitConversion")

        # Creating BlendColour node for the limb stretch toggle
        colourNode = cmds.createNode("blendColors", n="%s" % jList[i] + "_stretchToggle_blendColors") 

        # Get length of joint at resting position
        jLength = cmds.getAttr("%s.translateX" % jList[i])                                                    
        
        # Setup and connect stretch and non-stretch values to blend node, and connect the toggle to the blendColour node.
        cmds.setAttr("%s" % colourNode + ".color1R", jLength)                                                        
        cmds.connectAttr("%s" % connectList[0] , "%s" %  colourNode + ".color2.color2R", force=True)
        cmds.connectAttr("%s" % IKSettingCtrl + ".ikStretchToggle", "%s" % colourNode + ".blender", force=True)
        cmds.connectAttr("%s" % colourNode + ".output.outputR", jList[i] + ".translate.translateX", force=True)
        
          
def closeWindow(myWin, *pArgs ):
    ''' Close gui window
    
        myWin : the specific instance of limb GUI window'''

    if cmds.window(myWin, exists=True):
        cmds.deleteUI(myWin)    


def updateTexField(currentTextField, *pArgs):
    ''' Allows user to click gui button to copy name of first selected item into text field
    
        currentTextField: Text field to copy text to.'''

    list = cmds.ls(selection = True)
    if len(list) == 0:
        print "Error: No object selected"
    else:    
        cmds.textField("%s" % currentTextField, edit=True, tx="%s" % list[0])
        
        
def copyDropDown(dropdown, *pArgs):
    ''' Copy the selected dropdown preset text into the GUI textfield

        dropdown : selected dropdown preset text'''

    cmds.textField("ikHandleName", edit=True, tx="%s" % dropdown)
   
        
def updateDropDown(gScaleObj, dropdown, *pArgs):
    ''' Populate dropdown GUI field with all user defined attrs of object specified to hold global scale property
    
        gScaleObj : obj named as containing global scale attribute
        dropdown : list of gScaleObj's user defined attrs'''

    # Delete existing items (if exist) in dropdown when call
    if dropdown != None:
            for i in cmds.optionMenu(dropdown, q=True, ill=True) or []:
                cmds.deleteUI(i)

    # Text field to update with dropdown text              
    updateString = cmds.textField("gScaleObj", q=True, text=True)
    cmds.select(updateString)

    userAttrs = cmds.listAttr(ud=True)

    if userAttrs == None:
        print "No user defined attributes."
    else:
        print "User defined attributes detected."
        for i in range(len(userAttrs)):
            cmds.menuItem( label="%s" % userAttrs[i], p = dropdown)
        

limbGUI()