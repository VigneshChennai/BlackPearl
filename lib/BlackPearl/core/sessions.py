#!/usr/bin/env python

# This file is part of BlackPearl.

# BlackPearl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BlackPearl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import time
import pickle
import logging

from http.cookies import SimpleCookie
from BlackPearl.common.security import encrypt, decrypt

logger = logging.getLogger(__name__)


# The below two variables will be initialized during the start of uwsgi
BLOCK_SIZE = 0
AES_KEY = ""


class Session:
    def __init__(self):
        self.created = time.time()
        self.last_accessed = time.time()

    def accessed(self):
        self.last_accessed = time.time()


def decode_session(session_b64_enc):
    if session_b64_enc:
        return pickle.loads(decrypt(session_b64_enc, AES_KEY=AES_KEY, BLOCK_SIZE=BLOCK_SIZE))
    return None


def encode_session(session):
    if session:
        session_bytes = pickle.dumps(session)
        return encrypt(session_bytes, AES_KEY=AES_KEY, BLOCK_SIZE=BLOCK_SIZE)


def parse_session(environ):
    # session.__status__ attribute can have one among the below three
    # values
    #
    # session.__status__ = "fetched" --> When the session is not expired
    # session.__status__ = "recreated" --> When the session is expired
    # session.__status__ = "created" --> When the session is not

    cookie = SimpleCookie()
    cookie.load(environ.get("HTTP_COOKIE", ""))

    try:
        cookie = SimpleCookie()
        cookie.load(environ.get("HTTP_COOKIE", ""))

        # trying to get the cookie encrypted "session" from the cookie object
        # if not there, exception raised
        session_b64_enc = cookie["session"].value

        # trying to decode the encrypted session value
        session = decode_session(session_b64_enc)

        # if the session is None, then "session' value in the cookie
        # is invalid or it got expired.
        if not session:
            session = Session()
            session.__status__ = "recreated"
        else:
            session.__status__ = "fetched"
    except:
        # When there is not session value in cookie,
        # new session cookie is created.
        session = Session()
        session.__status__ = "created"

    return session