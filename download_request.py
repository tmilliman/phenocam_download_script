#!/usr/bin/env python3

import os
import sys
import time
import calendar
import shutil
import requests
import lxml.html
import logging
import re
import http.client as http_client
import argparse
import zipfile
import glob

PHENOCAM_URL = "https://phenocam.sr.unh.edu"
REQUEST_URL = PHENOCAM_URL + "/webcam/network/download/"
LOGIN_URL= PHENOCAM_URL + "/webcam/accounts/login/"



def login(s, username, password):
    if verbose:
            print("GET request for login page")
    response = s.get(LOGIN_URL)
    if verbose:
        print("status: ", response.status_code)
    if response.status_code != 200:
        print("error, got status: {}".format(response.status_code))
        sys.exit(1)
        

    # grab the html from the login page
    login_html = lxml.html.fromstring(response.text)

    # get the hidden inputs
    hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')

    # construct login form data from hidden inputs plus username
    # and password
    form_data = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
    # print("hidden form fields: ", form_data)
    form_data['username'] = username
    form_data['password'] = password
    form_data['submit'] = ""
    form_data['next'] = REQUEST_URL

    # update session referer
    s.headers.update({'referer': LOGIN_URL})

    # submit login form
    if verbose:
        print("POST request to login page")
    response = s.post(LOGIN_URL, data=form_data)
    if verbose:
        print("status: ", response.status_code)

    if response.status_code != 200:
        print("error, got status: {}".format(response.status_code))
        sys.exit(1)

    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Download PhenoCam Images for a Site, Year, Month")
    
    # options
    parser.add_argument("-m","--mirror",
                        help="mirror directory for downloads",
                        action="store_true",
                        default=False )
    

    parser.add_argument("-v","--verbose",
                        help="increase output verbosity",
                        action="store_true",
                        default=False)

    parser.add_argument("-d","--debug",
                        help="log connections for debugging",
                        action="store_true",
                        default=False)

    # positional arguments
    parser.add_argument("site",help="PhenoCam site name")    
    parser.add_argument("year",type=int, help="Year")    
    parser.add_argument("month",type=int, help="Month")    
    parser.add_argument("day",nargs='?' , type=int, help="Day")


    # get env
    mirrorDir = os.getenv('PHENOCAM_MIRROR_DIR')

    # get args
    args = parser.parse_args()

    use_mirror = args.mirror
    verbose = args.verbose
    debug = args.debug
    sitename = args.site
    year = args.year
    month = args.month
    day = args.day



    if use_mirror:
        if not mirrorDir:
            sys.stderr.write('please specifiy environment variable PHENOCAM_MIRROR_DIR')
            sys.exit(1)

        if not os.path.isdir(mirrorDir):
            sys.stderr.write('Mirror directory {} does not exist.\n'.format(mirrorDir))
            sys.exit(1)

    # set up connection logging if verbose
    if debug:
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    if verbose:
        print("sitename: {}".format(sitename))
        print("year: {}".format(year))
        print("month: {}".format(month))
        if day:
            print("day: {}".format(day))
        print("verbose: {}".format(verbose))
        print("debug: {}".format(debug))

    # get phenocam user and password from
    # environment variables
    username = os.getenv('PHENOCAM_USER')
    if username is None:
        sys.stderr.write('Set username in PHENOCAM_USER env var\n')
        sys.exit(1)
    password = os.getenv('PHENOCAM_PASSWD')
    if password is None:
        sys.stderr.write('Set password in PHENOCAM_PASSWD env var\n')
        sys.exit(1)

    # open a web session and login
    with requests.session() as s:


        login(s, username, password)

        

        if day:
            start_date = "{}-{:02d}-{:02d}".format(year, month, day)
            end_date = "{}-{:02d}-{:02d}".format(year, month, day)
        else: 
            start_date = "{}-{:02d}-01".format(year, month)
            last_day = calendar.monthrange(year, month)[1]
            end_date = "{}-{:02d}-{:02d}".format(year, month, last_day)


        if use_mirror:
            mirror_files_directory = os.path.join(mirrorDir,'phenocamdata', sitename, str(year), "{:02d}".format(month))
            
            if os.path.isdir(mirror_files_directory):

                #example: NEON.D19.CARI.DP1.20002_2019_12_20_230006.jpg
                if day:
                    file_prefix = "_".join([sitename, str(year), "{:02d}".format(month), "{:02d}".format(day)])
                else:
                    file_prefix = "_".join([sitename, str(year), "{:02d}".format(month)])

                absoulte_prefix = os.path.join(mirror_files_directory, file_prefix)
                if verbose:
                    print("absoulte_prefix: ", absoulte_prefix)
                zip_file_count = len(glob.glob(absoulte_prefix+"*.jpg"))

                # this does not recognize partial downloads
                if zip_file_count > 0:
                    print("skipping download, files found in ", mirror_files_directory)
                    sys.exit(1)
                

            


        # get download form page
        if verbose:
            print("GET request to download page")
        response = s.get(REQUEST_URL)
        if verbose:
            print("status: ", response.status_code)
        if response.status_code != 200:
            print("error, got status: {}".format(response.status_code))
            sys.exit(1)

        # grab the html from the download page
        download_html = lxml.html.fromstring(response.text)
    
        # get the hidden inputs
        hidden_inputs = download_html.xpath(r'//form//input[@type="hidden"]')

        # construct login form data from hidden inputs plus username
        # and password
        form_data = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
        # prepare POST request for download submission
        form_data = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
        # print("hidden form fields: ", form_data)

        #
        form_data['submit'] = ""
        form_data['site'] = sitename

        
            

        form_data["start_date"] = start_date
        form_data["end_date"] = end_date

        form_data["start_time"] = "00:00"
        form_data["end_time"] = "23:59"
        form_data["ir_flag"] = ""

        # print("form data: ", form_data)
    
        # update session referer
        s.headers.update({'referer': REQUEST_URL})

        if verbose:
            print("POST to download page")
        r = s.post(REQUEST_URL, data=form_data)
        if verbose:
            print("status: {}".format(r.status_code))
        if r.status_code != 200:
            print("error, got status: {}".format(r.status_code))
            sys.exit(1)
        

        # parse page and get script which redirects 
        download_html = lxml.html.fromstring(r.text)
        scripts = download_html.xpath(r'//script')
        if len(scripts) < 4:
            if debug:
                print(r.text)
            sys.stderr.write('Error parsing response\n')
            sys.exit(1)
        redirect_script = scripts[3].text

        # extract redirect URL using regular expressions
        redirect_regex = re.compile('window.location.href = \'(.+)\'}')
        mo = redirect_regex.search(redirect_script)
        if mo == None:
            sys.stderr.write('Extracting redirect url failed\n')
            sys.exit(1)
        redirect_url = mo[1]
        redirect_url = PHENOCAM_URL + redirect_url
        # print('redirect URL: ', redirect_url)

    
        # get URL as a data stream
        if verbose:
            print("Get request to redirect_url "+ redirect_url)
        with s.get(redirect_url, stream=True,
                   allow_redirects=False) as r:


            if use_mirror:
                if day:
                    outfileBase = '{}_{}_{}_{}.zip'.format(sitename, year, month, day)
                else:
                    outfileBase = '{}_{}_{}.zip'.format(sitename, year, month)

                outfile = os.path.join(mirrorDir, outfileBase)
            else:
                # the Content-Disposition header contains the filename
                #
                # e.g.
                # Content-Disposition: attachment; filename*=UTF-8''alligatorriver_phenocam_data_20200110180648.zip
                # 
                cdisposition = r.headers['Content-Disposition']
                outfile = cdisposition.split('\'')[2]

            outfile_part = outfile + ".part"
            print("downloading file {}...".format(outfile))
            with open(outfile_part, 'wb') as f:
                # for chunk in r.iter_content(chunk_size=8192):
                #     if chunk:
                #         f.write(chunk)
                shutil.copyfileobj(r.raw, f)
            
            # final filename only when download complete
            os.rename(outfile_part, outfile)

            if use_mirror:
                print("unzipping {} to {} ...".format(outfile, mirrorDir))
                with zipfile.ZipFile(outfile, 'r') as myzip:
                    myzip.extractall(path=mirrorDir+'/')

                os.remove(outfile)
