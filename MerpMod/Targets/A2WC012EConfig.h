
//////////////////////////////
//		OPTIONS
//////////////////////////////

#define AUTO_TRANS 0
// 0 = no Delta MAP correction; 1 = include the 7x7 Delta MAP table.
// Runtime Speed Density Mode remains independent (1 = MAF, 2 = SD, 3 = blend).
#define SD_DMAP		1
					
#define ECU_IDENTIFIER_CHARS (10)
#define ECU_CALIBRATION_CHARS (8)
#define MOD_CALIBRATION_ID	FFFFFFFF
#define MOD_ECU_IDENTIFIER FFFFFFFFFF

#define EXPECTED_MAF_SENSOR 3.47f
#define EXPECTED_MAF_SD 3.73053f