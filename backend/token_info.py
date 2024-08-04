# @ -1,200 +1,200 @@
import sys
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.api import Client
from spl.token.client import Token
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

import base64
import base58
import struct
import requests

import env
import common
import asyncio
import aiohttp

import json
import input_pg

r = common.connect_redis()
if env.USE_PG:
    conn = common.connect_db()
    cur = conn.cursor()
#TODO: get your own solana rpc node
#devnet
clients = [Client(key) for key in env.RPC_LIST.split(',')]
cnt = 0

METADATA_PROGRAM_ID = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
def get_nft_pda(mint_key):
    pda = Pubkey.find_program_address([
        b'metadata', 
        bytes(METADATA_PROGRAM_ID), 
        bytes(Pubkey.from_string(mint_key))
        ], METADATA_PROGRAM_ID)[0]
    return pda

def unpack_metadata_account(data):
    assert(data[0] == 4)
    i = 1
    source_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    mint_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    name_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4
    name = struct.unpack('<' + "B"*name_len, data[i:i+name_len])
    i += name_len
    symbol_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    symbol = struct.unpack('<' + "B"*symbol_len, data[i:i+symbol_len])
    i += symbol_len
    uri_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    uri = struct.unpack('<' + "B"*uri_len, data[i:i+uri_len])
    i += uri_len
    fee = struct.unpack('<h', data[i:i+2])[0]
    i += 2
    has_creator = data[i] 
    i += 1
    creators = []
    verified = []
    share = []
    if has_creator:
        creator_len = struct.unpack('<I', data[i:i+4])[0]
        i += 4
        for _ in range(creator_len):
            creator = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
            creators.append(creator)
            i += 32
            verified.append(data[i])
            i += 1
            share.append(data[i])
            i += 1
    primary_sale_happened = bool(data[i])
    i += 1
    is_mutable = bool(data[i])
    metadata = {
        "update_authority": source_account,
        "mint": mint_account,
        "data": {
            "name": bytes(name).decode("utf-8").strip("\x00"),
            "symbol": bytes(symbol).decode("utf-8").strip("\x00"),
            "uri": bytes(uri).decode("utf-8").strip("\x00"),
            "seller_fee_basis_points": fee,
            "creators": creators,
            "verified": verified,
            "share": share,
        },
        "primary_sale_happened": primary_sale_happened,
        "is_mutable": is_mutable,
    }
    return metadata

def get_metadata(client, mint_address):
    metadata_pda = Pubkey.find_program_address(
        [b"metadata", 
         bytes(Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")),
         bytes(Pubkey.from_string(mint_address))],
        Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
    )[0]
    response = client.get_account_info(metadata_pda)
    # decoded = base64.b64decode(response.value.data)
    meta = unpack_metadata_account(response.value.data)
    return meta
        
def get_nft(id, mint_key):
    try:
        client = clients[id % len(clients)]
        meta = get_metadata(client, mint_key)['data']
        # client = Client(env.API_KEY_TEST)
        token = Token(client, Pubkey.from_string(mint_key), TOKEN_PROGRAM_ID, Keypair())
        info = token.get_mint_info()
        try:  # TODO slow
            uri_data = requests.get(meta['uri']).json()
        except:
            uri_data = {}
        
    except Exception as e:
        return None    #probably not a nft
    return (id, mint_key, meta['name'], meta['symbol'], meta['uri'], meta['seller_fee_basis_points'], [val.decode() for val in meta['creators']], meta['verified'], meta['share'],
            str(info.mint_authority) if info.mint_authority else None, info.supply, info.decimals, info.supply / (10.0 ** info.decimals), info.is_initialized,
            str(info.freeze_authority), 
            uri_data["image"] if "image" in uri_data else None, 
            uri_data["description"] if "description" in uri_data else None, 
            uri_data["twitter"] if "twitter" in uri_data else None, 
            uri_data["website"] if "website" in uri_data else None, 0, 0 )

async def update_nft(cur, id, mint):
    # print(f"start token info: {mint}")
    meta = get_nft(id, mint)

    tokens = []
    if meta:
        print(f'{meta[0]} - {meta[3]} : {meta[4]} => {meta[15]}') # type: ignore
        if meta[15] and meta[15].startswith("data:image/"):
            meta = list(meta)
            meta[15] = None     # TODO make thumbnail image to server
        tokens = [common.toT(meta)]
        # write to file
        # common.writeT(meta)
    else:
        print(f"update_nft error: {id}: {mint}")
        tokens = [common.defaultT(id, mint)]
        # common.writeFailedT(id, mint)
    
    r.json().mset(tokens)
    
    pids = r.smembers(f'S_TtoPs:{id}')
    if not pids: return
    pairs = r.json().mget([f'P:{t.decode()}' for t in pids], ".") # type: ignore
    if not pairs: return
    p_update = {}
    for t in tokens:
        if t[2]['symbol']:
            for p in pairs:
                if not p['baseSymbol']:
                    if p['baseMint'] == mint:
                        p['baseName'] = t[2]['name']
                        p['baseSymbol'] = t[2]['symbol']
                    elif p['quoteMint'] == mint:
                        p['quoteName'] = t[2]['name']
                        p['quoteSymbol'] = t[2]['symbol']
                    pid = p['id']
                    p_update[f'P:{pid}'] = p
    if p_update:
        # r.json().mset(p_update)
        r.json().mset([(f'P:{p["id"]}', ".", p) for p in p_update.values()])
        input_pg.write_pairs(cur, p_update)

    # r.lpop('L_TOKEN_REQUEST')


async def token_thread():
    print('-- token_info process started. --')
    
    # r.xtrim("TOKEN_STREAM", maxlen = 0)
    
    session = aiohttp.ClientSession()

    curRequests = 0
    tasks = []
    
    while True:
        # tokens = r.xread( streams = {"TOKEN_STREAM": 0}, block = 600000 )
        cmd = r.brpop('L_TOKENS')[1].decode()
        # if cmd == 'QUIT':
            # while r.llen('L_TOKEN_REQUEST') > 0:
                # asyncio.sleep(0.1)
            # break
        split = cmd.split(',')
        # print(r.llen('L_TOKEN_REQUEST'))
        # while r.llen('L_TOKEN_REQUEST') > env.NUM_REQUESTS:
            # await asyncio.sleep(0.2)
        input_pg.write_tokens(cur, [common.defaultT(split[0], split[1])])
        tasks.append(asyncio.create_task(update_nft(cur, int(split[0]), split[1])))
        # r.lpush('L_TOKEN_REQUEST', int(split[0]))
        # await temp
        remain = r.llen('L_TOKENS')
        num_tasks = len(tasks)
        print(f'{remain}___{num_tasks}')
        while len(tasks) >= env.NUM_REQUESTS:
            await tasks[0]
            tasks.pop(0)
        conn.commit()

if __name__ == "__main__":
    asyncio.run(token_thread())
    # print(get_nft(1, "4ytpZgVoNB66bFs6NRCUaAVsLdtYk2fHq4U92Jnjpump"))


