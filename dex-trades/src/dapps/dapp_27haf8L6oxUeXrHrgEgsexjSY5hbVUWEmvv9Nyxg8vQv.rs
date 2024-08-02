use crate::trade_instruction::TradeInstruction;
use crate::utils::get_mint;
use substreams_solana::pb::sf::solana::r#type::v1::TokenBalance;
use crate::structure::StructuredInstruction;
use crate::structure::get_transfer_amounts;

pub fn parse_trade_instruction(
    inst: &StructuredInstruction,
    input_accounts: Vec<String>,
    post_token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> Option<TradeInstruction> {
    let bytes_stream = inst.data.clone();
    let (disc_bytes, rest) = bytes_stream.split_at(1);
    let discriminator: u8 = u8::from(disc_bytes[0]);

    let mut result = None;

    match discriminator {
        9 => {
            let vault_a = get_vault_a(&input_accounts, post_token_balances, accounts);
            let vault_b = get_vault_b(&input_accounts, post_token_balances, accounts);
            let (base_amount, quote_amount) = get_transfer_amounts(inst, accounts, &vault_a, &vault_b);
            result = Some(TradeInstruction {
                dapp_address: String::from("27haf8L6oxUeXrHrgEgsexjSY5hbVUWEmvv9Nyxg8vQv"),
                name: String::from("SwapBaseIn"),
                amm: accounts.get(1).unwrap().to_string(),
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

fn get_vault_a(
    input_accounts: &Vec<String>,
    post_token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> String {
    let mut vault_a = input_accounts.get(4).unwrap().to_string();
    let mint_a = get_mint(&vault_a, post_token_balances, accounts);

    if mint_a.is_empty() {
        vault_a = input_accounts.get(5).unwrap().to_string();
    }

    return vault_a;
}

fn get_vault_b(
    input_accounts: &Vec<String>,
    post_token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> String {
    let vault_a = input_accounts.get(4).unwrap().to_string();
    let mint_a = get_mint(&vault_a, post_token_balances, accounts);
    let mut vault_b = input_accounts.get(5).unwrap().to_string();

    if mint_a.is_empty() {
        vault_b = input_accounts.get(6).unwrap().to_string();
    }

    return vault_b;
}
