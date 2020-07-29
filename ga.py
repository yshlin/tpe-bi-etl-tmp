"""Hello Analytics Reporting API V4."""

import argparse
import os
import httplib2
from googleapiclient.discovery import build
from oauth2client import client
from oauth2client import file
from oauth2client import tools
import csv
import datetime

from config import GA_CLIENT_SECRETS_PATH, GA_VIEW_ID, GA_DEST

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

FILENAME_PATTERN = './ga/vpn-ga%s-%s.csv'

# start = datetime.datetime.strptime('2020-07-16', '%Y-%m-%d')
# end = datetime.datetime.strptime('2020-07-20', '%Y-%m-%d')
# date_list = [start + datetime.timedelta(days=x) for x in range((end - start).days + 1)]
date_list = [datetime.datetime.today() - datetime.timedelta(days=1)]
PREFIX = ''
FILTER = '(^/$|^/\#|^/\?)'
GOAL = 'ga:goal1Starts'

# VIEW_ID = 'ga:202945185'  # fpn.firefox.com
# start = datetime.datetime.strptime('2020-04-01', '%Y-%m-%d')
# end = datetime.datetime.strptime('2020-06-24', '%Y-%m-%d')
# date_list = [start + datetime.timedelta(days=x) for x in range((end - start).days + 1)]
# PREFIX = '-legacy'
# FILTER = '(^/vpn$|^/vpn\#|^/vpn\?|^/vpn/$|^/vpn/\#|^/vpn/\?)'
# GOAL = 'ga:goal5Starts'


def initialize_analyticsreporting():
    """Initializes the analyticsreporting service object.

    Returns:
      analytics an authorized analyticsreporting service object.
    """
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    flags = parser.parse_args([])

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(
        GA_CLIENT_SECRETS_PATH, scope=SCOPES,
        message=tools.message_if_missing(GA_CLIENT_SECRETS_PATH))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storage = file.Storage('analyticsreporting.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())

    # Build the service object.
    analytics = build('analyticsreporting', 'v4', http=http)

    return analytics


def get_report(analytics, d):
    # Use the Analytics Service Object to query the Analytics Reporting API V4.
    return analytics.reports().batchGet(
        body={
            'reportRequests': [
                {
                    'viewId': GA_VIEW_ID,
                    'pageSize': 10000,
                    'dateRanges': [{'startDate': d, 'endDate': d}],
                    'metrics': [
                        {'expression': 'ga:users'},
                        {'expression': 'ga:sessions'},
                        {'expression': 'ga:pageviews'},
                        {'expression': 'ga:goal1Starts'},
                    ],
                    'dimensions': [
                        {'name': 'ga:date'},
                        {'name': 'ga:countryIsoCode'},
                        {'name': 'ga:fullReferrer'},
                        {'name': 'ga:campaign'},
                        {'name': 'ga:source'},
                        {'name': 'ga:medium'},
                    ],
                    'dimensionFilterClauses': [
                        {
                            'operator': 'AND',
                            'filters': [
                                {'dimensionName': 'ga:landingPagePath', 'operator': 'REGEXP',
                                 'expressions': FILTER},
                            ],
                        }
                    ],
                    "orderBys": [
                        {
                            "fieldName": "ga:users",
                            "sortOrder": "DESCENDING"
                        }
                    ]
                }]
        }
    ).execute()


def print_response(response, d):
    """Parses and prints the Analytics Reporting API V4 response"""
    f = open(FILENAME_PATTERN % (PREFIX, d), 'w', encoding='utf-8')
    writer = csv.writer(f, lineterminator='\n')

    for report in response.get('reports', []):
        columnHeader = report.get('columnHeader', {})
        dimensionHeaders = columnHeader.get('dimensions', [])
        metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
        rows = report.get('data', {}).get('rows', [])

        temp_header_row = []
        header_row = []
        header_row.extend(dimensionHeaders)
        header_row.extend(['ga:goalStarts' if mh['name'].startswith('ga:goal') else mh['name'] for mh in metricHeaders])
        temp_header_row.extend(header_row)
        temp_header_row = [x[3:] for x in temp_header_row]
        writer.writerow(temp_header_row)

        for row in rows:
            dimensions_data = row.get('dimensions', [])
            dimensions_data[0] = datetime.datetime.strptime(dimensions_data[0], '%Y%m%d').strftime('%Y-%m-%d')
            metrics_data = [m['values'] for m in row.get('metrics', [])][0]

            temp_data_row = []
            data_row = []
            data_row.extend(dimensions_data)
            data_row.extend(metrics_data)

            temp_data_row.extend(data_row)
            writer.writerow(temp_data_row)

        # dimensions = row.get('dimensions', [])
        # dateRangeValues = row.get('metrics', [])

        # for header, dimension in zip(dimensionHeaders, dimensions):
        # print(header + ': ' + dimension)

        # for i, values in enumerate(dateRangeValues):
        #  print('Date range (' + str(i) + ')')
        #  for metricHeader, value in zip(metricHeaders, values.get('values')):
        #    print(metricHeader.get('name') + ': ' + value)
        f.close()


def main():
    analytics = initialize_analyticsreporting()
    # daily breakdown
    for d in date_list:
        print(d)
        dt = d.strftime('%Y-%m-%d')
        response = get_report(analytics, dt)
        print_response(response, dt)
        os.system('gsutil cp %s %s/ga/daily/' % ((FILENAME_PATTERN % (PREFIX, dt)), GA_DEST))


if __name__ == '__main__':
    main()
