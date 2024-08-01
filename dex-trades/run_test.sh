make build
rm out.json
export SUBSTREAMS_API_KEY="server_d17cb4bc4e18ce015daff68f45c8a0cf"
substreams run -e mainnet.sol.streamingfast.io:443 substreams.yaml map_block -s 272430060 -t +1 > out.json
