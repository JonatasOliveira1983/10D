from py_vapid import Vapid
v = Vapid()
keys = v.generate_keys()
# The keys are objects, need to extract PEM or similar?
# Actually, pywebpush expects Base64 encoded keys.
import base64

# v.save_key("private.pem") # Alternative
# Let's just get the raw keys
private_key = v.private_key.private_bytes(
    encoding=Vapid.Encoding.PEM,
    format=Vapid.PrivateFormat.PKCS8,
    encryption_algorithm=Vapid.NoEncryption()
).decode()

# This is getting complicated. 
# Let's try the most common library way:
from pywebpush import vapid_external
# Wait, I tried this and it failed.
