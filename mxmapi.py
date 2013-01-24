"""
MXM JSON API Client

v1.0

@category   Mxm
@module     mxmapi
@copyright  Copyright (c) 2007-2012 Emailcenter UK. (http://www.emailcenteruk.com)
@license    Commercial

"""

import urlparse
import json
import socket
import ssl
import base64
import urllib
import sys
import re

class JsonClient:

    def __init__(self, **config):
        self._url = config['url'].rstrip('/') + '/api/json/'
        self._username = config['user']
        self._password = config['pass']
        self._services = {}

    def _getInstance(self, service):
        if service not in self._services:
            url = self._url + service
            self._services[service] = self.Client(url, self._username, self._password)
        return  self._services[service]

    def __getattr__(self, name):
        return self._getInstance(name)

    def __repr__(self):
        return "%s(url='%s',user='%s',pass='%s')" % (self.__class__, self._url, self._username, self._password)

    class Client:

        def __init__(self, url, username, password):
            self._url = url
            parts = urlparse.urlparse(url)
            self._scheme = parts.scheme
            self._host = parts.netloc
            self._path = parts.path
            self._username = username
            self._password = password
            self._lastRequest = None
            self._lastResponse = None

        def _postRequest(self, data):
            useSSL = self._scheme.lower() == 'https'
            port = 443 if useSSL else 80
            host = self._host

            basicAuth = base64.b64encode(self._username + ':' + self._password)
            body = urllib.urlencode(data)

            headers = {
                'Host' : self._host,
                'Connection' : 'close',
                'Authorization' : "Basic %s" % (basicAuth),
                'Content-type' : 'application/x-www-form-urlencoded',
                'Content-length' : len(body),
                'User-Agent' : "MxmJsonClient/1.0a Python/"
            }
            request = "POST %s HTTP/1.0\r\n" % (self._path)
            for key in headers:
                request += "%s: %s\r\n" % (key, headers[key])

            request += "\r\n%s" % (body)
            self._lastRequest = request

            s = None
            for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
                af, socktype, proto, canonname, sa = res
                try:
                    s = socket.socket(af, socktype, proto)
                except socket.error as msg:
                    s = None
                    continue
                if useSSL:
                    s = ssl.wrap_socket(s)
                try:
                    s.connect(sa)
                except socket.error as msg:
                    s.close()
                    s = None
                    continue
                break
            if s is None:
                raise Exception('Could not open socket')

            s.sendall(request)

            response = ''
            while 1:
                data = s.recv(1024)
                if not data: break
                response += data
            s.close()

            self._lastResponse = response

            matches = re.match("^HTTP\/[\d\.x]+ (\d+)", response)
            code = int(matches.group(1))

            parts = re.split('(?:\r?\n){2}', response, 2)
            content = parts[1]

            if code != 200:
                try:
                    message = self._decodeJson(content)
                    if 'msg' in message:
                        content = message['msg']
                except Exception:
                    pass

                raise Exception("%s (%d)" % (content, code))

            return content   

        def getLastRequest(self):
            return self._lastRequest

        def getLastResponse(self):
            return self._lastResponse

        def _decodeJson(self, string):
            try:
                result = json.loads(string)
            except Exception, e:
                raise Exception('Problem decoding json (%s), %s' % (string, e))
            return result


        def __getattr__(self, name):
            data = {'method': name}
            def function(*args):
                i = 0
                for arg in args:
                    if (isinstance(arg, (list, tuple, dict))):
                        data['arg' + str(i)] = json.dumps(arg)
                    else:
                        data['arg' + str(i)] = arg
                    i += 1
                result = self._postRequest(data)
                return self._decodeJson(result)
            return function

        def __repr__(self):
            return "%s('%s','%s','%s')" % (self.__class__, self._url, self._username, self._password)