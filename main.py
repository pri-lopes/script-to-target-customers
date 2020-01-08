import sys
import getopt
import pandas as pd

def main(argv):
    input_file_path = ''
    output_file_path = ''
    log = False

    try:
        opts, args = getopt.getopt(argv,'hi:o:l')
    except getopt.GetoptError:
        print('RFM-analysis.py -i <orders.csv> -o <rfm-table.csv>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('RFM-analysis.py -i <orders.csv> -o <rfm-table.csv> -l to log')
            sys.exit()
        elif opt in ('-i', '--ifile'):
            input_file_path = arg
        elif opt in ('-o', '--ofile'):
            output_file_path = arg
        elif opt in ('-l', '--log'):
            log = True

    run(input_file_path, output_file_path, log)

def run(input_file_path, output_file_path, log):
    print('---------------------------------------------')
    print(' Calculating RFM segmentation')
    print('---------------------------------------------')

    rfm_data = build_rfm_data(input_file_path)

    if log:
        create_log_file(rfm_data)

    build_output_file(rfm_data, output_file_path)
    
    print('')
    print('DONE! Check %s' % (output_file_path))

def build_rfm_data(input_file_path):
    rfm_data = get_rfm_data_from_input_file(input_file_path)

    quartiles = get_quartiles(rfm_data)

    rfm_data['recency_quartile'] = rfm_data['recency'].apply(classification_calc, args=('recency', quartiles, True))
    rfm_data['frequency_quartile'] = rfm_data['frequency'].apply(classification_calc, args=('frequency', quartiles, False))
    rfm_data['monerary_value_quartile'] = rfm_data['monetary_value'].apply(classification_calc, args=('monetary_value', quartiles, False))

    rfm_data['rfm_class_code'] = rfm_data['recency_quartile'].map(str) + rfm_data['frequency_quartile'].map(str) + rfm_data['monerary_value_quartile'].map(str)
    rfm_data['rfm_class'] = rfm_data['rfm_class_code'].apply(get_customer_classification_by_rfm_code)

    return rfm_data

def get_rfm_data_from_input_file(input_file_path):
    return pd.read_csv(input_file_path, sep=',', converters={'customer_id': lambda x: str(x)})

def get_quartiles(rfm_data):
    quantiles = rfm_data.quantile(q=[0.25,0.5,0.75])
    return quantiles.to_dict()

def classification_calc(customer_rfm_value, rfm_key, quartiles, reverse_calc):
    if customer_rfm_value <= quartiles[rfm_key][0.25]:
        return 1 if reverse_calc else 4
    elif customer_rfm_value <= quartiles[rfm_key][0.50]:
        return 2 if reverse_calc else 3
    elif customer_rfm_value <= quartiles[rfm_key][0.75]: 
        return 3 if reverse_calc else 2
    else:
        return 4 if reverse_calc else 1

def get_customer_classification_by_rfm_code(rfm_class_code):
    classifications = {
        '111': 'BEST_CUSTOMER',
        '311': 'ALMOST_LOST',
        '411': 'LOST_CUSTOMER',
        '444': 'LOST_CHEAP_CUSTOMER'
    }

    if rfm_class_code in classifications:
        return classifications[rfm_class_code]
    elif len(rfm_class_code) == 3 and rfm_class_code[1] == '1':
            return 'LOYAL_CUSTOMER'
    elif len(rfm_class_code) == 3 and rfm_class_code[2] == '1':
        return 'BIG_SPENDER'
    else:
        return 'NO_CLASSIFICATION'

def create_log_file(rfm_data):
    rfm_data.to_csv('log.csv', sep=',', index=False)

def build_output_file(rfm_data, output_file_path):
    output_data = rfm_data[['customer_id','trip_market_type', 'rfm_class']]
    output_data.to_csv(output_file_path, sep=',', index=False)
    
if __name__ == '__main__':
    main(sys.argv[1:])