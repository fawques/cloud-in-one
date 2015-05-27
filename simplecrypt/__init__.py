import tempfile
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, HMAC
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random.random import getrandbits
from Crypto.Util import Counter

# see: http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

EXPANSION_COUNT = (10000, 10000, 100000)
AES_KEY_LEN = 256
SALT_LEN = (128, 256, 256)
HASH = SHA256
PREFIX = b'sc'
HEADER = (PREFIX + b'\x00\x00', PREFIX + b'\x00\x01', PREFIX + b'\x00\x02')
LATEST = 2   # index into SALT_LEN, EXPANSION_COUNT, HEADER

# lengths here are in bits, but pcrypto uses block size in bytes
HALF_BLOCK = AES.block_size*8//2
for salt_len in SALT_LEN:
    assert HALF_BLOCK <= salt_len  # we use a subset of the salt as nonce

HEADER_LEN = 4
for header in HEADER:
    assert len(header) == HEADER_LEN

CHUNKSIZE = 100 * 1024 * 1024


def encrypt(password, data):
    '''
    Encrypt some data.  Input can be bytes or a string (which will be encoded
    using UTF-8).

    @param password: The secret value used as the basis for a key.
    This should be as long as varied as possible.  Try to avoid common words.

    @param data: The data to be encrypted.

    @return: The encrypted data, as bytes.
    '''
    return _encrypt_internal(password, data)[0]


def encrypt_file(password, infile):
    '''
    Encrypt some file.  Input must be a file-like object.

    @param password: The secret value used as the basis for a key.
    This should be as long as varied as possible.  Try to avoid common words.

    @param infile: The file to be encrypted.

    @return: A temporary file-like object with the encrypted data.
    '''
    cipher = None

    outfile = tempfile.TemporaryFile()

    while True:
        chunk = infile.read(CHUNKSIZE)
        if len(chunk) == 0:
            break
        encrypted, cipher = _encrypt_internal(password, chunk, cipher)
        outfile.write(encrypted)

    outfile.seek(0)
    return outfile


def decrypt(password, data):
    '''
    Decrypt some data.  Input must be bytes.

    @param password: The secret value used as the basis for a key.
    This should be as long as varied as possible.  Try to avoid common words.

    @param data: The data to be decrypted, typically as bytes.

    @return: The decrypted data, as bytes.  If the original message was a
    string you can re-create that using `result.decode('utf8')`.
    '''
    return _decrypt_internal(password, data)[0]


def decrypt_file(password, infile):
    '''
    Decrypt some file.  Input must be a file-like object.

    @param password: The secret value used as the basis for a key.
    This should be as long as varied as possible.  Try to avoid common words.

    @param infile: The file to be decrypted, a file-like object.

    @return: A temporary file-like object with the decrypted data.
    The file position is reset to 0.
    '''
    cipher = None

    outfile = tempfile.TemporaryFile()

    while True:
        # adding the overhead of the encryption
        chunk = infile.read(CHUNKSIZE + 68)
        if len(chunk) == 0:
            break
        decrypted, cipher = _decrypt_internal(password, chunk, cipher)
        outfile.write(decrypted)

    outfile.seek(0)
    return outfile


def _encrypt_internal(password, data, cipher=None):
    data = _str_to_bytes(data)
    _assert_encrypt_length(data)
    salt = bytes(_random_bytes(SALT_LEN[LATEST]//8))
    hmac_key, cipher_key = _expand_keys(password, salt, EXPANSION_COUNT[LATEST])
    counter = Counter.new(HALF_BLOCK, prefix=salt[:HALF_BLOCK//8])
    if not cipher:
        cipher = AES.new(cipher_key, AES.MODE_CTR, counter=counter)
    encrypted = cipher.encrypt(data)
    hmac = _hmac(hmac_key, HEADER[LATEST] + salt + encrypted)
    return (HEADER[LATEST] + salt + encrypted + hmac, cipher)


def _decrypt_internal(password, data, cipher=None):
    _assert_not_unicode(data)
    _assert_header_prefix(data)
    version = _assert_header_version(data)
    _assert_decrypt_length(data, version)
    raw = data[HEADER_LEN:]
    salt = raw[:SALT_LEN[version]//8]
    hmac_key, cipher_key = _expand_keys(password, salt, EXPANSION_COUNT[version])
    hmac = raw[-HASH.digest_size:]
    hmac2 = _hmac(hmac_key, data[:-HASH.digest_size])
    _assert_hmac(hmac_key, hmac, hmac2)
    counter = Counter.new(HALF_BLOCK, prefix=salt[:HALF_BLOCK//8])
    if not cipher:
        cipher = AES.new(cipher_key, AES.MODE_CTR, counter=counter)
    return (cipher.decrypt(raw[SALT_LEN[version]//8:-HASH.digest_size]), cipher)


class DecryptionException(Exception): pass
class EncryptionException(Exception): pass


def _assert_not_unicode(data):
    # warn confused users
    u_type = type(b''.decode('utf8'))
    if isinstance(data, u_type):
        raise DecryptionException('Data to decrypt must be bytes; ' +
        'you cannot use a string because no string encoding will accept all possible characters.')

def _assert_encrypt_length(data):
    # for AES this is never going to fail
    if len(data) > 2**HALF_BLOCK:
        raise EncryptionException('Message too long.')

def _assert_decrypt_length(data, version):
    if len(data) < HEADER_LEN + SALT_LEN[version]//8 + HASH.digest_size:
        raise DecryptionException('Missing data.')

def _assert_header_prefix(data):
    if len(data) >= 2 and data[:2] != PREFIX:
        raise DecryptionException('Data passed to decrypt were not generated by simple-crypt (bad header).')

def _assert_header_version(data):
    if len(data) >= HEADER_LEN:
        try:
            return HEADER.index(data[:HEADER_LEN])
        except:
            raise DecryptionException(
                'The data appear to be encrypted with a more recent version of simple-crypt (bad header). ' +
                'Please update the library and try again.')
    else:
        raise DecryptionException('Missing header.')

def _assert_hmac(key, hmac, hmac2):
    # https://www.isecpartners.com/news-events/news/2011/february/double-hmac-verification.aspx
    if _hmac(key, hmac) != _hmac(key, hmac2):
        raise DecryptionException('Bad password or corrupt / modified data.')

def _pbkdf2(password, salt, n_bytes, count):
    # the form of the prf below is taken from the code for PBKDF2
    return PBKDF2(password, salt, dkLen=n_bytes,
                  count=count, prf=lambda p,s: HMAC.new(p,s,HASH).digest())

def _expand_keys(password, salt, expansion_count):
    if not salt: raise ValueError('Missing salt.')
    if not password: raise ValueError('Missing password.')
    key_len = AES_KEY_LEN // 8
    keys = _pbkdf2(_str_to_bytes(password), salt, 2*key_len, expansion_count)
    return keys[:key_len], keys[key_len:]

def _hide(ranbytes):
    # appelbaum recommends obscuring output from random number generators since it can reveal state.
    # we can do this explicitly with a hash, but this is what a PBKDF does anyway, so use one.
    # we don't care about the salt or work factor because there is a large space of values anyway.
    return bytearray(_pbkdf2(bytes(ranbytes), b'', len(ranbytes), 1))

def _random_bytes(n):
    return _hide(bytearray(getrandbits(8) for _ in range(n)))

def _hmac(key, data):
    return HMAC.new(key, data, HASH).digest()

def _str_to_bytes(data):
    u_type = type(b''.decode('utf8'))
    if isinstance(data, u_type):
        return data.encode('utf8')
    return data
