use crate::trade_instruction::TradeInstruction;
use crate::structure::StructuredInstruction;
use crate::structure::get_transfer_amounts;

pub fn parse_trade_instruction(
    inst: &StructuredInstruction,
    input_accounts: Vec<String>,
    accounts: &Vec<String>,
) -> Option<TradeInstruction> {
    let bytes_stream = inst.data.clone();
    let (disc_bytes, rest) = bytes_stream.split_at(1);
    let discriminator: u8 = u8::from(disc_bytes[0]);

    let mut result = None;

    match discriminator {
        1 => {
            let vault_a = input_accounts.get(4).unwrap().to_string();
            let vault_b = input_accounts.get(5).unwrap().to_string();
            let (base_amount, quote_amount) = get_transfer_amounts(inst, accounts, &vault_a, &vault_b);
            result = Some(TradeInstruction {
                dapp_address: String::from("SSwpkEEcbUqx4vtoEByFjSkhKdCT862DNVb52nZg1UZ"),
                name: String::from("Swap"),
                amm: input_accounts.get(0).unwrap().to_string(),
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
