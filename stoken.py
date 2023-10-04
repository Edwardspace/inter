from itsdangerous import URLSafeTimedSerializer
from key import salt,secretkey
def token(data):
    serializer=URLSafeTimedSerializer(secretkey)
    return serializer.dumps(data,salt=salt)

