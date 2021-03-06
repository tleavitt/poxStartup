import json
import pdb
#17695084.0889

#with open('ecmp8_N50.json', 'r') as f:
#with open('ecmp8_N50_n10_r10_flow8_lr15M_pkts8K', 'r') as f:
#with open('ksp8.json', 'r') as f:
with open('ksp8_N50_n10_r10_flow8_lr15M_pkts8K', 'r') as f:
#with open('ecmp64_N50_n10_r10_lr15M_pkts8K', 'r') as f:
#with open('ecmp8_N100_n10_r10.pretty', 'r') as f:
#with open('ecmp8_N100_n10_r10.pretty', 'r') as f:
    distros_dict = json.load(f)
    #pdb.set_trace()
    #arr = distros_dict
    #print(arr['results'])
    seconds = 0
    counter = 0
    txbytes = 0
    rxbytes = 0
    for item in distros_dict:
        for result in item['results']:
            dest = result["dest"]

            #if not dest in throughputs:
            #    throughputs[dest] = []

            #seconds = 0
            #txbytes = 0
            #rxbytes = 0
            cur_seconds = 0
            for dest_stats in result['destStats(seconds,txbytes,rxbytes)']:
                #seconds += dest_stats[0]
                cur_seconds = dest_stats[0]
                txbytes += dest_stats[1]
                rxbytes += dest_stats[2]
            seconds += cur_seconds
            #print(dest)
    #seconds = 0.5*counter
    print("Total seconds:", seconds)
    print("Total txmitted bytes:", txbytes)
    print("Total rxvd bytes: ", rxbytes)
    txm = 8*1024*txbytes/ seconds
    rcv = 8*1024*rxbytes/ seconds
    print("Average throughput (kbps): ", rcv / 1024)
    link_bandwidth_bits = 17695084.0889
    print("Percent utilisation is: ", 100 * rcv / link_bandwidth_bits)


            #print("next switch")

# pair_intervals results
#{}


             