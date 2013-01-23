Maxemail JSON Client (Python)
=============================

Self contained JSON client in Python for simplifying access to the Maxemail API

Usage Example
-------------
```python
# Instantiate Client:
import mxmapi
config = {
    'url':'https://maxemail.emailcenteruk.com/',
    'user':'api@user.com',
    'pass':'apipass'
}
client = mxmapi.JsonClient(**config)
 
 
# General:
result = client.serviceName.method(arg1, arg2)
print result
```
