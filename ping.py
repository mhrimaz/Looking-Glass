import urllib.request, subprocess, json, time, sys, re

pings = 40
batchSize = 80
mode = "ipv4"
target = ""
file = "https://raw.githubusercontent.com/mhrimaz/Looking-Glass/master/data/everything.json"

if len(sys.argv) >= 2:
    print("arguments ", sys.argv)
    args = re.findall("((-c|-p|-l|-a)\s?([0-9A-Za-z]+)|-6)",' '.join(sys.argv[1:]))
    for arg in args:
        if arg[1] == "-c": pings = float(arg[2])
        if arg[1] == "-p": batchSize = int(arg[2])
        if arg[1] == "-l": target = arg[2]
        if arg[1] == "-a": file = "https://raw.githubusercontent.com/Ne00n/Looking-Glass/master/data/everything.json"
        if arg[0] == "-6": mode = "ipv6"
            
print("Ping count:",pings," Batch size:",batchSize," Mode:", mode)


def error(run):
    print(f"Retrying {run+1} of 4")
    if run == 3:
        print("Aborting, limit reached.")
        exit()
    time.sleep(2)

for run in range(4):
    try:
        print(f"Fetching {file}")
        request = urllib.request.urlopen(file, timeout=7)
        if (request.getcode() == 200):
            raw = request.read().decode('utf-8')
            json = json.loads(raw)
            print("load json file")
            break
        else:
            print("Got non 200 response code")
            error(run)
    except Exception as e:
        print(f"Error {e}")
        error(run)

targets,count,mapping = [],0,{}

for domain,lgs in json.items():
    try:
        for lg,ip in lgs.items():
            if ip:
                for ip,location in ip[mode].items():
                    mapping[ip] = {}
                    if target == "" or target in location:
                        mapping[ip] = {"domain":domain,"lg":lg,"geo":location}
                        targets.append(ip)
    except Exception as e:
        print("error parsing", domain,lgs)
        
results = ""
while count <= len(targets):
    print(f"fping {count} of {len(targets)}")
    if count+batchSize >= len(targets):
        batch = ' '.join(targets[count:len(targets)])
    else:
        batch = ' '.join(targets[count:count+batchSize])
    p = subprocess.run(f"fping -q -c {pings} {batch}", stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if not p.stderr.decode('utf-8'):
        print("Please install fping (apt-get install fping / yum install fping)")
        exit()
    results += p.stderr.decode('utf-8')
    count += batchSize


parsed = re.findall("([0-9.:a-z]+).*?[/]([0-9]+[.]?[0-9]*)%.*?([0-9]+[.]?[0-9]*)[/]([0-9]+[.]?[0-9]*)[/]([0-9]+[.]?[0-9]*)",results, re.MULTILINE)
results = {}
for ip,loss,min,avg,max in parsed:
    results[ip] = (float(avg),float(loss),float(max)-float(min),float(min),float(max))
  

sorted =  sorted(results.items(), key=lambda x : (x[1][0],x[1][1],x[1][2]))



result = []
result.append("Latency\tIP address\tDomain\tLocation (Maxmind)\tLooking Glass")
result.append("-------\t-------\t-------\t-------\t-------")
for index,ip in enumerate(sorted):
    data = mapping[ip[0]]
    result.append(f"{ip[1][0]:.1f}ms,{ip[1][1]:.1f}%,{ip[1][2]:.1f}\t{ip[0]}\t{data['domain']}\t{data['geo']}\t{data['lg']}")
    

def formatTable(list):
    longest,response = {},""
    for row in list:
        elements = row.split("\t")
        for index, entry in enumerate(elements):
            if not index in longest: longest[index] = 0
            if len(entry) > longest[index]: longest[index] = len(entry)
    for i, row in enumerate(list):
        elements = row.split("\t")
        for index, entry in enumerate(elements):
            if len(entry) < longest[index]:
                diff = longest[index] - len(entry)
                while len(entry) < longest[index]:
                    entry += " "
            response += f"{entry}" if response.endswith("\n") or response == "" else f" {entry}"
        if i < len(list) -1: response += "\n"
    return response

result = formatTable(result)
print(result)
