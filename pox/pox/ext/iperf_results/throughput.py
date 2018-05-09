import json



with open('ecmp8_N100_n10_r10.pretty', 'r') as f:
#with open('ecmp64_N50_n10_r10_lr15M_pkts8K', 'r') as f:
#with open('ecmp8_N100_n10_r10.pretty', 'r') as f:
#with open('ecmp8_N100_n10_r10.pretty', 'r') as f:
    distros_dict = json.load(f)
    #arr = distros_dict
    #print(arr['results'])
    seconds = 0
    txbytes = 0
    rxbytes = 0
    for item in distros_dict:
    	for result in item['results']:
    		#seconds = 0
    		#txbytes = 0
    		#rxbytes = 0
    		for dest_stats in result['destStats(seconds,txbytes,rxbytes)']:
    			seconds += dest_stats[0]
    			txbytes += dest_stats[1]
    			rxbytes += dest_stats[2]
    print(seconds)
    print(txbytes)
    print(rxbytes)


'''
 json_data = [] # your list with json objects (dicts)

for item in json_data:
    for data_item in item['data']:
        print data_item['name'], data_item['value']

        '''
    #print(distros_dict['Results'])
    #data = json.loads("results")
    #readable_json = json.dumps(distros_dict)

    #for i in readable_json:
    #	print(i[0].type)

#print(distros_dict)

#print(distros_dict["s12"]["s12-eth2"])
'''
json_data = [] # your list with json objects (dicts)

for item in json_data:
    for data_item in item['data']:
        print data_item['name'], data_item['value']

 '''