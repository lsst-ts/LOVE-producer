from numpy import array, int32

dictionary =  {
  'avoidanceRegions': {
    'avoidanceRegions': 0,
    'scale': 0.5692038536071777,
    'timestamp': 0.8022650611681835,
    'zero': 0.06310681998729706
  },
  'bulkCloud': {
    'bulkCloud': 0.11791870367106105,
    'timestamp': 0.7609624449125756
  },
  'cameraConfig': {
    'filterChangeTime': 0.47224524357611664,
    'filterMaxChangesAvgNum': 1,
    'filterMaxChangesAvgTime': 0.7887233511355132,
    'filterMaxChangesBurstNum': 0,
    'filterMaxChangesBurstTime': 0.48785665652414756,
    'filterMountTime': 0.8933170425576351,
    'filterMounted': 'b',
    'filterPos': 'b',
    'filterRemovable': 'c',
    'filterUnmounted': 'a',
    'readoutTime': 0.6958328667684435,
    'shutterTime': 0.26633056045725956
  },
  'cloudMap': {
    'cloudMap': 0,
    'scale': 0.5911534428596497,
    'timestamp': 0.10222715811004823,
    'zero': 0.31742963194847107
  },
  'domeConfig': {
    'altitudeAccel': 0.022322111021323865,
    'altitudeDecel': 0.6495461355254983,
    'altitudeFreerange': 0.009204938554384978,
    'altitudeMaxspeed': 0.8812338589221554,
    'azimuthAccel': 0.6864838541790798,
    'azimuthDecel': 0.9690406502940995,
    'azimuthFreerange': 0.7258526014465152,
    'azimuthMaxspeed': 0.5276294143623982,
    'settleTime': 0.7637009951314895
  },
  'downtime': {
    'scheduledDowntime': array([1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1,
      0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0,
      0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0,
      1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0,
      0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1,
      0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1,
      0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1,
      0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0,
      0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1,
      0, 1
    ], dtype = int32),
    'timestamp': 0.866168357366572,
    'unscheduledDowntimes': array([0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0,
      0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
      0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0,
      1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0,
      0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1,
      0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0,
      1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0,
      0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1,
      0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0,
      0, 0
    ], dtype = int32)
  },
  'driverConfig': {
    'coaddValues': 1,
    'filtercostWeight': 0.850970394345431,
    'ignoreAirmass': 0,
    'ignoreClouds': 1,
    'ignoreSeeing': 1,
    'ignoreSkyBrightness': 1,
    'lookaheadBonusWeight': 0.16475421868327378,
    'lookaheadWindowSize': 0.3254672884941101,
    'newMoonPhaseThreshold': 0.1263300748348425,
    'nightBoundary': 0.9088847599027046,
    'propboostWeight': 0.9594240800441438,
    'startupDatabase': 'a',
    'startupType': 'b',
    'timeBalancing': 1,
    'timecostCostRef': 0.9092960366464408,
    'timecostTimeMax': 0.6605097077449822,
    'timecostTimeRef': 0.2776724342123893,
    'timecostWeight': 0.37884950451237565
  },
  'generalPropConfig': {
    'acceptConsecutiveVisits': 0,
    'acceptSerendipity': 0,
    'airmassBonus': 0.5283631566075464,
    'brightLimit': array([0.57908262, 0.03080839, 0.97309148, 0.24223919, 0.26039679,
      0.17285225, 0.14841044, 0.20044725, 0.31113565, 0.75741966
    ]),
    'darkLimit': array([0.83235493, 0.44639652, 0.8612411, 0.85508923, 0.16797956,
      0.35695543, 0.41996654, 0.12180001, 0.20894523, 0.8789299
    ]),
    'decWindow': 0.204821737736817,
    'deltaLst': 0.8105616130541206,
    'excludePlanets': 0,
    'exclusionBounds': array([0.11807153, 0.74726523, 0.54528709, 0.96494533, 0.76106566,
      0.97351978, 0.13659401, 0.50037147, 0.57257829, 0.31125146
    ]),
    'exclusionMaximums': array([0.50303249, 0.35681876, 0.52839397, 0.00084472, 0.44231433,
      0.44955214, 0.30479919, 0.39940275, 0.78308731, 0.68341288
    ]),
    'exclusionMinimums': array([0.49229913, 0.64766824, 0.37755821, 0.20391405, 0.00387566,
      0.27762125, 0.5981642, 0.88166293, 0.82942125, 0.51096021
    ]),
    'exclusionTypes': 'b',
    'exposures': array([0.60083239, 0.51691247, 0.93747657, 0.71212907, 0.98758588,
      0.7028919, 0.44938814, 0.66884042, 0.19736112, 0.5261907,
      0.67854818, 0.5793462, 0.97031264, 0.3360102, 0.62162483,
      0.97448623, 0.69950375, 0.96749501, 0.06774573, 0.98763347
    ]),
    'fieldRevisitLimit': 0,
    'filterNames': 'c',
    'hourAngleBonus': 0.9670043785031545,
    'hourAngleMax': 0.29088600449022173,
    'maxAirmass': 0.02077631955593051,
    'maxCloud': 0.7212843345795723,
    'maxGroupedVisits': array([0, 1, 1, 0, 0, 0, 1, 1, 1, 1], dtype = int32),
    'maxNumTargets': 0,
    'maxSeeing': array([0.46207076, 0.25935085, 0.16962191, 0.51032645, 0.27082047,
      0.09863009, 0.59063623, 0.06975429, 0.0669989, 0.44248352
    ]),
    'maxVisitsGoal': 0,
    'minDistanceMoon': 0.5071635969746414,
    'name': 'a',
    'numExclusionSelections': 0,
    'numFilterExposures': array([1, 1, 1, 0, 0, 0, 1, 1, 0, 0], dtype = int32),
    'numFilters': 1,
    'numGroupedVisits': array([1, 0, 0, 1, 1, 1, 0, 1, 1, 0], dtype = int32),
    'numRegionSelections': 1,
    'numSelectionMappings': array([1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0],
      dtype = int32),
    'numTimeRanges': 0,
    'numVisits': array([1, 1, 1, 1, 0, 0, 0, 1, 0, 0], dtype = int32),
    'propId': 0,
    'regionBounds': array([0.39700786, 0.4923615, 0.09997421, 0.18676126, 0.05534305,
      0.59751357, 0.88887612, 0.21655779, 0.03471344, 0.70392359
    ]),
    'regionCombiners': 'c',
    'regionMaximums': array([0.96412159, 0.61317896, 0.34244317, 0.83786862, 0.11806711,
      0.69263694, 0.09523085, 0.39970575, 0.49502288, 0.37789427
    ]),
    'regionMinimums': array([0.16859758, 0.23171731, 0.82015, 0.4625758, 0.57993274,
      0.21190702, 0.71493506, 0.33011726, 0.59361859, 0.90948706
    ]),
    'regionTypes': 'a',
    'restartCompleteSequences': 0,
    'restartLostSequences': 0,
    'restrictGroupedVisits': 0,
    'selectionMappings': array([1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0,
      0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1,
      1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0,
      1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1,
      1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0
    ], dtype = int32),
    'timeInterval': 0.12972348669599687,
    'timeRangeEnds': array([1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1],
      dtype = int32),
    'timeRangeStarts': array([1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
      dtype = int32),
    'timeWeight': 0.5756040130041492,
    'timeWindowEnd': 0.9924975279861579,
    'timeWindowMax': 0.7839485499662527,
    'timeWindowStart': 0.7029162166549554,
    'twilightBoundary': 0.7466490368444387
  },
  'interestedProposal': {
    'numProposals': 1,
    'observationId': 1,
    'proposalBonuses': array([0.40257461, 0.46457158, 0.97975493, 0.5321284, 0.16779754,
      0.14835499, 0.6872422, 0.56277553, 0.90680626, 0.18460034
    ]),
    'proposalBoosts': array([0.41110881, 0.72796022, 0.05010503, 0.09922241, 0.5457079,
      0.26572922, 0.1069376, 0.26169757, 0.63214109, 0.52637744
    ]),
    'proposalIds': array([0, 0, 0, 0, 1, 0, 1, 1, 1, 0], dtype = int32),
    'proposalNeeds': array([0.89128149, 0.598078, 0.86549332, 0.89279337, 0.42544408,
      0.67560034, 0.54447631, 0.94473524, 0.79816074, 0.7258185
    ]),
    'proposalValues': array([0.81403237, 0.99815995, 0.25656119, 0.20136363, 0.74678281,
      0.77033251, 0.5142838, 0.48707581, 0.40374307, 0.88269693
    ])
  },
  'loopTimeMs': {
    'loopTimeMs': 0.796231877641984
  },
  'nightSummary': {
    'timestamp': 0.5845975982069754,
    'totalVisits': 0.04011908435692091
  },
  'obsSiteConfig': {
    'height': 0.8511415942600505,
    'latitude': 0.4584536776423547,
    'longitude': 0.1897605282107142,
    'name': 'b',
    'pressure': 0.6959955296764856,
    'relativeHumidity': 0.6420784891062011,
    'temperature': 0.5407724463942992
  },
  'observation': {
    'airmass': 0.8218648903269591,
    'altitude': 0.5124919555126976,
    'angle': 0.9939323868368598,
    'azimuth': 0.3155520183652022,
    'cloud': 0.7765687670039291,
    'decl': 0.6450478328166024,
    'exposureTimes': array([1, 1, 1, 1, 1, 1, 0, 1, 0, 0], dtype = int32),
    'fieldId': 1,
    'filter': 'c',
    'fiveSigmaDepth': 0.009605817456029397,
    'groupId': 1,
    'moonAlt': 0.736135286551329,
    'moonAz': 0.5659085142333045,
    'moonDec': 0.36836315259984176,
    'moonDistance': 0.40213888348307436,
    'moonPhase': 0.9365230922325852,
    'moonRa': 0.8953304495737955,
    'night': 0,
    'note': 'a',
    'numExposures': 0,
    'numProposals': 0,
    'observationId': 1,
    'observationStartLst': 0.2688752074864852,
    'observationStartMjd': 0.27195761200716717,
    'observationStartTime': 0.7815398452627139,
    'proposalIds': array([1, 1, 1, 1, 0, 1, 1, 0, 1, 0], dtype = int32),
    'ra': 0.01816357668492674,
    'seeingFwhm500': 0.17207397382000555,
    'seeingFwhmEff': 0.26023304736439834,
    'seeingFwhmGeom': 0.8578840280109546,
    'skyBrightness': 0.5895771368306654,
    'slewTime': 0.28714490644357715,
    'solarElong': 0.9977266968258558,
    'sunAlt': 0.257920600019801,
    'sunAz': 0.5137883371656904,
    'sunDec': 0.7395197854992286,
    'sunRa': 0.6913205405598513,
    'targetId': 1,
    'visitTime': 0.33590341193227236
  },
  'observatoryState': {
    'domeAltitude': 0.9139706081583656,
    'domeAzimuth': 0.21546427693564485,
    'filterMounted': 'b',
    'filterPosition': 'b',
    'filterUnmounted': 'c',
    'pointingAltitude': 0.42512259700430355,
    'pointingAngle': 0.06444119013451133,
    'pointingAzimuth': 0.20613962386932072,
    'pointingDec': 0.14960333875736864,
    'pointingPa': 0.7301654668609503,
    'pointingRa': 0.10326501170712521,
    'pointingRot': 0.1557128241642345,
    'telescopeAltitude': 0.7747037779701393,
    'telescopeAzimuth': 0.09895236342497093,
    'telescopeRotator': 0.6496603319310068,
    'timestamp': 0.18743499245019646,
    'tracking': 0
  },
  'opticsLoopCorrConfig': {
    'telOpticsClAltLimit': array([0.08916202, 0.61189195, 0.99578436]),
    'telOpticsClDelay': array([0.54959597, 0.53448618]),
    'telOpticsOlSlope': 0.3467025387811272
  },
  'parkConfig': {
    'domeAltitude': 0.9461053956418471,
    'domeAzimuth': 0.9695992389771277,
    'filterPosition': 'a',
    'telescopeAltitude': 0.7345209013881822,
    'telescopeAzimuth': 0.6790678457888157,
    'telescopeRotator': 0.8349094068381648
  },
  'photometricQuality': {
    'photometricQuality': 0.7411209279197948,
    'timestamp': 0.9951256831387749
  },
  'predictedSchedule': {
    'decl': 0.6845544150378806,
    'filter': 'a',
    'ra': 0.47971293930054115,
    'skyAngle': 0.7932828344714875,
    'visitTime': 0.8578475121235484
  },
  'rotatorConfig': {
    'accel': 0.7864236400590823,
    'decel': 0.6768068346699463,
    'filterChangePos': 0.08719275792238956,
    'followsky': 1,
    'manualRotator': 0,
    'maxpos': 0.6687016222424277,
    'maxspeed': 0.2942477813509059,
    'minpos': 0.5078183971193535,
    'resumeAngle': 1
  },
  'schedulerConfig': {
    'surveyDuration': 0.11615703706526204
  },
  'seeing': {
    'seeing': 0.8538766539036542,
    'timestamp': 0.10582967213640748
  },
  'sequencePropConfig': {
    'acceptConsecutiveVisits': 1,
    'acceptSerendipity': 0,
    'airmassBonus': 0.16712342590646911,
    'brightLimit': array([0.25760954, 0.74317706, 0.93514925, 0.53671561, 0.86893097,
      0.63366232, 0.81020251, 0.9130402, 0.78871167, 0.62355674
    ]),
    'darkLimit': array([0.86104801, 0.10285942, 0.75777615, 0.72928247, 0.3468786,
      0.88515993, 0.70880068, 0.05643878, 0.62545187, 0.2998642
    ]),
    'decWindow': 0.9041925954996471,
    'deltaLst': 0.10075863621056191,
    'excludePlanets': 1,
    'exposures': array([0.27033766, 0.24634935, 0.14833684, 0.25631616, 0.40771787,
      0.63002604, 0.90349577, 0.0584299, 0.83444585, 0.50936564,
      0.94586409, 0.27016221, 0.48014696, 0.30579705, 0.49132646,
      0.49875815, 0.59900671, 0.24166252, 0.1761588, 0.75891677,
      0.73920692, 0.58054701, 0.45111364, 0.14942955, 0.50394644,
      0.5284815, 0.13506735, 0.76140819, 0.98886818, 0.2131808,
      0.62254767, 0.48040696, 0.11840709, 0.88725471, 0.69834875,
      0.22502783, 0.63526264, 0.82902705, 0.05003101, 0.17208367,
      0.11613748, 0.56326035, 0.50301678, 0.65990455, 0.30786316,
      0.32764096, 0.77378918, 0.82172396, 0.82220807, 0.22026647
    ]),
    'filterNames': 'c',
    'hourAngleBonus': 0.2245103439701539,
    'hourAngleMax': 0.680690553975496,
    'masterSubSequenceNames': 'b',
    'masterSubSequenceTimeIntervals': 0.2690742656673415,
    'masterSubSequenceTimeWeights': 0.7187653073551493,
    'masterSubSequenceTimeWindowEnds': 0.3792765365773795,
    'masterSubSequenceTimeWindowMaximums': 0.1216563606994927,
    'masterSubSequenceTimeWindowStarts': 0.3470232348102419,
    'maxAirmass': 0.11340058036760736,
    'maxCloud': 0.8986096514014973,
    'maxNumTargets': 0,
    'maxSeeing': array([0.68120258, 0.04102293, 0.07737512, 0.72492922, 0.1032097,
      0.31701999, 0.26933763, 0.04976651, 0.03116997, 0.13903478
    ]),
    'maxVisitsGoal': 1,
    'minDistanceMoon': 0.3720571989842185,
    'name': 'c',
    'nestedSubSequenceFilters': 'c',
    'nestedSubSequenceNames': 'c',
    'nestedSubSequenceTimeIntervals': 0.24206099729136576,
    'nestedSubSequenceTimeWights': 0.6796441847743212,
    'nestedSubSequenceTimeWindowEnds': 0.27363318955870597,
    'nestedSubSequenceTimeWindowMaximums': 0.515238016010762,
    'nestedSubSequenceTimeWindowStarts': 0.3218276870172574,
    'numFilterExposures': array([0, 1, 0, 1, 1, 0, 1, 1, 1, 1], dtype = int32),
    'numFilters': 0,
    'numMasterSubSequenceEvents': 1,
    'numMasterSubSequenceMaxMissed': 0,
    'numMasterSubSequences': 0,
    'numNestedSubSequenceEvents': 0,
    'numNestedSubSequenceFilterVisits': 0,
    'numNestedSubSequenceFilters': 0,
    'numNestedSubSequenceMaxMissed': 0,
    'numNestedSubSequences': 1,
    'numSubSequenceEvents': array([1, 0, 1, 1, 1, 1, 0, 1, 0, 1], dtype = int32),
    'numSubSequenceFilterVisits': array([0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1,
      1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0,
      0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1
    ], dtype = int32),
    'numSubSequenceFilters': array([0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0],
      dtype = int32),
    'numSubSequenceMaxMissed': array([1, 0, 1, 0, 0, 0, 1, 1, 0, 1], dtype = int32),
    'numSubSequences': 1,
    'numUserRegions': 1,
    'propId': 1,
    'restartCompleteSequences': 0,
    'restartLostSequences': 1,
    'subSequenceFilters': 'b',
    'subSequenceNames': 'b',
    'subSequenceTimeIntervals': array([0.54202392, 0.57142865, 0.92677094, 0.83974718, 0.14988124,
      0.37612072, 0.1089725, 0.02622382, 0.07458596, 0.18296554
    ]),
    'subSequenceTimeWeights': array([0.76607718, 0.66722142, 0.79787098, 0.28850342, 0.15551102,
      0.97210027, 0.82602491, 0.94678207, 0.01878707, 0.39654748
    ]),
    'subSequenceTimeWindowEnds': array([0.63379822, 0.73607458, 0.91265062, 0.53773179, 0.3907924,
      0.00532402, 0.80386324, 0.98215793, 0.90724644, 0.66226851
    ]),
    'subSequenceTimeWindowMaximums': array([0.34247546, 0.23915026, 0.77501969, 0.93542937, 0.96032609,
      0.17560738, 0.58535275, 0.51311827, 0.42742518, 0.79440069
    ]),
    'subSequenceTimeWindowStarts': array([0.93578238, 0.72462482, 0.70030586, 0.69061452, 0.6535567,
      0.53675398, 0.2479157, 0.77947702, 0.11909344, 0.64388817
    ]),
    'twilightBoundary': 0.38698731429640454,
    'userRegionIds': array([0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1],
      dtype = int32)
  },
  'skyBrightness': {
    'filter': 'b',
    'scale': 0.3599909245967865,
    'skyBrightnress': 0,
    'timestamp': 0.25945266013498836,
    'zero': 0.27948829531669617
  },
  'slewConfig': {
    'prereqAdc': 'a',
    'prereqDomalt': 'c',
    'prereqDomaz': 'c',
    'prereqDomazSettle': 'a',
    'prereqExposures': 'c',
    'prereqFilter': 'b',
    'prereqGuiderAdq': 'b',
    'prereqGuiderPos': 'a',
    'prereqInsOptics': 'b',
    'prereqReadout': 'b',
    'prereqTelOpticsClosedLoop': 'b',
    'prereqTelOpticsOpenLoop': 'b',
    'prereqTelRot': 'b',
    'prereqTelSettle': 'b',
    'prereqTelalt': 'c',
    'prereqTelaz': 'b'
  },
  'surveyTopology': {
    'generalPropos': 'a',
    'numGeneralProps': 0,
    'numSeqProps': 0,
    'sequencePropos': 'b'
  },
  'telescopeConfig': {
    'altitudeAccel': 0.2259153961874819,
    'altitudeDecel': 0.07045972944573031,
    'altitudeMaxpos': 0.5793457667347551,
    'altitudeMaxspeed': 0.6184265404821278,
    'altitudeMinpos': 0.5430120336206041,
    'azimuthAccel': 0.7161098634594348,
    'azimuthDecel': 0.23982850892552843,
    'azimuthMaxpos': 0.13919291312928683,
    'azimuthMaxspeed': 0.46050383442132226,
    'azimuthMinpos': 0.7115276768493461,
    'settleTime': 0.08256970066878999
  },
  'temperature': {
    'temperature': 0.9347450589921281,
    'timestamp': 0.15308072258673566
  },
  'timeHandler': {
    'downDuration': 0.6672971774453286,
    'isDown': 0,
    'night': 1,
    'timestamp': 0.38262914432029493
  },
  'timestamp': {
    'timestamp': 0.6824114332903526
  },
  'wind': {
    'direction': 0.5910054042704707,
    'speed': 0.1291756754568837,
    'timestamp': 0.5385021012004435
  }
}