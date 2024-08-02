use crate::trade_instruction::TradeInstruction;
use crate::structure::StructuredInstruction;
use crate::structure::get_transfer_amounts;

const SWAP_DISCRIMINATOR: u64 = u64::from_le_bytes([248, 198, 158, 145, 225, 117, 135, 200]);

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
        SWAP_DISCRIMINATOR => {
            let vault_a = input_accounts.get(3).unwrap().to_string();
            let vault_b = input_accounts.get(4).unwrap().to_string();
            let (base_amount, quote_amount) = get_transfer_amounts(inst, accounts, &vault_a, &vault_b);
            result = Some(TradeInstruction {
                dapp_address: String::from("CURVGoZn8zycx6FXwwevgBTB2gVvdbGTEpvMJDbgs2t4"),
                name: String::from("Swap"),
                amm: input_accounts.get(2).unwrap().to_string(),
                vault_a: vault_a,
                vault_b: vault_b,
                base_amount: base_amount,
                quote_amount: quote_amount,
                i_type: "123".to_string(),
            });
        }
        _ => {}
    }

    return result;
}
