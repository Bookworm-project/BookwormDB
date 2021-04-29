



def apache(self = None):
    print("""
    Instructions for Apache:


    First: Serve the Bookworm API over port 10012. (`bookworm serve`).

    Then: Install an Apache host on port 80.

    Then: enable proxy servers and turn off any existing cgi.

    # If you were previously using the CGI bookworm.
    `sudo a2dismod cgi`

    `sudo a2enmod proxy proxy_ajp proxy_http rewrite deflate headers proxy_balancer proxy_connect proxy_html`

    Then: Add the following to your '/etc/apache2/sites-available/000-default.conf'
    (or whatever site from which you run your apache.

    ~~~~~~~~~~~~~~~~

    <Proxy *>
      Order deny,allow
      Allow from all
    </Proxy>
      ProxyPreserveHost On
    <Location "/cgi-bin">
      ProxyPass "http://127.0.0.1:10012/"
      ProxyPassReverse "http://127.0.0.1:10012/"
    </Location>

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


""")
