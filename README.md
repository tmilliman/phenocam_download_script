# phenocam_download_script

Simple python script to automate image downloads.

    usage: download_request.py [-h] [-v] [-d] site year month [day]
    
    Download PhenoCam Images for a site, year, month and optionally day-of-month.
    
    positional arguments:
      site           PhenoCam site name
      year           Year [2000-present year]
      month          Month [1-12]
      day            optional day of Month, if omitted download entire month
    
    optional arguments:
      -h, --help      show this help message and exit
      -v, --verbose   increase output verbosity
      -d, --debug     log connections for debugging
      -i, --infrared  get infrared images only

The script reads two environment variables:

    PHENOCAM_USER
    PHENOCAM_PASSWD

which provide the login credentials for initiating the download.  As
with the download tool on the web site, downloads are limited to 2GB
but for most sites this is sufficient to download a month's worth of
data.
