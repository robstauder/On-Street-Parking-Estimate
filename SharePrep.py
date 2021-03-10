def getMsgs(startMsg):
    msgCnt = arcpy.GetMessageCount()
    msg=arcpy.GetMessage(msgCnt-1)
    arcpy.AddMessage("{} {}".format(startMsg,msg))

def runSelFeatures(inFeats, selType, whereSel, invert):
	arcpy.management.SelectLayerByAttribute(inFeats, selType, whereSel, invert)
	d = arcpy.Describe(inFeats)
	selCnt = len(d.FIDset.split(";"))
	if selCnt < 1:
		arcpy.AddWarning("No features selected in {} by {}".format(inFeats, whereSel))
	else:
		getMsgs("Selected {} features in {}".format(selCnt, inFeats))

def doFldCalc(calcLayer, calcField, expression, pydef):
	arcpy.management.CalculateField(calcLayer, calcField, expression, "PYTHON3", pydef, "TEXT")
	getMsgs("Calculated {} in {} using expression {} with codeblock {}".format(calcLayer, calcField, expression, pydef))	

OUT_TAZ = 'OnStreetPKG_Taz_Summary'

inLyr = arcpy.GetParameterAsText(0)
inTaz = arcpy.GetParameterAsText(1)
outTaz = OUT_TAZ

# check for a selection set
d = arcpy.Describe(inLyr)
if d.FIDset != '':
	arcpy.AddError("Clear the selection set from {}".format(inLyr))
	sys.exit(0)
	
# calculate any num_stall rows that are < 0
runSelFeatures(inLyr, "NEW_SELECTION", "NUM_STALLS < 0", "")
d = arcpy.Describe(inLyr)
if d.FIDset != '':
	doFldCalc(inLyr, "NUM_STALLS", "0", "")

# get the feature class underlying inLyr
ds = d.catalogPath

result = arcpy.analysis.SummarizeWithin(inTaz, ds, outTaz, "KEEP_ALL", "NUM_STALLS Sum", "ADD_SHAPE_SUM", "KILOMETERS", None, "NO_MIN_MAJ", "NO_PERCENT", None)
outTazLyr = result.getOutput(0)
getMsgs("Created {} from SummarizeWithin against {}".format(outTaz, ds))

arcpy.SetParameter(2,outTazLyr)