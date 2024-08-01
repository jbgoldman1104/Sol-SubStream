#![allow(dead_code)]
#![allow(unused_variables)]
#![allow(non_snake_case)]

mod dapps;
mod pb;
mod utils;

mod structure;
pub use structure::*;

use pb::sf::solana::dex::trades::v1::{Output, TradeData};
use substreams::log;
use substreams_solana::pb::sf::solana::r#type::v1::{Block, TokenBalance};
use substreams_solana::pb::sf::solana::r#type::v1::{
    ConfirmedTransaction, InnerInstructions, Transaction,
};
use trade_instruction::TradeInstruction;
use utils::convert_to_date;
use utils::get_mint_all;
mod trade_instruction;

#[substreams::handlers::map]
fn map_block(block: Block) -> Result<Output, substreams::errors::Error> {
    process_block(block)
}

fn process_block(block: Block) -> Result<Output, substreams::errors::Error> {
    let slot = block.slot;
    let parent_slot = block.parent_slot;
    let timestamp = block.block_time.as_ref();
    let mut data: Vec<TradeData> = vec![];
    if let Some(timestamp) = timestamp {
        let timestamp = timestamp.timestamp;
        for tx in block.transactions_owned() {
            if tx.transaction.is_some() {
                // Clone the entire tx to avoid partial move issues
                let tx_clone = tx.clone();
                let mut tis: Vec<TradeInstruction> = vec![];
                parse_tx(&mut tis, &tx_clone);

                let accounts = tx.resolved_accounts_as_strings();
                let tx_id = bs58::encode(&tx.transaction.unwrap().signatures[0]).into_string();

                let meta = tx.meta.as_ref().unwrap().clone();
                let pre_balances = meta.pre_balances;
                let post_balances = meta.post_balances;
                let pre_token_balances = meta.pre_token_balances;
                let post_token_balances = meta.post_token_balances;

                for (id, ti) in tis.into_iter().enumerate() {
                    if tx_id == "2JhLFuj6J5QcEM2Nj4TrrD2idEBBfFQMAA9ATHHekqDDPQVXtN2yiTyia3tsmLA2fegXdgSGBVbvV8QkYjmHV7L8" {
                    data.push(TradeData {
                        block_date: convert_to_date(timestamp),
                        tx_id: tx_id.clone(),
                        block_slot: slot,
                        block_time: timestamp,
                        signer: accounts.get(0).unwrap().to_string(),
                        pool_address: ti.amm.to_string(),
                        base_mint: ti.base_mint.to_string(),
                        quote_mint: ti.quote_mint.to_string(),
                        base_amount: ti.base_amount,
                        quote_amount: ti.quote_amount,
                        base_vault: ti.vault_a.to_string(),
                        quote_vault: ti.vault_b.to_string(),
                        is_inner_instruction: false,
                        instruction_index: id as u32,
                        instruction_type: ti.i_type.to_string(),
                        inner_instruction_index: 0,
                        outer_program: ti.dapp_address.to_string(),
                        inner_program: "".to_string(),
                        txn_fee: 0,
                        signer_sol_change: get_signer_balance_change(
                            &pre_balances,
                            &post_balances,
                        ),
                        base_reserve: get_amt_reserve(&ti.vault_a, &post_token_balances, &accounts),
                        quote_reserve: get_amt_reserve(&ti.vault_b, &post_token_balances, &accounts),
                    });
                }
                }
            }
        }
    }
    log::info!("{:#?}", slot);
    Ok(Output { data })
}

fn parse_tx(data: &mut Vec<TradeInstruction>, tx: &ConfirmedTransaction) {
    let meta = tx.meta.as_ref().unwrap().clone();
    let accounts = tx.resolved_accounts_as_strings();
    if let Some(transaction) = &tx.transaction {
        let tx_id = bs58::encode(&transaction.signatures[0]).into_string();
        let pre_balances = meta.pre_balances;
        let post_balances = meta.post_balances;
        let pre_token_balances = meta.pre_token_balances;
        let post_token_balances = meta.post_token_balances;

        let structured_instructions = get_structured_instructions(&tx);
        for (idx, inst) in structured_instructions.into_iter().enumerate() {
            get_trades(data, &inst, &accounts, &transaction);
        }
    }
}

fn get_trades(
    data: &mut Vec<TradeInstruction>,
    inst: &StructuredInstruction,
    accounts: &Vec<String>,
    transaction: &Transaction,
) {
    if let Some(ti) = parse_instruction(inst, accounts, transaction) {
        let vault_a = ti.vault_a.clone();
        let vault_b = ti.vault_b.clone();

        // if ti.base_amount != 0.0 && ti.quote_amount != 0.0 {
        data.push(ti);
        // }
    } else {
        for inst1 in &inst.inner_instructions {
            get_trades(data, inst1, accounts, transaction);
        }
    }
}

fn parse_instruction(
    inst: &StructuredInstruction,
    accounts: &Vec<String>,
    transaction: &Transaction,
) -> Option<TradeInstruction> {
    let ti = TradeInstruction {
        amm: "1".to_string(),
        dapp_address: "123".to_string(),
        name: "123".to_string(),
        vault_a: "123".to_string(),
        vault_b: "123".to_string(),
        base_mint: "123".to_string(),
        quote_mint: "123".to_string(),
        base_amount: 0.0,
        quote_amount: 0.0,
        i_type: "123".to_string(),
    };
    let result: Option<TradeInstruction> = Some(ti);
    return result;
    // let program = &accounts[inst.program_id_index as usize];
    // let data = &inst.data();
    // let input_accounts = prepare_input_accounts(&inst.accounts(), accounts);

    // let mut result = None;
    // match dapp_address.as_str() {
    //     "CLMM9tUoggJu2wagPkkqs9eFG4BWhVBZWkP1qv3Sp7tR" => {
    //         result =
    //             dapps::dapp_CLMM9tUoggJu2wagPkkqs9eFG4BWhVBZWkP1qv3Sp7tR::parse_trade_instruction(
    //                 instruction_data,
    //                 input_accounts,
    //             );
    //     }
    //     "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8" => {
    //         result =
    //             dapps::dapp_675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8::parse_trade_instruction(
    //                 instruction_data,
    //                 input_accounts,
    //                 &post_token_balances,
    //                 accounts,
    //             );
    //     }
    // }
}

fn prepare_input_accounts(account_indices: &Vec<u8>, accounts: &Vec<String>) -> Vec<String> {
    let mut instruction_accounts: Vec<String> = vec![];
    for (index, &el) in account_indices.iter().enumerate() {
        instruction_accounts.push(accounts.as_slice()[el as usize].to_string());
    }
    return instruction_accounts;
}

fn get_amt(
    address: &String,
    pre_token_balances: &Vec<TokenBalance>,
    post_token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> f64 {
    let index = accounts.iter().position(|r| r == address).unwrap();

    let mut pre_balance: f64 = 0 as f64;
    let mut post_balance: f64 = 0 as f64;

    pre_token_balances
        .iter()
        .filter(|token_balance| token_balance.account_index == index as u32)
        .for_each(|token_balance: &TokenBalance| {
            pre_balance = token_balance.ui_token_amount.clone().unwrap().ui_amount;
        });

    post_token_balances
        .iter()
        .filter(|token_balance| token_balance.account_index == index as u32)
        .for_each(|token_balance: &TokenBalance| {
            post_balance = token_balance.ui_token_amount.clone().unwrap().ui_amount;
        });

    return post_balance - pre_balance;
}

fn get_amt_reserve(
    address: &String,
    token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> f64 {
    return 1.0;
    let index = accounts.iter().position(|r| r == address).unwrap();

    let mut balance: f64 = 0 as f64;

    token_balances
        .iter()
        .filter(|token_balance| token_balance.account_index == index as u32)
        .for_each(|token_balance: &TokenBalance| {
            balance = token_balance.ui_token_amount.clone().unwrap().ui_amount;
        });

    return balance;
}

fn get_signer_balance_change(pre_balances: &Vec<u64>, post_balances: &Vec<u64>) -> i64 {
    return (post_balances[0] - pre_balances[0]) as i64;
}

fn filter_inner_instructions(
    meta_inner_instructions: &Vec<InnerInstructions>,
    idx: u32,
) -> Vec<InnerInstructions> {
    let mut inner_instructions: Vec<InnerInstructions> = vec![];
    let mut iterator = meta_inner_instructions.iter();
    while let Some(inner_inst) = iterator.next() {
        if inner_inst.index == idx as u32 {
            inner_instructions.push(inner_inst.clone());
        }
    }
    return inner_instructions;
}
