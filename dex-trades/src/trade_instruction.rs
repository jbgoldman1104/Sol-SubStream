#[derive(Debug)]
pub struct TradeInstruction {
    pub dapp_address: String,
    pub name: String,
    pub amm: String,
    pub vault_a: String,
    pub vault_b: String,
    pub base_mint: String,
    pub quote_mint: String,
    pub base_amount: f64,
    pub quote_amount: f64,
    pub i_type: String,
}
