#!/usr/bin/env python

#This file is part of BlackPearl.

#BlackPearl is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#BlackPearl is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with BlackPearl.  If not, see <http://www.gnu.org/licenses/>.

import base64
import os

from Crypto.Cipher import AES

BLOCK_SIZE=None
AES_KEY=None

PADDING = b"{"

def encrypt(privateInfo):
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    # encrypt with AES, encode with base64
    EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
    cipher = AES.new(AES_KEY)
    encoded = EncodeAES(cipher, privateInfo)
    return encoded

def decrypt(encryptedString):
    DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
    cipher = AES.new(AES_KEY)
    decoded = DecodeAES(cipher, encryptedString)
    return decoded
