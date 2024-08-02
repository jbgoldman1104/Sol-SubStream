use crate::structure::get_transfer_amounts;
use crate::structure::StructuredInstruction;
use crate::{prepare_input_accounts, trade_instruction::TradeInstruction};

const SWAP_DISCRIMINATOR: u64 = u64::from_le_bytes([248, 198, 158, 145, 225, 117, 135, 200]);

fn parse_vault_a(
    user_ata_in: String,
    accounts: &Vec<String>,
    inst: &StructuredInstruction,
) -> String {
    let mut result: String = String::new();
    for inner_inst in &inst.inner_instructions {
        let inner_program = &accounts[inner_inst.program_id_index as usize];
        if inner_program
            .as_str()
            .eq("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        {
            let (discriminator_bytes, rest) = inner_inst.data.split_at(1);
            let discriminator: u8 = u8::from(discriminator_bytes[0]);
            match discriminator {
                3 => {
                    let input_accounts = prepare_input_accounts(&inner_inst.accounts, accounts);

                    let _source = input_accounts.get(0).unwrap().to_string();
                    let _destination = input_accounts.get(1).unwrap().to_string();

                    if user_ata_in.as_str().eq(_source.as_str()) {
                        if result.is_empty() {
                            result = _destination;
                        }
                    }
                }
                _ => {}
            }
        }
    }
    result
}

fn parse_vault_b(
    user_ata_out: String,
    accounts: &Vec<String>,
    inst: &StructuredInstruction,
) -> String {
    let mut result: String = String::new();
    for inner_inst in &inst.inner_instructions {
        let inner_program = &accounts[inner_inst.program_id_index as usize];
        if inner_program
            .as_str()
            .eq("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        {
            let (discriminator_bytes, rest) = inner_inst.data.split_at(1);
            let discriminator: u8 = u8::from(discriminator_bytes[0]);
            match discriminator {
                3 => {
                    let input_accounts = prepare_input_accounts(&inner_inst.accounts, accounts);

                    let _source = input_accounts.get(0).unwrap().to_string();
                    let _destination = input_accounts.get(1).unwrap().to_string();

                    if user_ata_out.as_str().eq(_destination.as_str()) {
                        if result.is_empty() {
                            result = _source;
                        }
                    }
                }
                _ => {}
            }
        }
    }
    result
}

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
            let user_ata_in = input_accounts.get(5).unwrap().to_string();
            let user_ata_out = input_accounts.get(6).unwrap().to_string();
            let vault_a: String = parse_vault_a(user_ata_in, &accounts, inst);
            let vault_b: String = parse_vault_b(user_ata_out, &accounts, inst);
            let (base_amount, quote_amount) = get_transfer_amounts(inst, accounts, &vault_a, &vault_b);
            result = Some(TradeInstruction {
                dapp_address: String::from("GFXsSL5sSaDfNFQUYsHekbWBW1TsFdjDYzACh62tEHxn"),
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
