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


DISSOLVE_RCLs = "intermediateDissolvedRCLs"
DISSOLVE_RCLs_Lyr = 'intermediatedissolvedRclsLayer'
INTERSECTIONS = "intermediateRCL_Intersections"
ON_STREET_PKG = 'OnStreetPKG_2_IntersectionCounts'
SPATIAL_JOIN = 'intermediateSpatilJoin'
FREQENCY_SEGs = 'intermediateFreqSegFullName'


###
# Generates road intersections from RCLs that self-intersect (points at supposed intersections)
# Summarizes number of intersections along a FULLNAME
# Erase any streets within that no parking zone


inRCLs = arcpy.GetParameterAsText(0)

# dissolve by fullname - creates an RCL where 1 RCL has 1 Fullname. This reduces total # of intersection points created below
result = arcpy.management.Dissolve(inRCLs, DISSOLVE_RCLs, "FULLNAME", None, "SINGLE_PART", "DISSOLVE_LINES")
getMsgs("Dissolved {} into {}".format(inRCLs, DISSOLVE_RCLs))
intersectedDissolved = result.getOutput(0)

result = arcpy.management.MakeFeatureLayer(intersectedDissolved, DISSOLVE_RCLs_Lyr)
intersectedDissolvedlyr = "{} #".format(result.getOutput(0))

# create a point where RCL segments touch/cross other, different RCL segments
result = arcpy.analysis.Intersect(intersectedDissolvedlyr, INTERSECTIONS, "ALL", None, "POINT")
intersectedRcls = result.getOutput(0)
getMsgs("Intersected {} to points".format(intersectedRcls))

# spatial join the onstreet parking rcl layer to the intersected points (which seems odd but there's good reason)
result = arcpy.analysis.SpatialJoin(inRCLs, intersectedRcls, SPATIAL_JOIN, "JOIN_ONE_TO_MANY", "KEEP_ALL", "", "INTERSECT", None, '')
spatialJoinLyr = result.getOutput(0)
getMsgs("Joined {} to {} by intersect".format(inRCLs, intersectedRcls))

# summarize on segid, fullname and fullname1 to create a count of points along each segmentid
result = arcpy.analysis.Frequency(spatialJoinLyr, FREQENCY_SEGs, "SEGMENTID;FULLNAME;FULLNAME_1", None)
frequencySegFullnames = result.getOutput(0)
getMsgs("Ran Frequency on {}".format(spatialJoinLyr))

arcpy.management.AddField(frequencySegFullnames, "ismatch", "SHORT", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
getMsgs("added field to {}".format(frequencySegFullnames))

# field calc expression
functionDef = """
def docomp(f1,f2):
    if f1==f2:
        return 1
    else:
        return 0"""

# calc field just created; Where the fullnames do not match, set a flag to 0. This removes mismatches created by spatial join
arcpy.management.CalculateField(frequencySegFullnames, "ismatch", "docomp(!FULLNAME!,!FULLNAME_1!)", "PYTHON3", functionDef, "TEXT")
getMsgs("Calc'ed ismatch field in {}".format(frequencySegFullnames))

# run table select to remove the mismatches
# create a name first
d=arcpy.Describe(frequencySegFullnames)
trimmedTableName = "{}_trimmed".format(d.basename)
trimWhere = "ismatch = 1"
result = arcpy.analysis.TableSelect(frequencySegFullnames, trimmedTableName, trimWhere)
trimmedTable = result.getOutput(0)
getMsgs("Selected rows from {} where {}".format(frequencySegFullnames, trimWhere))

# join field back to the input RCL no parking layer (to get the frequency (which is the point count) field into it)
# copy the original data first
result = arcpy.management.CopyFeatures(inRCLs, ON_STREET_PKG)
outLyr = result.getOutput(0)
getMsgs("Copied {} into {}".format(inRCLs, outLyr))

arcpy.management.JoinField(outLyr, "SEGMENTID", trimmedTable, "SEGMENTID", "FREQUENCY")
getMsgs("Joined {} to {} on SEGMENTID".format(trimmedTable, outLyr))

# RENAME THE frequency field to something nicer :)
arcpy.management.AlterField(outLyr, "FREQUENCY", "NumIntersections", "Number of Intersections", "LONG", 4, "NULLABLE", "DO_NOT_CLEAR")
getMsgs("Renamed FREQUENCY field in {} to NumIntersections".format(outLyr))

arcpy.SetParameter(1, outLyr)

cleanUp(intersectedDissolved)
cleanUp(frequencySegFullnames)
#cleanUp(intersectedRcls)
cleanUp(spatialJoinLyr)
cleanUp(trimmedTable)