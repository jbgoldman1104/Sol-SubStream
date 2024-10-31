make build
rm out.json
export SUBSTREAMS_API_KEY="server_eddbaf05178573d4900533eb274b730c"
substreams run -e mainnet.sol.streamingfast.io:443 substreams.yaml map_block -s 281435031 -t +1 > out.json
