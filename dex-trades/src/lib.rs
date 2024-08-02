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
use utils::{convert_to_date, get_mint_all};
// use utils::get_mint_all;
use utils::{convert_to_date, get_mint_all};
// use utils::get_mint_all;
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
                    // if tx_id == "59eDpHgeozVwaN5t8z8wAm7C79CY91NeSUXvQd17hvkBdFXscD7X7hipHBcNRobQ8Lo5Nmoc1zUaBnfdSBWviQz9" {
                    let decimal1 = get_decimals(&ti.vault_a, &post_token_balances, &accounts);
                    let decimal2 = get_decimals(&ti.vault_b, &post_token_balances, &accounts);
                    // if tx_id == "59eDpHgeozVwaN5t8z8wAm7C79CY91NeSUXvQd17hvkBdFXscD7X7hipHBcNRobQ8Lo5Nmoc1zUaBnfdSBWviQz9" {
                    let decimal1 = get_decimals(&ti.vault_a, &post_token_balances, &accounts);
                    let decimal2 = get_decimals(&ti.vault_b, &post_token_balances, &accounts);
                    data.push(TradeData {
                        block_date: convert_to_date(timestamp),
                        tx_id: tx_id.clone(),
                        block_slot: slot,
                        block_time: timestamp,
                        signer: accounts.get(0).unwrap().to_string(),
                        pool_address: ti.amm.to_string(),
                        base_mint: get_mint_all(
                            &ti.vault_a,
                            &pre_token_balances, &post_token_balances,
                            &accounts,
                        ),
                        quote_mint: get_mint_all(
                            &ti.vault_b,
                            &pre_token_balances, &post_token_balances,
                            &accounts,
                        ),
                        base_amount: ti.base_amount as f64/ 10.0_f64.powi(decimal1 as i32),
                        quote_amount: ti.quote_amount as f64/ 10.0_f64.powi(decimal2 as i32),
                        base_mint: get_mint_all(
                            &ti.vault_a,
                            &pre_token_balances, &post_token_balances,
                            &accounts,
                        ),
                        quote_mint: get_mint_all(
                            &ti.vault_b,
                            &pre_token_balances, &post_token_balances,
                            &accounts,
                        ),
                        base_amount: ti.base_amount as f64/ 10.0_f64.powi(decimal1 as i32),
                        quote_amount: ti.quote_amount as f64/ 10.0_f64.powi(decimal2 as i32),
                        base_vault: ti.vault_a.to_string(),
                        quote_vault: ti.vault_b.to_string(),
                        is_inner_instruction: false,
                        instruction_index: 0,
                        instruction_type: ti.name.to_string(),
                        instruction_index: 0,
                        instruction_type: ti.name.to_string(),
                        inner_instruction_index: 0,
                        outer_program: ti.dapp_address.to_string(),
                        inner_program: "".to_string(),
                        txn_fee: meta.fee,
                        txn_fee: meta.fee,
                        signer_sol_change: get_signer_balance_change(
                            &pre_balances,
                            &post_balances,
                        ),
                        base_reserve: get_amt_reserve(&ti.vault_a, &post_token_balances, &accounts),
                        quote_reserve: get_amt_reserve(&ti.vault_b, &post_token_balances, &accounts),
                    });
                // }
                // }
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
            let outer_program = &accounts[inst.program_id_index as usize];
            get_trades(data, &inst, &accounts, &transaction, outer_program, &pre_token_balances, &post_token_balances);
            let outer_program = &accounts[inst.program_id_index as usize];
            get_trades(data, &inst, &accounts, &transaction, outer_program, &pre_token_balances, &post_token_balances);
        }
    }
}

fn get_trades(
    data: &mut Vec<TradeInstruction>,
    inst: &StructuredInstruction,
    accounts: &Vec<String>,
    transaction: &Transaction,
    outer_program: &String,
    pre_token_balances: &Vec<TokenBalance>,
    post_token_balances: &Vec<TokenBalance>,
    outer_program: &String,
    pre_token_balances: &Vec<TokenBalance>,
    post_token_balances: &Vec<TokenBalance>,
) {
    // parse swap instruction
    if let Some(ti) = parse_swap_instruction(inst, accounts, transaction, outer_program, pre_token_balances, post_token_balances) {
        if ti.base_amount != 0 && ti.quote_amount != 0 {
            data.push(ti);
        }
    } else {
        for inner_inst in &inst.inner_instructions {
            get_trades(data, inner_inst, accounts, transaction, outer_program, pre_token_balances, post_token_balances);
        for inner_inst in &inst.inner_instructions {
            get_trades(data, inner_inst, accounts, transaction, outer_program, pre_token_balances, post_token_balances);
        }
    }
    // parse trasfer instruction
    // if let Some(ti) = parse_transfer_instruction(inst, accounts) {
    //     if ti.base_amount != 0 && ti.quote_amount != 0 {
    //         data.push(ti);
    //     }
    // }
}

use substreams_solana_program_instructions::token_instruction_2022::TokenInstruction;

fn parse_transfer_instruction(
    inst: &StructuredInstruction,
    accounts: &Vec<String>,
) -> Option<TradeInstruction> {
    let ti = None;
    match TokenInstruction::unpack(&inst.data) {
        Err(err) => {
            return None;
        }
        Ok(instruction) => match instruction {
            TokenInstruction::Transfer { amount: amt } => {
                let source = &accounts[inst.accounts[0] as usize];
                let destination = &accounts[inst.accounts[1] as usize];
                
            }
            TokenInstruction::TransferChecked { amount: amt, .. } => {
                let source = &accounts[inst.accounts[0] as usize];
                let destination = &accounts[inst.accounts[2] as usize];
                
            }
            _ => {}
        },
    }
    return ti;
}

fn parse_swap_instruction(
    inst: &StructuredInstruction,
    accounts: &Vec<String>,
    transaction: &Transaction,
    outer_program: &String,
    pre_token_balances: &Vec<TokenBalance>,
    post_token_balances: &Vec<TokenBalance>,
    outer_program: &String,
    pre_token_balances: &Vec<TokenBalance>,
    post_token_balances: &Vec<TokenBalance>,
) -> Option<TradeInstruction> {
    // let ti = TradeInstruction {
    //     amm: "1".to_string(),
    //     dapp_address: "123".to_string(),
    //     name: "123".to_string(),
    //     vault_a: "123".to_string(),
    //     vault_b: "123".to_string(),
    //     base_mint: "123".to_string(),
    //     quote_mint: "123".to_string(),
    //     base_amount: 0.0,
    //     quote_amount: 0.0,
    //     i_type: "123".to_string(),
    // };
    // let result: Option<TradeInstruction> = Some(ti);
    // return result;
    let dapp_address = &accounts[inst.program_id_index as usize];
    let input_accounts = prepare_input_accounts(&inst.accounts, accounts);
    let is_inner = inst.stack_height > 0;


    let mut result = None;
    match dapp_address.as_str() {
        "CLMM9tUoggJu2wagPkkqs9eFG4BWhVBZWkP1qv3Sp7tR" => {
            result =
                dapps::dapp_CLMM9tUoggJu2wagPkkqs9eFG4BWhVBZWkP1qv3Sp7tR::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "Dooar9JkhdZ7J3LHN3A7YCuoGRUggXhQaG4kijfLGU2j" => {
            result =
                dapps::dapp_Dooar9JkhdZ7J3LHN3A7YCuoGRUggXhQaG4kijfLGU2j::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB" => {
            result =
                dapps::dapp_Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY" => {
            result =
                dapps::dapp_PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SSwapUtytfBdBn1b9NUGG6foMVPtcWgpRU32HToDUZr" => {
            result =
                dapps::dapp_SSwapUtytfBdBn1b9NUGG6foMVPtcWgpRU32HToDUZr::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX" => {
            let jupiter_dapps = vec![
                "JUP2jxvXaqu7NQY1GmNF4m1vodw12LVXYxbFL2uJvfo".to_string(),
                "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB".to_string(),
                "JUP3c2Uh3WA4Ng34tw6kPd2G4C5BB21Xo36Je1s32Ph".to_string(),
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4".to_string(),
                "JUP6i4ozu5ydDCnLiMogSckDPpbtr7BJ4FtzYWkb5Rk".to_string(),
                "JUP5cHjnnCx2DppVsufsLrXs8EBZeEZzGtEK9Gdz6ow".to_string(),
                "JUP5pEAZeHdHrLxh5UCwAbpjGwYKKoquCpda2hfP4u8".to_string(),
            ];

            if is_inner & jupiter_dapps.contains(outer_program) {
                result =
                dapps::dapp_srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
            }
        }
        "HyaB3W9q6XdA5xwpU4XnSZV94htfmbmqJXZcEbRaJutt" => {
            result =
                dapps::dapp_HyaB3W9q6XdA5xwpU4XnSZV94htfmbmqJXZcEbRaJutt::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc" => {
            result =
                dapps::dapp_whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "EewxydAPCCVuNEyrVN68PuSYdQ7wKn27V9Gjeoi8dy3S" => {
            result =
                dapps::dapp_EewxydAPCCVuNEyrVN68PuSYdQ7wKn27V9Gjeoi8dy3S::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "2wT8Yq49kHgDzXuPxZSaeLaH1qbmGXtEyPy64bL7aD3c" => {
            result =
                dapps::dapp_2wT8Yq49kHgDzXuPxZSaeLaH1qbmGXtEyPy64bL7aD3c::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SSwpkEEcbUqx4vtoEByFjSkhKdCT862DNVb52nZg1UZ" => {
            result =
                dapps::dapp_SSwpkEEcbUqx4vtoEByFjSkhKdCT862DNVb52nZg1UZ::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK" => {
            result =
                dapps::dapp_CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP" => {
            result =
                dapps::dapp_9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "AMM55ShdkoGRB5jVYPjWziwk8m5MpwyDgsMWHaMSQWH6" => {
            result =
                dapps::dapp_AMM55ShdkoGRB5jVYPjWziwk8m5MpwyDgsMWHaMSQWH6::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "CURVGoZn8zycx6FXwwevgBTB2gVvdbGTEpvMJDbgs2t4" => {
            result =
                dapps::dapp_CURVGoZn8zycx6FXwwevgBTB2gVvdbGTEpvMJDbgs2t4::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "cysPXAjehMpVKUapzbMCCnpFxUFFryEWEaLgnb9NrR8" => {
            result =
                dapps::dapp_cysPXAjehMpVKUapzbMCCnpFxUFFryEWEaLgnb9NrR8::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "7WduLbRfYhTJktjLw5FDEyrqoEv61aTTCuGAetgLjzN5" => {
            result =
                dapps::dapp_7WduLbRfYhTJktjLw5FDEyrqoEv61aTTCuGAetgLjzN5::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin" => {
            let jupiter_dapps = vec![
                "JUP2jxvXaqu7NQY1GmNF4m1vodw12LVXYxbFL2uJvfo".to_string(),
                "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB".to_string(),
                "JUP3c2Uh3WA4Ng34tw6kPd2G4C5BB21Xo36Je1s32Ph".to_string(),
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4".to_string(),
                "JUP6i4ozu5ydDCnLiMogSckDPpbtr7BJ4FtzYWkb5Rk".to_string(),
                "JUP5cHjnnCx2DppVsufsLrXs8EBZeEZzGtEK9Gdz6ow".to_string(),
                "JUP5pEAZeHdHrLxh5UCwAbpjGwYKKoquCpda2hfP4u8".to_string(),
            ];

            if is_inner & jupiter_dapps.contains(outer_program) {
                result =
                dapps::dapp_9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
            }
        }
        "GFXsSL5sSaDfNFQUYsHekbWBW1TsFdjDYzACh62tEHxn" => {
            result =
                dapps::dapp_GFXsSL5sSaDfNFQUYsHekbWBW1TsFdjDYzACh62tEHxn::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SSwpMgqNDsyV7mAgN9ady4bDVu5ySjmmXejXvy2vLt1" => {
            result =
                dapps::dapp_SSwpMgqNDsyV7mAgN9ady4bDVu5ySjmmXejXvy2vLt1::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SCHAtsf8mbjyjiv4LkhLKutTf6JnZAbdJKFkXQNMFHZ" => {
            result =
                dapps::dapp_SCHAtsf8mbjyjiv4LkhLKutTf6JnZAbdJKFkXQNMFHZ::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "dp2waEWSBy5yKmq65ergoU3G6qRLmqa6K7We4rZSKph" => {
            result =
                dapps::dapp_dp2waEWSBy5yKmq65ergoU3G6qRLmqa6K7We4rZSKph::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "CTMAxxk34HjKWxQ3QLZK1HpaLXmBveao3ESePXbiyfzh" => {
            result =
                dapps::dapp_CTMAxxk34HjKWxQ3QLZK1HpaLXmBveao3ESePXbiyfzh::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "PSwapMdSai8tjrEXcxFeQth87xC4rRsa4VA5mhGhXkP" => {
            result =
                dapps::dapp_PSwapMdSai8tjrEXcxFeQth87xC4rRsa4VA5mhGhXkP::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "D3BBjqUdCYuP18fNvvMbPAZ8DpcRi4io2EsYHQawJDag" => {
            result =
                dapps::dapp_D3BBjqUdCYuP18fNvvMbPAZ8DpcRi4io2EsYHQawJDag::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "2KehYt3KsEQR53jYcxjbQp2d2kCp4AkuQW68atufRwSr" => {
            result =
                dapps::dapp_2KehYt3KsEQR53jYcxjbQp2d2kCp4AkuQW68atufRwSr::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8" => {
            result =
                dapps::dapp_675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8::parse_trade_instruction(
                    inst,
                    input_accounts,
                    &post_token_balances,
                    accounts,
                );
        }
        "27haf8L6oxUeXrHrgEgsexjSY5hbVUWEmvv9Nyxg8vQv" => {
            result =
                dapps::dapp_27haf8L6oxUeXrHrgEgsexjSY5hbVUWEmvv9Nyxg8vQv::parse_trade_instruction(
                    inst,
                    input_accounts,
                    &post_token_balances,
                    accounts,
                );
        }
        "BSwp6bEBihVLdqJRKGgzjcGLHkcTuzmSo1TQkHepzH8p" => {
            result =
                dapps::dapp_BSwp6bEBihVLdqJRKGgzjcGLHkcTuzmSo1TQkHepzH8p::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "FLUXubRmkEi2q6K3Y9kBPg9248ggaZVsoSFhtJHSrm1X" => {
            result =
                dapps::dapp_FLUXubRmkEi2q6K3Y9kBPg9248ggaZVsoSFhtJHSrm1X::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "9tKE7Mbmj4mxDjWatikzGAtkoWosiiZX9y6J4Hfm2R8H" => {
            result =
                dapps::dapp_9tKE7Mbmj4mxDjWatikzGAtkoWosiiZX9y6J4Hfm2R8H::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "MERLuDFBMmsHnsBPZw2sDQZHvXFMwp8EdjudcU2HKky" => {
            result =
                dapps::dapp_MERLuDFBMmsHnsBPZw2sDQZHvXFMwp8EdjudcU2HKky::parse_trade_instruction(
                    inst,
                    input_accounts,
                    &pre_token_balances,
                    &post_token_balances,
                    accounts,
                );
        }
        "DjVE6JNiYqPL2QXyCUUh8rNjHrbz9hXHNYt99MQ59qw1" => {
            result =
                dapps::dapp_DjVE6JNiYqPL2QXyCUUh8rNjHrbz9hXHNYt99MQ59qw1::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "6MLxLqiXaaSUpkgMnWDTuejNZEz3kE7k2woyHGVFw319" => {
            result =
                dapps::dapp_6MLxLqiXaaSUpkgMnWDTuejNZEz3kE7k2woyHGVFw319::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo" => {
            result =
                dapps::dapp_LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        _ => {}
    }
    // let ti = TradeInstruction {
    //     amm: "1".to_string(),
    //     dapp_address: "123".to_string(),
    //     name: "123".to_string(),
    //     vault_a: "123".to_string(),
    //     vault_b: "123".to_string(),
    //     base_mint: "123".to_string(),
    //     quote_mint: "123".to_string(),
    //     base_amount: 0.0,
    //     quote_amount: 0.0,
    //     i_type: "123".to_string(),
    // };
    // let result: Option<TradeInstruction> = Some(ti);
    // return result;
    let dapp_address = &accounts[inst.program_id_index as usize];
    let input_accounts = prepare_input_accounts(&inst.accounts, accounts);
    let is_inner = inst.stack_height > 0;


    let mut result = None;
    match dapp_address.as_str() {
        "CLMM9tUoggJu2wagPkkqs9eFG4BWhVBZWkP1qv3Sp7tR" => {
            result =
                dapps::dapp_CLMM9tUoggJu2wagPkkqs9eFG4BWhVBZWkP1qv3Sp7tR::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "Dooar9JkhdZ7J3LHN3A7YCuoGRUggXhQaG4kijfLGU2j" => {
            result =
                dapps::dapp_Dooar9JkhdZ7J3LHN3A7YCuoGRUggXhQaG4kijfLGU2j::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB" => {
            result =
                dapps::dapp_Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY" => {
            result =
                dapps::dapp_PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SSwapUtytfBdBn1b9NUGG6foMVPtcWgpRU32HToDUZr" => {
            result =
                dapps::dapp_SSwapUtytfBdBn1b9NUGG6foMVPtcWgpRU32HToDUZr::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX" => {
            let jupiter_dapps = vec![
                "JUP2jxvXaqu7NQY1GmNF4m1vodw12LVXYxbFL2uJvfo".to_string(),
                "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB".to_string(),
                "JUP3c2Uh3WA4Ng34tw6kPd2G4C5BB21Xo36Je1s32Ph".to_string(),
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4".to_string(),
                "JUP6i4ozu5ydDCnLiMogSckDPpbtr7BJ4FtzYWkb5Rk".to_string(),
                "JUP5cHjnnCx2DppVsufsLrXs8EBZeEZzGtEK9Gdz6ow".to_string(),
                "JUP5pEAZeHdHrLxh5UCwAbpjGwYKKoquCpda2hfP4u8".to_string(),
            ];

            if is_inner & jupiter_dapps.contains(outer_program) {
                result =
                dapps::dapp_srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
            }
        }
        "HyaB3W9q6XdA5xwpU4XnSZV94htfmbmqJXZcEbRaJutt" => {
            result =
                dapps::dapp_HyaB3W9q6XdA5xwpU4XnSZV94htfmbmqJXZcEbRaJutt::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc" => {
            result =
                dapps::dapp_whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "EewxydAPCCVuNEyrVN68PuSYdQ7wKn27V9Gjeoi8dy3S" => {
            result =
                dapps::dapp_EewxydAPCCVuNEyrVN68PuSYdQ7wKn27V9Gjeoi8dy3S::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "2wT8Yq49kHgDzXuPxZSaeLaH1qbmGXtEyPy64bL7aD3c" => {
            result =
                dapps::dapp_2wT8Yq49kHgDzXuPxZSaeLaH1qbmGXtEyPy64bL7aD3c::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SSwpkEEcbUqx4vtoEByFjSkhKdCT862DNVb52nZg1UZ" => {
            result =
                dapps::dapp_SSwpkEEcbUqx4vtoEByFjSkhKdCT862DNVb52nZg1UZ::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK" => {
            result =
                dapps::dapp_CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP" => {
            result =
                dapps::dapp_9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "AMM55ShdkoGRB5jVYPjWziwk8m5MpwyDgsMWHaMSQWH6" => {
            result =
                dapps::dapp_AMM55ShdkoGRB5jVYPjWziwk8m5MpwyDgsMWHaMSQWH6::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "CURVGoZn8zycx6FXwwevgBTB2gVvdbGTEpvMJDbgs2t4" => {
            result =
                dapps::dapp_CURVGoZn8zycx6FXwwevgBTB2gVvdbGTEpvMJDbgs2t4::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "cysPXAjehMpVKUapzbMCCnpFxUFFryEWEaLgnb9NrR8" => {
            result =
                dapps::dapp_cysPXAjehMpVKUapzbMCCnpFxUFFryEWEaLgnb9NrR8::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "7WduLbRfYhTJktjLw5FDEyrqoEv61aTTCuGAetgLjzN5" => {
            result =
                dapps::dapp_7WduLbRfYhTJktjLw5FDEyrqoEv61aTTCuGAetgLjzN5::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin" => {
            let jupiter_dapps = vec![
                "JUP2jxvXaqu7NQY1GmNF4m1vodw12LVXYxbFL2uJvfo".to_string(),
                "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB".to_string(),
                "JUP3c2Uh3WA4Ng34tw6kPd2G4C5BB21Xo36Je1s32Ph".to_string(),
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4".to_string(),
                "JUP6i4ozu5ydDCnLiMogSckDPpbtr7BJ4FtzYWkb5Rk".to_string(),
                "JUP5cHjnnCx2DppVsufsLrXs8EBZeEZzGtEK9Gdz6ow".to_string(),
                "JUP5pEAZeHdHrLxh5UCwAbpjGwYKKoquCpda2hfP4u8".to_string(),
            ];

            if is_inner & jupiter_dapps.contains(outer_program) {
                result =
                dapps::dapp_9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
            }
        }
        "GFXsSL5sSaDfNFQUYsHekbWBW1TsFdjDYzACh62tEHxn" => {
            result =
                dapps::dapp_GFXsSL5sSaDfNFQUYsHekbWBW1TsFdjDYzACh62tEHxn::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SSwpMgqNDsyV7mAgN9ady4bDVu5ySjmmXejXvy2vLt1" => {
            result =
                dapps::dapp_SSwpMgqNDsyV7mAgN9ady4bDVu5ySjmmXejXvy2vLt1::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "SCHAtsf8mbjyjiv4LkhLKutTf6JnZAbdJKFkXQNMFHZ" => {
            result =
                dapps::dapp_SCHAtsf8mbjyjiv4LkhLKutTf6JnZAbdJKFkXQNMFHZ::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "dp2waEWSBy5yKmq65ergoU3G6qRLmqa6K7We4rZSKph" => {
            result =
                dapps::dapp_dp2waEWSBy5yKmq65ergoU3G6qRLmqa6K7We4rZSKph::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "CTMAxxk34HjKWxQ3QLZK1HpaLXmBveao3ESePXbiyfzh" => {
            result =
                dapps::dapp_CTMAxxk34HjKWxQ3QLZK1HpaLXmBveao3ESePXbiyfzh::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "PSwapMdSai8tjrEXcxFeQth87xC4rRsa4VA5mhGhXkP" => {
            result =
                dapps::dapp_PSwapMdSai8tjrEXcxFeQth87xC4rRsa4VA5mhGhXkP::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "D3BBjqUdCYuP18fNvvMbPAZ8DpcRi4io2EsYHQawJDag" => {
            result =
                dapps::dapp_D3BBjqUdCYuP18fNvvMbPAZ8DpcRi4io2EsYHQawJDag::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "2KehYt3KsEQR53jYcxjbQp2d2kCp4AkuQW68atufRwSr" => {
            result =
                dapps::dapp_2KehYt3KsEQR53jYcxjbQp2d2kCp4AkuQW68atufRwSr::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8" => {
            result =
                dapps::dapp_675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8::parse_trade_instruction(
                    inst,
                    input_accounts,
                    &post_token_balances,
                    accounts,
                );
        }
        "27haf8L6oxUeXrHrgEgsexjSY5hbVUWEmvv9Nyxg8vQv" => {
            result =
                dapps::dapp_27haf8L6oxUeXrHrgEgsexjSY5hbVUWEmvv9Nyxg8vQv::parse_trade_instruction(
                    inst,
                    input_accounts,
                    &post_token_balances,
                    accounts,
                );
        }
        "BSwp6bEBihVLdqJRKGgzjcGLHkcTuzmSo1TQkHepzH8p" => {
            result =
                dapps::dapp_BSwp6bEBihVLdqJRKGgzjcGLHkcTuzmSo1TQkHepzH8p::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "FLUXubRmkEi2q6K3Y9kBPg9248ggaZVsoSFhtJHSrm1X" => {
            result =
                dapps::dapp_FLUXubRmkEi2q6K3Y9kBPg9248ggaZVsoSFhtJHSrm1X::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "9tKE7Mbmj4mxDjWatikzGAtkoWosiiZX9y6J4Hfm2R8H" => {
            result =
                dapps::dapp_9tKE7Mbmj4mxDjWatikzGAtkoWosiiZX9y6J4Hfm2R8H::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "MERLuDFBMmsHnsBPZw2sDQZHvXFMwp8EdjudcU2HKky" => {
            result =
                dapps::dapp_MERLuDFBMmsHnsBPZw2sDQZHvXFMwp8EdjudcU2HKky::parse_trade_instruction(
                    inst,
                    input_accounts,
                    &pre_token_balances,
                    &post_token_balances,
                    accounts,
                );
        }
        "DjVE6JNiYqPL2QXyCUUh8rNjHrbz9hXHNYt99MQ59qw1" => {
            result =
                dapps::dapp_DjVE6JNiYqPL2QXyCUUh8rNjHrbz9hXHNYt99MQ59qw1::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "6MLxLqiXaaSUpkgMnWDTuejNZEz3kE7k2woyHGVFw319" => {
            result =
                dapps::dapp_6MLxLqiXaaSUpkgMnWDTuejNZEz3kE7k2woyHGVFw319::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo" => {
            result =
                dapps::dapp_LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo::parse_trade_instruction(
                    inst,
                    input_accounts,
                    accounts,
                );
        }
        _ => {}
    }
    return result;
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

fn get_decimals(
    address: &String,
    token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> u32 {
    let index = accounts.iter().position(|r| r == address).unwrap();
    let mut result: u32 = 0 as u32;
    token_balances
        .iter()
        .filter(|token_balance| token_balance.account_index == index as u32)
        .for_each(|token_balance: &TokenBalance| {
            result = token_balance.ui_token_amount.clone().unwrap().decimals;
        });
    return result;
}

fn get_decimals(
    address: &String,
    token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> u32 {
    let index = accounts.iter().position(|r| r == address).unwrap();
    let mut result: u32 = 0 as u32;
    token_balances
        .iter()
        .filter(|token_balance| token_balance.account_index == index as u32)
        .for_each(|token_balance: &TokenBalance| {
            result = token_balance.ui_token_amount.clone().unwrap().decimals;
        });
    return result;
}

fn get_amt_reserve(
    address: &String,
    token_balances: &Vec<TokenBalance>,
    accounts: &Vec<String>,
) -> f64 {
    // return 1.0;
    // return 1.0;
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
