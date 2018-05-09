import json
import pdb


def get_throughput(packets, time):
    return 8.0 * 1024.0 * packets / time

def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)

# with open('ecmp8_N50.json', 'r') as f:
with open('ksp8.json', 'r') as f:
#with open('ecmp64_N50_n10_r10_lr15M_pkts8K', 'r') as f:
#with open('ecmp8_N100_n10_r10.pretty', 'r') as f:
#with open('ecmp8_N100_n10_r10.pretty', 'r') as f:
    distros_dict = json.load(f)
    #pdb.set_trace()
    #arr = distros_dict
    #print(arr['results'])


dest_throughputs = {}
for item in distros_dict:
    for result in item['results']:

        dest = result["dest"]
        txbytes = 0
        rxbytes = 0

        if dest not in dest_stats:
            dest_throughputs[dest] = []

        #if not dest in throughputs:
        #    throughputs[dest] = []

        #seconds = 0
        #txbytes = 0
        #rxbytes = 0
        iperf_stats = result['destStats(seconds,txbytes,rxbytes)']
        for stat in iperf_stats:
            txbytes += stat[1]
            rxbytes += stat[2]
        time = iperf_stats[len(iperf_stats) - 1][0]
        dest_throughputs[dest].append(get_throughput(rxbytes, time))

        #print(dest)

avg_dest_throughputs = [
    mean(throughputs) for dest, throughputs in dest_throughputs.items()
    ]

avg_throughput = mean(avg_dest_throughputs)
pdb.set_trace()
print("Average throughput (kbps): ", throughput_bits / 1024)
link_bandwidth_bits = (15*1024*1024)
print("Percent utilisation is: ", 100 * throughput_bits / link_bandwidth_bits)


            #print("next switch")

# pair_intervals results
#{}


             