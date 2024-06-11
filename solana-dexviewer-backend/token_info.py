import sys
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from spl.token.client import Token
from solana.keypair import Keypair
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

import base64
import base58
import struct
import json
import requests

import env
import common
#TODO: get your own solana rpc node
#devnet
solana_client = Client(env.API_KEY)

METADATA_PROGRAM_ID = PublicKey('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
def get_nft_pda(mint_key):
    pda = PublicKey.find_program_address([b'metadata', bytes(METADATA_PROGRAM_ID), bytes(PublicKey(mint_key))],METADATA_PROGRAM_ID)[0]
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

def get_metadata(mint_key):
    data = base64.b64decode(solana_client.get_account_info(get_nft_pda(mint_key))['result']['value']['data'][0]) # type: ignore
    return(unpack_metadata_account(data))
        
def get_nft(id, mint_key):
    try:
        meta = get_metadata(mint_key)['data']
        client = Client(env.API_KEY)
        token = Token(client, PublicKey(mint_key), TOKEN_PROGRAM_ID, Keypair.generate())
        info = token.get_mint_info()
        try:
            uri_data = requests.get(meta['uri']).json()
        except:
            uri_data = {}
        
    except:
        return None    #probably not a nft
    return (id, meta['name'], meta['symbol'], meta['uri'], meta['seller_fee_basis_points'], [val.decode() for val in meta['creators']], meta['verified'], meta['share'],
            str(info.mint_authority) if info.mint_authority else None, info.supply, info.supply, info.supply / (1.0 ** info.supply), info.is_initialized,
            str(info.freeze_authority), 
            uri_data["image"] if "image" in uri_data else None, 
            uri_data["description"] if "description" in uri_data else None, 
            uri_data["twitter"] if "twitter" in uri_data else None, 
            uri_data["website"] if "website" in uri_data else None )

def update_nft(cur, r, id, mint):
    # print(f"start token info: {mint}")
    meta = get_nft(id, mint)

    if meta:
        print(f'{meta[0]} - {meta[2]} : {meta[3]} => {meta[14]}') # type: ignore
        r.json().mset([common.toT(meta)])
    else:
        print(f"update_nft error: {mint}")

async def test(mint):
    meta = get_nft(11, mint)
    print(meta)
    

if __name__ == "__main__":
    print(get_nft('123', "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1"))
    pass


