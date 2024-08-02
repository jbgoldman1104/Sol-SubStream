#[derive(Debug)]
pub struct TradeInstruction {
    pub dapp_address: String,
    pub name: String,
    pub amm: String,
    pub vault_a: String,
    pub vault_b: String,
    pub base_amount: i64,
    pub quote_amount: i64,
    pub i_type: String,
    // pub id: u32,
    // pub is_inner: bool,
    // pub inner_id: u32,
    // pub inner_dapp_address: String
}
