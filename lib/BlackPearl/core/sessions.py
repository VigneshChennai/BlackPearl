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

from BlackPearl.common.security import encrypt, decrypt

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