# coding: utf-8

import BaseHTTPServer
import urlparse


def http_authorise(url, oauth_key='oauth_verifier', port=8888):
    import webbrowser

    webbrowser.open(url)

    class ServerRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        code = None
        key = oauth_key

        def echo_html(self, content):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(content)
            self.wfile.close()

        def do_GET(self):
            if ServerRequestHandler.key is not None:
                qs = urlparse.parse_qs(urlparse.urlsplit(self.path).query)
                if ServerRequestHandler.key in qs:
                    ServerRequestHandler.code = qs[self.key][0]
            else:
                ServerRequestHandler.code = True
            if ServerRequestHandler.code:
                self.echo_html('''<html>
    <head>
    <meta charset="utf-8"/>
    <title>OK</title>
    </head>
    <body>Succeed.</body>
    </html> ''')

    httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', port), ServerRequestHandler)
    httpd.handle_request()
    while ServerRequestHandler.code is None:
        pass
    httpd.server_close()

    return ServerRequestHandler.code
