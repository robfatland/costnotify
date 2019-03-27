import csv

cols = {
    0: 'InvoiceID',
    1: 'PayerAccountId',
    2: 'LinkedAccountId',
    3: 'RecordType',
    4: 'RecordId',
    5: 'ProductName',
    6: 'RateId',
    7: 'SubscriptionId',
    8: 'PricingPlanId',
    9: 'UsageType',
    10: 'Operation',
    11: 'AvailabilityZone',
    12: 'ReservedInstance',
    13: 'ItemDescription',
    14: 'UsageStartDate',
    15: 'UsageEndDate',
    16: 'UsageQuantity',
    17: 'BlendedRate',
    18: 'BlendedCost',
    19: 'UnBlendedRate',
    20: 'UnBlendedCost',
    21: 'ResourceId',
    22: 'user:Application',
    23: 'user:Name',
    24: 'user:Owner',
    25: 'user:Project',
    26: 'user:ProjectName'
    }

cols_inv = {v: k for k, v in cols.items()}

with open('../billingdata/febdata.csv') as f:
    reader = csv.reader(f, delimiter=',')
    data=list(reader)
    n = len(data)           # returns 112494
    # print(data[7000])
    # for r in readCSV:
    # print(r[9], 'op', r[10], 'item', r[13], r[14], r[16], r[18])
    #     nrows += 1
    #     if nrows > 1000: break
    s = sum(float(line[18]) for line in data[1:-1])
    print(s)
        

