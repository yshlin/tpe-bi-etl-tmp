import datetime
import datedelta
import os

from config import GP_DEST, GP_SOURCE, GP_BUILD_ID_SRC

today = datetime.datetime.today()
month_list = [today - datedelta.datedelta(months=x) for x in range(3)]


def extract_load_gcs(src, prefix, dst):
    for month in month_list:
        mo = month.strftime('%Y%m')
        os.system('gsutil cp %s%s%s_country.csv ./gp/' % (src, prefix, mo))
        if os.path.exists('./gp/%s%s_country.csv' % (prefix, mo)) and os.stat('./gp/%s%s_country.csv' % (prefix, mo)).st_size > 0:
            os.system('iconv -f utf-16 -t utf-8 ./gp/%s%s_country.csv > ./gp/%s%s_country_utf8.csv' % (prefix, mo, prefix, mo))
            os.system('file -I ./gp/%s%s_country_utf8.csv' % (prefix, mo))
            os.system('gsutil cp ./gp/%s%s_country_utf8.csv %s' % (prefix, mo, dst))
        else:
            print('./gp/%s%s_country.csv does not exists!' % (prefix, mo))
        os.system('gsutil cp %s%s%s_utm_tagged.csv ./gp/' % (src, prefix, mo))
        if os.path.exists('./gp/%s%s_utm_tagged.csv' % (prefix, mo)) and os.stat('./gp/%s%s_utm_tagged.csv' % (prefix, mo)).st_size > 0:
            os.system('iconv -f utf-16 -t utf-8 ./gp/%s%s_utm_tagged.csv > ./gp/%s%s_utm_tagged_utf8.csv' % (prefix, mo, prefix, mo))
            os.system('file -I ./gp/%s%s_utm_tagged_utf8.csv' % (prefix, mo))
            os.system('gsutil cp ./gp/%s%s_utm_tagged_utf8.csv %s' % (prefix, mo, dst))
            print('./gp/%s%s_country.s_utm_tagged does not exists!' % (prefix, mo))


extract_load_gcs(GP_SOURCE, 'retained_installers_org.mozilla.firefox.vpn_', '%s/mozvpn/gp/' % GP_DEST)
extract_load_gcs(GP_SOURCE, 'retained_installers_org.mozilla.rocket_', '%s/mango/gp/' % GP_DEST)
os.system('curl -o ./build_ids.csv %s' % GP_BUILD_ID_SRC)
os.system('gsutil cp ./build_ids.csv %s/mango/' % GP_DEST)
