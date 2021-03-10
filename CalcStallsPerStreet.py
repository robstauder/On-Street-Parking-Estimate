def getMsgs(startMsg):
    msgCnt = arcpy.GetMessageCount()
    msg=arcpy.GetMessage(msgCnt-1)
    arcpy.AddMessage("{} {}".format(startMsg,msg))


def cleanUp(layer):
	d = arcpy.Describe(layer)
	datasetPath = d.catalogpath
	if arcpy.Exists(datasetPath):
		arcpy.management.Delete(datasetPath)
		getMsgs("Deleted {}".format(datasetPath))
	else:
		arcpy.AddMessage("{} does not exist".format(datasetPath))

def doFldCalc(calcLayer, calcField, expression, pydef):
	arcpy.management.CalculateField(calcLayer, calcField, expression, "PYTHON3", pydef, "TEXT")
	getMsgs("Calculated {} in {} using expression {} with codeblock {}".format(calcLayer, calcField, expression, pydef))	

def runSelFeatures(inFeats, selType, whereSel, invert):
	arcpy.management.SelectLayerByAttribute(inFeats, selType, whereSel, invert)
	d = arcpy.Describe(inFeats)
	selCnt = len(d.FIDset.split(";"))
	if selCnt < 1:
		arcpy.AddWarning("No features selected in {} by {}".format(inFeats, whereSel))
	else:
		getMsgs("Selected {} features in {}".format(selCnt, inFeats))


ONEWAY_STREETS='onewayStreets'
OUT_RCLs = 'OnStreetPKG_5_Fc'
OUT_RCL_LYR = 'OnStreetPKG_5_Final'

###
# Calculates number of stalls per street segmentid
# 

inLyr = arcpy.GetParameterAsText(0)
inSpace = arcpy.GetParameterAsText(1)
inHydrantSpace = arcpy.GetParameterAsText(2)
inBusSpace = arcpy.GetParameterAsText(3)
inDriveSpace = arcpy.GetParameterAsText(4)

# remove protected bike lanes from the inLyr
result = arcpy.management.GetCount(inLyr)
getMsgs("{} feature count = ".format(int(result.getOutput(0))))

where = "BikePlanType = 'Protected Bike Lane'"
runSelFeatures(inLyr, 'NEW_SELECTION', where, 'INVERT')
d = arcpy.Describe(inLyr)
fids = d.FIDset.split(";")
getMsgs("Select {} features in {}".format(len(fids),inLyr))

result = arcpy.management.CopyFeatures(inLyr, OUT_RCLs)
onStreetPkgFC = result.getOutput(0)
getMsgs("Copied selected features in {} to {}".format(inLyr, OUT_RCLs))

result = arcpy.management.MakeFeatureLayer(onStreetPkgFC,OUT_RCL_LYR)
onStreetPkgLyr = result.getOutput(0)
result = arcpy.management.GetCount(onStreetPkgLyr)
featureCnt = int(result.getOutput(0))
getMsgs("Copied {} features into {}".format(featureCnt, onStreetPkgLyr))

# set null values in hydrants, bus, and driveway space fields to 0
functionDef = """
def calcNull(fld):
	return 0 if fld == None else fld"""

nullexpression = "calcNull(!NumHydrants!)"
doFldCalc(onStreetPkgLyr, "NumHydrants", nullexpression, functionDef)

nullexpression = "calcNull(!NumBusStops!)"
doFldCalc(onStreetPkgLyr, "NumBusStops", nullexpression, functionDef)

nullexpression = "calcNull(!NumDriveways!)"
doFldCalc(onStreetPkgLyr, "NumDriveways", nullexpression, functionDef)

arcpy.management.AddField(onStreetPkgLyr, "NUM_STALLS","LONG")
getMsgs("Added NUM_STALLS field to {}".format(onStreetPkgLyr))

# select features where roadway buffers are not = 0 (to remove them from the calc)
where = "RoadwayBuffer_SBLeft = 0 And RoadwayBuffer_NBRight = 0"
runSelFeatures(onStreetPkgLyr, "NEW_SELECTION", where, "INVERT")
d = arcpy.Describe(onStreetPkgLyr)
fids = d.FIDset.split(";")
getMsgs("Selected {} features in {}".format(len(fids),onStreetPkgLyr))

# calc only those features that are not roadway buffers
doFldCalc(onStreetPkgLyr, "NUM_STALLS", "0","")

functionDef = """
def calcStalls(sb, nb, rclLen, intOffset, hydrants, stops, dwys, hydrantSpace, busSpace, dwySpace, stallSpace):
    lenWithNoPKing = rclLen - (intOffset + (hydrants * hydrantSpace) + (stops * busSpace) + (dwys * dwySpace))
    if (sb == 0 and nb == 1) or (sb==1 and nb == 0):
        return lenWithNoPKing / stallSpace
    else:
        return (lenWithNoPKing * 2) / stallSpace """

# calc length of hydrant no-parking zone 
#expression = "(!Shape_Length!- !INTERSECTION_OFFSET! - ((!NumHydrants!*{})+(!NumBusStops!* {})+(!NumDriveways!*{})))/{}".format(inHydrantSpace, inBusSpace, inDriveSpace, inSpace)
expression = "calcStalls(!RoadwayBuffer_SBLeft!,!RoadwayBuffer_NBRight!,!Shape_Length!, !INTERSECTION_OFFSET!, !NumHydrants!, !NumBusStops!, !NumDriveways!, {}, {}, {}, {})".format(inHydrantSpace, inBusSpace, inDriveSpace, inSpace)
doFldCalc(onStreetPkgLyr, "NUM_STALLS", expression, functionDef)

arcpy.SetParameter(5,onStreetPkgLyr)
