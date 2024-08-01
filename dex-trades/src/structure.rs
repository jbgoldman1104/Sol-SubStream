use substreams_solana::pb::sf::solana::r#type::v1 as pb;

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
    fn new(instruction: &WrappedInstruction, inner_instructions: Vec<StructuredInstruction>) -> Self {
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

pub(crate) fn structure_wrapped_instructions_with_logs<'a>(instructions: &'a [WrappedInstruction], logs: &[String]) -> Vec<StructuredInstruction> {
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
            let inner_instructions = structure_wrapped_instructions_with_logs(&instructions[i + 1..j], logs);
            structured_instructions.push(StructuredInstruction::new(&instructions[i], inner_instructions));
            i = j;
        }
    }
    let inner_instructions = structure_wrapped_instructions_with_logs(&instructions[i + 1..], logs);
    structured_instructions.push(StructuredInstruction::new(&instructions[i], inner_instructions));

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

fn get_wrapped_instructions(confirmed_transaction: &pb::ConfirmedTransaction) -> Vec<WrappedInstruction> {
    let compiled_instructions = confirmed_transaction.transaction.as_ref().map(|x| x.message.as_ref().map(|y| &y.instructions)).unwrap().unwrap();
    let inner_instructions = confirmed_transaction.meta.as_ref().map(|x| &x.inner_instructions).unwrap();

    let mut wrapped_instructions: Vec<WrappedInstruction> = Vec::new();
    let mut j = 0;
    for (i, instr) in compiled_instructions.iter().enumerate() {
        wrapped_instructions.push(instr.into());
        if let Some(inner) = inner_instructions.get(j) {
            if inner.index == i as u32 {
                wrapped_instructions.extend(inner_instructions[j].instructions.iter().map(|x| x.into()));
                j += 1;
            }
        }
    }
    wrapped_instructions
}

pub fn get_structured_instructions(transaction: &pb::ConfirmedTransaction) -> Vec<StructuredInstruction> {
    let wrapped_instructions = get_wrapped_instructions(transaction);
    structure_wrapped_instructions_with_logs(&wrapped_instructions, &Vec::new())
}
