import maya.cmds as cmds
from functools import partial


def createCtrlGUI():
    ''' Gui window setup'''

    myWin = cmds.window(title="Create NURB Control", width = 300, height = 70)
    rowColumn = cmds.rowColumnLayout(nc=3, cw=[(1, 300), (2, 10), (3,130)], columnAttach=[(1, "both", 2), (2, "left", 3), (3, "both", 5)], cs=(2, 2), rs=(2,2))
    
    cmds.text("Controls:", al="left", parent = rowColumn)
    cmds.separator(style="none", parent = rowColumn) 
    cmds.text("Functions:", al="left", parent = rowColumn)
    
    # ROW 1
    row1 = cmds.rowLayout(numberOfColumns=3, p=rowColumn, cw3=(100,100,100))
    cmds.button(label="Locator",    command= 'cmds.spaceLocator()', parent=row1, width = 100)
    cmds.button(label="Circle",     command= partial(importShape,"Circle.ma"), parent=row1, width = 100)
    cmds.button(label="Sphere",     command= partial(importShape,"Sphere.ma"), parent = row1, width = 100)
    cmds.separator(style="single", parent = rowColumn)
    cmds.button(label="Freeze Selected", command="cmds.makeIdentity(apply=True)", parent = rowColumn)
    
    # ROW 2
    row2 = cmds.rowLayout(numberOfColumns=3, p=rowColumn, cw3=(100,100,100))
    cmds.button(label="Square",     command= partial(importShape,"Square.ma"), parent = row2, width = 100)
    cmds.button(label="Cube",       command= partial(importShape,"Cube.ma"), parent = row2, width = 100)
    cmds.button(label="Pyramid",    command= partial(importShape,"Pyramid.ma"), parent = row2, width = 100)
    cmds.separator(style="single", parent = rowColumn)
    cmds.button(label="Match to Selected", command="cmds.matchTransform()", parent = rowColumn)
    
    # ROW 3
    row3 = cmds.rowLayout(numberOfColumns=3, p=rowColumn, cw3=(100,100,100))
    cmds.button(label="Diamond",    command= partial(importShape,"Diamond.ma"), parent = row3, width = 100)
    cmds.button(label="Lollipop",   command= partial(importShape,"Lollipop.ma"), parent = row3, width = 100)
    cmds.separator(style="single", parent = rowColumn)
    cmds.button(label="Select CVs", parent = rowColumn, command=partial(cvSelect))  
        
    # COLOR SECTION SEPARATORS
    cmds.separator(style="double", parent = rowColumn)  
    cmds.separator(style="double", parent = rowColumn) 
    cmds.separator(style="double", parent = rowColumn) 
    
    colourRow = cmds.rowLayout(numberOfColumns=2, p=rowColumn, cw2=(100,100))
    cmds.text("Colour:", al="left", parent = colourRow)
    cmds.optionMenu("colDropdown", parent = colourRow, changeCommand=partial(sliderChange))
    cmds.menuItem("Index")
    cmds.menuItem("RGB")
    cmds.separator(style="single", parent = rowColumn)
    cmds.button(label="Update Colour", parent = rowColumn, command=partial(colUpdate))
    
    # Want to have an Index and RGB Slider available and able to seamlessly swap between them.
    # Implementation is very hack-y: both sliders are 'visible' at all times
    # But their heights are swapped depending upon which is active. Results in only one being actually seen at a time.

    sliderColumn = cmds.columnLayout(w=300, adj=True, parent = rowColumn)                             
    cmds.colorIndexSliderGrp("index", parent = sliderColumn, min=1, max=32, value=1, h=20)            
    cmds.colorSliderGrp("rgb", parent = sliderColumn, h=1)
    
    cmds.separator(style="single", parent = rowColumn)
    cmds.button(label="Close", command=partial(closeWindow,myWin), parent = rowColumn)
    
    cmds.showWindow(myWin)     


def importShape(shapeFile, *pArgs):
    # File path needs to be updated to wherever the Shapes folder has been saved!
    filepath = "D:/Important Documents/Maya/My Scripts/Shapes/" + shapeFile
    cmds.file("%s" % filepath, i=True, dns=True) 

    
def sliderChange(*pArgs):
    ''' Update the GUI colour slider's height when function called (every time dropdown menu is changed)
    
        On Exit:
        The Colour Sliders heights are adjusted based upon the selected slider option (Index/RGB)
        Whichever one is selected is 'active' and has its height increased. The other is decreased and impossible to see.'''

    tracker = cmds.optionMenu("colDropdown", q=True, value=True) 

    if tracker == "Index":
        cmds.colorIndexSliderGrp("index", edit=True, h=20)
        cmds.colorSliderGrp("rgb", edit=True, h=1)
        
    if tracker == "RGB":
        cmds.colorIndexSliderGrp("index", edit=True, h=1)
        cmds.colorSliderGrp("rgb", edit=True, h=20)
        
def colUpdate(*pArgs):
    ''' Update colour of selected nurbs Shapes with given RGB or Index Slider colours
    
        On Exit:
        All curves of selected shapes are updated to the selected colour.'''

    tracker = cmds.optionMenu("colDropdown", q=True, value=True) 
    shapeList = cmds.ls(sl=True)
    

    for i in range(len(shapeList)):
        # Enable colour override for selected options if not enabled already.
        cmds.setAttr("%s.overrideEnabled" % shapeList[i], 1)
        
        # Query the colour provided by the index/rgb slider, set the RGB/Index mode in the shape's attributes to match
        # the one used in the GUI, and apply the colour appropriately.
 
        if tracker == "Index":
            index = cmds.colorIndexSliderGrp("index", q=True, value=True)
            cmds.setAttr("%s.overrideRGBColors" % shapeList[i], 0)
            cmds.setAttr("%s.overrideColor" % shapeList[i], index-1)
            
        if tracker == "RGB":
            rgb = cmds.colorSliderGrp("rgb", q=True, rgbValue=True)
            cmds.setAttr("%s.overrideRGBColors" % shapeList[i], 1)
            
            cmds.setAttr("%s.overrideColorRGB" % shapeList[i], rgb[0], rgb[1], rgb[2])
        
        
def cvSelect(*pArgs):
    ''' Allows selection of all of first input nurbsShape's CVs
    
        On Exit: All CVs of first given shape are selected and active.'''

    # Get list of all selected objs, and clear selection 
    selected = cmds.ls(sl=True)
    cmds.select(clear=True)

    # Gets list of shapes in first nurb object
    for i in range(len(selected)):
        shapes = cmds.listRelatives(selected[0], s=True) 

        for i in range(len(shapes)):
            # Get spans and degrees of each shape to calculate num of CVs, and select them additively.

            spans = cmds.getAttr("%s.spans" % shapes[i])
            degree = cmds.getAttr("%s.degree" % shapes[i])
            numCVs = (spans+degree) - 1
            
            cmds.select("%s.cv[0:%i]" % (shapes[i], numCVs), add=True)
        
def closeWindow(myWin, *pArgs ):

    ''' Close gui window
    
        myWin : the specific instance of nurbCtrl's GUI window'''

    if cmds.window(myWin, exists=True):
        cmds.deleteUI(myWin) 
        
createCtrlGUI()