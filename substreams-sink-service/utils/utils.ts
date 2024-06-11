import { rpc_url } from "../postgres/config.js";
import { Connection, PublicKey } from "@solana/web3.js";
import { Metaplex } from "@metaplex-foundation/js";
import { getMint } from "@solana/spl-token";

export async function getTokenMetadata(token: String) {
    try {
        const connection = new Connection(rpc_url);
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
