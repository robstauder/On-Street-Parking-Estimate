# On-Street-Parking-Estimate
A set of ArcGIS Pro Python Script Tools to estimate the amount of on-street parking space.

## What you need
1. ArcGIS Pro 2.7 or newer
2. Data: 
     - Road Centerlines with type, class and segmentid fields. Class equates to TIGER types.
     - Land use with LUSE_DESCR types including 'urban'
     - Hydrants
     - Bus stops
     - Buildings
     - metered parking with a transfer field (something without nulls)
     - Modal Plan data with RoadwayBuffer_SBLeft and RoadwayBuffer_NBRight fields
     - TAZ (Traffic Analysis Zones)

### Important Info
1. There are 6 tools that are meant to be run in succession. Tool 3 - Remove Segments with Metered Parking can be run once per metered parking dataset.
2. <b>All outputs are derived</b>. Therefore, if you run a tool multiple times, it will overwrite previous tool outputs. Copy outputs if you need to save them.
3. The py scripts are imported into the toolbox to make distribution easier. You can right-click a tool, choose edit, and make changes

### How to use
1. Download the tbx
2. In a pro project, right-click toolboxes and choose Add Toolbox
3. Browse to the location of the downloaded toolbox

### Analytical Method:
1. Erase RCLs from agriculture and conservation land use types
2. Filter out street types: EXIT; FWY; HWY; ON RAMP; RAMP
3. Filter out TIGER classes: A71; A64; empty or null
4. NEAR + JOIN FIELD RCLs to hydrants, bus stops and buildings to estimate the number of hyrants, bus stops and buildings (driveways) per segmentID. The tool counts each building as having 1 driveway. This causes an undercount as many buildings share or have not driveways.
5. Intersect RCLs on RCLs to generate points where RCLs cross
6. Spatial Join RCLs to the intersection points to find the number of intersections per segmentID
7. Remove segmentIDs that already have metered parking associated to them.
8. Remove segmentIDs that have <b>protected bike lanes</b> along them. Protected bike lane is a type.
9. Spatial Join RCLs to the PED plan to process the Roadway Buffer attributes (SB and NB)
10. If SB or NB roadway buffer = 0,1 or 1,0, reduce the number of driveways by 50% as there's only 1 side available for parking
11. Create a no parking zone on 15' on either side of a hydrant
12. Create a no parking zone within a 100' around a bus stop
13. Create a no parking zone within an 18' area per driveway
14. Create a no parking zone within 50' of an intersection along an avenue, parkway or a boulevard and within 20' of an intersection along any other street type. Multiply the value by 2 (to account for both sides of the street) under the following conditions:
     - SB and NB = null
     - SB and NB = 1
     - SB and NB = 0
15. For each segmentID, subtract the total no parking space from the segmentID length, then divide by stall length (20'). This is the estimate of the number of spaces per segmentID
     - If SB and NB = 1, multiply the total by 2 to account for space on either side of the street.
Summarize the segmentIDs within each TAZ, summing the number of stalls per segmentID. This generates the total stalls per TAZ
