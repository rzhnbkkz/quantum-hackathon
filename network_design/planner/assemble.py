import json
pre=json.load(open('presets.json'))
EV=[
 {"device":"IonQ Forte 1 (QPU)","attack":"none (Step 1)","result":"0.004","job":"openquantum:ionq:qpu:forte-1-b095-qjob-6af88c54c8f5265fb3f1bdde"},
 {"device":"IonQ Forte 1 (QPU)","attack":"tap every round","result":"0.171","job":"openquantum:ionq:qpu:forte-1-91f5-qjob-6af9149011c57442e208cb02"},
 {"device":"IonQ Forte 1 (QPU)","attack":"tap 3/12 rounds","result":"0.085","job":"openquantum:ionq:qpu:forte-1-91f5-qjob-6af91e8cc8f5265fb3f234c9"},
 {"device":"IonQ Forte 1 (QPU)","attack":"detector blinding","result":"0.003 (yield 67%)","job":"same as tap"},
 {"device":"IonQ sim (noise)","attack":"none","result":"0.000","job":"ionq:ionq:sim:simulator-91f5-qjob-6af8fcf6c8f5265fb3f21bf1"},
 {"device":"IonQ sim (noise)","attack":"tap 3/12 rounds","result":"0.117","job":"ionq:ionq:sim:simulator-91f5-qjob-6af8fd17c8f5265fb3f21c04"},
 {"device":"IonQ sim (noise)","attack":"tap every round","result":"0.242","job":"ionq:ionq:sim:simulator-91f5-qjob-6af8fd07c8f5265fb3f21bfc"},
 {"device":"IonQ sim (noise)","attack":"detector blinding","result":"0.000 (yield 50%)","job":"same as tap"},
 {"device":"IonQ sim (noise)","attack":"scrambling (DoS)","result":"0.874","job":"ionq:ionq:sim:simulator-91f5-qjob-6af8fd27c8f5265fb3f21c10"},
 {"device":"Quantinuum H2 emulator","attack":"none","result":"0.001","job":"quantinuum:quantinuum:sim:h2-emulator-91f5-qjob-6af8fd37c8f5265fb3f21c17"},
 {"device":"Quantinuum H2 emulator","attack":"tap 3/12 rounds","result":"0.125","job":"quantinuum:quantinuum:sim:h2-emulator-91f5-qjob-6af8fe7ec8f5265fb3f21cad"},
 {"device":"Quantinuum H2 emulator","attack":"tap every round","result":"0.259","job":"quantinuum:quantinuum:sim:h2-emulator-91f5-qjob-6af8fd66c8f5265fb3f21c32"},
 {"device":"Quantinuum H2 emulator","attack":"scrambling (DoS)","result":"0.875","job":"quantinuum:quantinuum:sim:h2-emulator-91f5-qjob-6af8febcc8f5265fb3f21cc9"},
]
s=open('template.html').read().replace('/*PRESETS*/[]',json.dumps(pre,separators=(',',':'))).replace('/*EVIDENCE*/[]',json.dumps(EV))
open('grid_planner.html','w').write(s); print(len(s))
