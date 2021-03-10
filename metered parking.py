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


TEMP_METERED_PKG = 'intermediateMeteredParking'
ON_STREET_PKG = 'OnStreetPKG_3_no_meters'
TEMP_RCLs = 'intermediateRCLs'

###
# Returns streets that have no metered parking
inMeteredParkingLyr = arcpy.GetParameterAsText(0)
inJoinTransferFld = arcpy.GetParameterAsText(1)
inRCLs = arcpy.GetParameterAsText(2)
nameSuffix = arcpy.GetParameterAsText(3)

outRCLs = "{}_{}".format(ON_STREET_PKG,nameSuffix)

# copy input layers to a intermediate datasts
result = arcpy.management.CopyFeatures(inMeteredParkingLyr,TEMP_METERED_PKG)
meteredParking = result.getOutput(0)
getMsgs("Copied {} to {}".format(inMeteredParkingLyr,meteredParking))

#result = arcpy.management.CopyFeatures(inRCLs,outRCLs)
result = arcpy.management.CopyFeatures(inRCLs,TEMP_RCLs)
parkingRCLs = result.getOutput(0)
getMsgs("Copied {} to {}".format(inRCLs,parkingRCLs))

# near to get closest segment ids
arcpy.analysis.Near(meteredParking, parkingRCLs, None, "NO_LOCATION", "NO_ANGLE", "PLANAR", "NEAR_FID NEAR_FID")
getMsgs("Near {} to {}".format(meteredParking, parkingRCLs))

# join field
arcpy.management.JoinField(parkingRCLs, 'OBJECTID', meteredParking, 'NEAR_FID', inJoinTransferFld)
getMsgs("Join Field {} to {}".format(parkingRCLs,meteredParking))

# filter out segments with metered parking 
where = "{} IS NULL".format(inJoinTransferFld)
# get the feature class name from outRCLs to use with makefeaturelayer
# d = arcpy.Describe(outRCLs)
# outLyrName = d.basename
# arcpy.AddMessage("Making a featurelayer from {}".format(outLyrName))
# result = arcpy.management.MakeFeatureLayer(parkingRCLs, outLyrName, where, None, "OBJECTID OBJECTID VISIBLE NONE;Shape Shape VISIBLE NONE;SEGMENTID SEGMENTID VISIBLE NONE;STREETID STREETID VISIBLE NONE;FULLNAME FULLNAME VISIBLE NONE;PREDIR PREDIR VISIBLE NONE;NAME NAME VISIBLE NONE;PROPERNAME PROPERNAME VISIBLE NONE;TYPE TYPE VISIBLE NONE;POSTDIR POSTDIR VISIBLE NONE;SCLL SCLL VISIBLE NONE;SCLH SCLH VISIBLE NONE;SCRL SCRL VISIBLE NONE;SCRH SCRH VISIBLE NONE;CLASS CLASS VISIBLE NONE;STREET_CLA STREET_CLA VISIBLE NONE;ZIPCODER ZIPCODER VISIBLE NONE;ZIPCODEL ZIPCODEL VISIBLE NONE;TOWNL TOWNL VISIBLE NONE;TOWNR TOWNR VISIBLE NONE;NEIGHBORL NEIGHBORL VISIBLE NONE;NEIGHBORR NEIGHBORR VISIBLE NONE;TRACTL TRACTL VISIBLE NONE;TRACTR TRACTR VISIBLE NONE;ONEWAY ONEWAY VISIBLE NONE;TELEV TELEV VISIBLE NONE;FELEV FELEV VISIBLE NONE;EDITTYPE EDITTYPE VISIBLE NONE;E911 E911 VISIBLE NONE;TRANSITION TRANSITION VISIBLE NONE;SHARED SHARED VISIBLE NONE;BUILT BUILT VISIBLE NONE;REVISEDATE REVISEDATE VISIBLE NONE;OWNER OWNER VISIBLE NONE;MAINTAINER MAINTAINER VISIBLE NONE;MAX_Shape_Length MAX_Shape_Length VISIBLE NONE;MIN_Shape_Length MIN_Shape_Length VISIBLE NONE;MEAN_Shape_Length MEAN_Shape_Length VISIBLE NONE;MAXROW_BUF MAXROW_BUF VISIBLE NONE;MINROW_BUF MINROW_BUF VISIBLE NONE;MEANROW_BUF MEANROW_BUF VISIBLE NONE;_1986_ROW _1986_ROW VISIBLE NONE;isDualCarriage isDualCarriage VISIBLE NONE;NEAR_FID NEAR_FID VISIBLE NONE;Shape_Length Shape_Length VISIBLE NONE")
result = arcpy.analysis.Select(parkingRCLs, outRCLs, where)
getMsgs("Selected features from {} where {} into {}".format(parkingRCLs, where, outRCLs))
outLyr = result.getOutput(0)

arcpy.DeleteField_management(outLyr, inJoinTransferFld)

arcpy.SetParameter(4,outLyr)

cleanUp(meteredParking)
cleanUp(TEMP_RCLs)