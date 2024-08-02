use crate::trade_instruction::TradeInstruction;
use crate::structure::StructuredInstruction;
use crate::structure::get_transfer_amounts;

const SWAP_FUND_TOKENS_DISCRIMINATOR: u64 =
    u64::from_le_bytes([112, 246, 21, 136, 172, 62, 27, 20]);

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
        SWAP_FUND_TOKENS_DISCRIMINATOR => {
            let vault_a = input_accounts.get(3).unwrap().to_string();
            let vault_b = input_accounts.get(5).unwrap().to_string();
            let (base_amount, quote_amount) = get_transfer_amounts(inst, accounts, &vault_a, &vault_b);
            result = Some(TradeInstruction {
                dapp_address: String::from("2KehYt3KsEQR53jYcxjbQp2d2kCp4AkuQW68atufRwSr"),
                name: String::from("SwapFundTokens"),
                amm: input_accounts.get(1).unwrap().to_string(),
                vault_a: input_accounts.get(3).unwrap().to_string(),
                vault_b: input_accounts.get(5).unwrap().to_string(),
                base_amount: base_amount,
                quote_amount: quote_amount,
                i_type: "123".to_string(),
            });
        }
        _ => {}
    }

    return result;
}
