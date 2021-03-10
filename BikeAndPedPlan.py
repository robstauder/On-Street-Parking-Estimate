import math

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


TEMP_BIKE = "intermediateBikeLanes"
TEMP_PED_RIGHT = "intermediatePedRight"
TEMP_PED_LEFT = "intermediatePedLeft"
wherebike = "Fac_Type IS NOT NULL"
wherepedLeft = "SBLeftPe_6 > 0"
wherepedRight = "NBRightP_7 > 0"
JOINFIELD = "SEGMENTID"
BIKEFLD = "Fac_Type"
LEFTFLD = "SBLeftPe_6"
RIGHTFLD = "NBRightP_7"
ON_STREET_PKG = 'OnStreetPKG_4_Bike_Ped'
BIKEPLANFLD = 'BikePlanType'
BIKEPLANFLD_ALIAS = "Bike Plan Type"
RB_NB_FLD = "RoadwayBuffer_NBRight"
RB_SB_FLD = "RoadwayBuffer_SBLeft"
RB_NB_ALIAS = "Roadway Buffer NB Right"
RB_SB_ALIAS = "Roadway Buffer SB Left"

###
# Moves bike and ped plan attributes into parkable streets
# 

inRCLs = arcpy.GetParameterAsText(0)
inPlanWorking = arcpy.GetParameterAsText(1)
#outRCLs = arcpy.GetParameterAsText(2)
outRCLs = ON_STREET_PKG
#cleanUp = arcpy.GetParameter(3)

## copy the input dataset to the output dataset
arcpy.management.CopyFeatures(inRCLs, outRCLs)

## create intermediate datasets - bikes
result = arcpy.analysis.Select(inPlanWorking,TEMP_BIKE,wherebike)
bikeLyr = result.getOutput(0)
getMsgs("Created {} from {} using {}".format(bikeLyr, inPlanWorking, wherebike))

## left side buffer ped plan
result = arcpy.analysis.Select(inPlanWorking, TEMP_PED_LEFT) ##, wherepedLeft)
pedLeftLyr = result.getOutput(0)
getMsgs("Created {} from {}".format(pedLeftLyr, inPlanWorking))
#getMsgs("Created {} from {} using {}".format(pedLeftLyr, inPlanWorking, wherepedLeft))

## right side buffer ped plan
result = arcpy.analysis.Select(inPlanWorking, TEMP_PED_RIGHT)##, wherepedRight)
pedRightLyr = result.getOutput(0)
getMsgs("Created {} from {}".format(pedRightLyr, inPlanWorking))
##getMsgs("Created {} from {} using {}".format(pedRightLyr, inPlanWorking))##, wherepedRight))

##join fields
arcpy.management.JoinField(outRCLs, JOINFIELD, bikeLyr, JOINFIELD, BIKEFLD)
getMsgs("Joined {} to {}".format(bikeLyr, outRCLs))

arcpy.management.JoinField(outRCLs, JOINFIELD, pedLeftLyr, JOINFIELD, LEFTFLD)
getMsgs("Joined {} to {}".format(pedLeftLyr, outRCLs))

arcpy.management.JoinField(outRCLs, JOINFIELD, pedRightLyr, JOINFIELD, RIGHTFLD)
getMsgs("Joined {} to {}".format(pedRightLyr, outRCLs))

## rename fields to make them happier :)
arcpy.management.AlterField(outRCLs, BIKEFLD, BIKEPLANFLD, BIKEPLANFLD_ALIAS, "TEXT", 70, "NULLABLE", "DO_NOT_CLEAR")
getMsgs("Renamed {} field to {}".format(BIKEFLD, BIKEPLANFLD))

arcpy.management.AlterField(outRCLs, RIGHTFLD, RB_NB_FLD, RB_NB_ALIAS)
getMsgs("Renamed {} field to {}".format(RIGHTFLD, RB_NB_FLD))

arcpy.management.AlterField(outRCLs, LEFTFLD, RB_SB_FLD, RB_SB_ALIAS)
getMsgs("Renamed {} field to {}".format(LEFTFLD, RB_SB_FLD))

# when roadway buff sb and nb = 0,1 or 1,0, reduce the number of driveways as there's only 1 side available for parking (NumDriveways)
functionDef = """
def adjustNumDriveways(sb, nb, numDwy):
	numDwy = 0 if numDwy is None else numDwy
	if sb is None and nb is None:
		return numDwy		
	elif sb == 1 and nb == 1:
		return numDwy 
	elif sb == 0 and nb == 0:
		return numDwy
	else:
		return math.ceil(numDwy / 2) """

expression = "adjustNumDriveways(!RoadwayBuffer_SBLeft!, !RoadwayBuffer_NBRight!, !NumDriveways!)"
doFldCalc(outRCLs, "NumDriveways", expression, functionDef)
getMsgs("Updated NumDriveways where RoadwayBuffer_SBLeft = 0 or RoadwayBuffer_NBRight = 0")

# func to calc the distance of no parking zones around intersections
# if we have a null value for the number of intersections, we default to 2 intersections but shorten the no parking distance
functionDef = """
def calcByType(Street_Type, fld):
	if fld is None:
		fld = 0
		
	if Street_Type == 'AVE' or Street_Type == 'BLVD' or Street_Type == 'PKWY':
		return 50 * fld
	else:
		return 20 * fld """

arcpy.management.AddField(outRCLs, "INTERSECTION_OFFSET", "LONG")
getMsgs("Added INTERSECTION_OFFSET field to {}".format(outRCLs))

expression = "calcByType(!TYPE!, !NumIntersections!)"
doFldCalc(outRCLs, "INTERSECTION_OFFSET", expression, functionDef)

# now adjust that distance depending upon the roadway buffer
functionDef = """
def adjustIntersectionOffset(sb, nb, intrOffset):
	intrOffset = 0 if intrOffset is None else intrOffset
	if (sb is None and nb is None) or (sb == 1 and nb == 1) or (sb == 0 and nb == 0):
		return math.ceil(intrOffset * 2) 
	else:
		return math.ceil(intrOffset * 1) """

expression = "adjustIntersectionOffset(!RoadwayBuffer_SBLeft!, !RoadwayBuffer_NBRight!, !INTERSECTION_OFFSET!)"
doFldCalc(outRCLs, "INTERSECTION_OFFSET", expression, functionDef)
getMsgs("Updated intersection offsets where (RoadwayBuffer_SBLeft = 1 And RoadwayBuffer_NBRight = 1) or (RoadwayBuffer_SBLeft = 1 or RoadwayBuffer_NBRight = 1)")

arcpy.SetParameter(2, outRCLs)

# clean up intermediate datasets
cleanUp(bikeLyr)
cleanUp(pedLeftLyr)
cleanUp(pedRightLyr)
