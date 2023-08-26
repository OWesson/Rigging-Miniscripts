import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as api
import math


def bendyGUI():
    ''' GUI command for creating bendy joints tool window '''
    
    bendyWin = cmds.window(title="Bendy Joints Window", width = 300, height = 200)
    cmds.rowColumnLayout(nc=2, cw=[(1, 170), (2, 150)], columnAttach=[(1, "right", 2), (2, "both", 3)], cs=(2, 2), rs=(2,2))

    cmds.text("Prefix:")
    cmds.textField("prefix", text="prefix_format_")
    cmds.text("Start Joint:")
    cmds.textField("startJoint", text="Start_Joint")
    cmds.text("End Joint:")
    cmds.textField("endJoint", text="End_Joint")
    
    cmds.separator(st="doubleDash")
    cmds.separator(st="singleDash")
   
    cmds.text("Bendy Controls per Joint:")
    cmds.intField("numBendies", v=1)
    cmds.text("Ribbon Joint Density:")
    cmds.intField("deformers", v=1)
    cmds.text("Control Size:")
    cmds.floatField("ctrlSize", min=0.0, v=1.0, pre=3)
    
    cmds.separator()
    cmds.checkBox("ribbonTwist", l="Twist Blendshape", v=True)
    cmds.separator()
    cmds.checkBox("ribbonSine", l="Sine Blendshape", v=True)
    cmds.separator()
    cmds.checkBox("limbMode", label = "Limb Mode", v=True,
                    onc = "cmds.checkBox('isoCrease', e=True, v=True, en=False)", 
                    ofc = "cmds.checkBox('isoCrease', e=True, en=True)")
    cmds.separator()
    cmds.checkBox("isoCrease", label = "Isoparm Creasing", v=True, en=False)
    
    def getData(*args):
        prefix = cmds.textField("prefix", q=True, tx=True)
        sJnt = cmds.textField("startJoint", q=True, tx=True)
        eJnt = cmds.textField("endJoint", q=True, tx=True)
        
        bendyPerJnt = cmds.intField("numBendies", q=True, v=True)
        deformersPerManip = cmds.intField("deformers", q=True, v=True) + 1
        ctrlSize = cmds.floatField("ctrlSize", q=True, v=True)
        
        twistOn = cmds.checkBox("ribbonTwist", q=True, v=True)
        sineOn = cmds.checkBox("ribbonSine", q=True, v=True)
        limbMode = cmds.checkBox("limbMode", q=True, v=True)
        isoCrease = cmds.checkBox("isoCrease", q=True, v=True)
                 
        bendyMain(prefix, sJnt, eJnt, bendyPerJnt, deformersPerManip, ctrlSize, twistOn, sineOn, limbMode, isoCrease)
        
    cmds.separator()
    cmds.button(label="Create", command=getData)
    cmds.showWindow(bendyWin)


def bendyMain(prefix, sJnt, eJnt, bendyPerJnt, deformersPerManip, ctrlSize, twistOn, sineOn, limbMode, isoCrease):
    ''' Creates ribbon at user defined joints with user defined settings.
    
        prefix             : string, identifier prefix for ribbon system being constructed.
        sJnt               : string, the name of the start Skeleton Joint
        eJnt               : string, the name of the end Skeleton joint. This should be somewhere in a hierarchy beneath sJnt
        
        bendyPerJnt        : int, the number of bendy controls to be made for each joint. Default of 1
        deformersPerManip  : int, the number of deformer joints between manipulator controls. Default of 1
        ctrlSize           : float, multiplier value to control size of nurb controls. Default of 1.
        
        twistOn            : bool, toggle switch for creation of twist deformer blendshape
        sineOn             : bool, toggle switch for creation of sine deformer blendshape
        limbMode           : bool, toggle switch for additional systems for better limb-ribbon deformation. Forces isoCrease True.
        isoCrease          : bool, True/False switch to toggle isoparm creasing. True by default.
            
        On Exit:
        Creates a ribbon system for bendy joints set up in the joint chain including sJnt and eJnt, created to user
        defined specifications. Nodes are named to a fixed naming scheme, with a user-defined prefix string. This 
        function is the main function that processes data and calls to other functions. '''
            
    
    ''' There are 3 joint types to keep in mind in this ribbon process. They are referred to as such:
         'Skeleton / Skel'     = The joints defined by the user. For the arm, this would be the shoulder, elbow and wrist joints.
         'Deformers'           = The joints that follow the ribbon that will later be skinned to the mesh.
         'Manipulators'        = Joints that control deformations of the ribbon. Split into 2 sub-groups.
             'Controls / Ctrl'     = Manipulators that coincide with Skeleton joints
             'Bendies'             = Manipulators that do not overlap with the Skeleton Joints.'''

    skelJntList = []                   # List of names of Skeleton joints
    numCtrlJnts = 0                    # Number of control joints.
    currentJnt = eJnt                  # Holding variable for names of Skeleton joints for comparison.

    # Get list of names of all Skeleton joints in desired chain, ordered root-end.
    while currentJnt[0] != sJnt:
        currentJnt = cmds.listRelatives(currentJnt, p=True, pa=True, typ="joint")
        skelJntList.insert(0, currentJnt)
        numCtrlJnts += 1
    skelJntList.append(eJnt)    
    
    numSpans = (deformersPerManip + (bendyPerJnt * deformersPerManip)) * numCtrlJnts     # Number of spans on the ribbon.
    numIsos = (numSpans + 1)                                                             # Number of isoparms on the ribbon.
    
    # Get primary and secondary axis orientation of sJnt
    priVec = priAxisTest(skelJntList)                                                    # List of primary axis index and magnitude. 
    secVec = secAxisTest(sJnt, priVec)                                                   # List of secondary axis index and magnitude. 
        
        
    # Get world positions of sJnt and eJnt
    startPos = cmds.xform(sJnt, q=True, ws=True, t=True)
    endPos = cmds.xform(eJnt, q=True, ws=True, t=True)
    
    # Modify startPos & endPos values but maintain the same distance.
    # New Dist. Dim. nodes are not created when specifying the same points as an existing one.
    # Modify our values to avoid disrupting any existing distance nodes in the rig.
    startPos[1] = startPos[1] + 1
    endPos[1] = endPos[1] + 1
    
    # Calculate distance between startPos and endPos, and clean up after.
    distShape = cmds.distanceDimension(sp = startPos, ep = endPos)
    distLocList = cmds.listConnections(distShape, s=True, d=True)
    
    skelDist = cmds.getAttr(distShape + ".distance")
    cmds.delete(distLocList, distShape.replace("Shape", ""))
    
    
    # Function Calls
    orientation = calcJointOrient(priVec, secVec)
    
    createRibbon(prefix, numSpans, numIsos, orientation, skelDist)
    
    if isoCrease == True:
        creaseRibbon(prefix, numCtrlJnts, numSpans)
    
    addDeformers(twistOn, sineOn, prefix)
    
    manipJntList, ctrlJntList, bendyJntList, limbFixList = createManipJnts(numIsos, bendyPerJnt, deformersPerManip, prefix)
    
    createNurbsControls(priVec, manipJntList, ctrlSize)
    
    bindRibbon(manipJntList, prefix)
    
    orderedBendyJntList = setupConstraints(bendyPerJnt, manipJntList, skelJntList, ctrlJntList, bendyJntList)
    
    matchRibbon(manipJntList, skelJntList, bendyPerJnt, orderedBendyJntList)
    
    if limbMode == True:
        limbFix(limbFixList, ctrlJntList, prefix, bendyPerJnt, deformersPerManip, skelJntList)
 
    fixConstraintWeights(orderedBendyJntList)
    
    putInGroup(prefix)
    
    
def createRibbon(prefix, numSpans, numIsos, orientation, skelDist):
    ''' Creates basic starting point for the ribbon
        
        prefix       : string, the identifier prefix for the ribbon system
        numSpans     : int, number of spans on the ribbon
        numIsos      : int, number of isoparms on the ribbon
        orientation  : list, XYZ rotation values used when joints are created.
        skelDist     : int, distance between sJnt and eJnt, used for scaling ribbon
        
        On Exit:
        A ribbon scaled proportionally to skelDist is created at 0,0,0 oriented horizontally.
        Extra nodes produced during creation are deleted. It has spans equal to numSpans, and 
        isoparms equal to numIsos. A hair follicle system drives follicles at each isoparm to
        'follow' deformation of the ribbon. A Deformation Joint at the position of each follicle
        is driven by the follicle.  '''
          
    # Create nurbsPlane and hairSystem that form basis of ribbon
    cmds.nurbsPlane(w=skelDist, lr=0.2, ax=[0,0,1], d=3, u=numSpans, v=1, n=prefix + "ribbon")
    mel.eval("createHair " + str(numIsos)+ " 1 10 0 0 1 0 5 0 1 2 1")

    # Cleanup unneeded nodes and renamimg.
    cmds.delete("hairSystem1", "pfxHair1", "nucleus1")            
    cmds.rename("hairSystem1Follicles", prefix + "follicle_grp")
    
    folList = cmds.listRelatives(prefix + "follicle_grp")
    
    # Delete unneeded nodes under each follicle and rename.
    for i in range((len(folList))):
        curveToDel = cmds.listRelatives(folList[i])
        cmds.delete(curveToDel[1])
        cmds.rename(folList[i], prefix + "follicle_1")
                
    # Create Deformation Joints, with same Joint Orientation as sJnt, and parent beneath each follicle.
    for i in range(0, numIsos):
        defJntName = prefix + "deformation_joint_" + str(i+1)
        cmds.joint(p=[0,0,0], o=orientation, rad=0.5, n=defJntName)
        cmds.parent(defJntName, prefix + "follicle_"+str(i+1))
        cmds.setAttr(defJntName+".t", 0, 0, 0)
        cmds.select(cl=True)


def creaseRibbon(prefix, numCtrlJnts, numSpans):
    ''' Adds "creasing" to Skeleton Joint-aligned isoparms
    
        prefix       : string, the identifier prefix for the ribbon system
        numCtrlJnts  : int, number of Control Joints along the ribbon, minus one.
        numSpans     : int, number of spans on the ribbon.
        
        On Exit:
        Isoparms aligned to Skeleton Joints (except sJnt or eJnt) are 'creased' 
        with additional isoparms on either side. This is done to aid in weight painting
        to allow ribbon to more accurately follow Skeleton Joints.'''
        
    # Calculate creasePercent - all target isoparms are located at multiples of creasePercent (eg. 0.25 -> 0.25, 0.5, 0.75)
    spansPerJnt = numSpans / numCtrlJnts        
    creasePercent = float(spansPerJnt) / numSpans 
    # History deleted to avoid needless warning.
    cmds.delete(prefix + "ribbon", ch=True)
    
    # Add creases to targeted isoparms. 
    for i in range(1, numCtrlJnts):
        targetIso = creasePercent * i
        cmds.select(prefix + "ribbon" + ".u[" + str(targetIso - 0.01) + "]")
        cmds.select(prefix + "ribbon" + ".u[" + str(targetIso + 0.01) + "]", add=True)
        cmds.insertKnotSurface(rpo=True)
        
    # Delete history again.
    cmds.delete(prefix + "ribbon", ch=True)
    
    
def priAxisTest(skelJntList):
    ''' Calculates the primary axis of a given joint, assuming it has a child joint.
    
        skelJntList  : list, list of user defined Skeleton Joint chain joints.
        
        On Exit:
        Returns list containing both the index for the primary axis(0 = x, 1 = y, 2 = z),
        and the magnitude'''

    # Get vectors of the X, Y and Z axes of the joint.
    sJntData = cmds.xform(skelJntList[0], q=True, m=True, ws=True)
    axisX = sJntData[0:3]
    axisY = sJntData[4:7]
    axisZ = sJntData[8:11]
    axisVecs = [axisX, axisY, axisZ]
    
    # Get vector between sJnt and the next joint in the chain.
    nextJnt = cmds.listRelatives(skelJntList[0], c=True, typ="joint")
    p1 = api.MVector(cmds.joint(skelJntList[0], q=True, p=True))
    p2 = api.MVector(cmds.joint(skelJntList[1], q=True, p=True))
    vec = p2-p1
    
    # Calculate dot product of axis and joint vectors. 
    dotX = (api.MVector(axisX) * vec)
    dotY = (api.MVector(axisY) * vec)
    dotZ = (api.MVector(axisZ) * vec)
    dotProds = [dotX, dotY, dotZ]
    
    # Greatest dot product indicates which axis is the primary axis, as they should be aligned.
    priAxisMag = max(dotProds, key=abs)
    priAxisIndex = dotProds.index(priAxisMag)
    
    # Convert the needed axisVec to an MVector for Vector multiplication.
    priAxisVec = api.MVector(axisVecs[priAxisIndex])
    
    # Normalize vectors.
    vecNorm = 0
    priAxisVecNorm = 0
    
    for i in range(len(vec)):
        vecNorm += (vec[i] * vec[i])
        priAxisVecNorm += (priAxisVec[i] * priAxisVec[i])
                
    vecNorm = math.sqrt(vecNorm)
    priAxisVecNorm = math.sqrt(priAxisVecNorm)

    # Calculate cosine similarity to check that primary axis is actually aligned to the joint.
    cosineSimilarity = (vec * priAxisVec) / (vecNorm * priAxisVecNorm)
    
    # Error handling.
    if abs(cosineSimilarity) < 0.995:
        cmds.error("ERROR: Primary Axis of joint " +str(sJnt) + " is not aligned to joint. Similarity is " + str(cosineSimilarity*100) + "%." )
        return     
    else:
        return dotProds.index(priAxisMag), priAxisMag
        
    
def secAxisTest(sJnt, priVec):
    ''' Calculates which axis to treat as the secondary axis,
        based on alignment to either World +Z or World +Y axes.
    
        sJnt    : string, the name of the start Skeleton Joint
        priVec  : list, primary axis index & magnitude of starting Skeleton joint. 
        
        On Exit:
        Returns list containing both the index for the secondary axis(0 = x, 1 = y, 2 = z),
        and the magnitude.'''
    
    # Get vectors of the X, Y and Z axes of the joint.
    sJntData = cmds.xform(sJnt, q=True, m=True, ws=True)
    axisX = sJntData[0:3]
    axisY = sJntData[4:7]
    axisZ = sJntData[8:11]
    
    # Get world vectors for positive Y and positive Z.
    worldUp = api.MVector(0,1,0)
    worldFwrd = api.MVector(0,0,1)
    
    # Dot Products of axis and world vectors
    dotX = (api.MVector(axisX) * worldFwrd)
    dotY = (api.MVector(axisY) * worldFwrd)
    dotZ = (api.MVector(axisZ) * worldFwrd)
    dotProds = [dotX, dotY, dotZ]
    
    # Greatest dot product indicates which axis is the secondary axis (the one most similar to positive Z world axis).
    secAxisMag = max(dotProds, key=abs)
    
    # Alt. calculation if primary and secondary axes are the same.
    if dotProds.index(secAxisMag) == priVec[0]:

        # Axis calculated on similarity to positive Y world vector instead of Z.
        dotX = (api.MVector(axisX) * worldUp)
        dotY = (api.MVector(axisY) * worldUp)
        dotZ = (api.MVector(axisZ) * worldUp)
        
        # Cancel out the dot product of the primary axis.
        if priVec[0] == 0:
            dotX = 0
 
        elif priVec[0] == 1:
            dotY = 0

        else:
            dotZ = 0
        
        # Return new secondary axis.
        dotProds = [dotX, dotY, dotZ]
        secAxisMag = max(dotProds, key=abs)       
            
    return dotProds.index(secAxisMag), secAxisMag
   

def calcJointOrient(priVec, secVec):
    ''' Calculate the joint orientation ribbon joints require to properly match Skeleton joints.
    
        priVec  : list, primary axis index & magnitude of starting Skeleton joint. 
        secVec  : list, secondary axis index & magnitude of starting Skeleton joint. 
        
        On Exit:
        Returns variable with rotation values needed to create ribbon joints with their 
        primary axis aligned to world X axis, and secondary axis aligned to world Z axis.'''
        
    rotPresets = [[0,0,0], [90,0,180]], [[0,-90,-90], [0,0,90]], [[90,0,90], [0,-90,0]]       # Rotations needed to align joint +/- XYZ axis to world +X axis.
    rot = [0,0,0]                                                                             # To be assigned relevant rotPreset rotation.
    
    # Allows selection of correct strings later based on primary axis being X/Y/Z, and +/-.
    xyzStrings = ["x", "y", "z"]
    tStrings = [".translateX", ".translateY", ".translateZ"]
    zUpDownStrings = ["zup", "zdown"]
    
    # Split priVec and secVec into separate variables for clarity. 
    priIndex = priVec[0]
    secIndex = secVec[0]
    priMag = priVec[1]
    secMag = secVec[1]   
     
    # Assign primary, secondary and tertiary axes. 
    priAxis = xyzStrings[priIndex]   
    secAxis = xyzStrings[secIndex]
    xyzStrings.remove(priAxis)
    xyzStrings.remove(secAxis)
    rHandAxis = xyzStrings.pop(0)
    
    # Combine into single ordered string (e.g "yzx")
    oriJntString = priAxis + secAxis + rHandAxis
    
    # Identify whether axes are positive or negative.
    if priMag >= 0:
        isPriNeg = 0
    else:
        isPriNeg = 1
        
    if secMag >= 0:
        isSecNeg = 0
    else:
        isSecNeg = 1
        
    # Assign correct primary axis rotation preset
    rot = rotPresets[priIndex][isPriNeg]
    
    # Create temporary 2-joint chain along world X axis, with same primary axis as sJnt.
    cmds.select(cl=True)
    tempJntRoot = cmds.joint(p=[0,0,0], o=rot, rad=0.5)
    tempJntEnd = cmds.duplicate(tempJntRoot)
    cmds.parent(tempJntEnd, tempJntRoot)
    cmds.setAttr(tempJntEnd[0] + tStrings[priIndex], abs(priMag))
    
    # Orient secondary axis to +Z world axis.
    cmds.joint(tempJntRoot, e=True, oj= oriJntString, sao = zUpDownStrings[isSecNeg])
    
    # Get rotation value, cleanup, and exit function.
    orientation = cmds.joint(tempJntRoot, q=True, o=True)
    cmds.delete(tempJntRoot, tempJntEnd)
    return orientation
    

def createManipJnts(numIsos, bendyPerJnt, deformersPerManip, prefix):
    ''' Creates all Manipulator joints and their controls.
    
        numIsos            : int, number of isoparms on the ribbon
        bendyPerJnt        : int, number of Bendy joints desired per Skeleton joint
        deformersPerManip  : int, the number of deformer joints between manipulator controls.
        prefix             : string, the identifier prefix for the ribbon system
            
        On Exit:
        Manipulator Joints are created according to user settings, using Deformation Joints.
        Manipulator Joint created at Deformation Joint (i), and the next (x) Deformation Joints
        are skipped. (x) is deformerPerManip. Manupulator Joints are created according to whether
        they are Control or Bendy Joints, and lists created for each.
        
        Returns lists of every Manipulator Joint, Control Joints only, Bendy Joints only
        and follicles aligned with Control Joints.
        
        For Example:
        defJnt01 -> ctrlJnt01
        defJnt02
        defJnt03 -> bendyJnt01
        defJnt04
        defJnt05 -> ctrlJnt02'''
        
    manipJntList = []        # All joints that can be used to manipulate the ribbon ("Manipulator Joints")
    ctrlJntList = []         # Manipulator Joints that overlap with Skeleton Joints ("Control Joints")
    bendyJntList = []        # Manipulator Joints that do not overlap with Skeleton Joints. ("Bendy Joints")
    limbFixList = []         # Follicle joints aligned with Control Joints. Used for limb fix function.
    ctrlBendyCounter = 0     # Counter to be used as an if condition: differentiates between Control and Bendy joints.
    
    # Loop iterates to values where Manipulator Joints should be created (using i and existing deformation joints.)
    for i in range(1, numIsos+1, deformersPerManip): 
    
        # Create Manipulator Joint, add to Manip list.
        manipJnt = prefix + "ribbon_manip_"+str(i)
        cmds.duplicate(prefix + "deformation_joint_"+str(i), n=manipJnt)
        cmds.parent(manipJnt, world=True)
        cmds.makeIdentity(apply=True, r=True)  
        manipJntList.append(manipJnt)
         
        # OffsetGrp creation       
        cmds.group(em=True, n=manipJnt+"_offset")
        cmds.matchTransform(manipJnt+"_offset", manipJnt)
       
        # Manip Joint is a Control Joint - aligns with Skeleton Joint
        if ctrlBendyCounter == 0 or bendyPerJnt == 0:
            cmds.parent(manipJnt, manipJnt+"_offset")
            ctrlBendyCounter += 1
            ctrlJntList.append(manipJnt)
            limbFixList.append(prefix + "deformation_joint_"+str(i))
        
        # Manip Joint is a Bendy Joint             
        else:
            cmds.group(em=True, n=manipJnt+"_aim")
            cmds.matchTransform(manipJnt+"_aim", manipJnt)
            cmds.parent(manipJnt+"_aim", manipJnt+"_offset")
            cmds.parent(manipJnt, manipJnt+"_aim")
            bendyJntList.append(manipJnt)
            
            # Iterate or reset counter.
            if ctrlBendyCounter == bendyPerJnt:
                ctrlBendyCounter = 0
            else:            
                ctrlBendyCounter += 1
               
    return manipJntList, ctrlJntList, bendyJntList, limbFixList
            
        
def bindRibbon(manipJntList, prefix):
    ''' Binds Manipulator Joints to the Ribbon
    
        manipJntList  : list, names of all Manipulator Joints
        prefix        : string, the identifier prefix for the ribbon system 
                    
        On Exit:
        Ribbon is skinned to Manipulator Joints with necessary settings.'''

    # Select all joints and the ribbon, and skin.
    cmds.select(manipJntList, prefix + "ribbon")
    cmds.skinCluster(tsb=True, sm=0, mi=2)
    
  
def setupConstraints(bendyPerJnt, manipJntList, skelJntList, ctrlJntList, bendyJntList):
    ''' Sets up constraints required for Bendy Joints to properly follow Control Joints.
    
        bendyPerJnt   : int, number of user-defined Bendy Joints per Skeleton Joint
        manipJntList  : list, all Manipulator Joints that affect the ribbon. (Bendy and Control Joints)
        skelJntList   : list, all Skeleton Joints from sJnt to eJnt.
        ctrlJntList   : list, all Control Joints on the ribbon. (overlap Skeleton Joints)
        bendyJntList  : list, all Bendy Joints on the ribbon. (do not overlap Skeleton Joints)
        
        On Exit:
        Ribbon is skinned to Manipulator Joints with necessary settings. Returns a list
        of Bendy Joints broken down into lists dependant on the Control Joints they're
        located between.'''
        
    # Initialize new lists.
    holdingList = []
    orderedBendyJntList = []
    
    # Create ordered Bendy list based on which Control Joints the Bendy Joint lies between.
    # ie. [[bendy1, bendy2], [bendy3, bendy4]].
    for i in range(len(skelJntList)):
        for j in range(bendyPerJnt):
            if bendyJntList:
                holdingList.append(bendyJntList.pop(0))
        
        if len(holdingList) > 0:
            orderedBendyJntList.append(holdingList)
        holdingList = []
    
    # Sample the orientation data from the first control joint.
    orientedCtrlJnt = cmds.xform(ctrlJntList[0], q=True, m=True, ws=True)
    # Setup presets for aim constraints
    worldAxisVec = [[[-1,0,0],[0,-1,0],[0,0,-1]], [[1,0,0],[0,1,0],[0,0,1]]]
    aimVec = 0
    
    # Checking the x Value of the X, Y, Z vectors of orientedCtrlJoint to determine preset needed.
    for k in 0, 4, 8:
        if orientedCtrlJnt[k] == 1.0:
            aimVec = worldAxisVec[0][k/4]

        elif orientedCtrlJnt[k] == -1.0:
            aimVec = worldAxisVec[1][k/4]
    
    # Convert to floats for Maya 2019 support.        
    #for i in range(len(aimVec)):
        #aimVec[0] = float(aimVec[i])
            
    # Create aimTarget groups on Control Joints EXCEPT the last.
    for i in range(len(skelJntList)-1):
        firstJnt = ctrlJntList[i]
        secondJnt = ctrlJntList[i+1]
        
        aimTarget = cmds.group(n=str(firstJnt)+"_aimTarget", em=True)
        cmds.parent(aimTarget, firstJnt)
        cmds.makeIdentity()

        # Point Constrain each Bendy Joint to the Control Joints it's between.
        # Aim Constrain each Bendy Joint to the Control Joint "before" it.
        for j in range(bendyPerJnt):
            cmds.pointConstraint(firstJnt, secondJnt, str(orderedBendyJntList[i][j]) + "_offset", mo=True)
            cmds.aimConstraint(aimTarget, str(orderedBendyJntList[i][j]) + "_aim", wut = "objectrotation", wuo = aimTarget, aim = aimVec)
            
    return orderedBendyJntList

    
def matchRibbon(manipJntList, skelJntList, bendyPerJnt, orderedBendyJntList):
    ''' Snaps Control Joints to corresponding Skeleton Joints.
    
        manipJntList         : list, all Manipulator Joints that affect the ribbon. (Bendy and Control Joints)
        skelJntList          : list, all Skeleton Joints from sJnt to eJnt.
        bendyPerJnt          : int, number of user-defined Bendy Joints per Skeleton Joint
        orderedBendyJntList  : list, list of lists of Bendy Joints, grouped by Control Joints they're between.

        On Exit:
        Control Joints are snapped to their corresponding Control Joints. Bendy Joints
        copy the orientation of preceeding Control Joints to ensure proper snapping.
        Control Joints are 100% aligned to Skeleton Joints.'''
    
    # Create duplicate of end Skeleton Joint that ribbon can be snapped to.
    # Original end joint may not be oriented ideally for ribbon setup but cannot be altered.
    # Temporary joint is used instead.
    tempJnt = cmds.duplicate(skelJntList[-1])
    skelJntList[-1] = tempJnt[0]
    
    cmds.setAttr(str(tempJnt[0]) + ".jointOrientX", 0)
    cmds.setAttr(str(tempJnt[0]) + ".jointOrientY", 0)
    cmds.setAttr(str(tempJnt[0]) + ".jointOrientZ", 0)
    
    # Snap each OffsetGrp to corresponding Skeleton Joint.
    for i in range(len(skelJntList)):
        k = (i * bendyPerJnt) + i
        
        # Get grp at top of hierarchy. Various constraint groups in way.
        offsetGrp = manipJntList[k]
        for j in (0,1):
            offsetGrp = cmds.listRelatives(offsetGrp, p=True)
 
        cmds.matchTransform(offsetGrp[0], skelJntList[i])

    # Match the orientation of each Bendy Joint to preceeding Control Joint.
    for i in range(len(skelJntList) - 1):    
        # Get rotation values of Control Joint
        j = (i * bendyPerJnt) + i    
          
        # Get offsetGrp rot values of "last" Control Joint.    
        rotX = cmds.getAttr(offsetGrp[0] + ".rotateX")
        rotY = cmds.getAttr(offsetGrp[0] + ".rotateY")
        rotZ = cmds.getAttr(offsetGrp[0] + ".rotateZ")

        # Pass rotation values to all relevant Bendy Joints.
        for m in range(len(orderedBendyJntList[i])):
            # Get the offsetGrp of the current Bendy Joint
            offsetGrp = orderedBendyJntList[i][m]
            for k in (0,2,1):
                offsetGrp = cmds.listRelatives(offsetGrp, p=True)
                
            cmds.setAttr(str(offsetGrp[0]) + ".rotateX", rotX)
            cmds.setAttr(str(offsetGrp[0]) + ".rotateY", rotY)
            cmds.setAttr(str(offsetGrp[0]) + ".rotateZ", rotZ)

    # Delete temporary joint.
    cmds.delete(tempJnt[0])
            
                  
def createNurbsControls(priVec, manipJntList, ctrlSize):
    '''Creates nurbsSquare controls to manipulate Control Joints with.
    
        priVec        : list, list of primary joint axis' index and magnitude.
        manipJntList  : list, list of all Manipulator Joints - these require controls.
        ctrlSize      : float, value that control size is multiplied by. Controls created at size of 1 unit.
        
        On Exit:
        Creates a single nurbsSquare control oriented to the ribbon, and 
        proportionally sized to the ribbon.'''
    
    # Setup primary axis index and name for nurbsControl creation   
    priAxisIndex = priVec[0]
    name = manipJntList[0]
    name = name.replace("manip_1", "control_0")
        
    # Alternate curves created based on primary axis.
    if priVec[0] == 0:
        # X AXIS
        templateControl = cmds.curve(d=1, p=[(0,1,1), (0,1,-1), (0,-1,-1), (0,-1,1), (0,1,1)], n=name)
    elif priVec[0] == 1:
        # Y AXIS
        templateControl = cmds.curve(d=1, p=[(1,0,1), (1,0,-1), (-1,0,-1), (-1,0,1), (1,0,1)], n=name)
    else:
        #Z AXIS
        templateControl = cmds.curve(d=1, p=[(1,1,0), (1,-1,0), (-1,-1,0), (-1,1,0), (1,1,0)], n=name)
    
    
    # Apply control size multiplier, duplicate template control and setup parenting for each Manipulator Joint.
    cmds.scale(ctrlSize, ctrlSize, ctrlSize, templateControl)
    cmds.makeIdentity(apply=True)
    
    for i in range(len(manipJntList)):
        nurbsControl = cmds.duplicate(templateControl)        
        cmds.matchTransform(nurbsControl, manipJntList[i])
        parentDest = cmds.listRelatives(manipJntList[i], p=True)
        cmds.parent(nurbsControl, parentDest[0])
        cmds.parent(manipJntList[i], nurbsControl)

    # Cleanup        
    cmds.delete(templateControl)
    
    
def fixConstraintWeights(orderedBendyJntList):
    ''' Changes the weighting values of Bendy Joints' point constraints
        when there is more than 1 Bendy Joint. Also fixes matching issues.
        
        orderedBendyJntList  : list, list of Bendy Joints grouped by Control Joints they lie between
        (i.e. CtrlJ - BendJ - BendJ - CtrlJ - BendJ - BendJ - CtrlJ == ([BendJ, BendJ],[BendJ, BendJ])
        
        On Exit:
        All Bendy Joints are proportionally weighted between their point-constraint parents. I.e two Bendy
        Joints located 1/3 and 2/3 "between" Control Joints A & B are weighted proportionally; Bendy Joint 1
        is weighted 66% A, 33% B. Bendy Joint 2 is the inverse. Issues with Offsets being introduced to the 
        constraints during the matching process eliminated.'''
    
    # Iterate per number of "inbetween" collections. See above definition.
    for i in range(len(orderedBendyJntList)):
            
        # Initialize variables. Separate out bendyJoints on a per-skeleton joint basis and get count of how many.
        bendiesPerJointList = orderedBendyJntList[i]
        numGrouped = len(bendiesPerJointList)
        weight = [1,1]
        belowHalf = []
        aboveHalf = [] 

        # Iterate for numGrouped.
        for j in range(numGrouped):
            
            # Aiming to calculate index in list bendiesPerJointList that marks "halfway" point.
            halfwayIndex = 0
            
            # Method only works with 3 or more bendies.
            if numGrouped > 2:
                # Calculate halfwayIndex
                halfwayIndex = (float(len(bendiesPerJointList)) + 1) / 2.0
            
                # If current iteration is operating on bendy joint above/below index, append to appropriate list.
                if (j+1) > halfwayIndex:
                    aboveHalf.append(bendiesPerJointList[i])
                        
                elif (j+1) < halfwayIndex:
                    belowHalf.append(bendiesPerJointList[i])
            
            # If 2 or less bendyJnts we need a separate methodology. Return both lists empty.
            else:
                aboveHalf = []

    # Establish variables used for iteration.
    counter = 0    
    decrease = False
    
    # Iterate for numGrouped. Calculates the weighting each Bendy requires.
    for k in range(numGrouped):
        # Calculates the "position" of the bendy in terms of distance between Control Joints. i.e 0.5, 0.33 etc.
        weightpos = float(k+1) / (numGrouped+1)
        
        # Increase/decrease counter depending on bool. Needed for subsequent loops.
        if decrease == False:
            counter += 1
        elif decrease == True:
            counter -= 1
              
        # Swap decrease's value depending on value of counter. Done as weighting on Bendy joints is inversed 
        # past the "halfway" mark, only need to calculate to that point. I.e bendy at 0.2 position between 
        # A and B has 80% A weight, 20% B weight. Bendy at 0.8 has those same weightings reversed.
        if counter > len(aboveHalf):
            decrease = True 
        elif counter < 1:
            decrease = False
        
        # Initializ variables based on counter value. Used for clarity.
        m = counter + 1
        n = counter      
         
        # Weighting value calculated.               
        weightvalue = (1.0 / ((numGrouped+1)-n)) * (n) 
        
        # All weighting done by modifying only one value of weighting. So one value will always be 1.
        # Simply change whether we affect A or B value based on position of bendy Joint.
        if weightpos > 0.5:
            weight[0] = weightvalue
        elif weightpos < 0.5:
            weight[1] = weightvalue
        else:
            weight = [1,1]
            
        # Get OffsetGrps        
        for m in range(len(orderedBendyJntList)):
            # Know that bendy joints have 3 parents incl. offsetGrp. Need offsetGrp.
            for n in (0,2,1):
                orderedBendyJntList[m][k] = cmds.listRelatives(orderedBendyJntList[m][k], p=True)
                
            # If we have less than 3 bendy joints, we know the necessary weighting without calculation.
            if numGrouped == 2:
                twoJntWeight = [[1,0.5],[0.5,1]]
                weight = twoJntWeight[k]
            
            # Remove any offsets from when ribbon was matched to skeleton joints.           
            cmds.setAttr(str(orderedBendyJntList[m][k][0]) + "_pointConstraint1.offsetX", 0)
            cmds.setAttr(str(orderedBendyJntList[m][k][0]) + "_pointConstraint1.offsetY", 0)
            cmds.setAttr(str(orderedBendyJntList[m][k][0]) + "_pointConstraint1.offsetZ", 0)
            
            # Get weight attribute of pointConstraint of joints in single variable.
            pntCnstAttrs = cmds.listAttr(str(orderedBendyJntList[m][k][0]) + "_pointConstraint1")
            
            # Apply weights.
            cmds.setAttr(str(orderedBendyJntList[m][k][0]) + "_pointConstraint1." + str(pntCnstAttrs[-2]), weight[0])
            cmds.setAttr(str(orderedBendyJntList[m][k][0]) + "_pointConstraint1." + str(pntCnstAttrs[-1]), weight[1])

                 
def addDeformers(twistOn, sineOn, prefix):
    ''' Creates blendShapes of the ribbon with twist and/or sine deformers for use.
        
        twistOn   : bool, switch to enable whether twist deformer blendShape created
        sineOn    : bool, switch to enable whether sine deformer blendShape created
        prefix    : string, identifier prefix for ribbon system being constructed.
        
        On Exit:
        Creates duplicates of ribbon's nurbsPlane, applying twist/sine deformers to them
        and orienting handles accordingly. BlendShape is established between ribbon and
        deformer ribbons. Deformer ribbons remain at origin.
        '''
        
    # Initialize variables; empty list and concatenated string for clarity.
    ribbon = prefix + "ribbon" 
    deformList = []
    
    # Same processes for twist and sine. Duplicates the ribbon, renames and adds to list of deformers.
    if twistOn == True:
        twistRib = cmds.duplicate(ribbon, n=ribbon + "_twist")
        deformList.append(twistRib)
        
    if sineOn == True:
        sineRib = cmds.duplicate(ribbon, n=ribbon + "_curve")
        deformList.append(sineRib)
        
    # Select all deformers that were created and the ribbon, create blendShape.
    cmds.select(cl=True)
    if deformList:
        for i in range(len(deformList)):
            cmds.select(deformList[i], add=True)
            
        cmds.select(ribbon, add=True)
        cmds.blendShape()
    cmds.select(cl=True)

    # Apply twist/sine deformers, orient handles to ribbons, and add handles to deformList.
    if twistOn == True:
        cmds.select(twistRib)
        twistDef = cmds.nonLinear(typ="twist", n=twistRib[0])
        deformList.append(twistDef[1])
        cmds.rotate(0,0,"-90deg", r=True) 
        
    if sineOn == True:
        cmds.select(sineRib)
        sineDef = cmds.nonLinear(type="sine", n=sineRib[0])
        deformList.append(sineDef[1])
        cmds.rotate(0,0,"-90deg", r=True)

    # If any deformers were created, put all nodes into single group and hide.
    if deformList:
        deformGrp = cmds.group(n=ribbon+"_deformer_grp", em=True)
        for i in range(len(deformList)):
            cmds.parent(deformList[i], deformGrp)     
        cmds.hide(deformGrp)


def limbFix(limbFixList, ctrlJntList, prefix, bendyPerJnt, deformersPerManip, skelJntList):
    ''' Creates additional systems to enable ribbon system to deform like limbs.
        
        limbFixList          : list, list of all follicles that align with Control Joints.
        ctrlJntList          : list, list of all Control Joints
        prefix               : string, identifier prefix for ribbon system being constructed.
        bendyPerJnt          : int, number of Bendy Joints created per (non-terminating) Skeleton Joints.
        deformersPerManip    : int, number of Deformation Joints between all Manipulator Joints.
        skelJntList          : list, root-end list of all Skeleton Joints in desired chain.
        
        On Exit:
        Ribbon is supplemented with additional joint chains running "up" the ribbon, from Control Joint
        to Control Joint. In a ribbon created for a 3-joint root-middle-end chain, the result is 2 additional
        chains that run from end-middle and middle-root. The start of each chain is parented beneath the 
        corresponding Control Joint Controller. The end is applied a single-chain IK Solver to maintain its position.
        
        Weighting on ribbon is repainted such that the start of the new chains take priority over original weight painting.
        The result is that the ribbon is "straight" from Skeleton Joint to Skeleton Joint; the ribbon will not
        affect the deformation of the limb compared to a normal setup until the ribbon controls are actually used.
        '''
    
    # Get name of ribbon's SkinCluster.
    skinClust = cmds.listConnections(prefix + "ribbonShape", t="skinCluster")
    
    # Shorten long concatenated string into variable.
    ribString = prefix + "ribbon.cv["
    
    # Establish variables. NumCreases is number of times isoCrease was performed.
    # CreaseCVFactor is how many CV's "across" from start of ribbon to the middle of first crease. Multipliable to find next creases.
    numCreases = len(skelJntList) - 2
    creaseCVFactor = 2 + (deformersPerManip + (bendyPerJnt * deformersPerManip))  
      
    # Main loop, performs once per non-terminating Skeleton Joint (ctrlJntList is equivelant.)    
    for i in range(len(limbFixList) - 1):
        # Turn off envelope for joint creation and skinning.
        cmds.setAttr(str(skinClust[0]) + ".envelope", 0)
        
        # Fix Joints created that aim 'up' the ribbon. 
        endJnt = cmds.duplicate(limbFixList[i], n= prefix + "fix_end_" + str(i+1), po=True)
        startJnt = cmds.duplicate(limbFixList[i+1], n= prefix + "fix_start_" + str(i+1), po=True)
       
        cmds.parent(endJnt, startJnt)
        cmds.parent(startJnt, w=True)
        cmds.hide(startJnt)
               
        # startJnt and endJnt added to influences on skinCluster. Locked to prevent gaining and influence when added. Unlocked after.
        cmds.skinCluster(skinClust[0], e=True, ai = startJnt[0], lw=True, wt=0.0)
        cmds.setAttr(str(startJnt[0]) + ".liw", 0)
        
        # Per iteration, calculate target area via CV's U value. Middle of isoparm creases is target area.
        creaseCVIndex = creaseCVFactor + (creaseCVFactor * i)
        
        # Select CV's 1 BEFORE iso crease. Used for isoparm creases.
        if i != numCreases:
            for j in range(0,4):
                cmds.select(ribString + str(creaseCVIndex-1) + "][" + str(j) + "]", add=True)
                
        # Select CV's at the end of the ribbon and 1 before end. Used for end of ribbon, not isoparm crease.
        else:
            for j in range(0,4):
                cmds.select(ribString + str(creaseCVIndex-1) + "][" + str(j) + "]", add=True)
                cmds.select(ribString + str(creaseCVIndex) + "][" + str(j) + "]", add=True)
            
        # Weight selected CV's to 1 for startJnt.
        cmds.skinPercent(skinClust[0], transformValue=[(startJnt[0], 1.0)])
        cmds.select(cl=True)
            
        # Select CV's 2 crease OR end of rbbon, and weight startJnt to 0.5
        for k in range(0,4):
            cmds.select(ribString + str(creaseCVIndex-2) + "][" + str(k) + "]", add=True)
        cmds.skinPercent(skinClust[0], transformValue=[(startJnt[0], 0.5)])
        cmds.select(cl=True)
        
        # If still working on iso creases and not end of ribbon.
        if i != numCreases:
            # Scale up number of iterations for more dense ribbons.
            for j in range(deformersPerManip):
                # Select CV's 2 + j before iso crease.
                for m in range(0,4):
                    cmds.select(ribString + str(creaseCVIndex - (2 + j)) + "][" + str(m) + "]", add=True)
                    
            # Transfer influence old Control Joint (at StartJnt pos) has in unwanted area to fix joint.
            cmds.skinPercent(skinClust[0], transformMoveWeights=(str(ctrlJntList[i+1]), str(startJnt[0])))
            
        # Turn envelope back on and ikHandle parented to control above endJnt
        cmds.setAttr(str(skinClust[0]) + ".envelope", 1)
    
        # Single-Chain IKSolver created, parented and offsets removed.
        cmds.ikHandle(sj= startJnt[0], ee= endJnt[0], sol = "ikSCsolver", n = str(endJnt[0]) + "_ikHandle")
        cmds.hide(str(endJnt[0]) + "_ikHandle")
        cmds.parent(str(endJnt[0]) + "_ikHandle", ctrlJntList[i])
        cmds.matchTransform(str(endJnt[0]) + "_ikHandle", ctrlJntList[i])
                
        # Fix joints parented under relevant controller, and snapped to required positions.
        newParent = cmds.listRelatives(ctrlJntList[i+1], p=True)
        cmds.parent(startJnt, newParent[0])
        cmds.matchTransform(startJnt, ctrlJntList[i+1])
        cmds.matchTransform(endJnt, ctrlJntList[i])
        
def putInGroup(prefix):
    ''' Groups all created nodes under single group.
        
        prefix  : string, identifier prefix for ribbon system being constructed.
        
        On Exit:
        All top-level groups/nodes created by the tool are grouped under a single new group
        with relevant name. Inherit Transform of the ribbon and follicle group are disabled
        to eliminate double transforms within the new group.
        '''
        
    # Build group everything is parented to.
    newGrp = cmds.group(n=prefix+"ribbon_grp", em=True) 
       
    # Get list of all OffsetGrps created.
    offsetGrps = cmds.ls(prefix + "ribbon_manip*_offset")
    
    # Check if any blend shape deformers were created, and select if True.
    blendGrp = cmds.objExists(prefix + "ribbon_deformer_grp")
    if blendGrp:
        cmds.select(prefix + "ribbon_deformer_grp")

    # Select everything to go under group, as well as select group last, and parent. 
    cmds.select(prefix + "ribbon", prefix + "follicle_grp", offsetGrps, newGrp, add=True)
    cmds.parent()
    
    # Avoid double transformations within parent group.
    cmds.setAttr(prefix + "ribbon.inheritsTransform", 0)
    cmds.setAttr(prefix + "follicle_grp.inheritsTransform", 0)
    
  
bendyGUI()