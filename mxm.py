"""
MXM JSON API Client

v2.0
"""

import urlparse
import json
import socket
import base64
import urllib
import sys
import re

class Api:

    def __init__(self, host, username, password, useSsl = True):
        self._host     = host
        self._username = username
        self._password = password
        self._useSsl   = useSsl
        self._services = {}

    def _getInstance(self, service):
        if service not in self._services:
            serviceConfig = {
                'service'  : service,
                'host'     : self._host,
                'username' : self._username,
                'password' : self._password,
                'useSsl'   : self._useSsl
            }
            self._services[service] = self.JsonClient(**serviceConfig)
        return  self._services[service]

    def __getattr__(self, name):
        return self._getInstance(name)

    def __repr__(self):
        return "%s(host='%s')" % (self.__class__, self._host)

    class JsonClient:

        def __init__(self, service, host, username, password, useSsl):
            self._service  = service
            self._host     = host
            self._username = username
            self._password = password
            self._useSsl   = useSsl

            self._lastRequest  = None
            self._lastResponse = None

        def getLastRequest(self):
            return self._lastRequest

        def getLastResponse(self):
            return self._lastResponse

        def _postRequest(self, data):
            host = ('ssl://' if self._useSsl else '') + self._host
            port = 443 if self._useSsl else 80
            s = self._createSocket(host, port)

            basicAuth = base64.b64encode(self._username + ':' + self._password)
            body = urllib.urlencode(data)

            headers = {
                'Host'           : self._host,
                'Connection'     : 'close',
                'Authorization'  : "Basic %s" % (basicAuth),
                'Content-type'   : 'application/x-www-form-urlencoded',
                'Content-length' : len(body),
                'User-Agent'      : "MxmJsonClient/2.0 Python/"
            }
            request = "POST /api/json/%s HTTP/1.0\r\n" % (self._service)
            for key in headers:
                request += "%s: %s\r\n" % (key, headers[key])

            request += "\r\n%s" % (body)
            self._lastRequest = request

            s.sendall(request)

            return self._handleResponse(s)

        def _handleResponse(self, s):
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

        def _createSocket(self, host, port):
            s = None
            for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
                af, socktype, proto, canonname, sa = res
                try:
                    s = socket.socket(af, socktype, proto)
                except socket.error as msg:
                    s = None
                    continue
                try:
                    s.connect(sa)
                except socket.error as msg:
                    s.close()
                    s = None
                    continue
                break
            if s is None:
                raise Exception('Could not open socket')
            return s

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
            return "%s(service='%s',host='%s')" % (self.__class__, self._service, self._host)
