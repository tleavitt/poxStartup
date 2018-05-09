import json



with open('ecmp8_N50.json', 'r') as f:
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
            for dest in result["dest"]:

                seconds = 0
                txbytes = 0
                rxbytes = 0
                for dest_stats in result['destStats(seconds,txbytes,rxbytes)']:
                    seconds += dest_stats[0]
                    txbytes += dest_stats[1]
                    rxbytes += dest_stats[2]

                print(dest,)
                print(seconds)
                print(txbytes)
                print(rxbytes)


                print("next switch")

# pair_intervals results
{}


             