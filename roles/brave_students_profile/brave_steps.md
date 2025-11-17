BRAVE

## Install
curl -fsS https://dl.brave.com/install.sh | sh

## Set as default browser
xdg-settings set default-web-browser brave-browser.desktop

## Policies
https://support.brave.app/hc/en-us/articles/360039248271-Group-Policy?policy=BrowserThemeColor


mkdir -p /etc/brave/policies/managed/


### Blocklist
bgi@laptop-asus:/etc/brave/policies/managed $ cat lock.json
{
  "URLBlocklist": [
    "tiktok.com",
    "brave://settings",
    "brave://extensions",
    "chrome://settings",
    "chromewebstore.google.com"
  ]
}

{
  "URLBlocklist": [
    "tiktok.com",
    "brave://*",
    "brave://extensions",
    "chrome://settings",
    "chromewebstore.google.com"
  ]
}

TODO : search engines



### SafeSearch
Open Terminal.
Enter the command ping forcesafesearch.google.com.

Note the IP address.
Example IP address: 216.239.38.120.
Enter the command sudo nano /etc/hosts.
Create an entry at the end of the hosts file with the IP address that you obtained. For example: 216.239.38.120 www.google.com #forcesafesearch.
Copy this line for any other Google country or region domains that your users may use, like www.google.co.uk.

### NewTab
/* If you want a *plain colour* instead of white, point to a tiny local
   HTML file you create once, e.g. file:///usr/share/brave/ntp-dark.html
   with:  <body style="margin:0;background:#202124"></body>   


##