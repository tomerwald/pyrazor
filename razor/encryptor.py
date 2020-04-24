from Crypto.Cipher import AES


class AESCipher:
    BS = 32

    def __init__(self, key, nonce):
        self.key = key
        self.nonce = nonce

    def encrypt(self, raw):
        raw = self.pad(raw)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=self.nonce)
        return cipher.encrypt(raw)

    def decrypt(self, enc):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=self.nonce)
        c = cipher.decrypt(enc)
        return self.unpad(c)

    def unpad(self, s):
        return s[0:-ord(s[-1:])]

    def pad(self, s):
        padding_amount = self.BS - (len(s) % self.BS)
        return s + bytes(chr(padding_amount) * padding_amount, 'utf-8')
