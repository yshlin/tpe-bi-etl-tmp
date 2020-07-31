import datetime
import datedelta
import os

from config import GP_DEST, GP_SOURCE

today = datetime.datetime.today()
month_list = [today - datedelta.datedelta(months=x) for x in range(3)]


def extract_load_gcs(src, prefix, dst):
    for month in month_list:
        mo = month.strftime('%Y%m')
        os.system('gsutil cp %s%s%s_country.csv ./gp/' % (src, prefix, mo))
        os.system('gsutil cp %s%s%s_utm_tagged.csv ./gp/' % (src, prefix, mo))
        os.system('iconv -f utf-16 -t utf-8 ./gp/%s%s_country.csv > ./gp/%s%s_country_utf8.csv' % (prefix, mo, prefix, mo))
        os.system('iconv -f utf-16 -t utf-8 ./gp/%s%s_utm_tagged.csv > ./gp/%s%s_utm_tagged_utf8.csv' % (prefix, mo, prefix, mo))
        os.system('file -I ./gp/%s%s_country_utf8.csv' % (prefix, mo))
        os.system('file -I ./gp/%s%s_utm_tagged_utf8.csv' % (prefix, mo))
        os.system('gsutil cp ./gp/%s%s_country_utf8.csv %s' % (prefix, mo, dst))
        os.system('gsutil cp ./gp/%s%s_utm_tagged_utf8.csv %s' % (prefix, mo, dst))


extract_load_gcs(GP_SOURCE, 'retained_installers_org.mozilla.firefox.vpn_', '%s/mozvpn/gp/' % GP_DEST)
extract_load_gcs(GP_SOURCE, 'retained_installers_org.mozilla.rocket_', '%s/mango/gp/' % GP_DEST)
