#!/usr/bin/env python3
# ZestyCraft — Craftland LW Engine (Web Edition)
# Full c.py parity · Credit: @Zestyxff570 · Web rebuild 2026
import os
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import sys, asyncio, random, json, socket, re, struct, time, uuid, hmac, hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import httpx
import requests as _rq
import urllib3 as _u3
from google.protobuf import descriptor_pb2 as _dpb2
from google.protobuf import symbol_database as _sdb
from google.protobuf import message_factory as _mf
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from aiohttp import web

try:
    from protobuf_decoder.protobuf_decoder import Parser as _ProtoParser
    _HAS_PROTO_DECODER = True
except ImportError:
    _ProtoParser = None
    _HAS_PROTO_DECODER = False

_u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)

# ============================================================
# CONFIG
# ============================================================
WEB_PORT                 = int(os.environ.get("PORT", os.environ.get("ZestyCRAFT_DASH_PORT", "8090")))
BASE_DIR                 = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE            = os.path.join(BASE_DIR, "accounts.json")
TOKEN_CACHE_FILE         = os.path.join(BASE_DIR, "token_cache.json")
TRAFFIC_LOG              = os.path.join(BASE_DIR, "Zestycraft_traffic.log")
TOKEN_CACHE_TTL          = 1200

START_MATCH_INTERVAL     = 3.0
NEW_MATCH_DELAY          = 3.0
MAX_MATCH_DURATION       = 700
MATCH_IDLE_TIMEOUT       = 8.0
ROOM_JOIN_INTERVAL       = 30.0
GLOBAL_MATCH_SEM         = asyncio.Semaphore(40)
GLOBAL_LOGIN_SEM         = asyncio.Semaphore(6)

REGION                   = "IND"
REGION_BYTE              = 0x14
CRAFTLAND_CLIENT_VERSION = os.environ.get("CRAFTLAND_CLIENT_VERSION", "1.132.11")
CRAFTLAND_RELEASE_VERSION= os.environ.get("CRAFTLAND_RELEASE_VERSION", "OB55")

FALLBACK_UID             = os.environ.get("CRAFTLAND_UID", "")
FALLBACK_PASSWORD        = os.environ.get("CRAFTLAND_PW", "")
AUTO_ACCEPT_FRIEND       = os.environ.get("ZestyCRAFT_FRIEND_ACCEPT", "1") == "1"
EXP_REFRESH_INTERVAL     = int(os.environ.get("ZestyCRAFT_EXP_REFRESH", "0"))

AES_KEY  = b'Yg&tc%DEuh6%Zc^8'
AES_IV   = b'6oyZDr22E3ychjM%'
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
TOKEN_GRANT_URL = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"

GEN_SECRET       = CLIENT_SECRET
GEN_REGISTER_URL = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
GEN_GRANT_URL    = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
GEN_DATADOME_URL = "https://datadome.garena.com/js/"
GEN_UA_MSDK      = "GarenaMSDK/4.0.44(V2538 ;Android 16;en;US;app 1.132.1 2019121227;)"
GEN_UA_WEB       = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
GEN_REGIONS = ["IND","ID","TH","ME","EUROPE","VN","BD","PK","TW","RU","NA","SAC","BR","SG","US"]
GEN_GROUP   = {"IND":"IND","BR":"AMERICA","US":"AMERICA","NA":"AMERICA","SAC":"AMERICA",
               "ID":"OTHERS","TH":"OTHERS","ME":"OTHERS","EUROPE":"OTHERS","VN":"OTHERS",
               "BD":"OTHERS","PK":"OTHERS","TW":"OTHERS","RU":"OTHERS","SG":"OTHERS"}
GEN_HOSTS   = {"IND":     ("https://loginbp.ppmainecoonghj.com/", "https://client.ind.freefiremobile.com/"),
               "AMERICA": ("https://loginbp.ppmainecoonghj.com/", "https://client.us.freefiremobile.com/"),
               "OTHERS":  ("https://loginbp.ppmainecoonghj.com/", "https://clientbp.ppmainecoonghj.com/")}
GEN_COUNTRY = {"IND":"IN","ID":"ID","TH":"TH","ME":"AE","EUROPE":"DE","VN":"VN","BD":"BD","PK":"PK",
               "TW":"TW","RU":"RU","NA":"US","SAC":"MX","BR":"BR","SG":"SG","US":"US"}
GEN_LANG    = {"ME":"ar","IND":"hi","ID":"id","VN":"vi","TH":"th","BD":"bn","PK":"ur",
               "TW":"zh","EUROPE":"fr","RU":"ru","NA":"na","SAC":"es","BR":"pt","SG":"ms","US":"us"}
# ✅ CORRECT capture keystream
GEN_KEYSTREAM = bytes([48,48,48,50,48,49,55,48,48,48,48,48,50,48,49,55,
                       48,48,48,48,48,50,48,49,55,48,48,48,48,48,50,48])
GEN_GGRE = bytes.fromhex(
    "47475245010101006d020000832363e79711efb391707fad6381be1acaef57ae198e95d7005ec74d16dd406b7d"
    "5356f25b38699671436eb29e6c5ffc6107073ea5fbe9795714af5661bed317bb90d6962420a1edb389ad1911"
    "5a1b6eeb5205173fd7804b7d23418697ed1c288f66acf0701640c7a613ae69464d9404e38b24d595be1c97c"
    "4eac6772952fccbc6714a9472629d0609aeb5de0afb1c078390195a8b6cf96f30b27d7c5120f43af278a150"
    "830d3e91f9fa89098d0be519e3802b826e67640293352402ad27479581fcf6e5997f4fc7709bdcb129dc803"
    "d1c254b8d5bca4cff1a3d021f169b4e133aca832f1c227baaa2f78ff0ce59b9934af15724766aba47d99de6"
    "2dc3232f04920cc9dabc292bee3ad4c342f3c7aa94021f7b468417a21eb57bb45b23c27de9e3c5c972012cc"
    "cfc4e4794d0a6d5368bfcbec8a8ba327815d20f9df47c7eb3c99a18e6747cc3ceb1823a8fcf57afcd5aaf3"
    "ca536b76a77c3c218c8dc1860a22fcb87a5a9f8c017745e523a1a4ab8a836993515b6040a33936c39f07b2"
    "641885cc90e218555c9539ba541896fdca071175a8cbd8157615b788efeca65bb5b81aeb5cdb5f0712d6e1a"
    "50016656d6409e1888546c40fd2f01aab95a05da798b48c1bb9fa01b28d949f903bf3428be1506bb724b13b"
    "8e04469bda807ca56d5cdd7d78bd804e9041ebef8e992ff41d441196430efb5ce5ebc4c09f08abd966019132"
    "e24cfb54d89fb48d84042963501640b6eec1658d8b1455887cbeae2884cd441ffe0ee1d25b353e83668bc87"
    "0c9ce8e91991a737e962f8d411d08537352b6fb50c1f65596c9faf1262d9a38e9fb509ecc036b3b0e410b7e"
    "f100006c692ca3ba025cda9a13dc649d883bee4c68b051161067d432d080e9e6907e11d895aae0d9e2aa9eb"
    "e945e3dee4392bfc353fe98f99895b3bbc69f4")

ML_HEADERS = {
    "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "Accept": "*/*", "Authorization": "Bearer ", "X-GA": "v1 1",
    "ReleaseVersion": CRAFTLAND_RELEASE_VERSION,
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Unity-Version": "2018.4.12f1",
}
GLD_HEADERS = {k: v for k, v in ML_HEADERS.items() if k != "Authorization"}
IP_POOL = ["103.16.33.109","106.202.108.146","117.214.98.55","122.176.45.12",
           "27.147.192.34","59.152.101.77","123.49.34.201","49.36.128.66",
           "171.48.112.90","223.190.56.14","45.124.24.66","157.38.27.201"]

# ============================================================
# CAPTURED TEMPLATES (2026-10-19 · c.py verbatim)
# ============================================================
_MATCHMAKING_TEMPLATE_HEX = (
    "080712db031202656e1ad2036db490eb5572dcbe0601d5762b2a1595a22f075d5cc3ef6ea97b2a551490ca051deb5ebb60d2079cfe113e87c3c3cf28aa840cf36044bc0ad39eab33c42b82cac7a3de587fe1039d63992fc44ac41a864393a30314104b0d1b904bf9550e17269ece63405e0c1d45b4816be1033707447791722ce26f14fa8fc6ec13b57f2c762fcdac33cc68e8f7cf9b171e0ddea1d2ea749a2e293c5ce4ede99093273b52fab76a230e0676c21d21c085c467539024c5956cfed3d02ebc76f8f63c0375506295e12dcb8e528a3ebede5d054180121faf60050e4aaa2dbdefb6a63d336f8d89777f588c951bd99e612a8c2fb0bc04d3ab68c5567440bdece9bddbf2c87b3c00ff1b74f3a6adabf9dfaea070dc0e7dfd2d365a42ac86b89cd6dbce0bf41bc08ca5d6184ed603febdb6513406da2f13968f9499f5851f409b6e4906a07119314b2870f3e5267f1874e16019b15a2e2b88c386028a7b34a9958d1b27bc55c5034d08201cc9af6621caf94bf23711efdd3c306a8218f0a56d82c80df08bef9c5fc581849be43f7d437b01bef4bdcdd7b99617c30304920230e84a6c81064afaf185cc765146cb9cc6baaec88b4cd27145b04e4be757f462a70412c39fd604b78b40f22de3beecce5ba59307f15195fd9f33cddb2801")
_GIN_HELLO_TEMPLATE_HEX = (
    "080212d2030acf036db490eb4a8448157b01d5762b2a1595c4d52a248fa3cc0fda3d55efe75231ce2cd785d46460f116bfb9711bb54de42e20039b4d42c6e17fc3a24ab860dc9d445fef68ff9a6d39dbaab068f75c9f6645205744e9bbbc4757a5567bfab49239a711e3bab619ae30390857b739ee3d8911f5be1bc684c46ff3421d78282840d844baecd7b6db3fa36c47fc47a6cc192a691263e4b82dc49d9f234456b781aed5ced8feb878e275d7699671a3902eb9709c05dcaa0416a7419cf433d4343bbcfc17580b8b468c87f2e9e9bbecb3afbbecec68b4c3389f5ce5aab9e57beecd0894e4b9a4318bbb65a05682a5ea524633c0bdf0d9e6733590bdc066b4af9e2101d159a4b6ee8e0a47ef3e060a4e2fb07c693dc57b3064e3f9bb51f60031decb8398a29a3e7d932f29bf115678d24f8514202dc9dc27443d0ec4327eb26b0fa75b2afad7855c5ea5dc21942e4ca7c0d3ca8fa764f424e55d58039162b406de26bb9f73d2ea4f7de0e1489fe802b75549d75763e5b6e0f86c364e735c742c3da60da8368c10942bac6ae1e9a14207141e27bc5e7ade1aa37c71b2bc813391fc1a76b7e9b98c54a23fb9cf856b2cae0be94a3d199298f31f680c98f50f172f8c547e33366ed1793a23f31a2711e92373b90009")
_GIN_ACK_TEMPLATE_HEX = (
    "080b12da040ad704f014426380af9ff8cc5d8e39cf7f4330ff11f567b3e8f531d3e4680538d19808d38b16c831bebbe6cbf26caf2c67d0cb6cc7b8dcb228ee86cb4044f0a3202bc5f358b69fe7ab7352796de6c37a6bdcc57c794b453d1eafae429e9180fa2322a9caeda438a7b620d2f744e91f185c02849b71f23af6c285fbf0e211fdadc940a9fd9e9782374dac9e701acd2df6a4be806d246f77f7124f098d7210aafa9d6afec4d344f149f1016ae1306b5cdb9d9237602c78f7c9debdaec623a5fa9bc1fb605e754f3f677f80db08f7a6e95fd7feba612ae9f092f254e7f1d3ac94de2b55e5179272a2ef61475a5ac458d8a52bfcee7f7b5ef6c01338c40b204a840e6282eebdeb08c8c80ac1b70b431d3821de12a9261c69c102207e40cf2a7bc7752924e6d47f1ab6c2843dbfd3f93b926ad9f1e1cc5f6da865e77b55cf55c3bc466a6e29fa08934fbeec1c59ad5fbecf056528755d847ab25d96297aefb5d0f334d0da4f720a0f1fac1bd65af160f4e04187a8be47f2a01f5c03cf33cb34e66524e8a707b073e4c3c8c8bd5a324c015d9fd8b3334f1453a19b7e687bc30636ce2be78b0e0a29227aa94c8ed02058fe7737f8d9b519fcad5c277d094c68a04920a8301300fbeb190304901661f87f731ae00645cd1a140284d313d9ba5d9588bf806c0e21b869ae4bb575e70c4e45b8448adcef032566c125a0039a43eaaef6f2bf352af0132040a27d4e37359df3fe4b71d13a29e921a8ced6ffbe2250a150737dcb0c1c37ce119203006265710bf2ba6c12ad248eea596b2a71fc3300bad1d451a54265354b7bcec2a96299f30c42d78051c0d97699bad1b43a9e")
# The massive stage-2 blob is loaded from c.py verbatim — see _load_stage2()
_GIN_STAGE2_TEMPLATE_HEX = None  # lazily populated below
_ROOM_JOIN_TEMPLATE_HEX = (
    "083312f00a080112065130374436342a0f01030407090a0b1216191a201d2729301a38014202656e70017a9f0a0a40323830323030303436303230344231383032303130303030303030303030303030303030303030303030303030303030453539303634353730303030303030301089011ab9037e585d511108034a56090f5c545007540b51020400565a0853020a580507505c05015457050200031503084b7d5c41404b11031a03101409034d04547771055d6146627e7b664b4f71605c70730e770961790b7a7b0f1a06447b5c66537f507b4876637f765755767f4a5d7c58585a5b5055614e0e155456594c1e627c1f7e434600456f557779635868456e5b695b505001555451045f7d0c067005077d0f1a02054e737d4049524378734600744d537d647f7e02497a7c06536e0e79780911014f420569185362631b680077456853445343785f4b127d1d5d4144790c12064e12754e567f461740505c7d576944454a5a5a03010d664103445b700a1b084d714a0d757f514079080306467f6940716843725b7d5350535459060f1a06004d000d42504b7775725f0c67754044437562596801705f76635843540b110a4b701a0050616a02724412055e0559620758461d5d0a7013771a63020410024e5f4e7f50467e6b7802676b0c4569687701614d50194143007f747409110b034a437e01135058467c5e7f44596c634a43440505417d054750784f700c1707455c4041507f5e5f5a75405b465b196d705041527e634e1c0f6663400522047c56595d300c3a1a1608444b420307000a0212166d7f7163756b7e5051755a5c54534208312e3133322e3131480650025ae90503626253513638616a6c433761417456324b796f566c56627a3764752b6863376161592f50614734394558465a594d4376594155434973755146385832522f6f50623548784c61396c594c6e32776a3063766554583052714752654d4559496554425062574e326f597a3953655777794a7a34474e356851614e314c756664667779456c70673562345a755a4f6b6e2b41564e5a596374307265317133654c30774c383055646a7746707947366c4c457a33596e706d2f4967637548585164707136567878784b496f6a4a704e4f5831706f6f5a463668436968694451796d586942594b38693933755a6a7869686e57724264434547734d5477576a5869336a7a6b7a4733434c657a3554397175674e4b55755261784574594537666e377656594866576a43523732335a744c3046536845626b4b516c732f566f4d6244503563566558574f35776b3054666a77444558464d643453415454553153397a30367438364835666164665a476877356c34774a5939566f303159784f4d2b4e2b57343878716931426f47707369515172326d625373565735354b355562306d767772654a4e726e7a507970596a6e4e415639586a4a2f7a324b5239306d436356732f4e523965507241344930434e536a48485a54654f397852796d664452362f4a59467a51327450425a663167695a6c765335485337473876567456443065496a3157776b755958347470352b494c6476644d4372324c5668596d7971597075684d54394e736336586a7a592b444734566a505062543053305a54526f3665344f4e7079596e56492f5557655465654936444564752b78303631454a636d6f69616d4e6578626b6150624d3944777066374f6e6d6336486e33543161703859466464355555654d334865765036484a5276794d736b555968564d5a614a707650723041794f32374c56765a63356d756f55467a484130696266396a324a335774424a33356863437844582f55674c432b6d454b6375374470704a454c74386b2f2b6f7538777161756f348a01260a16434c506c6174666f726d5f5265636f6d6d656e646564120c4d6f737420506f70756c6172")
_ROOM_PING_A = bytes.fromhex("0820")
_ROOM_PING_B = bytes.fromhex("080f")

def _load_stage2():
    """Loads _GIN_STAGE2_TEMPLATE_HEX lazily from c.py on disk if present, else from a bundled file, else empty."""
    global _GIN_STAGE2_TEMPLATE_HEX
    if _GIN_STAGE2_TEMPLATE_HEX is not None:
        return _GIN_STAGE2_TEMPLATE_HEX
    for cand in ("c.py", "stage2.hex", "gin_stage2.hex"):
        p = os.path.join(BASE_DIR, cand)
        if os.path.exists(p):
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
                if cand.endswith(".py"):
                    m = re.search(r'_GIN_STAGE2_TEMPLATE_HEX\s*=\s*\(\s*"([0-9a-fA-F]+)"\s*\)', txt)
                    if m:
                        _GIN_STAGE2_TEMPLATE_HEX = m.group(1)
                        return _GIN_STAGE2_TEMPLATE_HEX
                else:
                    hx = "".join(ch for ch in txt if ch in "0123456789abcdefABCDEF")
                    if len(hx) >= 1000:
                        _GIN_STAGE2_TEMPLATE_HEX = hx
                        return _GIN_STAGE2_TEMPLATE_HEX
            except Exception:
                pass
    _GIN_STAGE2_TEMPLATE_HEX = ""
    return _GIN_STAGE2_TEMPLATE_HEX

SVC_MATCHMAKING = 0x03
SVC_ROOM        = 0x0E
SVC_GIN         = 0x28
RADAR_CMDS      = {2001, 2002, 2012, 2014, 2016}
_TPL_MISSING    = False

# ============================================================
# STATE
# ============================================================
class EngineState:
    def __init__(self):
        self.status       = "IDLE"
        self.running      = False
        self.started_at   = None
        self.stopped_at   = None
        self.config       = {}
        self.tasks        = []
        self.stop_event   = None
        self.last_error   = ""
        self.total_matches= 0
        self.accounts     = {}
        self.logs         = []
        self.radar_players= {}
        self.start_count  = 0

    def log(self, msg, level="info"):
        self.logs.append({"t": time.strftime("%H:%M:%S"), "lvl": level, "msg": str(msg)})
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    def add_account(self, uid, nickname, region, level=1, exp=0):
        uid = str(uid)
        if uid not in self.accounts:
            self.accounts[uid] = {"uid": uid, "nickname": nickname or f"Player_{uid[:6]}",
                                  "region": region, "level": level, "exp": exp,
                                  "matches": 0, "status": "OFFLINE",
                                  "last_match": None, "joined_at": time.time()}
        else:
            a = self.accounts[uid]
            if nickname: a["nickname"] = nickname
            if level > a.get("level", 1): a["level"] = level
            if exp   > a.get("exp",   0): a["exp"]   = exp

    def set_status(self, uid, status):
        uid = str(uid)
        if uid in self.accounts:
            self.accounts[uid]["status"] = status

    def inc_match(self, uid):
        uid = str(uid)
        self.total_matches += 1
        if uid in self.accounts:
            self.accounts[uid]["matches"] += 1
            self.accounts[uid]["last_match"] = time.strftime("%H:%M:%S")

    def update_exp(self, uid, exp, level=None):
        uid = str(uid)
        a = self.accounts.get(uid)
        if not a: return
        if exp > a.get("exp", 0): a["exp"] = exp
        if level and level > a.get("level", 1): a["level"] = level

ENGINE = EngineState()
ENGINE.log("Engine initialized. Waiting for start...")

class RadarState:
    def __init__(self):
        self.players = {}
        self.lock = asyncio.Lock()
    async def feed(self, pid, x, y, z):
        async with self.lock:
            self.players[pid] = {"id": pid, "x": round(x,2), "y": round(y,2),
                                 "z": round(z,2), "ts": time.time()}
    async def snapshot(self):
        async with self.lock:
            now = time.time()
            for k in [k for k,v in self.players.items() if now - v["ts"] > 10]:
                del self.players[k]
            return {"players": list(self.players.values()), "matches": ENGINE.total_matches}
RADAR = RadarState()

def log_traffic(direction, svc, data):
    if os.environ.get("ZestyCRAFT_TRAFFIC_LOG", "0") != "1":
        return
    try:
        with open(TRAFFIC_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {direction} svc={svc:02x} len={len(data)} {data.hex()}\n")
    except Exception:
        pass

# ============================================================
# CRYPTO
# ============================================================
async def aes_encrypt(payload, key, iv):
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(payload, AES.block_size))

def _static_aes_encrypt(data):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(data, 16))

_DELTA = 0x9E3779B9
_ROUNDS = 16
CRC7_TABLE = bytes([
    0,9,18,27,36,45,54,63,72,65,90,83,108,101,126,119,25,16,11,2,61,52,47,38,81,88,67,74,117,124,103,110,
    50,59,32,41,22,31,4,13,122,115,104,97,94,87,76,69,43,34,57,48,15,6,29,20,99,106,113,120,71,78,85,92,
    100,109,118,127,64,73,82,91,44,37,62,55,8,1,26,19,125,116,111,102,89,80,75,66,53,60,39,46,17,24,3,10,
    86,95,68,77,114,123,96,105,30,23,12,5,58,51,40,33,79,70,93,84,107,98,121,112,7,14,21,28,35,42,49,56,
    65,72,83,90,101,108,119,126,9,0,27,18,45,36,63,54,88,81,74,67,124,117,110,103,16,25,2,11,52,61,38,47,
    115,122,97,104,87,94,69,76,59,50,41,32,31,22,13,4,106,99,120,113,78,71,92,85,34,43,48,57,6,15,20,29,
    37,44,55,62,1,8,19,26,109,100,127,118,73,64,91,82,60,53,46,39,24,17,10,3,116,125,102,111,80,89,66,75,
    23,30,5,12,51,58,33,40,95,86,77,68,123,114,105,96,14,7,28,21,42,35,56,49,70,79,84,93,98,107,112,121,
])

async def _tea_enc_block(v0, v1, k0, k1, k2, k3):
    s = 0
    for _ in range(_ROUNDS):
        s = (s + _DELTA) & 0xFFFFFFFF
        v0 = (v0 + ((((v1 << 4) & 0xFFFFFFFF) + k0) & 0xFFFFFFFF ^
                    ((v1 + s) & 0xFFFFFFFF) ^ (((v1 >> 5) + k1) & 0xFFFFFFFF))) & 0xFFFFFFFF
        v1 = (v1 + ((((v0 << 4) & 0xFFFFFFFF) + k2) & 0xFFFFFFFF ^
                    ((v0 + s) & 0xFFFFFFFF) ^ (((v0 >> 5) + k3) & 0xFFFFFFFF))) & 0xFFFFFFFF
    return v0, v1

async def _tea_dec_block(v0, v1, k0, k1, k2, k3):
    s = (_DELTA * _ROUNDS) & 0xFFFFFFFF
    for _ in range(_ROUNDS):
        v1 = (v1 - ((((v0 << 4) & 0xFFFFFFFF) + k2) & 0xFFFFFFFF ^
                    ((v0 + s) & 0xFFFFFFFF) ^ (((v0 >> 5) + k3) & 0xFFFFFFFF))) & 0xFFFFFFFF
        v0 = (v0 - ((((v1 << 4) & 0xFFFFFFFF) + k0) & 0xFFFFFFFF ^
                    ((v1 + s) & 0xFFFFFFFF) ^ (((v1 >> 5) + k1) & 0xFFFFFFFF))) & 0xFFFFFFFF
        s = (s - _DELTA) & 0xFFFFFFFF
    return v0, v1

async def tea_cbc_encrypt(padded, key_bytes):
    k = [struct.unpack_from("<I", key_bytes, o)[0] for o in (0,4,8,12)]
    out = bytearray(len(padded)); pc = bytearray(8); pi = bytearray(8)
    for i in range(0, len(padded), 8):
        x = bytearray(8)
        for j in range(8): x[j] = padded[i+j] ^ pc[j]
        e0, e1 = await _tea_enc_block(struct.unpack_from("<I", x, 0)[0],
                                      struct.unpack_from("<I", x, 4)[0], *k)
        enc = bytearray(8); struct.pack_into("<I", enc, 0, e0); struct.pack_into("<I", enc, 4, e1)
        for j in range(8): out[i+j] = enc[j] ^ pi[j]
        pc[:] = out[i:i+8]; pi[:] = x
    return bytes(out)

async def tea_cbc_decrypt(body, key_bytes):
    k = [struct.unpack_from("<I", key_bytes, o)[0] for o in (0,4,8,12)]
    out = bytearray(len(body)); pi = bytearray(8); pc = bytearray(8)
    for i in range(0, len(body), 8):
        x = bytearray(8)
        for j in range(8): x[j] = body[i+j] ^ pi[j]
        d0, d1 = await _tea_dec_block(struct.unpack_from("<I", x, 0)[0],
                                      struct.unpack_from("<I", x, 4)[0], *k)
        dec = bytearray(8); struct.pack_into("<I", dec, 0, d0); struct.pack_into("<I", dec, 4, d1)
        for j in range(8): out[i+j] = dec[j] ^ pc[j]
        pc[:] = body[i:i+8]; pi[:] = dec
    return bytes(out)

async def crc7_buff(crc, buf):
    c = crc & 0x7F
    for b in buf: c = CRC7_TABLE[((2 * (c & 0xFF)) ^ (b & 0xFF)) & 0xFF] & 0x7F
    return c & 0x7F

_FIELD_SIZES = {0:1, 1:2, 2:2, 3:1, 4:2}
_FIELD_NAMES = {0:"sendOption", 1:"cmd", 2:"orderId", 3:"flags", 4:"length"}

# ============================================================
# DNS / SOCKETS
# ============================================================
_DNS_CACHE = {}; _DNS_CACHE_TTL = 300.0
async def resolve_host(hostname):
    parts = hostname.split(".")
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return hostname
    now = time.time()
    if hostname in _DNS_CACHE and now < _DNS_CACHE[hostname][1]:
        return _DNS_CACHE[hostname][0]
    try:
        info = await asyncio.get_running_loop().getaddrinfo(hostname, None, family=socket.AF_INET)
        ip = info[0][4][0]; _DNS_CACHE[hostname] = (ip, now + _DNS_CACHE_TTL); return ip
    except Exception:
        return hostname

def optimize_tcp_socket(sock):
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    except Exception: pass

def optimize_udp_socket(sock):
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
    except Exception: pass

# ============================================================
# TOKEN CACHE
# ============================================================
def _json_serializer(obj):
    if isinstance(obj, (bytes, bytearray)):
        return {"__bytes_hex__": bytes(obj).hex()}
    raise TypeError(f"Type {type(obj)} not serializable")

def _json_deserializer(obj):
    if isinstance(obj, dict):
        if "__bytes_hex__" in obj and len(obj) == 1:
            try: return bytes.fromhex(obj["__bytes_hex__"])
            except Exception: return b""
        return {k: _json_deserializer(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_deserializer(x) for x in obj]
    return obj

def _load_token_cache():
    if not os.path.exists(TOKEN_CACHE_FILE): return {}
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            d = json.loads(f.read().strip() or "{}")
        return _json_deserializer(d) if isinstance(d, dict) else {}
    except Exception:
        try: os.remove(TOKEN_CACHE_FILE)
        except Exception: pass
        return {}

def _save_token_cache(cache):
    try:
        tmp = TOKEN_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, default=_json_serializer)
        os.replace(tmp, TOKEN_CACHE_FILE)
    except Exception as e:
        ENGINE.log(f"Token cache save error: {e}", "err")

def cache_get(uid):
    e = _load_token_cache().get(str(uid))
    if not e: return None
    if time.time() - e.get("cached_at", 0) > TOKEN_CACHE_TTL:
        cache_invalidate(uid); return None
    if not isinstance(e.get("login_payload_data"), (bytes, bytearray)):
        cache_invalidate(uid); return None
    return e

def cache_set(uid, data):
    c = _load_token_cache()
    e = dict(data); e["cached_at"] = time.time()
    c[str(uid)] = e; _save_token_cache(c)

def cache_invalidate(uid):
    c = _load_token_cache()
    if str(uid) in c:
        del c[str(uid)]; _save_token_cache(c)

# ============================================================
# LOGIN DESCRIPTORS
# ============================================================
_T = _dpb2.FieldDescriptorProto

def _build_login_descriptors():
    req_fd = _dpb2.FileDescriptorProto(); req_fd.name = 'FCReq.proto'; req_fd.syntax = 'proto3'
    gs = req_fd.message_type.add(); gs.name = 'GameSecurity'
    f = gs.field.add(); f.name='version'; f.number=6; f.type=_T.TYPE_INT32
    f = gs.field.add(); f.name='hidden_value'; f.number=8; f.type=_T.TYPE_UINT64
    m = req_fd.message_type.add(); m.name = 'MajorLogin'
    fields = [
        ('event_time',3,_T.TYPE_STRING),('game_name',4,_T.TYPE_STRING),('platform_id',5,_T.TYPE_INT32),
        ('client_version',7,_T.TYPE_STRING),('system_software',8,_T.TYPE_STRING),
        ('system_hardware',9,_T.TYPE_STRING),('telecom_operator',10,_T.TYPE_STRING),
        ('network_type',11,_T.TYPE_STRING),('screen_width',12,_T.TYPE_UINT32),
        ('screen_height',13,_T.TYPE_UINT32),('screen_dpi',14,_T.TYPE_STRING),
        ('processor_details',15,_T.TYPE_STRING),('memory',16,_T.TYPE_UINT32),
        ('gpu_renderer',17,_T.TYPE_STRING),('gpu_version',18,_T.TYPE_STRING),
        ('unique_device_id',19,_T.TYPE_STRING),('client_ip',20,_T.TYPE_STRING),
        ('language',21,_T.TYPE_STRING),('open_id',22,_T.TYPE_STRING),
        ('open_id_type',23,_T.TYPE_STRING),('device_type',24,_T.TYPE_STRING),
        ('device_model',25,_T.TYPE_STRING),('country_code',26,_T.TYPE_STRING),
        ('access_token',29,_T.TYPE_STRING),('platform_sdk_id',30,_T.TYPE_INT32),
        ('network_operator_a',41,_T.TYPE_STRING),('network_type_a',42,_T.TYPE_STRING),
        ('client_using_version',57,_T.TYPE_STRING),('external_storage_total',60,_T.TYPE_INT32),
        ('external_storage_available',61,_T.TYPE_INT32),('internal_storage_total',62,_T.TYPE_INT32),
        ('internal_storage_available',63,_T.TYPE_INT32),('game_disk_storage_available',64,_T.TYPE_INT32),
        ('game_disk_storage_total',65,_T.TYPE_INT32),('external_sdcard_avail_storage',66,_T.TYPE_INT32),
        ('external_sdcard_total_storage',67,_T.TYPE_INT32),('field_70',70,_T.TYPE_INT32),
        ('login_by',73,_T.TYPE_INT32),('library_path',74,_T.TYPE_STRING),
        ('reg_avatar',76,_T.TYPE_INT32),('library_token',77,_T.TYPE_STRING),
        ('channel_type',78,_T.TYPE_INT32),('cpu_type',79,_T.TYPE_INT32),
        ('cpu_architecture',81,_T.TYPE_STRING),('client_version_code',83,_T.TYPE_STRING),
        ('field_85',85,_T.TYPE_INT32),('graphics_api',86,_T.TYPE_STRING),
        ('supported_astc_bitset',87,_T.TYPE_UINT32),('login_open_id_type',88,_T.TYPE_INT32),
        ('analytics_detail',89,_T.TYPE_BYTES),('field_90',90,_T.TYPE_STRING),
        ('field_91',91,_T.TYPE_STRING),('loading_time',92,_T.TYPE_UINT32),
        ('release_channel',93,_T.TYPE_STRING),('extra_info',94,_T.TYPE_STRING),
        ('android_engine_init_flag',95,_T.TYPE_UINT32),('field_96',96,_T.TYPE_STRING),
        ('if_push',97,_T.TYPE_INT32),('is_vpn',98,_T.TYPE_INT32),
        ('origin_platform_type',99,_T.TYPE_STRING),('primary_platform_type',100,_T.TYPE_STRING),
        ('field_102',102,_T.TYPE_BYTES),('field_103',103,_T.TYPE_INT32),
        ('field_104',104,_T.TYPE_UINT32),('field_105',105,_T.TYPE_INT32),
        ('field_106',106,_T.TYPE_STRING),('field_107',107,_T.TYPE_STRING),
    ]
    for name, num, ftype in fields:
        f = m.field.add(); f.name = name; f.number = num; f.type = ftype
    _sdb.Default().pool.Add(req_fd)
    ml = _mf.GetMessageClass(_sdb.Default().pool.FindMessageTypeByName('MajorLogin'))

    res_fd = _dpb2.FileDescriptorProto(); res_fd.name = 'FCRes.proto'; res_fd.syntax = 'proto3'
    bl = res_fd.message_type.add(); bl.name = 'BlacklistInfo'
    en = res_fd.enum_type.add(); en.name = 'BanReason'
    for nm, num in [('UNKNOWN',0),('IN_GAME_AUTO',1),('REFUND',2),('OTHERS',3),
                    ('SKINMOD',4),('IN_GAME_AUTO_NEW',1014)]:
        ev = en.value.add(); ev.name = nm; ev.number = num
    f = bl.field.add(); f.name='ban_reason'; f.number=1; f.type=_T.TYPE_ENUM; f.type_name='.BanReason'
    f = bl.field.add(); f.name='expire_duration'; f.number=2; f.type=_T.TYPE_UINT32
    f = bl.field.add(); f.name='ban_time'; f.number=3; f.type=_T.TYPE_UINT32
    f = bl.field.add(); f.name='ban_type'; f.number=4; f.type=_T.TYPE_STRING
    q = res_fd.message_type.add(); q.name = 'QueueInfo'
    f = q.field.add(); f.name='allow'; f.number=1; f.type=_T.TYPE_BOOL
    f = q.field.add(); f.name='queue_position'; f.number=2; f.type=_T.TYPE_UINT32
    f = q.field.add(); f.name='need_wait_secs'; f.number=3; f.type=_T.TYPE_UINT32
    f = q.field.add(); f.name='queue_is_full'; f.number=4; f.type=_T.TYPE_BOOL
    cfg = res_fd.message_type.add(); cfg.name = 'RspConfig'
    f = cfg.field.add(); f.name='f1'; f.number=1; f.type=_T.TYPE_INT32
    rb = res_fd.message_type.add(); rb.name = 'RspRegionBlock'
    f = rb.field.add(); f.name='region'; f.number=1; f.type=_T.TYPE_STRING
    r = res_fd.message_type.add(); r.name = 'MajorLoginRes'
    res_fields = [
        ('account_id',1,_T.TYPE_UINT64),('region',2,_T.TYPE_STRING),
        ('noti_region',3,_T.TYPE_STRING),('country_code',4,_T.TYPE_STRING),
        ('environment',5,_T.TYPE_STRING),('new_active_region',6,_T.TYPE_STRING),
        ('recommend_regions',7,_T.TYPE_STRING,_T.LABEL_REPEATED),
        ('token',8,_T.TYPE_STRING),('ttl',9,_T.TYPE_UINT32),
        ('server_url',10,_T.TYPE_STRING),('emulator_score',11,_T.TYPE_UINT32),
        ('blacklist',12,_T.TYPE_MESSAGE,_T.LABEL_OPTIONAL,'.BlacklistInfo'),
        ('queue_info',13,_T.TYPE_MESSAGE,_T.LABEL_OPTIONAL,'.QueueInfo'),
        ('tp_url',14,_T.TYPE_STRING),
        ('config',15,_T.TYPE_MESSAGE,_T.LABEL_OPTIONAL,'.RspConfig'),
        ('ip_city',16,_T.TYPE_STRING),('ip_subdivision',17,_T.TYPE_STRING),
        ('kts',21,_T.TYPE_UINT32),('ak',22,_T.TYPE_BYTES),('aiv',23,_T.TYPE_BYTES),
        ('ffanti_url',24,_T.TYPE_STRING),
        ('region_block',25,_T.TYPE_MESSAGE,_T.LABEL_OPTIONAL,'.RspRegionBlock'),
        ('connection_seed_enabled',26,_T.TYPE_BOOL),('session_id',27,_T.TYPE_STRING),
    ]
    for entry in res_fields:
        f = r.field.add(); f.name = entry[0]; f.number = entry[1]; f.type = entry[2]
        if len(entry) > 3: f.label = entry[3]
        if len(entry) > 4: f.type_name = entry[4]
    _sdb.Default().pool.Add(res_fd)
    mlres = _mf.GetMessageClass(_sdb.Default().pool.FindMessageTypeByName('MajorLoginRes'))

    gfd = _dpb2.FileDescriptorProto(); gfd.name='FCGLD.proto'; gfd.syntax='proto3'
    rg = gfd.message_type.add(); rg.name='GldRegion'
    f = rg.field.add(); f.name='id'; f.number=1; f.type=_T.TYPE_INT32
    f = rg.field.add(); f.name='code'; f.number=2; f.type=_T.TYPE_STRING
    gm = gfd.message_type.add(); gm.name='GldRes'
    g_fields = [
        ('account_id',1,_T.TYPE_UINT64),('f2',2,_T.TYPE_UINT32),('region',3,_T.TYPE_STRING),
        ('network_id',4,_T.TYPE_STRING),('server_time',5,_T.TYPE_UINT64),
        ('f6',6,_T.TYPE_UINT32),('f7',7,_T.TYPE_UINT32),('f8',8,_T.TYPE_UINT32),
        ('online',14,_T.TYPE_STRING),('f15',15,_T.TYPE_UINT32),('event_url',16,_T.TYPE_STRING),
        ('regions',19,_T.TYPE_MESSAGE,_T.LABEL_REPEATED,'.GldRegion'),
        ('f23',23,_T.TYPE_UINT64),('noti_region',24,_T.TYPE_STRING),
        ('f30',30,_T.TYPE_UINT64),('chat',32,_T.TYPE_STRING),('f34',34,_T.TYPE_BYTES),
        ('f37',37,_T.TYPE_UINT32),('network_log',39,_T.TYPE_STRING),
        ('ip_region',42,_T.TYPE_STRING),('servers',44,_T.TYPE_BYTES,_T.LABEL_REPEATED),
        ('f45',45,_T.TYPE_UINT64),('f48',48,_T.TYPE_BYTES),('grtc',62,_T.TYPE_STRING),
        ('gin',63,_T.TYPE_BYTES),('f65',65,_T.TYPE_BYTES),('f69',69,_T.TYPE_BYTES),
        ('f70',70,_T.TYPE_BYTES),('f75',75,_T.TYPE_UINT32),('f77',77,_T.TYPE_UINT64),
        ('gateway',79,_T.TYPE_STRING),('f84',84,_T.TYPE_UINT32),('f86',86,_T.TYPE_BYTES),
        ('f88',88,_T.TYPE_STRING),('f89',89,_T.TYPE_UINT64),('vodka',92,_T.TYPE_STRING),
        ('f96',96,_T.TYPE_UINT32),('f97',97,_T.TYPE_UINT32),('cs',98,_T.TYPE_STRING),
        ('f100',100,_T.TYPE_STRING),
    ]
    for entry in g_fields:
        f = gm.field.add(); f.name = entry[0]; f.number = entry[1]; f.type = entry[2]
        if len(entry) > 3: f.label = entry[3]
        if len(entry) > 4: f.type_name = entry[4]
    _sdb.Default().pool.Add(gfd)
    gldres = _mf.GetMessageClass(_sdb.Default().pool.FindMessageTypeByName('GldRes'))
    return ml, mlres, gldres

LoginReqMsg, LoginResMsg, GldResMsg = _build_login_descriptors()

def region_endpoints(region):
    grp = GEN_GROUP.get(str(region).upper(), "OTHERS")
    return GEN_HOSTS[grp]

# ============================================================
# GUEST REGISTRATION / TOKEN GRANT (DataDome)
# ============================================================
_gen_dd_cookie = None; _gen_dd_exp = 0.0; _gen_last_reg = 0.0

def _gen_datadome(force=False):
    global _gen_dd_cookie, _gen_dd_exp
    now = time.time()
    if not force and _gen_dd_cookie and _gen_dd_exp > now:
        return _gen_dd_cookie
    hdrs = {"User-Agent": GEN_UA_WEB, "Content-Type":"application/x-www-form-urlencoded",
            "Referer":"https://sso.garena.com/universal/register?locale=en-SG",
            "Origin":"https://sso.garena.com","Accept":"application/json, text/plain, */*"}
    payload = {"jsType":"le","eventCounters":'{"mousemove":1,"click":1,"keydown":11}',
               "ddk":"AE3F04AD3F0D3A462481A337485081",
               "Referer":"https://sso.garena.com/universal/register?locale=en-SG",
               "request":"/universal/register?locale=en-SG",
               "responsePage":"origin","ddv":"5.7.0"}
    last = None
    for attempt in range(1, 5):
        try:
            r = _rq.post(GEN_DATADOME_URL, data=payload, headers=hdrs, timeout=15)
            r.raise_for_status(); res = r.json()
        except Exception as e:
            last = e; time.sleep(1.5 * attempt); continue
        if res.get("status") == 200 and res.get("cookie"):
            for part in res["cookie"].split(";"):
                if "datadome=" in part:
                    dd = part.replace("datadome=","").strip()
                    if dd:
                        _gen_dd_cookie = dd; _gen_dd_exp = now + 300.0; return dd
        last = res; time.sleep(1.5 * attempt)
    raise RuntimeError(f"DataDome failed: {last}")

def _gen_sign(body):
    return hmac.new(GEN_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()

def _gen_register(password):
    global _gen_last_reg
    body = json.dumps({"app_id":100067,"client_type":2,"password":password,"source":2},
                     separators=(",",":"))
    last = None
    for attempt in range(1, 7):
        wait = 1.0 - (time.time() - _gen_last_reg)
        if wait > 0: time.sleep(wait)
        _gen_last_reg = time.time()
        dd = _gen_datadome(force=(attempt > 1 and attempt % 3 == 0))
        hdrs = {"User-Agent": GEN_UA_MSDK, "Authorization": f"Signature {_gen_sign(body)}",
                "Cookie": f"datadome={dd}", "Accept":"application/json",
                "Content-Type":"application/json; charset=utf-8"}
        try:
            r = _rq.post(GEN_REGISTER_URL, data=body, headers=hdrs, timeout=25); data = r.json()
        except Exception as e:
            last = e; time.sleep(2.0 * attempt); continue
        code = data.get("code")
        if code == 0: return str(data["data"]["uid"])
        if code in (1006, 1005):
            last = data; time.sleep(min(10.0 * (2 ** (attempt - 1)), 60.0)); continue
        raise RuntimeError(f"guest:register failed: {data}")
    raise RuntimeError(f"guest:register gave up: {last}")

def _gen_token(uid, password):
    body = json.dumps({"client_id":100067,"client_secret":GEN_SECRET,"client_type":2,
                      "device_id":"","password":password,"response_type":"token",
                      "uid": int(uid) if str(uid).isdigit() else uid}, separators=(",",":"))
    dd = _gen_datadome(); last = None
    for attempt in range(1, 5):
        hdrs = {"User-Agent": GEN_UA_MSDK, "Authorization": f"Signature {_gen_sign(body)}",
                "Cookie": f"datadome={dd}", "Accept":"application/json",
                "Content-Type":"application/json; charset=utf-8"}
        try:
            r = _rq.post(GEN_GRANT_URL, data=body, headers=hdrs, timeout=20); data = r.json()
        except Exception as e:
            last = e; time.sleep(2.0 * attempt); continue
        code = data.get("code")
        if code == 0:
            return data["data"]["access_token"], data["data"]["open_id"]
        last = data
        if code in (1006, 1005):
            time.sleep(min(10.0 * (2 ** (attempt - 1)), 60.0))
        else:
            dd = _gen_datadome(force=True); time.sleep(1.5 * attempt)
    raise RuntimeError(f"guest/token:grant failed: {last}")

def _g_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n: out.append(b | 0x80)
        else: out.append(b); break
    return bytes(out)
def _g_tag(f, wt):    return _g_varint((f << 3) | wt)
def _g_fvint(f, n):   return _g_tag(f, 0) + _g_varint(n)
def _g_fstr(f, s):
    b = s.encode("utf-8"); return _g_tag(f, 2) + _g_varint(len(b)) + b
def _g_fbytes(f, b):  return _g_tag(f, 2) + _g_varint(len(b)) + b

def _gen_encode_open_id(open_id):
    return bytes(ord(open_id[i]) ^ GEN_KEYSTREAM[i % len(GEN_KEYSTREAM)]
                 for i in range(len(open_id)))

def _gen_major_register(open_id, access_token, nickname, region):
    grp = GEN_GROUP.get(str(region).upper(), "OTHERS")
    url = GEN_HOSTS[grp][0].rstrip("/") + "/MajorRegister"
    lang = GEN_LANG.get(str(region).upper(), "en")
    body  = _g_fstr(1, nickname) + _g_fstr(2, access_token) + _g_fstr(3, open_id)
    body += _g_fvint(5, 102000007) + _g_fvint(6, 4) + _g_fvint(7, 1) + _g_fvint(13, 1)
    body += _g_fbytes(14, _gen_encode_open_id(open_id)) + _g_fstr(15, lang)
    body += _g_fvint(16, 2) + _g_fstr(20, "2.132.4") + _g_fvint(21, 1)
    body += _g_fbytes(22, GEN_GGRE)
    hdrs = {"User-Agent": ML_HEADERS["User-Agent"], "Accept":"*/*",
            "Accept-Encoding":"deflate, gzip","Authorization":"Bearer","X-GA":"v1 1",
            "X-GA-SV": str(int(time.time())),
            "ReleaseVersion": CRAFTLAND_RELEASE_VERSION,
            "Content-Type":"application/x-www-form-urlencoded",
            "X-Unity-Version":"2018.4.12f1"}
    r = _rq.post(url, data=_static_aes_encrypt(body), headers=hdrs, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"MajorRegister HTTP {r.status_code}: {r.text[:120]}")

def generate_guest_account(region):
    raw = "Zesty_" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=4))
    pw  = hashlib.sha256(raw.encode()).hexdigest().upper()
    uid = _gen_register(pw)
    access, open_id = _gen_token(uid, pw)
    _gen_major_register(open_id, access, raw, region)
    return {"uid": uid, "password": pw, "nickname": raw, "region": region.upper()}

def token_grant(uid, pw):
    for attempt in range(1, 4):
        try:
            gr = _rq.post(TOKEN_GRANT_URL, json={"client_id":100067,"client_secret":CLIENT_SECRET,
                                                 "client_type":2,"password":pw,
                                                 "response_type":"token","uid": int(uid)},
                          timeout=25)
            err = gr.json(); data = err.get("data", {})
            if data.get("access_token"):
                return data["access_token"], data.get("open_id", "")
            if err.get("code") == 1006:
                time.sleep(15 * attempt + random.randint(0, 15))
            else: break
        except Exception:
            time.sleep(5 * attempt)
    return None, None

# ============================================================
# DEVICE POOLS
# ============================================================
_DEV_POOL_32 = None; _DEV_POOL_64 = None

def _load_device_pools():
    global _DEV_POOL_32, _DEV_POOL_64
    try:
        for cand in ("devices.json", "devices(1).json"):
            p = os.path.join(BASE_DIR, cand)
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    d = json.load(f)
                _DEV_POOL_32 = d.get("armv7_32bit") or None
                _DEV_POOL_64 = d.get("arm64") or None
                if _DEV_POOL_32: return
    except Exception:
        pass

_load_device_pools()

_BUILT_IN_32 = [{"model":"Xiaomi M2006C3LII","w":1600,"h":720,"dpi":"320",
                 "cpu":"ARMv7 VFPv3 NEON | 2001 | 8","mem":3790,
                 "gpu":"PowerVR Rogue GE8320",
                 "gpu_v":"OpenGL ES 3.2 build 1.11@5425693"}]
_BUILT_IN_64 = [{"model":"samsung SM-E156B",
                 "sw":"Android OS 14 / API-34 (UP1A.231005.007/E156BXXS6AYD4)",
                 "w":2340,"h":1080,"dpi":"295","cpu":"ARM64 FP ASIMD AES | 2200 | 8",
                 "mem":5586,"gpu":"Mali-G57 MC2","gpu_v":"OpenGL ES 3.2 v1.r38p1"}]

def _dev32():
    if _DEV_POOL_32:
        d = random.choice(_DEV_POOL_32)
        return {"model": d["model"], "w": d["screen_width"], "h": d["screen_height"],
                "dpi": d["screen_dpi"], "cpu": d["processor_details"],
                "mem": d["memory"], "gpu": d["gpu_renderer"], "gpu_v": d["gpu_version"]}
    return dict(random.choice(_BUILT_IN_32))

def _dev64():
    if _DEV_POOL_64:
        d = random.choice(_DEV_POOL_64)
        return {"model": d["model"], "sw": d["system_software"],
                "w": d["screen_width"], "h": d["screen_height"], "dpi": d["screen_dpi"],
                "cpu": d["processor_details"], "mem": d["memory"],
                "gpu": d["gpu_renderer"], "gpu_v": d["gpu_version"]}
    return dict(random.choice(_BUILT_IN_64))

# ============================================================
# LOGIN CHAIN
# ============================================================
def build_majorlogin(open_id, access_token, version, dev, country=None, lang=None):
    country = country or "IN"; lang = lang or "en"
    r = LoginReqMsg()
    r.event_time = str(datetime.now())[:-7]; r.game_name = "free fire"; r.platform_id = 1
    r.client_version = version
    r.system_software = "Android OS 14 / API-34 (UP1A.231005.007/E135FXXSEEZE2)"
    r.system_hardware = "Handheld"; r.telecom_operator = "CarrierDataNetwork"
    r.network_type = "CarrierDataNetwork"; r.screen_width = 1672; r.screen_height = 750
    r.screen_dpi = "338"; r.processor_details = "ARMv7 VFPv3 NEON | 2002 | 8"
    r.memory = 3702; r.gpu_renderer = "Mali-G52"
    r.gpu_version = "OpenGL ES 3.2 v1.r38p1-01bet0-mbs2v41_0.6d20ec041e51b2f2d25dfc265586ebe8"
    r.unique_device_id = f"Google|{uuid.uuid4()}"; r.client_ip = "104.28.197.151"
    r.language = lang; r.open_id = open_id; r.open_id_type = "4"
    r.device_type = "Handheld"; r.device_model = "samsung SM-E135F"
    r.country_code = country; r.access_token = access_token; r.platform_sdk_id = 1
    r.network_operator_a = "CarrierDataNetwork"; r.network_type_a = "Cellular"
    r.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    r.external_storage_total = 52037; r.external_storage_available = 5355
    r.internal_storage_total = 3723; r.game_disk_storage_available = 5483
    r.game_disk_storage_total = 52037; r.external_sdcard_avail_storage = 5483
    r.external_sdcard_total_storage = 52037; r.field_70 = 4; r.login_by = 2
    r.library_path = ("/data/app/~~yACsV8QOk9OexgajWQP30A==/com.dts.freefireth-Bi_wPVrrhYM2nYncc29q7Q==/lib/arm")
    r.reg_avatar = 1
    r.library_token = ("b8e0cd5e295eee42f5860d3c86e483dd|"
                       "/data/app/~~yACsV8QOk9OexgajWQP30A==/com.dts.freefireth-Bi_wPVrrhYM2nYncc29q7Q==/base.apk")
    r.channel_type = 3; r.cpu_type = 1; r.cpu_architecture = "32"
    r.client_version_code = "2019121229"; r.field_85 = 3; r.graphics_api = "OpenGLES2"
    r.supported_astc_bitset = 8191; r.login_open_id_type = 4; r.loading_time = 16091
    r.release_channel = "android"
    r.extra_info = ("KqsHT3Yeqo3RLRl8efNiL3aL/1SHwlSrtK0DwNAqdkNBQz70TeVy+icaIwuR3UK4b65Uf3IG5xBFEv0uu"
                    "+jQZI+rOYCmNCsXjJT4QcZaYgoaaUGG")
    r.android_engine_init_flag = 111107
    r.field_96 = '{"cur_rate":null,"support_etc2":false}'; r.if_push = 1
    r.origin_platform_type = "4"; r.primary_platform_type = "4"
    r.field_102 = bytes.fromhex("4503454457550c0766"); r.field_104 = 53792; r.field_105 = 1
    r.field_106 = ("https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|"
                   "https://core-bs.ggpolarbear.com/live/ABHotUpdates/|"
                   "6b2078db9d22dd98f8e9386a39af8462")
    r.field_107 = "c8e41b7a93f02d56e1a94c7b8203f5d1"
    return r

def build_getlogindata(open_id, access_token, version, dev, country=None, lang=None, region=None):
    r = build_majorlogin(open_id, access_token, version, dev, country, lang)
    r.field_90 = "Khulna"; r.field_91 = "D"
    r.origin_platform_type = "0"; r.field_103 = 1
    return r, dev

def parse_majorlogin_response(raw):
    body = raw[64:] if len(raw) > 64 else raw
    msg = LoginResMsg()
    try:
        msg.ParseFromString(body); return msg, 64
    except Exception:
        for skip in range(0, 128, 4):
            try:
                m2 = LoginResMsg(); m2.ParseFromString(raw[skip:])
                if m2.account_id or m2.token or m2.ak:
                    return m2, skip
            except Exception: continue
    return msg, 64

def parse_wire(data):
    fields = []; off = 0
    while off < len(data):
        key = shift = 0
        while True:
            b = data[off]; off += 1
            key |= (b & 0x7F) << shift
            if not (b & 0x80): break
            shift += 7
        fn, wt = key >> 3, key & 7
        if wt == 0:
            v = shift = 0
            while True:
                b = data[off]; off += 1
                v |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            fields.append((fn, wt, v))
        elif wt == 2:
            ln = shift = 0
            while True:
                b = data[off]; off += 1
                ln |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            fields.append((fn, wt, data[off:off+ln])); off += ln
        elif wt == 1: fields.append((fn, wt, data[off:off+8])); off += 8
        elif wt == 5: fields.append((fn, wt, data[off:off+4])); off += 4
        else: break
    return fields

def parse_server_entry(blob):
    out = {"region":"","name":"","addr":"","weight":0}
    try:
        for fn, wt, v in parse_wire(blob):
            if fn == 1 and wt == 2: out["region"] = v.decode("utf-8","ignore")
            elif fn == 2 and wt == 2: out["name"] = v.decode("utf-8","ignore")
            elif fn == 3 and wt == 2: out["addr"] = v.decode("utf-8","ignore")
            elif fn == 4 and wt == 0: out["weight"] = v
    except Exception: pass
    return out

def _decode_proto_manual(data):
    result = {}; offset = 0; n = len(data)
    while offset < n:
        header = 0; shift = 0
        while offset < n:
            b = data[offset]; offset += 1
            header |= (b & 0x7F) << shift
            if not (b & 0x80): break
            shift += 7
            if shift > 28: break
        if header == 0: break
        fn = header >> 3; wt = header & 0x7
        if fn == 0: break
        if wt == 0:
            v = 0; shift = 0
            while offset < n:
                b = data[offset]; offset += 1
                v |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
                if shift > 63: break
            result[fn] = v
        elif wt == 2:
            ln = 0; shift = 0
            while offset < n:
                b = data[offset]; offset += 1
                ln |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
                if shift > 28: break
            if ln > n - offset: break
            value = data[offset:offset+ln]; offset += ln
            try:
                s = value.decode("utf-8")
                if s and all(31 < ord(c) < 127 or ord(c) in (9,10,13) for c in s):
                    result[fn] = s
                else:
                    nested = _decode_proto_manual(value)
                    result[fn] = nested if nested else value.hex()
            except UnicodeDecodeError:
                nested = _decode_proto_manual(value)
                result[fn] = nested if nested else value.hex()
        elif wt == 5: offset += 4
        elif wt == 1: offset += 8
        else: break
    return result

def do_full_login(uid, pw, region="IND"):
    region = str(region or "IND").upper()
    server_url, client_url = region_endpoints(region)
    login_major = server_url.rstrip("/") + "/MajorLogin"
    login_gld   = client_url.rstrip("/") + "/GetLoginData"
    country = GEN_COUNTRY.get(region, "IN"); lang = GEN_LANG.get(region, "en")
    access_token, open_id = token_grant(uid, pw)
    if not access_token: return None
    dev = _dev32()
    req = build_majorlogin(open_id, access_token, CRAFTLAND_CLIENT_VERSION, dev, country, lang)
    login_payload = _static_aes_encrypt(req.SerializeToString())
    hdrs = dict(ML_HEADERS); hdrs["X-Ga-Sv"] = str(int(time.time()))
    try:
        resp = _rq.post(login_major, data=login_payload, headers=hdrs, verify=False, timeout=25)
    except Exception as e:
        ENGINE.log(f"MajorLogin error: {str(e)[:100]}", "err"); return None
    if resp.status_code != 200:
        ENGINE.log(f"MajorLogin HTTP {resp.status_code}: {resp.text[:120]}", "err"); return None
    ml, _ = parse_majorlogin_response(resp.content)
    if not ml.account_id or not ml.token:
        ENGINE.log(f"MajorLogin bad payload: {str(ml)[:200]}", "err"); return None
    greq, gd = build_getlogindata(open_id, access_token, CRAFTLAND_CLIENT_VERSION, dev, country, lang, region)
    gld_payload = _static_aes_encrypt(greq.SerializeToString())
    gh = dict(GLD_HEADERS); gh["X-GA-SV"] = str(int(time.time())); gh["Authorization"] = "Bearer " + ml.token
    try:
        gresp = _rq.post(login_gld, data=gld_payload, headers=gh, verify=False, timeout=25)
    except Exception as e:
        ENGINE.log(f"GetLoginData error: {str(e)[:100]}", "err"); return None
    if gresp.status_code != 200:
        ENGINE.log(f"GetLoginData HTTP {gresp.status_code}", "err"); return None
    g = GldResMsg()
    try: g.ParseFromString(gresp.content)
    except Exception as e:
        ENGINE.log(f"GetLoginData parse error: {str(e)[:80]}", "err"); return None
    functional    = g.online or ""
    informational = g.chat or ""
    if not functional:
        for s in [parse_server_entry(b) for b in g.servers]:
            if s["addr"]: functional = s["addr"]; break
    if not functional:
        ENGINE.log("GetLoginData: no functional addr", "err"); return None
    d = _decode_proto_manual(gresp.content)
    try: level = int(d.get(6, 1) or 1)
    except Exception: level = 1
    try: exp = int(d.get(7, 0) or 0)
    except Exception: exp = 0
    nickname = str(d.get(4, "")) or f"Player_{ml.account_id}"
    return {
        "account_id": ml.account_id, "nickname": nickname,
        "region": ml.region or region, "level": level, "exp": exp,
        "open_id": open_id, "access_token": access_token, "platform": "4",
        "token": ml.token, "server_time": ml.kts,
        "aes_ak": bytes(ml.ak), "iv_i": bytes(ml.aiv),
        "functional_addrs": functional, "informational_addrs": informational,
        "release_version": CRAFTLAND_RELEASE_VERSION, "client_version": CRAFTLAND_CLIENT_VERSION,
        "server_url": login_gld, "auth_uid": uid, "auth_password": pw,
        "login_payload_data": login_payload, "gld_payload_data": gld_payload,
        "auth_type": "guest",
    }

# ============================================================
# PROTO HELPERS + MATCH PARSER (c.py parity)
# ============================================================
async def _parse_results_c(parsed_results):
    out = {}
    for r in parsed_results:
        fd = {"wire_type": r.wire_type}
        if r.wire_type in ("varint", "string", "bytes"):
            fd["data"] = r.data
        elif r.wire_type == "length_delimited":
            fd["data"] = await _parse_results_c(r.data.results)
        out[str(r.field)] = fd
    return out

async def _decode_protobuf_c(data_hex):
    if not _HAS_PROTO_DECODER: return "{}"
    parsed = _ProtoParser().parse(data_hex)
    return json.dumps(await _parse_results_c(parsed))

def _get_field(d, key, default=None):
    if not isinstance(d, dict): return default
    v = d.get(key) if key in d else d.get(str(key))
    if isinstance(v, dict) and "data" in v: return v["data"]
    return v if v is not None else default

async def try_match_packet(body, default_match_code):
    res = None
    if _HAS_PROTO_DECODER:
        try: res = json.loads(await _decode_protobuf_c(body.hex()))
        except Exception: res = None
    if not isinstance(res, dict):
        try: res = _decode_proto_manual(body)
        except Exception: return None
    f4 = _get_field(res, 4)
    if f4 != 16: return None
    f5 = _get_field(res, 5)
    server_ip_port = udp_key = token = None
    match_code = default_match_code; block_val = 0
    if isinstance(f5, dict):
        for key in list(f5.keys()):
            v = _get_field(f5, key)
            if isinstance(v, str):
                if re.match(r'^\d{1,3}(\.\d{1,3}){3}:\d{2,5}$', v):
                    server_ip_port = v
                elif re.fullmatch(r'[0-9a-fA-F]{32}', v):
                    if not udp_key: udp_key = v
                    elif not token and v != udp_key: token = v
                elif v.isdigit() and 4 <= len(v) <= 6:
                    match_code = v
                elif len(v) > 100 and not v.startswith("{") and not token:
                    token = v
            elif isinstance(v, int) and block_val == 0:
                block_val = v
        if not token:
            t52 = _get_field(f5, 52)
            if isinstance(t52, str) and len(t52) >= 16: token = t52
    return {"f4": f4, "server_ip_port": server_ip_port, "udp_key": udp_key,
            "token": token, "match_code": match_code, "block_val": block_val}

def extract_position(content):
    if not content or len(content) < 12: return None
    for off in range(0, min(len(content) - 12, 96)):
        try: x, y, z = struct.unpack_from("<fff", content, off)
        except struct.error: return None
        if abs(x) > 200000 or abs(z) > 200000: continue
        if not (-1000 < y < 10000): continue
        if max(abs(x), abs(y), abs(z)) < 0.5: continue
        return (x, y, z)
    return None

# ============================================================
# TCP FRAMING
# ============================================================
async def tcp_frame(service_id, content, ak, aiv):
    enc = await aes_encrypt(content, ak, aiv)
    return bytes([service_id, REGION_BYTE, 0x00]) + len(enc).to_bytes(3, "big") + enc

def parse_server_frame(data):
    if len(data) < 5: return None
    svc = data[0]; ln = int.from_bytes(data[2:5], "big")
    if len(data) < 5 + ln: return None
    return svc, data[5:5+ln]

async def build_tcp_startup_packet(account_id, token, server_time, key, iv, typ="OnLine"):
    uid_hex = f"{int(account_id):016x}"; ts_hex = f"{int(server_time):08x}"
    enc = (await aes_encrypt(token.encode(), key, iv)).hex()
    enc_len = f"{len(enc) // 2:08x}"
    if typ == "OnLine":
        return f"7214{uid_hex}{ts_hex}00000000{enc_len}{enc}"
    return f"8114{uid_hex}{ts_hex}{enc_len}{enc}"

async def send_keep_alive():
    return bytes.fromhex("0214")

# ============================================================
# UDP PACKETS
# ============================================================
async def build_padded(content):
    pl = (8 - (len(content) + 10) % 8) % 8
    return bytes([pl, 0, 0]) + b"\x00" * pl + content + b"\x00" * 7

async def encode_header(layout, send_option, cmd, order_id, flags, length, k, v80):
    out = bytearray()
    for code in layout:
        v = {0:send_option, 1:cmd, 2:order_id, 3:flags, 4:length}[code]
        if _FIELD_SIZES[code] == 1: out.append((v & 0xFF) ^ k)
        else:
            x = ((v & 0xFFFF) ^ v80) & 0xFFFF
            out.append(x & 0xFF); out.append((x >> 8) & 0xFF)
    return bytes(out)

async def build_packet(msg_key, layout, send_option, cmd, order_id, flags, content, key, encrypted=True):
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    body = await tea_cbc_encrypt(await build_padded(content), key) if encrypted else content
    hdr = bytearray([msg_key, 0]) + await encode_header(layout, send_option, cmd, order_id, flags, len(body), k, v80)
    pkt = bytearray(hdr + body); pkt[1] = await crc7_buff(0, bytes(pkt[2:])) & 0x7F
    return bytes(pkt)

async def produce_xor_key(secret_key):
    k = secret_key[0] if secret_key and len(secret_key) > 0 else 10
    return k, ((k << 8) | k) & 0xFFFF

async def build_hello_packet(text, key, layout):
    data = text.encode("utf-8")
    if len(data) > 25: raise ValueError("Text too long")
    content = b"\x10\x00\x00\x00" + data + b"\x00" * (29 - 4 - len(data))
    k, v80 = await produce_xor_key(key)
    layout = [int(c) for c in str(layout).strip()]
    eb = await tea_cbc_encrypt(await build_padded(content), key)
    hb = await encode_header(layout, 1, 1, 0, 1, len(eb), k, v80)
    pkt = bytearray([0x63, 0x00]) + hb + eb
    pkt[1] = await crc7_buff(0, pkt[2:]) & 0x7F
    return bytes(pkt).hex()

async def layouts_from_mask(mask):
    ru = [int(c) for c in str(mask).strip()]
    nr = [c for c in ru if c != 2]
    return ru, nr

async def classify(frame):
    cmd = frame["cmd"]
    if cmd == 1: return "HELLO"
    if cmd == 2: return "ACK"
    if cmd == 3: return "PING"
    if cmd == 100: return "JOIN_MATCH"
    if cmd in (103, 107): return "MATCH_END"
    return "DATA"

async def reply_for(frame, key, mask, ack_key=0x68, ping_key=0x6D, hello_key=0x5B):
    _, nr = await layouts_from_mask(mask)
    typ = await classify(frame)
    if typ == "HELLO":
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x01\x00", key)
    if typ == "ACK":
        c = frame["content"] if frame["content"] else b"\x01\x00"
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, c, key)
    if typ == "PING":
        c = frame["content"]; counter = c[:4] if len(c) >= 4 else c
        return typ, await build_packet(ping_key, nr, 0, 3, None, 0, counter + b"\x00\x00\x00", key, encrypted=False)
    if typ == "JOIN_MATCH":
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x02\x00", key)
    return typ, None

async def keepalive_ping(sock, ip, port, key_bytes, mask, stop_event):
    _, nr = await layouts_from_mask(mask)
    ping_keys = [0x66, 0x6D, 0x69, 0x6C, 0x6B, 0x6E, 0x6F, 0x70]
    templates = []
    for pk in ping_keys:
        pkt = await build_packet(pk, nr, 0, 3, None, 0, b"\x00" * 7, key_bytes, encrypted=False)
        templates.append(bytearray(pkt))
    loop = asyncio.get_event_loop(); i = 0
    while not stop_event.is_set():
        buf = templates[i % len(templates)]
        counter = int(time.time() * 1000) & 0xFFFFFFFF
        off = len(buf) - 7; buf[off:off+4] = struct.pack("<I", counter)
        try: await loop.sock_sendto(sock, bytes(buf), (ip, port))
        except Exception: pass
        i += 1
        try: await asyncio.wait_for(stop_event.wait(), timeout=3.0)
        except asyncio.TimeoutError: pass

async def has_ssan_zig(n):
    z = (n << 1) & 0xFFFFFFFFFFFFFFFF; out = bytearray()
    while z >= 0x80: out.append((z & 0x7F) | 0x80); z >>= 7
    out.append(z); return bytes(out)

async def uleb_encode(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n: b |= 0x80
        out.append(b)
        if not n: break
    return bytes(out)

async def build_match_startup_packets(token, udp_key, match_code, account_id, block_val,
                                     server_ip="", client_version=CRAFTLAND_CLIENT_VERSION,
                                     client_version_code="2019121227", access_token=""):
    udp_key = bytes.fromhex(udp_key)
    match_code = [int(ch) for ch in str(match_code).strip()]
    thunder_jwt = token[:660] if len(token) > 660 else token
    sharma_jwt  = token[660:] if len(token) > 660 else ""
    enc_thunder = thunder_jwt.encode() if isinstance(thunder_jwt, str) else thunder_jwt
    enc_sharma  = sharma_jwt.encode() if isinstance(sharma_jwt, str) else sharma_jwt
    garena420 = await has_ssan_zig(len(enc_thunder)) + enc_thunder
    csoversea_block = bytes.fromhex(
        "ca0163736f7665727365612e7374726f6e67686f6c642e66726565666972656d6f62696c652e636f6d"
        "3b302e302e302e303b33342e3132362e37362e34353b33342e38372e3137372e31343b33342e38372e"
        "3137302e3233303b33352e3138352e3138332e35370000000000000100000000000000000000000001"
        "00000800000100000000000100a8a2d7bebd8d8bdf110200")
    mid = bytes.fromhex("0000000001000102030101") + await has_ssan_zig(len(REGION)) + REGION.encode()
    mid += bytes.fromhex("0001030003000004")
    mid += await has_ssan_zig(len(client_version)) + client_version.encode()
    mid += await has_ssan_zig(len(client_version_code)) + client_version_code.encode()
    mid += csoversea_block
    clean_ip = server_ip.split(":")[0] if server_ip else "0.0.0.0"
    mid += await has_ssan_zig(len(clean_ip)) + clean_ip.encode()
    if access_token:
        mid += await has_ssan_zig(len(access_token)) + access_token.encode()
    mid += await has_ssan_zig(len(enc_sharma)) + enc_sharma
    tg = (await uleb_encode(int(account_id)) + await uleb_encode(int(block_val)) +
          await uleb_encode(1) + await uleb_encode(43) + await uleb_encode(int(block_val)) +
          await uleb_encode(11) + mid)
    process = await build_packet(0x5E, match_code, 2, 447, 0, 1, garena420, udp_key)
    loading = await build_packet(0x5A, match_code, 2, 448, 1, 1, tg, udp_key)
    return process.hex(), loading.hex()

async def try_header(buf, layout, k, v80):
    off = 2; out = {}
    for code in layout:
        size = _FIELD_SIZES[code]
        if off + size > len(buf): return None
        out[_FIELD_NAMES[code]] = (buf[off] ^ k) if size == 1 else ((buf[off] | (buf[off+1] << 8)) ^ v80) & 0xFFFF
        off += size
    out["headerLen"] = off; return out

async def oicq_unpad(padded):
    if not padded or len(padded) < 8: return None
    if not all(padded[-1-i] == 0 for i in range(7)): return None
    pl = padded[0] & 0x07; s = 3 + pl; e = len(padded) - 7
    return padded[s:e] if s < e else b""

async def decode_packet(packet, key, mask=None):
    data = bytes(packet) if isinstance(packet, bytes) else bytes.fromhex(packet)
    if len(data) < 8: return None
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    crc_ok = (data[1] & 0x7F) == await crc7_buff(0, data[2:])
    if mask:
        ru, nr = await layouts_from_mask(mask)
        layouts = [("RUDP", ru), ("nonRUDP", nr)]
    else:
        import itertools
        layouts = [("RUDP", list(p)) for p in itertools.permutations([0,1,2,3,4])]
        layouts += [("nonRUDP", list(p)) for p in itertools.permutations([0,1,3,4])]
    best = None
    for kind, layout in layouts:
        f = await try_header(data, layout, k, v80)
        if not f or f["flags"] > 7 or f["sendOption"] > 7: continue
        if f["length"] != len(data) - f["headerLen"]: continue
        body = data[f["headerLen"]:f["headerLen"] + f["length"]]
        content = None
        if f["flags"] & 1:
            if len(body) < 8 or len(body) % 8 != 0: continue
            padded = await tea_cbc_decrypt(body, key)
            content = await oicq_unpad(padded)
            if content is None: continue
        else: content = body
        score = (1 if crc_ok else 0) + (1 if content is not None else 0) + (1 if kind == "RUDP" else 0)
        cand = {"kind": kind, "layout": layout, "headerLen": f["headerLen"],
                "msgKey": data[0], "cmd": f["cmd"], "flags": f["flags"],
                "sendOption": f["sendOption"], "orderId": f.get("orderId"),
                "length": f["length"], "content": content,
                "crcOk": crc_ok, "score": score, "total": len(data)}
        if best is None or cand["score"] > best["score"]: best = cand
    return best

# ============================================================
# PLAY GAME (UDP)
# ============================================================
async def play_game(server_ip_port, thunder, sharma, udp_key, match_code,
                    account_id, client_version, radar_base_id):
    start = time.time(); sock = None; ping_task = None
    ping_stop = asyncio.Event()
    uid = str(account_id); completed = False; radar_id = radar_base_id
    try:
        ip, port = server_ip_port.split(":"); port = int(port)
        resolved = await resolve_host(ip)
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        optimize_udp_socket(sock); sock.setblocking(False)
        key_bytes = bytes.fromhex(udp_key)
        hello = await build_hello_packet(f"{account_id}_2585", key_bytes, match_code)
        await loop.sock_sendto(sock, bytes.fromhex(hello), (resolved, port))
        ack_state = "waiting_for_hello_reply"
        thunder_sent = sharma_sent = False
        send_lock = asyncio.Lock()
        ping_task = asyncio.create_task(keepalive_ping(sock, resolved, port, key_bytes, match_code, ping_stop))
        last_act = time.time()

        async def send_ts():
            nonlocal ack_state, thunder_sent, sharma_sent
            if thunder_sent: return
            async with send_lock:
                if thunder_sent: return
                try:
                    await loop.sock_sendto(sock, bytes.fromhex(thunder), (resolved, port))
                    thunder_sent = True; await asyncio.sleep(0.1)
                    pa = await build_packet(0x68, (await layouts_from_mask(match_code))[1],
                                            0, 2, None, 1, b"\x01\x00", key_bytes)
                    await loop.sock_sendto(sock, pa, (resolved, port))
                    await asyncio.sleep(0.2)
                    await loop.sock_sendto(sock, bytes.fromhex(sharma), (resolved, port))
                    sharma_sent = True; ack_state = "thunder_sharma_sent"
                except Exception: pass

        while True:
            if time.time() - start > MAX_MATCH_DURATION: break
            try:
                resp, addr = await asyncio.wait_for(loop.sock_recvfrom(sock, 65535), timeout=1.5)
                if resp:
                    last_act = time.time()
                    fr = await decode_packet(resp, key_bytes, match_code)
                    if fr:
                        ptype = await classify(fr)
                        if ptype == "MATCH_END":
                            completed = True; break
                        if fr["cmd"] in RADAR_CMDS and fr.get("content"):
                            pos = extract_position(fr["content"])
                            if pos:
                                radar_id += 1
                                asyncio.ensure_future(RADAR.feed(radar_id, *pos))
                        if ptype in ("ACK", "PING", "HELLO", "JOIN_MATCH"):
                            if ptype == "HELLO" and ack_state == "waiting_for_hello_reply":
                                _, rep = await reply_for(fr, key_bytes, match_code)
                                if rep: await loop.sock_sendto(sock, rep, addr)
                                ack_state = "ack_sent_waiting"
                            elif ptype == "ACK":
                                if ack_state == "waiting_for_hello_reply":
                                    _, rep = await reply_for(fr, key_bytes, match_code)
                                    if rep: await loop.sock_sendto(sock, rep, addr)
                                    ack_state = "ready_to_send_thunder"
                                elif ack_state == "ack_sent_waiting":
                                    ack_state = "ready_to_send_thunder"
                                else:
                                    _, rep = await reply_for(fr, key_bytes, match_code)
                                    if rep: await loop.sock_sendto(sock, rep, addr)
                            elif ptype == "PING":
                                _, rep = await reply_for(fr, key_bytes, match_code)
                                if rep: await loop.sock_sendto(sock, rep, addr)
                            elif ptype == "JOIN_MATCH":
                                _, rep = await reply_for(fr, key_bytes, match_code)
                                if rep: await loop.sock_sendto(sock, rep, addr)
            except asyncio.TimeoutError:
                if ack_state == "ready_to_send_thunder" and not thunder_sent:
                    await send_ts()
                elif ack_state == "waiting_for_hello_reply":
                    if time.time() - last_act > 7.0:
                        try:
                            p = await build_hello_packet(f"{account_id}_2585", key_bytes, match_code)
                            await loop.sock_sendto(sock, bytes.fromhex(p), (resolved, port))
                        except Exception: pass
                        last_act = time.time()
                    if time.time() - start > 25.0: break
                elif ack_state == "thunder_sharma_sent":
                    if time.time() - last_act > MATCH_IDLE_TIMEOUT:
                        completed = True; break
                continue
            except Exception:
                await asyncio.sleep(0.5); continue
            if ack_state == "ready_to_send_thunder" and not thunder_sent:
                await send_ts()
        return "finished" if completed else "error"
    finally:
        if completed:
            ENGINE.inc_match(uid)
            ENGINE.log(f"[MATCH] {uid} completed", "ok")
        ping_stop.set()
        if ping_task:
            ping_task.cancel()
            try: await ping_task
            except asyncio.CancelledError: pass
        if sock:
            try: sock.close()
            except Exception: pass

# ============================================================
# ROOM CODE PATCHER
# ============================================================
def _emit_varint(v):
    out = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        if v: out.append(b | 0x80)
        else: out.append(b); break
    return bytes(out)

def _parse_fields(data):
    fields = []; i = 0
    while i < len(data):
        key = 0; sh = 0
        while True:
            b = data[i]; i += 1
            key |= (b & 0x7F) << sh
            if not (b & 0x80): break
            sh += 7
        fn, wt = key >> 3, key & 7
        if wt == 0:
            v = 0; sh = 0
            while True:
                b = data[i]; i += 1
                v |= (b & 0x7F) << sh
                if not (b & 0x80): break
                sh += 7
            fields.append([fn, wt, v])
        elif wt == 2:
            ln = 0; sh = 0
            while True:
                b = data[i]; i += 1
                ln |= (b & 0x7F) << sh
                if not (b & 0x80): break
                sh += 7
            fields.append([fn, wt, data[i:i+ln]]); i += ln
        else: raise ValueError("wt")
    return fields

def _emit_fields(fields):
    out = bytearray()
    for fn, wt, v in fields:
        out += _emit_varint((fn << 3) | wt)
        if wt == 0: out += _emit_varint(v)
        else: out += _emit_varint(len(v)); out += v
    return bytes(out)

def patch_room_code(payload, code):
    fields = _parse_fields(payload)
    for idx, (fn, wt, v) in enumerate(fields):
        if fn == 2 and wt == 2:
            sub = _parse_fields(v)
            for j, (f2, w2, v2) in enumerate(sub):
                if f2 == 2 and w2 == 2: sub[j][2] = code.encode()
            fields[idx][2] = _emit_fields(sub)
    return _emit_fields(fields)

# ============================================================
# INFORMATIONAL (chat gateway)
# ============================================================
async def informational(account_data, stop_event):
    addr = account_data.get("informational_addrs")
    if not addr: return
    reconnects = 0
    try: ip, port = addr.split(":")
    except Exception: return
    while not stop_event.is_set():
        writer = None; ping_task = None
        try:
            resolved = await resolve_host(ip)
            reader, writer = await asyncio.open_connection(resolved, int(port))
            raw = writer.get_extra_info("socket")
            if raw: optimize_tcp_socket(raw)
            chat_pkt = await build_tcp_startup_packet(
                account_data["account_id"], account_data["token"], account_data["server_time"],
                account_data["aes_ak"], account_data["iv_i"], typ="ChaT")
            writer.write(bytes.fromhex(chat_pkt)); await writer.drain()
            reconnects = 0
            try:
                writer.write(await send_keep_alive())
                await asyncio.wait_for(writer.drain(), timeout=3)
            except Exception: pass
            try:
                ake = bytes(account_data["aes_ak"]); aive = bytes(account_data["iv_i"])
                for cj in ("0803120610051a02656e", "08031206100b1a02656e"):
                    writer.write(await tcp_frame(0x12, bytes.fromhex(cj), ake, aive))
                await writer.drain()
            except Exception: pass

            async def ka():
                pkt = await send_keep_alive()
                while not stop_event.is_set():
                    await asyncio.sleep(5)
                    try:
                        if writer and not writer.is_closing():
                            writer.write(pkt); await writer.drain()
                    except Exception: break
            ping_task = asyncio.create_task(ka())
            while not stop_event.is_set():
                data = await reader.read(8192)
                if not data: raise ConnectionError("closed")
        except asyncio.CancelledError: break
        except Exception:
            if stop_event.is_set(): break
            reconnects += 1
            if reconnects > 3: await asyncio.sleep(3); reconnects = 0
            else: await asyncio.sleep(1)
        finally:
            if ping_task: ping_task.cancel()
            if writer:
                try: writer.close(); await writer.wait_closed()
                except Exception: pass

# ============================================================
# FUNCTIONAL LOOP (matchmaker + room)
# ============================================================
async def functional_craft(account_data, stop_event):
    play_matches = []
    uid = str(account_data["account_id"])
    radar_counter = random.randint(1000, 99999)
    tcp_online = await build_tcp_startup_packet(
        account_data["account_id"], account_data["token"], account_data["server_time"],
        account_data["aes_ak"], account_data["iv_i"], typ="OnLine")
    info_task = asyncio.create_task(informational(account_data, stop_event))
    exp_task = None
    if EXP_REFRESH_INTERVAL > 0:
        async def exp_loop():
            while not stop_event.is_set():
                await asyncio.sleep(EXP_REFRESH_INTERVAL)
                if stop_event.is_set(): break
                try: await asyncio.to_thread(_refresh_sync, account_data)
                except Exception: pass
        exp_task = asyncio.create_task(exp_loop())
    try:
        reconnects = 0
        while not stop_event.is_set():
            writer = None
            try:
                addr = account_data["functional_addrs"]
                ip, port = addr.split(":")
                resolved = await resolve_host(ip)
                reader, writer = await asyncio.open_connection(resolved, int(port))
                raw = writer.get_extra_info("socket")
                if raw: optimize_tcp_socket(raw)
                writer.write(bytes.fromhex(tcp_online)); await writer.drain()
                try:
                    writer.write(await send_keep_alive())
                    await asyncio.wait_for(writer.drain(), timeout=3)
                except Exception: pass
                ak = bytes(account_data["aes_ak"]); aiv = bytes(account_data["iv_i"])
                _map_code = (ENGINE.config.get("map_code") or "").strip()
                if not _map_code:
                    ENGINE.log("[ERR] no map_code configured", "err"); return
                rj_raw = patch_room_code(bytes.fromhex(_ROOM_JOIN_TEMPLATE_HEX), _map_code)
                mm_frame    = await tcp_frame(SVC_MATCHMAKING, bytes.fromhex(_MATCHMAKING_TEMPLATE_HEX), ak, aiv)
                gin_hello   = await tcp_frame(SVC_GIN, bytes.fromhex(_GIN_HELLO_TEMPLATE_HEX), ak, aiv)
                gin_ack_tpl = await tcp_frame(SVC_GIN, bytes.fromhex(_GIN_ACK_TEMPLATE_HEX), ak, aiv)
                _s2 = _load_stage2()
                gin_stage2_tpl = await tcp_frame(SVC_GIN, bytes.fromhex(_s2), ak, aiv) if _s2 else b""
                room_join_tpl = await tcp_frame(SVC_ROOM, rj_raw, ak, aiv)
                ENGINE.set_status(uid, "ONLINE")
                reconnects = 0; no_resp = 0
                last_start = 0.0; recv_buf = bytearray()
                ENGINE.log(f"[TCP] {uid} connected -> {addr}", "ok")
                writer.write(gin_hello); await writer.drain()

                async def send_match():
                    nonlocal last_start
                    try:
                        if account_reached_target(uid): return
                        await asyncio.sleep(random.uniform(0.3, 0.6))
                        writer.write(mm_frame); await writer.drain()
                        ENGINE.set_status(uid, "SEARCHING")
                    except Exception: pass
                    last_start = asyncio.get_running_loop().time()

                async def send_room_join():
                    try:
                        writer.write(room_join_tpl); await writer.drain()
                    except Exception: pass

                await send_match(); await send_room_join()
                last_gin2 = 0.0; last_rj = asyncio.get_running_loop().time()

                while not stop_event.is_set():
                    play_matches[:] = [m for m in play_matches if not m.done()]
                    if account_reached_target(uid) and not any(not m.done() for m in play_matches):
                        ENGINE.log(f"[DONE] {uid} reached target", "ok")
                        try: writer.close(); await writer.wait_closed()
                        except Exception: pass
                        return
                    now = asyncio.get_running_loop().time()
                    if now - last_start >= START_MATCH_INTERVAL and not account_reached_target(uid):
                        await send_match()
                    if now - last_rj >= ROOM_JOIN_INTERVAL:
                        await send_room_join(); last_rj = now
                    if gin_stage2_tpl and now - last_gin2 >= 150.0:
                        try: writer.write(gin_stage2_tpl); await writer.drain()
                        except Exception: pass
                        last_gin2 = now
                    try:
                        data = await asyncio.wait_for(reader.read(8192), timeout=2.0)
                    except asyncio.TimeoutError:
                        no_resp += 1
                        if no_resp > 80 and not account_reached_target(uid):
                            raise ConnectionError("Gateway idle")
                        continue
                    if not data: raise ConnectionError("closed")
                    no_resp = 0; recv_buf.extend(data)
                    frame = parse_server_frame(bytes(recv_buf))
                    if not frame:
                        if len(recv_buf) > 262144: recv_buf.clear()
                        continue
                    svc, body = frame
                    del recv_buf[:5+len(body)]
                    log_traffic("S2C", svc, body)
                    if AUTO_ACCEPT_FRIEND and svc == 0x06 and len(body) > 10:
                        try: asyncio.ensure_future(auto_accept_friend(body, account_data))
                        except Exception: pass
                        continue
                    if svc == SVC_GIN and len(body) == 0x6B:
                        try: writer.write(gin_ack_tpl); await writer.drain()
                        except Exception: pass
                        continue
                    if svc == SVC_GIN and len(body) == 0xB4: continue
                    if svc == SVC_ROOM and len(body) < 200: continue
                    if svc == SVC_MATCHMAKING and 10 < len(body) < 30: continue
                    if svc in (SVC_MATCHMAKING, SVC_ROOM) and len(body) >= 200:
                        try:
                            info = await try_match_packet(
                                body, str(ENGINE.config.get("map_code", "21403")))
                        except Exception as e:
                            info = None
                            ENGINE.log(f"[MATCH] parse err {e}", "err")
                        if info is not None:
                            try:
                                ENGINE.log(f"[MATCH] {uid} MATCH FOUND svc={svc:02x}", "ok")
                                server = info["server_ip_port"]
                                udp_key = info["udp_key"]
                                token = info["token"] or str(account_data["account_id"])
                                mcode = info["match_code"]
                                bval  = info["block_val"]
                                ENGINE.log(f"[MATCH] server={server} key={udp_key} mask={mcode} tok={str(token)[:24]}", "info")
                                if udp_key and server:
                                    thunder, sharma = await build_match_startup_packets(
                                        token, udp_key, mcode, account_data["account_id"], bval,
                                        server_ip=server,
                                        client_version=account_data["client_version"],
                                        access_token=account_data.get("access_token", ""))
                                    await GLOBAL_MATCH_SEM.acquire(); radar_counter += 1000
                                    async def _run():
                                        try:
                                            return await play_game(server, thunder, sharma,
                                                                   udp_key, mcode,
                                                                   account_data["account_id"],
                                                                   account_data["client_version"],
                                                                   radar_counter)
                                        finally: GLOBAL_MATCH_SEM.release()
                                    play_matches.append(asyncio.create_task(_run()))
                                else:
                                    ENGINE.log(f"[MATCH] packet missing fields", "warn")
                            except Exception as e:
                                ENGINE.log(f"[MATCH] launch err {e}", "err")
                            try: writer.close(); await writer.wait_closed()
                            except Exception: pass
                            await asyncio.sleep(1.0)
                            break
            except asyncio.CancelledError:
                for m in play_matches:
                    if not m.done(): m.cancel()
                if play_matches: await asyncio.gather(*play_matches, return_exceptions=True)
                raise
            except Exception as e:
                if stop_event.is_set(): break
                ENGINE.log(f"[TCP] {uid} disc: {type(e).__name__}: {e}", "warn")
                if writer:
                    try: writer.close(); await writer.wait_closed()
                    except Exception: pass
                reconnects += 1
                if reconnects > 12:
                    ENGINE.log(f"[TCP] {uid} max reconnects — re-login", "warn")
                    cache_invalidate(str(account_data.get("auth_uid", "")))
                    fresh = await asyncio.to_thread(do_full_login,
                                                    str(account_data.get("auth_uid", "")),
                                                    account_data.get("auth_password", ""),
                                                    account_data.get("region", "IND"))
                    if fresh:
                        account_data = fresh
                        tcp_online = await build_tcp_startup_packet(
                            account_data["account_id"], account_data["token"],
                            account_data["server_time"], account_data["aes_ak"],
                            account_data["iv_i"], typ="OnLine")
                    reconnects = 0
                    await asyncio.sleep(5)
                    continue
                await asyncio.sleep(min(reconnects, 3))
    finally:
        for t in (info_task, exp_task):
            if t and not t.done(): t.cancel()
        for t in (info_task, exp_task):
            if t:
                try: await t
                except (asyncio.CancelledError, Exception): pass
        for m in play_matches:
            if not m.done(): m.cancel()
        if play_matches: await asyncio.gather(*play_matches, return_exceptions=True)

# ============================================================
# FRIEND + EXP REFRESH (c.py parity)
# ============================================================
def _wrap_manual(inner):
    try:
        alt = _decode_proto_manual(inner)
        if alt: return {str(k): {"data": v} for k, v in alt.items()}
    except Exception: pass
    return None

def _friend_target_uid(raw):
    candidates = []
    if len(raw) >= 6:
        plen = raw[4]
        if 0 < plen <= (len(raw) - 5):
            d0 = _wrap_manual(bytes(raw[5:5+plen]))
            if d0: candidates.append(d0)
    hx = raw.hex()
    for off in (5, 6, 10, 8, 12, 4, 0):
        if off >= len(hx): continue
        try: inner = bytes.fromhex(hx[off:])
        except Exception: continue
        d = _wrap_manual(inner)
        if d: candidates.append(d)
    if not candidates: return None
    candidates.sort(key=lambda x: len(x), reverse=True)
    dec = candidates[0]
    def _v(c, k):
        if not isinstance(c, dict): return None
        v = c.get(k) if k in c else c.get(str(k))
        if isinstance(v, dict) and "data" in v: return v["data"]
        return v
    f5w = dec.get("5") or dec.get(5)
    f5 = f5w["data"] if isinstance(f5w, dict) and "data" in f5w else f5w
    if isinstance(f5, dict):
        for fk in (1, 2, 3, 4, 6):
            c = _v(f5, fk)
            if c and str(c).isdigit() and 6 <= len(str(c)) <= 15: return str(c)
    return None

async def auto_accept_friend(raw, ad):
    try:
        target = _friend_target_uid(raw)
        if not target: return
        own = str(ad.get("account_id", ""))
        if not own or target == own: return
        jwt = ad.get("token"); srv = ad.get("server_url"); rel = ad.get("release_version")
        if not (jwt and srv and rel): return
        base = srv.split("/GetLoginData")[0].rstrip("/")
        payload = _static_aes_encrypt(_g_fvint(1, int(target)) + _g_fvint(2, int(own)))
        hdrs = {"authorization": f"Bearer {jwt}",
                "host": base.replace("https://", "").replace("http://", ""),
                "x-ga": "v1 1", "content-type": "application/x-www-form-urlencoded",
                "accept-encoding": "deflate, gzip", "releaseversion": str(rel),
                "user-agent": "UnityPlayer/2022.3.47f1", "accept": "*/*",
                "x-unity-version": "2022.3.47f1"}
        async with httpx.AsyncClient(verify=False, timeout=8.0) as cli:
            r = await cli.post(base + "/ConfirmFriendRequest", headers=hdrs, content=payload)
        if r.status_code == 200 and len(r.content) > 0:
            ENGINE.log(f"[FRIEND] auto-accept -> {target}", "ok")
    except Exception: pass

def _refresh_sync(account_data):
    url = account_data.get("server_url"); token = account_data.get("token")
    payload = account_data.get("gld_payload_data") or account_data.get("login_payload_data")
    if not (url and token and payload): return
    if isinstance(payload, str):
        try: payload = bytes.fromhex(payload)
        except Exception: return
    gh = dict(GLD_HEADERS); gh["X-GA-SV"] = str(int(time.time()))
    gh["Authorization"] = "Bearer " + token
    try:
        r = _rq.post(url, data=payload, headers=gh, verify=False, timeout=25)
        if r.status_code != 200: return
        d = _decode_proto_manual(r.content)
        try: level = int(d.get(6, 1) or 1)
        except Exception: level = 1
        try: exp = int(d.get(7, 0) or 0)
        except Exception: exp = 0
        acc = str(account_data["account_id"])
        if exp > 0: ENGINE.update_exp(acc, exp, level)
        ENGINE.log(f"[EXP-REFRESH] UID {acc} -> L{level} EXP {exp}", "info")
    except Exception: pass

# ============================================================
# ACCOUNT LOOP + TARGET
# ============================================================
def get_target_matches():
    mode = ENGINE.config.get("match_mode", "unlimited")
    if mode == "single": return 1
    if mode == "custom": return int(ENGINE.config.get("matches_per_id", 5))
    return -1

def account_reached_target(uid):
    t = get_target_matches()
    if t == -1: return False
    a = ENGINE.accounts.get(str(uid))
    return bool(a and a["matches"] >= t)

async def account_loop(uid, password, region, stop_event):
    uid = str(uid)
    while not stop_event.is_set():
        try:
            ENGINE.set_status(uid, "CONNECTING")
            cached = cache_get(uid)
            if cached:
                cached = _restore_bytes(cached)
                ENGINE.add_account(str(cached["account_id"]), cached.get("nickname"),
                                   cached.get("region", "IND"), cached.get("level", 1), cached.get("exp", 0))
                ad = cached
            else:
                async with GLOBAL_LOGIN_SEM:
                    ad = await asyncio.to_thread(do_full_login, uid, password, region)
                if not ad:
                    ENGINE.set_status(uid, "LOGIN_FAILED")
                    await asyncio.sleep(15); continue
                ENGINE.add_account(str(ad["account_id"]), ad["nickname"], ad["region"], ad["level"], ad["exp"])
                cache_set(uid, ad)
            await functional_craft(ad, stop_event)
            if account_reached_target(str(ad["account_id"])):
                return
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            ENGINE.set_status(uid, "OFFLINE"); break
        except Exception as e:
            ENGINE.log(f"[ACCT] {uid} err: {e}", "err")
            await asyncio.sleep(10)

def _restore_bytes(d):
    if not isinstance(d, dict): return d
    out = {}
    for k, v in d.items():
        if k in ("aes_ak", "iv_i", "login_payload_data", "gld_payload_data") and isinstance(v, str):
            try: out[k] = bytes.fromhex(v)
            except Exception: out[k] = b""
        else: out[k] = v
    return out

# ============================================================
# ACCOUNT FILE HELPERS
# ============================================================
def load_accounts_file():
    if not os.path.exists(ACCOUNTS_FILE):
        if FALLBACK_UID and FALLBACK_PASSWORD:
            return [{"uid": FALLBACK_UID, "password": FALLBACK_PASSWORD, "region": "IND"}]
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []

def _append_account(acc):
    existing = load_accounts_file()
    existing.append({"uid": acc["uid"], "password": acc["password"], "region": acc.get("region", "IND")})
    try:
        tmp = ACCOUNTS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(existing, f, indent=2)
        os.replace(tmp, ACCOUNTS_FILE)
    except Exception: pass

def _save_region_uids(region, acc):
    fname = os.path.join(BASE_DIR, f"uids_{region.upper()}.json")
    data = []
    if os.path.exists(fname):
        try:
            with open(fname, encoding="utf-8") as f: data = json.load(f)
            if not isinstance(data, list): data = []
        except Exception: data = []
    data.append({"uid": acc["uid"], "password": acc["password"],
                 "nickname": acc.get("nickname",""), "region": region.upper(),
                 "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    try:
        with open(fname, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)
    except Exception as e:
        ENGINE.log(f"region uid save: {e}", "err")

# ============================================================
# WEB UI (HTML)
# ============================================================
HTML_UI = """<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zesty Craft Land UDP — Control Panel</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0a0e17;--card:#111827;--border:#1f2937;--green:#00ff88;--red:#ff4466;
      --yellow:#ffbb33;--blue:#44aaff;--text:#e5e7eb;--muted:#6b7280}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',sans-serif;min-height:100vh;padding:16px}
.wrap{max-width:1400px;margin:0 auto}
h1{font-size:22px;font-weight:700;margin-bottom:4px}
h1 span{color:var(--green)}
.sub{color:var(--muted);font-size:13px;margin-bottom:20px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px}
.card h2{font-size:14px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:14px}
label{display:block;font-size:12px;color:var(--muted);margin-bottom:6px;margin-top:12px}
label:first-of-type{margin-top:0}
input,select{width:100%;padding:10px 12px;background:#0f172a;border:1px solid var(--border);
             border-radius:6px;color:var(--text);font-size:14px;outline:none}
input:focus,select:focus{border-color:var(--green)}
input::placeholder{color:#4b5563}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.btns{display:flex;gap:10px;margin-top:18px}
.btn{flex:1;padding:12px;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer;transition:all .15s}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn-start{background:var(--green);color:#000}
.btn-start:hover:not(:disabled){background:#00dd77}
.btn-stop{background:var(--red);color:#fff}
.btn-stop:hover:not(:disabled){background:#dd3355}
.btn-restart{background:var(--yellow);color:#000}
.btn-restart:hover:not(:disabled){background:#eeaa22}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
@media(max-width:700px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;text-align:center}
.stat .val{font-size:26px;font-weight:700;color:var(--green)}
.stat .lbl{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:4px}
.status-bar{padding:12px 18px;background:var(--card);border:1px solid var(--border);border-radius:10px;
            margin-bottom:16px;display:flex;align-items:center;gap:12px}
.dot{width:10px;height:10px;border-radius:50%;background:var(--muted)}
.dot.running{background:var(--green);animation:pulse 1.5s infinite}
.dot.starting{background:var(--yellow);animation:pulse 1s infinite}
.dot.error{background:var(--red)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:8px;color:var(--muted);font-weight:600;font-size:11px;
   text-transform:uppercase;border-bottom:1px solid var(--border)}
td{padding:8px;border-bottom:1px solid #1a2332;font-family:monospace}
tr:last-child td{border-bottom:none}
.tag{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;text-transform:uppercase}
.tag.online,.tag.searching{background:rgba(0,255,136,.15);color:var(--green)}
.tag.searching{background:rgba(255,187,51,.15);color:var(--yellow)}
.tag.offline{background:rgba(107,114,128,.2);color:var(--muted)}
.tag.error,.tag.login_failed,.tag.connecting{background:rgba(255,68,102,.15);color:var(--red)}
.logs{max-height:360px;overflow-y:auto;font-family:monospace;font-size:12px;line-height:1.6;
      background:#0f172a;border-radius:6px;padding:12px}
.logs div{padding:1px 0;border-bottom:1px solid #1a2332}
.logs .t{color:var(--muted);margin-right:6px}
.logs .ok{color:var(--green)}.logs .err{color:var(--red)}
.logs .warn{color:var(--yellow)}.logs .info{color:var(--blue)}
.empty{text-align:center;color:var(--muted);padding:30px;font-size:13px}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-thumb{background:#374151;border-radius:3px}
</style></head><body><div class="wrap">
<h1>⚡ Zesty <span>Craft Land UDP</span></h1>
<div class="sub">Full c.py parity · Web control panel · engine runs only on demand</div>
<div class="status-bar"><div class="dot" id="dot"></div>
<div><strong id="statusText">IDLE</strong>
<span id="statusExtra" style="color:var(--muted);font-size:12px;margin-left:8px"></span></div></div>
<div class="stats">
<div class="stat"><div class="val" id="sAcc">0</div><div class="lbl">Accounts</div></div>
<div class="stat"><div class="val" id="sMatch">0</div><div class="lbl">Total Matches</div></div>
<div class="stat"><div class="val" id="sRun">0s</div><div class="lbl">Uptime</div></div>
<div class="stat"><div class="val" id="sLast">—</div><div class="lbl">Last Match</div></div></div>
<div class="grid">
<div class="card"><h2>⚙ Configuration</h2>
<label>Map / Room Code (required)</label>
<input id="mapCode" placeholder="e.g. V96H00 or Q07D64">
<div class="row">
<div><label>Region</label>
<select id="region"><option value="ALL">ALL (rotate)</option>
<option value="IND">IND</option><option value="ID">ID</option><option value="TH">TH</option>
<option value="ME">ME</option><option value="EUROPE">EUROPE</option><option value="VN">VN</option>
<option value="BD">BD</option><option value="PK">PK</option><option value="TW">TW</option>
<option value="RU">RU</option><option value="NA">NA</option><option value="SAC">SAC</option>
<option value="BR">BR</option><option value="SG">SG</option><option value="US">US</option></select></div>
<div><label>Total IDs to run</label>
<input id="totalIds" type="number" value="5" min="1"></div></div>
<div class="row">
<div><label>Generate new accounts</label>
<input id="genCount" type="number" value="0" min="0"></div>
<div><label>Match mode</label>
<select id="matchMode">
<option value="single">Single match per ID</option>
<option value="custom">Custom (set count)</option>
<option value="unlimited" selected>Unlimited (loop)</option></select></div></div>
<div id="customRow" style="display:none">
<label>Matches per ID</label><input id="matchesPerId" type="number" value="5" min="1"></div>
<div class="btns">
<button class="btn btn-start" id="btnStart" onclick="start()">▶ Start</button>
<button class="btn btn-stop" id="btnStop" onclick="stop()">⏹ Stop</button>
<button class="btn btn-restart" id="btnRestart" onclick="restart()">⟳ Restart</button></div>
<div id="msg" style="margin-top:12px;font-size:12px;color:var(--muted)"></div></div>
<div class="card"><h2>📊 Live Accounts</h2>
<div style="max-height:400px;overflow-y:auto"><table>
<thead><tr><th>UID</th><th>Nickname</th><th>Reg</th><th>Lvl</th><th>EXP</th><th>Matches</th><th>Status</th></tr></thead>
<tbody id="accBody"><tr><td colspan="7" class="empty">No accounts yet</td></tr></tbody>
</table></div></div></div>
<div class="card"><h2>📜 Logs</h2>
<div class="logs" id="logs"><div class="empty">Waiting...</div></div></div>
</div>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
$('matchMode').addEventListener('change',()=>{$('customRow').style.display=$('matchMode').value==='custom'?'block':'none';});
async function api(p,b){const o=b?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}:{};const r=await fetch(p,o);return await r.json();}
function getCfg(){return{map_code:$('mapCode').value.trim(),region:$('region').value,
  total_ids:parseInt($('totalIds').value)||1,generate_count:parseInt($('genCount').value)||0,
  match_mode:$('matchMode').value,matches_per_id:parseInt($('matchesPerId').value)||1};}
async function start(){const c=getCfg();if(!c.map_code){$('msg').textContent='❌ Map code required';return}
  $('msg').textContent='Starting...';const r=await api('/api/start',c);$('msg').textContent=(r.ok?'✅ ':'❌ ')+r.message;}
async function stop(){const r=await api('/api/stop',{});$('msg').textContent=(r.ok?'✅ ':'❌ ')+r.message;}
async function restart(){const c=getCfg();if(!c.map_code){$('msg').textContent='❌ Map code required';return}
  $('msg').textContent='Restarting...';const r=await api('/api/restart',c);$('msg').textContent=(r.ok?'✅ ':'❌ ')+r.message;}
function fmtU(s){if(s<60)return s+'s';if(s<3600)return Math.floor(s/60)+'m';return Math.floor(s/3600)+'h '+(Math.floor(s%3600/60))+'m';}
async function tick(){try{const d=await api('/api/status');
  const dot=$('dot');dot.className='dot';
  if(d.status==='RUNNING')dot.classList.add('running');
  else if(['STARTING','GENERATING','STOPPING'].includes(d.status))dot.classList.add('starting');
  else if(d.status==='ERROR')dot.classList.add('error');
  $('statusText').textContent=d.status;
  $('statusExtra').textContent=d.status==='RUNNING'&&d.config.map_code?('map #'+d.config.map_code+' · '+d.config.match_mode):(d.error||'');
  $('sAcc').textContent=d.accounts_count||0;$('sMatch').textContent=d.total_matches||0;
  $('sRun').textContent=fmtU(d.uptime||0);$('sLast').textContent=d.last_match_time||'—';
  $('btnStart').disabled=d.running;$('btnStop').disabled=!d.running;$('btnRestart').disabled=!d.running;
  if(d.accounts&&d.accounts.length){$('accBody').innerHTML=d.accounts.map(a=>
    `<tr><td>${esc(a.uid)}</td><td>${esc(a.nickname)}</td><td>${esc(a.region)}</td>
    <td>${a.level}</td><td>${a.exp}</td><td>${a.matches}</td>
    <td><span class="tag ${a.status.toLowerCase()}">${esc(a.status)}</span></td></tr>`).join('');}
  else{$('accBody').innerHTML='<tr><td colspan="7" class="empty">No accounts yet</td></tr>';}
  if(d.logs&&d.logs.length){$('logs').innerHTML=d.logs.slice(-80).reverse().map(l=>
    `<div><span class="t">${l.t}</span><span class="${l.lvl}">${esc(l.msg)}</span></div>`).join('');}
}catch(e){}}
setInterval(tick,2000);tick();
</script></body></html>"""

# ============================================================
# WEB HANDLERS
# ============================================================
async def handle_index(rq): return web.Response(text=HTML_UI, content_type="text/html")
async def handle_radar(rq): return web.json_response(await RADAR.snapshot())

async def handle_status(rq):
    now = time.time()
    up = int(now - ENGINE.started_at) if ENGINE.started_at else 0
    last = "—"
    ms = [a["last_match"] for a in ENGINE.accounts.values() if a.get("last_match")]
    if ms: last = max(ms)
    return web.json_response({
        "status": ENGINE.status, "running": ENGINE.running, "config": ENGINE.config,
        "accounts_count": len(ENGINE.accounts), "total_matches": ENGINE.total_matches,
        "uptime": up, "last_match_time": last, "error": ENGINE.last_error,
        "accounts": sorted(ENGINE.accounts.values(), key=lambda a: a.get("matches", 0), reverse=True),
        "logs": ENGINE.logs[-80:],
    })

async def handle_start(rq):
    try: cfg = await rq.json()
    except Exception: return web.json_response({"ok": False, "message": "invalid json"})
    if not cfg.get("map_code", "").strip():
        return web.json_response({"ok": False, "message": "map code required"})
    ok, msg = await engine_start(cfg)
    return web.json_response({"ok": ok, "message": msg})

async def handle_stop(rq):
    ok, msg = await engine_stop()
    return web.json_response({"ok": ok, "message": msg})

async def handle_restart(rq):
    try: cfg = await rq.json()
    except Exception: return web.json_response({"ok": False, "message": "invalid json"})
    if not cfg.get("map_code", "").strip():
        return web.json_response({"ok": False, "message": "map code required"})
    ok, msg = await engine_restart(cfg)
    return web.json_response({"ok": ok, "message": msg})

# ============================================================
# ENGINE CONTROLLER
# ============================================================
async def engine_start(cfg):
    if ENGINE.running: return False, "Engine already running"
    ENGINE.config = cfg
    ENGINE.status = "GENERATING" if int(cfg.get("generate_count", 0) or 0) > 0 else "STARTING"
    ENGINE.running = True; ENGINE.started_at = time.time(); ENGINE.stopped_at = None
    ENGINE.stop_event = asyncio.Event(); ENGINE.start_count += 1
    ENGINE.log(f"[ENGINE] start (map={cfg['map_code']}, region={cfg.get('region','IND')}, "
               f"ids={cfg.get('total_ids',1)}, mode={cfg.get('match_mode','unlimited')})", "ok")
    asyncio.create_task(_engine_run(cfg))
    return True, "Engine starting"

async def _engine_run(cfg):
    try:
        gen_n = int(cfg.get("generate_count", 0) or 0)
        region = (cfg.get("region") or "IND").strip().upper()
        if gen_n > 0:
            rotate = (region == "ALL")
            ENGINE.log(f"[GEN] {gen_n} account(s) ({'rotating' if rotate else region})...", "info")
            for i in range(gen_n):
                if ENGINE.stop_event.is_set(): break
                acc_region = GEN_REGIONS[i % len(GEN_REGIONS)] if rotate else region
                try:
                    acc = await asyncio.to_thread(generate_guest_account, acc_region)
                    _append_account(acc); _save_region_uids(acc_region, acc)
                    ENGINE.log(f"[GEN] {i+1}/{gen_n} uid={acc['uid']} {acc['nickname']} [{acc_region}]", "ok")
                except Exception as e:
                    ENGINE.log(f"[GEN] {i+1}/{gen_n} failed: {str(e)[:120]}", "err")
                await asyncio.sleep(1.2)
        all_accs = load_accounts_file()
        if not all_accs:
            ENGINE.status = "ERROR"; ENGINE.last_error = "No accounts available"
            ENGINE.running = False; ENGINE.log("[ENGINE] no accounts", "err"); return
        total = int(cfg.get("total_ids", len(all_accs)) or len(all_accs))
        selected = all_accs[:max(1, total)]
        ENGINE.log(f"[ENGINE] launching {len(selected)} account(s)...", "info")
        ENGINE.status = "RUNNING"
        for acc in selected:
            if ENGINE.stop_event.is_set(): break
            acc_region = acc.get("region") or region
            if str(acc_region).upper() == "ALL": acc_region = "IND"
            ENGINE.tasks.append(asyncio.create_task(
                account_loop(acc["uid"], acc["password"], acc_region, ENGINE.stop_event)))
            await asyncio.sleep(0.1)
        if ENGINE.tasks:
            await asyncio.gather(*ENGINE.tasks, return_exceptions=True)
        if not ENGINE.stop_event.is_set():
            ENGINE.log("[ENGINE] all accounts finished", "ok")
            ENGINE.status = "IDLE"; ENGINE.running = False; ENGINE.stopped_at = time.time()
    except Exception as e:
        ENGINE.log(f"[ENGINE] fatal: {e}", "err")
        ENGINE.status = "ERROR"; ENGINE.last_error = str(e); ENGINE.running = False

async def engine_stop():
    if not ENGINE.running: return False, "Engine not running"
    ENGINE.status = "STOPPING"; ENGINE.log("[ENGINE] stopping...", "warn")
    if ENGINE.stop_event: ENGINE.stop_event.set()
    for t in ENGINE.tasks:
        if not t.done(): t.cancel()
    if ENGINE.tasks:
        try: await asyncio.wait_for(asyncio.gather(*ENGINE.tasks, return_exceptions=True), timeout=15)
        except asyncio.TimeoutError: pass
    ENGINE.tasks.clear()
    for a in ENGINE.accounts.values():
        if a["status"] != "OFFLINE": a["status"] = "OFFLINE"
    ENGINE.running = False; ENGINE.status = "IDLE"; ENGINE.stopped_at = time.time()
    ENGINE.log("[ENGINE] stopped", "ok")
    return True, "Engine stopped"

async def engine_restart(cfg):
    await engine_stop(); await asyncio.sleep(1)
    return await engine_start(cfg)

# ============================================================
# MAIN
# ============================================================
async def main():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/radar", handle_index)
    app.router.add_get("/api/radar", handle_radar)
    app.router.add_get("/api/status", handle_status)
    app.router.add_post("/api/start", handle_start)
    app.router.add_post("/api/stop", handle_stop)
    app.router.add_post("/api/restart", handle_restart)
    runner = web.AppRunner(app); await runner.setup()
    actual = None
    for cand in range(WEB_PORT, WEB_PORT + 20):
        try:
            site = web.TCPSite(runner, "0.0.0.0", cand); await site.start(); actual = cand; break
        except OSError: continue
    if not actual:
        print("❌ Could not bind any port"); return
    print(f"✅ Zesty Craft Land UDP — Web Edition")
    print(f"   http://0.0.0.0:{actual}")
    print(f"   protobuf_decoder: {'available' if _HAS_PROTO_DECODER else 'MISSING (pip install protobuf-decoder)'}")
    print(f"   Engine IDLE — click Start in the web UI")
    print(f"   Stage-2 template loaded: {'yes' if _load_stage2() else 'NO (place c.py next to main.py)'}")
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("Stopped.")
