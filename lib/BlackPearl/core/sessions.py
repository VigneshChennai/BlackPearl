#!/usr/bin/env python

import time
import os
import base64
import pickle

from Crypto.Cipher import AES

BLOCK_SIZE=int(os.environ['BLOCK_SIZE'])
SESS_AES_KEY=os.environ['SESS_AES_KEY']
PADDING = b"{"

class Session:
    def __init__(self, webapp):
        self.created = time.time()
        self.lastaccessed = time.time()

    def accessed():
        self.lastaccessed = time.time()

def decode_session(session_b64_enc):
    if session_b64_enc:
        return pickle.loads(decrypt(session_b64_enc))
    return None

def encode_session(session):
    if session:
        session_bytes = pickle.dumps(session)
        return encrypt(session_bytes)

def encrypt(privateInfo):
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    # encrypt with AES, encode with base64
    EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
    cipher = AES.new(SESS_AES_KEY)
    encoded = EncodeAES(cipher, privateInfo)
    return encoded

def decrypt(encryptedString):
    DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
    cipher = AES.new(SESS_AES_KEY)
    decoded = DecodeAES(cipher, encryptedString)
    return decoded

