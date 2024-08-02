use crate::trade_instruction::TradeInstruction;
use crate::structure::StructuredInstruction;
use crate::structure::get_transfer_amounts;

const SWAP_WITH_PARTNER: u64 = u64::from_le_bytes([0x85, 0xd7, 0xbf, 0xd6, 0x66, 0xf3, 0x37, 0x19]);


pub fn parse_trade_instruction(
    inst: &StructuredInstruction,
    input_accounts: Vec<String>,
    accounts: &Vec<String>,
) -> Option<TradeInstruction> {
    let bytes_stream = inst.data.clone();
    let (disc_bytes, rest) = bytes_stream.split_at(8);
    let disc_bytes_arr: [u8; 8] = disc_bytes.to_vec().try_into().unwrap();
    let discriminator: u64 = u64::from_le_bytes(disc_bytes_arr);

    let mut result = None;

    match discriminator {
        SWAP_WITH_PARTNER => {
            let vault_a = input_accounts.get(6).unwrap().to_string();
            let vault_b = input_accounts.get(7).unwrap().to_string();
            let (base_amount, quote_amount) = get_transfer_amounts(inst, accounts, &vault_a, &vault_b);
            // let (base_amount, quote_amount) = (0, 0);
            result = Some(TradeInstruction {
                dapp_address: String::from("CLMM9tUoggJu2wagPkkqs9eFG4BWhVBZWkP1qv3Sp7tR"),
                name: String::from("SwapWithPartner"),
                amm: input_accounts.get(1).unwrap().to_string(),
                vault_a: vault_a,
                vault_b: vault_b,
                // base_mint: accounts.get(2).unwrap().to_string(),
                // quote_mint: accounts.get(3).unwrap().to_string(),
                base_amount: base_amount,
                quote_amount: quote_amount,
                i_type: String::from("Swap"),
            });
        }
        _ => {}
    }
    return result;
}
