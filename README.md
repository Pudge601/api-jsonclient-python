Maxemail JSON Client (Python)
=============================

Self contained JSON client in Python for simplifying access to the Maxemail API

Usage Example
-------------
```python
# Instantiate Client:
import mxm
config = {
    'host'     :'maxemail.emailcenteruk.com',
    'username' :'api@user.com',
    'password' :'apipass'
}
client = mxm.Api(**config)


# General:
result = client.serviceName.method(arg1, arg2)
print result
```
