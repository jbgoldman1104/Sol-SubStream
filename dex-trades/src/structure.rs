use substreams_solana::pb::sf::solana::r#type::v1 as pb;
// use solana_program::program_error::ProgramError;
// use spl_token::instruction::TokenInstruction;
// fn parse_spl_token_instruction(instruction_data: &[u8]) -> Result<TokenInstruction, ProgramError> {
//     TokenInstruction::unpack(instruction_data)
// }

// pub fn get_transfer_amounts(inst: &StructuredInstruction) -> (u64, u64) {
//     // return (100, 1000);
//     let mut amount1: u64 = 0;
//     let mut amount2: u64 = 0;
//     for inner_inst in &inst.inner_instructions {
//         match parse_spl_token_instruction(inner_inst.data.as_slice()) {
//             Ok(TokenInstruction::Transfer { amount }) => {
//                 // println!("SPL Token Transfer instruction: Amount = {}", amount);
//                 // Handle the transfer instruction
//                 if amount1 == 0 {
//                     amount1 = amount;
//                 } else if amount2 == 0 {
//                     amount2 = amount;
//                     break;
//                 }
//             },
//             Ok(TokenInstruction::TransferChecked { amount, decimals }) => {
//                 // println!("SPL Token TransferChecked instruction: Amount = {}, Decimals = {}", amount, decimals);
//                 // Handle the transfer checked instruction
//                 if amount1 == 0 {
//                     amount1 = amount;
//                 } else if amount2 == 0 {
//                     amount2 = amount;
//                     break;
//                 }
//             },
//             Ok(other_instruction) => {
//                 // println!("Other SPL Token instruction: {:?}", other_instruction);
//                 // Handle other types of instructions
//             },
//             Err(err) => {
//                 // println!("Error parsing SPL Token instruction: {:?}", err);
//                 // Handle the error
//             }
//         }
//     }
//     return (amount1, amount2)
// }

// use std::ops::Div;
// use substreams::errors::Error;

// use substreams_solana::pb::sf::solana::r#type::v1::{
//     CompiledInstruction, TokenBalance, TransactionStatusMeta,
// };

use substreams_solana_program_instructions::token_instruction_2022::TokenInstruction;

fn prepare_input_accounts(account_indices: &Vec<u8>, accounts: &Vec<String>) -> Vec<String> {
    let mut instruction_accounts: Vec<String> = vec![];
    for (index, &el) in account_indices.iter().enumerate() {
        instruction_accounts.push(accounts.as_slice()[el as usize].to_string());
    }
    return instruction_accounts;
}

pub fn get_transfer_amounts(
    inst: &StructuredInstruction,
    accounts: &Vec<String>,
    vault_a: &String,
    vault_b: &String,
) -> (i64, i64) {
    // return (100, 1000);
    let mut base_amount: i64 = 0;
    let mut quote_amount: i64 = 0;
    for inner_inst in &inst.inner_instructions {
        match TokenInstruction::unpack(&inner_inst.data) {
            Err(err) => {
                continue;
            }
            Ok(instruction) => match instruction {
                TokenInstruction::Transfer { amount: amt } => {
                    let source = &accounts[inner_inst.accounts[0] as usize];
                    let destination = &accounts[inner_inst.accounts[1] as usize];
                    if source == vault_a || destination == vault_a {
                        base_amount = amt as i64;
                        if source == vault_a {
                            base_amount = - base_amount;
                        }
                    } else if source == vault_b || destination == vault_b {
                        quote_amount = amt as i64;
                        if source == vault_b {
                            quote_amount = - quote_amount;
                        }
                    }
                    if base_amount != 0 && quote_amount != 0 {
                        break;
                    }
                }
                TokenInstruction::TransferChecked { amount: amt, .. } => {
                    let source = &accounts[inner_inst.accounts[0] as usize];
                    let destination = &accounts[inner_inst.accounts[2] as usize];
                    if source == vault_a || destination == vault_a {
                        base_amount = amt as i64;
                        if source == vault_a {
                            base_amount = - base_amount;
                        }
                    } else if source == vault_b || destination == vault_b {
                        quote_amount = amt as i64;
                        if source == vault_b {
                            quote_amount = - quote_amount;
                        }
                    }
                    if base_amount != 0 && quote_amount != 0 {
                        break;
                    }
                }
                _ => {}
            },
        }
    }
    return (base_amount, quote_amount);
}

#[derive(Debug)]
pub(crate) enum WrappedInstruction<'a> {
    Compiled(&'a pb::CompiledInstruction),
    Inner(&'a pb::InnerInstruction),
}

impl WrappedInstruction<'_> {
    pub fn program_id_index(&self) -> u32 {
        match self {
            Self::Compiled(instr) => instr.program_id_index,
            Self::Inner(instr) => instr.program_id_index,
        }
    }
    pub fn accounts(&self) -> &Vec<u8> {
        match self {
            Self::Compiled(instr) => &instr.accounts,
            Self::Inner(instr) => &instr.accounts,
        }
    }
    pub fn data(&self) -> &Vec<u8> {
        match self {
            Self::Compiled(instr) => &instr.data,
            Self::Inner(instr) => &instr.data,
        }
    }
    pub fn stack_height(&self) -> Option<u32> {
        match self {
            Self::Compiled(_) => Some(1),
            Self::Inner(instr) => instr.stack_height,
        }
    }
}

impl<'a> From<&'a pb::CompiledInstruction> for WrappedInstruction<'a> {
    fn from(value: &'a pb::CompiledInstruction) -> Self {
        WrappedInstruction::Compiled(&value)
    }
}

impl<'a> From<&'a pb::InnerInstruction> for WrappedInstruction<'a> {
    fn from(value: &'a pb::InnerInstruction) -> Self {
        WrappedInstruction::Inner(&value)
    }
}

#[derive(Debug)]
pub struct StructuredInstruction {
    pub program_id_index: u32,
    pub accounts: Vec<u8>,
    pub data: Vec<u8>,
    pub stack_height: u32,
    pub inner_instructions: Vec<Self>,
    pub logs: Vec<String>,
}

impl StructuredInstruction {
    fn new(
        instruction: &WrappedInstruction,
        inner_instructions: Vec<StructuredInstruction>,
    ) -> Self {
        Self {
            program_id_index: instruction.program_id_index(),
            accounts: instruction.accounts().clone(),
            data: instruction.data().clone(),
            stack_height: instruction.stack_height().unwrap(),
            inner_instructions: inner_instructions,
            logs: Vec::new(),
        }
    }
}

pub(crate) fn structure_wrapped_instructions_with_logs<'a>(
    instructions: &'a [WrappedInstruction],
    logs: &[String],
) -> Vec<StructuredInstruction> {
    let mut structured_instructions: Vec<StructuredInstruction> = Vec::new();

    if instructions.len() == 0 {
        return Vec::new();
    }

    let stack_height = instructions[0].stack_height();
    let mut i = 0;
    for (j, instr) in instructions.iter().enumerate() {
        if j == i {
            continue;
        }
        if instr.stack_height() == stack_height {
            let inner_instructions =
                structure_wrapped_instructions_with_logs(&instructions[i + 1..j], logs);
            structured_instructions.push(StructuredInstruction::new(
                &instructions[i],
                inner_instructions,
            ));
            i = j;
        }
    }
    let inner_instructions = structure_wrapped_instructions_with_logs(&instructions[i + 1..], logs);
    structured_instructions.push(StructuredInstruction::new(
        &instructions[i],
        inner_instructions,
    ));

    structured_instructions
}

pub trait StructuredInstructions {
    fn flattened(&self) -> Vec<&StructuredInstruction>;
}

impl StructuredInstructions for Vec<StructuredInstruction> {
    fn flattened(&self) -> Vec<&StructuredInstruction> {
        let mut instructions: Vec<&StructuredInstruction> = Vec::new();
        for instruction in self {
            instructions.push(instruction);
            instructions.extend(instruction.inner_instructions.flattened());
        }
        instructions
    }
}

fn get_wrapped_instructions(
    confirmed_transaction: &pb::ConfirmedTransaction,
) -> Vec<WrappedInstruction> {
    let compiled_instructions = confirmed_transaction
        .transaction
        .as_ref()
        .map(|x| x.message.as_ref().map(|y| &y.instructions))
        .unwrap()
        .unwrap();
    let inner_instructions = confirmed_transaction
        .meta
        .as_ref()
        .map(|x| &x.inner_instructions)
        .unwrap();

    let mut wrapped_instructions: Vec<WrappedInstruction> = Vec::new();
    let mut j = 0;
    for (i, instr) in compiled_instructions.iter().enumerate() {
        wrapped_instructions.push(instr.into());
        if let Some(inner) = inner_instructions.get(j) {
            if inner.index == i as u32 {
                wrapped_instructions
                    .extend(inner_instructions[j].instructions.iter().map(|x| x.into()));
                j += 1;
            }
        }
    }
    wrapped_instructions
}

pub fn get_structured_instructions(
    transaction: &pb::ConfirmedTransaction,
) -> Vec<StructuredInstruction> {
    let wrapped_instructions = get_wrapped_instructions(transaction);
    structure_wrapped_instructions_with_logs(&wrapped_instructions, &Vec::new())
}
