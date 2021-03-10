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


def findNearest(layerForNear, nearFeatures, distance, NewFrequencyFieldName, NewFrequencyFieldNameAlias):

	# make a copy of layerForNear so we don't create the near fields in the source data
	layerForNearCopyName = "{}_Copy".format(layerForNear)
	result = arcpy.CopyFeatures_management(layerForNear, layerForNearCopyName)
	layerForNearCopy = result.getOutput(0)
	getMsgs("Copied {} to {}".format(layerForNear, layerForNearCopy))

	result = arcpy.analysis.Near(layerForNearCopy, nearFeatures, distance, "NO_LOCATION", "NO_ANGLE", "PLANAR", "NEAR_FID NEAR_FID")
	getMsgs("Near {} and {}".format(layerForNearCopy, nearFeatures))

	# filter our -1 (nothing found within distance)
	where = "NEAR_FID > -1"
	freqLyrName = "{}_freq".format(layerForNearCopy)
	result = arcpy.management.MakeFeatureLayer(layerForNearCopy, freqLyrName, where)
	freqLyr = result.getOutput(0)

	# frequency to determine number of driveways per segmentid
	tempFreqTblName = "{}_tbl".format(freqLyrName)
	result = arcpy.analysis.Frequency(freqLyrName,tempFreqTblName,"NEAR_FID")
	freqTable = result.getOutput(0)

	# join field
	desc = arcpy.Describe(nearFeatures)
	oid = desc.OidFieldName
	arcpy.management.JoinField(nearFeatures, oid, freqTable, "NEAR_FID", "FREQUENCY")
	getMsgs("Joined {} to {} to add FREQUENCY field".format(freqTable, nearFeatures))

	# rename the frequency field created by this operation
	arcpy.management.AlterField(nearFeatures, "FREQUENCY", NewFrequencyFieldName, NewFrequencyFieldNameAlias, "LONG", 4, "NULLABLE", "DO_NOT_CLEAR")
	getMsgs("Renamed FREQUENCY field in {} to {}".format(nearFeatures, NewFrequencyFieldName))

	cleanUp(freqTable) # delete the frequency table
	cleanUp(layerForNearCopy)
	arcpy.management.Delete(freqLyr) # remove feature layer


###
# Data Prep:
# Get counts of hydrants, bus stops and driveways (from bldgs)

inLyr = arcpy.GetParameterAsText(0)
inLULayer = arcpy.GetParameterAsText(1)
inHydrants = arcpy.GetParameterAsText(2)
hydrantsSearchDistance = arcpy.GetParameterAsText(3)
inBusStops = arcpy.GetParameterAsText(4)
busStopSearchDist = arcpy.GetParameterAsText(5)
buildings = arcpy.GetParameterAsText(6)
bldsSearchDist = arcpy.GetParameterAsText(7)

RCL_CLIP_LU = "intermediateRCLs_clipped_by_LU"
LU_CLIP_LYR = "intermediateLUClipLyr"
ON_STREET_PKG = 'OnStreetPKG_1_hyd_bus_dwy_counts'
HYDRANTS = "intermediateHydrants"
FILTERED_HYDRANTS = "intermediateFilteredHydrants"
FREQ_HYDRANTS = "intermediateHydrantsFreq_segmentid"

# filter out conservation and rural lu types
where = "LUSE_DESCR = 'urban'"
result = arcpy.analysis.Select(inLULayer, LU_CLIP_LYR, where)
urbanLU = result.getOutput(0)
getMsgs("Select urban types from {} into {}".format(inLULayer, urbanLU))

# clip the input RCLS by the land uses
result = arcpy.analysis.Clip(inLyr, urbanLU, RCL_CLIP_LU)
urbanRCLs = result.getOutput(0)
getMsgs("Clipped {} using {} to create {}".format(inLyr, urbanLU, urbanRCLs))

# Filter out all streets that cannot support on street parking
where = "TYPE <> 'EXIT' And TYPE <> 'FWY' And TYPE <> 'HWY' And TYPE <> 'ON RAMP' And TYPE <> 'RAMP' And CLASS <> 'A71' And CLASS <> 'A64' And CLASS <> ' ' And TYPE <> 'MALL' And CLASS NOT LIKE 'A51%' AND (TYPE <> ' ' And FULLNAME <> ' ')"
result = arcpy.analysis.Select(urbanRCLs,ON_STREET_PKG,where)
outLyr = result.getOutput(0)
getMsgs("Created {} using where clause {}".format(outLyr, where))

result = arcpy.management.GetCount(outLyr)
getMsgs("{} has {} features".format(outLyr,result.getOutput(0)))

arcpy.management.AddField(outLyr,'isDualCarriage','TEXT')
getMsgs("Added isDualCarriage field to {}".format(outLyr))

where = "SEGMENTID = 3275 OR SEGMENTID = 3205 OR SEGMENTID = 35484 OR SEGMENTID = 34051 OR SEGMENTID = 3276 OR SEGMENTID = 34052 OR SEGMENTID = 3196 OR SEGMENTID = 34074 OR SEGMENTID = 35487 OR SEGMENTID = 35372 OR SEGMENTID = 35369 OR SEGMENTID = 35373 OR SEGMENTID = 35371 OR SEGMENTID = 35485 OR SEGMENTID = 35486 OR SEGMENTID = 35370 OR SEGMENTID=33815 or SEGMENTID=33809 OR SEGMENTID=33820 OR SEGMENTID=33824 OR SEGMENTID=33810 OR SEGMENTID=17624 OR SEGMENTID=18764 OR SEGMENTID=18745 OR SEGMENTID=33143 OR SEGMENTID=18423 OR SEGMENTID=18501 OR SEGMENTID=17591 OR SEGMENTID=18051 OR SEGMENTID=18522 OR SEGMENTID=18640 OR SEGMENTID=18098 OR SEGMENTID=17797 OR SEGMENTID=18431 OR SEGMENTID=17625 OR SEGMENTID=17896 OR SEGMENTID=17820 OR SEGMENTID=18542 OR SEGMENTID=18486 OR SEGMENTID=19222 OR SEGMENTID=34885 OR SEGMENTID=18929 OR SEGMENTID=18919 OR SEGMENTID=19310 OR SEGMENTID=19055 OR SEGMENTID=19161 OR SEGMENTID=18933 OR SEGMENTID=19185 OR SEGMENTID=19159 OR SEGMENTID=19315 OR SEGMENTID=19219 OR SEGMENTID=19048 OR SEGMENTID=18951 OR SEGMENTID=19289 OR SEGMENTID=16465 OR SEGMENTID=16686 OR SEGMENTID=16418 OR SEGMENTID=16420 OR SEGMENTID=16229 OR SEGMENTID=39613 OR SEGMENTID=39612 OR SEGMENTID=16588 OR SEGMENTID=16770 OR SEGMENTID=16459 OR SEGMENTID=16184 OR SEGMENTID=16815"
result = arcpy.management.MakeFeatureLayer(outLyr,'outLyrLyr', where)
dualCarriageLyr = result.getOutput(0)
getMsgs("Created new FLayer from {} using whereclause {}".format(outLyr,where))

arcpy.management.CalculateField(dualCarriageLyr, "isDualCarriage", "'YES'", "PYTHON3", '', "TEXT")
getMsgs("Calc'ed isDualCarriage field in {}".format(outLyr))

# find closest hydrants and summarize by street
findNearest(inHydrants, outLyr, "{} FEET".format(hydrantsSearchDistance), "NumHydrants", "Number of hydrants")

# find bus stations, summarize them by street
findNearest(inBusStops, outLyr, "{} FEET".format(busStopSearchDist), "NumBusStops", "Number of Bus Stops")

# find driveways and summarize them by street (use buildings, it's a bit of a stretch)
findNearest(buildings, outLyr, "{} FEET".format(bldsSearchDist), "NumDriveways", "Number of Driveways")

arcpy.SetParameter(8,outLyr)

cleanUp(urbanRCLs)
cleanUp(urbanLU)