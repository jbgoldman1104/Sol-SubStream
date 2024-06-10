import { setup, http } from "substreams-sink";

import { type ActionOptions } from "./bin/cli.js";

import { initialize, insertTrades } from './postgres/trade.js'

import { Metaplex } from "@metaplex-foundation/js";
import { Connection, PublicKey } from "@solana/web3.js";
import {
    getMint,
    getAccount,
    getAssociatedTokenAddress,
} from "@solana/spl-token";

async function getTokenMetadata(token: String) {
    try {
        const connection = new Connection("https://mainnet.helius-rpc.com/?api-key=e4226aa3-24f7-43c1-869f-a1b1e3fbb148");
        const metaplex = Metaplex.make(connection);

        const mintAddress = new PublicKey(token);

        let tokenName;
        let tokenSymbol;
        let tokenLogo;

        const metadataAccount = metaplex
            .nfts()
            .pdas()
            .metadata({ mint: mintAddress });

        const metadataAccountInfo = await connection.getAccountInfo(metadataAccount);

        if (metadataAccountInfo) {
            const token = await metaplex.nfts().findByMint({ mintAddress: mintAddress });
            tokenName = token.name;
            tokenSymbol = token.symbol;
            tokenLogo = token.json?.image;
        }
        const mintInfo = await getMint(connection, mintAddress);
        console.log("tokenName: " + tokenName);
        console.log("tokenSymbol: " + tokenSymbol);
        console.log("tokenLogo: " + tokenLogo);
        console.log("Decimals: " + mintInfo.decimals);
        console.log("Supply: " + mintInfo.supply);
    } catch (error) {
        console.log(error);
    }
}

if (false) {
    await initialize()
}

export async function action(options: ActionOptions) {
    const { emitter } = await setup(options);
    emitter.on("anyMessage", insertTrades);
    http.listen(options);
    await emitter.start();
    http.server.close()
}


getTokenMetadata("C2AzGig8NveCJCPTjdXHs4WePudYGzgsz4LXsRQaZsBb").then(()=>{}).catch(error=>{});