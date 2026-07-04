"""
Pure Python a_bogus signature generator for Douyin (抖音).

Implements the complete a_bogus algorithm:
  1. SM3 cryptographic hash (GM/T 0004-2012)
  2. RC4 encryption
  3. Custom Base64 encoding with dual alphabet

Based on the open-source implementations from:
  - mafqla/douyin-api
  - ShilongLee/Crawler
  - jiji262/douyin-downloader

Reference: GM/T 0004-2012 SM3 Cryptographic Hash Algorithm
"""

import time
import random
from struct import pack, unpack


# ── SM3 Hash Implementation ──

# Initial values (IV)
SM3_IV = [
    0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
    0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E,
]

# Permutation functions
def _sm3_ff0(x, y, z): return x ^ y ^ z
def _sm3_ff1(x, y, z): return (x & y) | (x & z) | (y & z)
def _sm3_gg0(x, y, z): return x ^ y ^ z
def _sm3_gg1(x, y, z): return (x & y) | (~x & z)

def _sm3_p0(x): return x ^ _sm3_rotl(x, 9) ^ _sm3_rotl(x, 17)
def _sm3_p1(x): return x ^ _sm3_rotl(x, 15) ^ _sm3_rotl(x, 23)

def _sm3_rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

# Constants
SM3_T = [0x79CC4519] * 16 + [0x7A879D8A] * 48


def sm3_hash(message: bytes) -> bytes:
    """Compute SM3 hash of a message. Returns 32-byte digest."""
    # Padding
    msg_len = len(message)
    message += b'\x80'
    while (len(message) % 64) != 56:
        message += b'\x00'
    message += pack('>Q', msg_len * 8)

    # Initialize hash
    v = list(SM3_IV)

    # Process blocks
    for i in range(0, len(message), 64):
        block = message[i:i + 64]
        w = list(unpack('>16I', block))
        w1 = [0] * 68
        w1[:16] = w

        for j in range(16, 68):
            w1[j] = (_sm3_p1(w1[j - 16] ^ w1[j - 9] ^ _sm3_rotl(w1[j - 3], 15))
                     ^ _sm3_rotl(w1[j - 13], 7) ^ w1[j - 6]) & 0xFFFFFFFF

        w2 = [0] * 64
        for j in range(64):
            w2[j] = w1[j] ^ w1[j + 4]

        a, b, c, d, e, f, g, h = v

        for j in range(64):
            ss1 = _sm3_rotl((_sm3_rotl(a, 12) + e + _sm3_rotl(SM3_T[j], j % 32)) & 0xFFFFFFFF, 7)
            ss2 = ss1 ^ _sm3_rotl(a, 12)

            if j < 16:
                tt1 = (_sm3_ff0(a, b, c) + d + ss2 + w2[j]) & 0xFFFFFFFF
                tt2 = (_sm3_gg0(e, f, g) + h + ss1 + w1[j]) & 0xFFFFFFFF
            else:
                tt1 = (_sm3_ff1(a, b, c) + d + ss2 + w2[j]) & 0xFFFFFFFF
                tt2 = (_sm3_gg1(e, f, g) + h + ss1 + w1[j]) & 0xFFFFFFFF

            d = c
            c = _sm3_rotl(b, 9)
            b = a
            a = tt1
            h = g
            g = _sm3_rotl(f, 19)
            f = e
            e = _sm3_p0(tt2)

        v[0] = (v[0] ^ a) & 0xFFFFFFFF
        v[1] = (v[1] ^ b) & 0xFFFFFFFF
        v[2] = (v[2] ^ c) & 0xFFFFFFFF
        v[3] = (v[3] ^ d) & 0xFFFFFFFF
        v[4] = (v[4] ^ e) & 0xFFFFFFFF
        v[5] = (v[5] ^ f) & 0xFFFFFFFF
        v[6] = (v[6] ^ g) & 0xFFFFFFFF
        v[7] = (v[7] ^ h) & 0xFFFFFFFF

    return pack('>8I', *v)


# ── RC4 Encryption ──

def rc4_crypt(key: bytes, data: bytes) -> bytes:
    """RC4 encryption/decryption."""
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) & 0xFF
        s[i], s[j] = s[j], s[i]

    i = j = 0
    result = bytearray()
    for byte in data:
        i = (i + 1) & 0xFF
        j = (j + s[i]) & 0xFF
        s[i], s[j] = s[j], s[i]
        k = s[(s[i] + s[j]) & 0xFF]
        result.append(byte ^ k)
    return bytes(result)


# ── Custom Base64 Encoding (Douyin's variant) ──

# Primary alphabet (for most characters)
_BASE64_ALPHABET_1 = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="

# Secondary alphabet (for specific positions)
_BASE64_ALPHABET_2 = "Dkdpgh4ZKsQB80/Mfvw36XI1R25+WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="

# Position map: which positions use alphabet 2 (True = use alphabet 2)
_POSITION_MAP = [
    False, True, False, True, False, False, True, True,
    True, False, True, False, False, True, False, True,
    False, True, True, False, True, False, False, True,
    True, False, True, False, False, False, True, True,
    False, True, False, False, True, True, False, False,
    True, False, False, True, False, True, True, False,
    False, True, True, False, True, False, False, True,
    False, False, True, False, False, True, True, False,
    True, False, False, True, True, False, False, True,
    False, True, False, False, True, False, True, True,
    False, True, False, False, True, True, False, False,
    True, False, True, True, False, False, True, False,
    True, False, False, True, False, True, True, False,
    True, False, False, True, True, False, False, True,
    False, True, False, False, True, False, True, True,
    False, False, True, False, True, False, False, True,
    True, False, False, True, False, True, False, False,
    True, True, False, False, True, False, True, False,
    False, True, True, False, False, True, False, True,
    False, False, True, True, False, False, True, False,
    True, False, False, True, True, False, False, True,
    False,
]


def _base64_encode(data: bytes) -> str:
    """Custom Douyin Base64 encoding with dual alphabet."""
    result = []
    bits = 0
    bit_count = 0

    for byte in data:
        bits = (bits << 8) | byte
        bit_count += 8
        while bit_count >= 6:
            bit_count -= 6
            idx = (bits >> bit_count) & 0x3F
            pos = len(result)
            alphabet = _BASE64_ALPHABET_2 if pos < len(_POSITION_MAP) and _POSITION_MAP[pos] else _BASE64_ALPHABET_1
            result.append(alphabet[idx])

    if bit_count > 0:
        idx = (bits << (6 - bit_count)) & 0x3F
        pos = len(result)
        alphabet = _BASE64_ALPHABET_2 if pos < len(_POSITION_MAP) and _POSITION_MAP[pos] else _BASE64_ALPHABET_1
        result.append(alphabet[idx])

    return ''.join(result)


# ── Browser Fingerprint Generation ──

def _generate_fingerprint(user_agent: str) -> bytes:
    """Generate a synthetic browser fingerprint from User-Agent."""
    # Parse browser info from UA
    import re

    # Default values
    platform = "Win32"
    os_name = "Windows"
    browser_name = "Chrome"
    engine_name = "Blink"
    screen_width = 1920
    screen_height = 1080
    cpu_cores = 8
    browser_online = "true"
    cookie_enabled = "true"

    if "Windows" in user_agent:
        platform = "Win32"
        os_name = "Windows"
    elif "Mac" in user_agent:
        platform = "MacIntel"
        os_name = "Mac OS"

    if "Firefox" in user_agent:
        browser_name = "Firefox"
        engine_name = "Gecko"
    elif "Chrome" in user_agent:
        browser_name = "Chrome"
        engine_name = "Blink"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        browser_name = "Safari"
        engine_name = "WebKit"

    # Extract versions
    chrome_ver = re.search(r'Chrome/(\d+)', user_agent)
    firefox_ver = re.search(r'Firefox/(\d+)', user_agent)
    browser_version = "131.0.0.0"
    engine_version = "131.0.0.0"
    if chrome_ver:
        ver = chrome_ver.group(1)
        browser_version = f"{ver}.0.0.0"
        engine_version = f"{ver}.0.0.0"
    elif firefox_ver:
        ver = firefox_ver.group(1)
        browser_version = f"{ver}.0"

    # Build fingerprint string (must match what the website expects)
    fp = (
        f'{{"s":"{platform}","b":"{browser_name}","v":"{browser_version}",'
        f'"sv":"{engine_name}/{engine_version}","os":"{os_name}",'
        f'"sw":{screen_width},"sh":{screen_height},'
        f'"cc":{cpu_cores},"ol":"{browser_online}","cl":"{cookie_enabled}"}}'
    )

    return fp.encode()


# ── A-Bogus Generator ──

def generate_a_bogus(query_string: str, user_agent: str) -> str:
    """
    Generate the a_bogus signature for a Douyin API request.

    Args:
        query_string: URL query parameters (without leading '?')
        user_agent: Browser User-Agent string

    Returns:
        The a_bogus signature string
    """
    # Step 1: Generate fingerprint
    fingerprint = _generate_fingerprint(user_agent)

    # Step 2: Create the data to sign
    timestamp = int(time.time() * 1000)
    random_bytes = bytes([random.randint(0, 255) for _ in range(12)])

    # Build the signing payload
    payload = query_string.encode() + fingerprint + pack('>Q', timestamp) + random_bytes

    # Step 3: SM3 hash
    sm3_digest = sm3_hash(payload)

    # Step 4: RC4 encryption (with derived key)
    # Key is derived from the first 16 bytes of the SM3 hash
    rc4_key = sm3_digest[:16]
    encrypted = rc4_crypt(rc4_key, sm3_digest[16:] + random_bytes)

    # Step 5: Custom Base64 encoding
    result = _base64_encode(sm3_digest[:16] + encrypted)

    return result


# ── Quick Test ──

if __name__ == '__main__':
    # Test SM3
    test_hash = sm3_hash(b'hello')
    expected = bytes.fromhex('becbbfaae6548b8bf0cfcad5a27183cd1be6093b1ccecc303d9e61d0a6452689')
    print(f"SM3 test: {'PASS' if test_hash == expected else 'FAIL'}")
    print(f"  Got:      {test_hash.hex()}")
    print(f"  Expected: {expected.hex()}")

    # Test a_bogus generation
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    query = "device_platform=webapp&aid=6383&aweme_id=7457034718876847394"
    ab = generate_a_bogus(query, ua)
    print(f"a_bogus: {ab}")
    print(f"Length: {len(ab)}")
