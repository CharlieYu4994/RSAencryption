from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import pss
from Crypto.Hash import SHA256
import sqlite3


# ------------------------------------BASIC Encrypt Part---------------------------------- #
def pkcs7padding(_data: bytes, _block_size: int) -> bytes:
    _padding_size = _block_size - len(_data) % _block_size
    return _data + chr(_padding_size).encode() * _padding_size

def pkcs7unpadding(_data: bytes) -> bytes:  # 去填充
    _length = len(_data)
    return _data[0:_length - int(_data[-1])] 

def aes_encrypt(_key: bytes, _data: bytes, _pad=True) -> bytes:
    _cipher = AES.new(_key, AES.MODE_CBC, _key[0:16])
    return _cipher.encrypt(pkcs7padding(_data, AES.block_size) if _pad else _data)

def aes_decrypt(_key: bytes, _data: bytes, _pad=True) -> bytes:
    _cipher = AES.new(_key, AES.MODE_CBC, _key[0:16])
    return pkcs7unpadding(_cipher.decrypt(_data)) if _pad else _cipher.decrypt(_data)

def rsa_decrypt(_prikey, _data: bytes) -> bytes:
    _cipher = PKCS1_OAEP.new(_prikey)
    return _cipher.decrypt(_data)

def rsa_encrypt(_pubkey, _data: bytes) -> bytes:
    _cipher = PKCS1_OAEP.new(_pubkey)
    return _cipher.encrypt(_data)

def gen_rsakey(_length: int, _passphrase: str) -> bytes:
    _key = RSA.generate(_length)
    return _key.export_key(passphrase=_passphrase if _passphrase else None),\
           _key.publickey().export_key()

def load_key(_pubkey: bytes, _prikey=None, _passphrase=None):
    if _prikey:
        try:
            _pubkey = RSA.import_key(_pubkey)
            _prikey = RSA.import_key(_prikey, passphrase=_passphrase if _passphrase else None)
        except Exception as E: return False, str(E), ''
        else: return True, _prikey, _pubkey
    else: return RSA.import_key(_pubkey)

def composite_decrypt(_prikey, _data: bytes, _session_key: bytes) -> bytes:
    _session_key = rsa_decrypt(_prikey, _session_key)
    return aes_decrypt(_session_key, _data)

def composite_encrypt(_pubkey, _data: bytes, _session_key=None) -> bytes:
    _session_key = _session_key if _session_key else get_random_bytes(16)
    return rsa_encrypt(_pubkey, _session_key), aes_encrypt(_session_key, _data)

def pss_sign(_prikey, _data: bytes, _hash=None) -> bytes:
    _hash = _hash if _hash else SHA256.new(_data)
    return pss.new(_prikey).sign(_hash)

def pss_verify(_pubkey, _data: bytes, _signature: bytes, _hash=None) -> bool:
    _verifier = pss.new(_pubkey)
    _hash = _hash if _hash else SHA256.new(_data)
    try:
        _verifier.verify(_hash, _signature)
        return True
    except Exception as E:
        return False

# ---------------------------------------Database Part------------------------------------ #
def gen_database():
    _db = sqlite3.connect('keyring.db')
    _cursor = _db.cursor()
    _cursor.execute("""CREATE TABLE UserKeys(
				ID           INTEGER PRIMARY KEY,
				PubKey       TEXT    NOT NULL,
				PriKey       TEXT    NOT NULL,
				Describe     CHAR(50)         );""")
    _cursor.execute("""CREATE TABLE ThirdKeys(
				ID           INTEGER PRIMARY KEY,
				PubKey       TEXT    NOT NULL,
				Describe     CHAR(20)NOT NULL );""")
    _cursor.execute("""CREATE TABLE Others(
                ID           INTEGER PRIMARY KEY,
                Settings     TEXT    NOT NULL)""")
    _db.commit()
    _db.close()

def add_userkey(_prikey: bytes, _pubkey: bytes, _describe: str, _db):
    _cursor = _db.cursor()
    _cursor.execute(f"INSERT INTO UserKeys (PubKey, PriKey, Describe) \
			      VALUES ('{_pubkey.decode()}', '{_prikey.decode()}', '{_describe}')")
    _db.commit()

def add_pubkey(_pubkey: bytes, _describe: str, _db):
    _cursor = _db.cursor()
    _cursor.execute(f"INSERT INTO ThirdKeys (PubKey, Describe) \
			      VALUES ('{_pubkey.decode()}', '{_describe}')")
    _db.commit()

def del_key(_id: int, _table: str, _db):
    _cursor = _db.cursor()
    _cursor.execute(f"DELETE FROM '{_table}' WHERE id = {_id}")
    _db.commit()

def get_keydict(_table: str, _db) -> dict:
    _keydict = dict()
    _cursor = _db.cursor()
    for row in _cursor.execute(f"SELECT ID, Describe FROM '{_table}'").fetchall():
        _keydict[f'{row[1]} ({str(row[0])})'] = row[0]
    return _keydict

def get_userkey(_id: int, _db) -> bytes:
    _cursor = _db.cursor()
    _pubkey, _prikey = _cursor.execute(f"SELECT PubKey, PriKey FROM UserKeys \
                                         WHERE ID = '{_id}'").fetchall()[0]
    return _prikey.encode(), _pubkey.encode()

def get_thirdkey(_id: int, _db) -> bytes:
    _cursor = _db.cursor()
    _cursor.execute(f"SELECT PubKey FROM ThirdKeys WHERE ID = '{_id}'")
    return _cursor.fetchall()[0][0].encode()

def get_cfg(_db):
    _cursor = _db.cursor()
    _cursor.execute(f"SELECT Settings FROM Others WHERE ID = '{_id}'")
    return _cursor.fet

# -----------------------------------------Other Part------------------------------------- #
def read_file(_path: str, _seek: int):
    BLOCK_SIZE = 1048576
    with open(_path, 'rb') as f:
        if _seek: f.seek(_seek, 0)
        while True:
            block = f.read(BLOCK_SIZE)
            if block: yield block, len(block) != BLOCK_SIZE
            else: return

# --------------------------------------------Debug--------------------------------------- #
if __name__ == '__main__':
    pass
