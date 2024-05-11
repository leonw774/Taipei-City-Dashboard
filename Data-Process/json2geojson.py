import json

# Given data
data = {
	"lon": [
		121.4184889550966,
		121.41527171036802,
		121.41410226471669,
		121.41180553785341,
		121.41222228207124,
		121.41199155652775,
		121.4100149369028,
		121.40940689687295,
		121.41062286426059,
		121.41136821564984,
		121.41217498918887,
		121.41230913783195,
		121.41515533621438,
		121.41716797734905,
		121.42190983815361,
		121.42665329101139,
		121.42843195033682,
		121.43127554569638,
		121.43144325643269,
		121.43188932922689,
		121.43284433121514,
		121.43384711855582,
		121.43607700063549,
		121.43956011626578,
		121.44265521090784,
		121.4458175046549,
		121.44881104333774,
		121.4494084481179,
		121.45455069303898,
		121.45885087447354,
		121.46358693663845,
		121.46570690586167,
		121.46647472424874,
		121.46684530341227,
		121.46844721286877,
		121.4700067980319,
		121.47798496333515,
		121.4857532354632,
		121.48764458657128,
		121.49304841673901,
		121.4956279985996,
		121.49801797193761,
		121.50149764752604,
		121.50558955154081,
		121.50823464486167,
		121.51142831598021,
		121.51604797914884,
		121.51974292306889,
		121.52464255205504,
		121.52877193621873,
		121.5362241948191,
		121.5371136194743,
		121.53801927864266,
		121.54429448131788,
		121.5486893779259,
		121.55010448363171,
		121.55170455259241,
		121.55448615950843,
		121.56356673493448,
		121.5682552971555,
		121.57061185954191,
		121.57370378652514,
		121.58163143378492,
		121.58858876645094,
		121.59149874993105,
		121.59639088582493,
		121.60037830145055,
		121.60829953080052,
		121.61278724787476,
		121.61928271010986,
		121.62382676867519,
		121.6259141798088,
		121.62754402821831,
		121.63310478708841,
		121.63926173297992,
		121.6454221895121,
		121.65048189813952,
		121.65977693253362,
		121.67119839949122,
		121.67902768083387,
		121.68369817950418,
		121.68844375689625,
		121.69375506914844,
		121.69805008882463,
		121.70429042753128,
		121.71524014206308,
		121.71983796139942,
		121.72364283592181,
		121.72963315024182,
		121.73146369001408,
		121.73579966342184,
		121.74083617055115,
		121.74344070273644,
		121.7462026231142,
		121.74768578557736,
		121.75008233665253,
		121.75857412888237
	],
	"lat": [
		24.99248225966552,
		25.00087179287186,
		25.002634857372488,
		25.007446646712243,
		25.012194698686425,
		25.01369816377317,
		25.016135053328686,
		25.018778297087636,
		25.02273729422623,
		25.0242808306378,
		25.02573988724916,
		25.02720572998923,
		25.031520551133134,
		25.033819256323024,
		25.041008222459133,
		25.048417426013682,
		25.053205450644306,
		25.059955233450758,
		25.0629641950661,
		25.070140939322947,
		25.073950345636764,
		25.078331254272182,
		25.082116079185358,
		25.08828110058369,
		25.090857232039667,
		25.093800297896482,
		25.097239458993865,
		25.098231570548723,
		25.10738936829072,
		25.11288398481953,
		25.116773137313434,
		25.120243134497695,
		25.123147956469353,
		25.125274686082104,
		25.12737895728866,
		25.129216616870842,
		25.135941961037684,
		25.13935730550636,
		25.140705928512123,
		25.146148831221424,
		25.146630815149514,
		25.147951509252422,
		25.1492136100837,
		25.151434735020427,
		25.153973508870664,
		25.156410425035777,
		25.158542563371267,
		25.16262613736931,
		25.165955991275524,
		25.168826327624704,
		25.175955877541128,
		25.176232495291814,
		25.176876691231865,
		25.178343090220146,
		25.18183395752503,
		25.18300006615563,
		25.184919338721375,
		25.186610527198216,
		25.195487101628025,
		25.200732558086127,
		25.202709264971276,
		25.203934966465596,
		25.206572860313226,
		25.208577741611474,
		25.211727278923355,
		25.214334850502226,
		25.21793276279413,
		25.223803024817695,
		25.22768509341813,
		25.23171991078546,
		25.233688181457364,
		25.234899002297386,
		25.235714168741108,
		25.241651697595366,
		25.24398484120752,
		25.24693867066319,
		25.248282589608525,
		25.24998004960609,
		25.25340595769353,
		25.257447793471357,
		25.262311110581777,
		25.264276120696305,
		25.269632879625277,
		25.27234483566003,
		25.280760175586774,
		25.284324425561124,
		25.288916460829217,
		25.293261638544045,
		25.3039520918987,
		25.307109921098476,
		25.309748538539882,
		25.31201403484599,
		25.312435374392642,
		25.312790038665856,
		25.31322803600202,
		25.315078997407504,
		25.319969019213957
	]
}

# Constructing GeoJSON format
geojson_data = {
    "type": "FeatureCollection",
    "features": []
}

for lon, lat in zip(data["lon"], data["lat"]):
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {}
    }
    geojson_data["features"].append(feature)

geojson_data_json = json.dumps(geojson_data, indent=4)

with open("shanchiao_fault.geojson", "w") as f:
	f.write(geojson_data_json)


print(geojson_data_json)