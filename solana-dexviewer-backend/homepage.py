
html_content = """
<!doctype html>
<html>
<head>
    <title>Data Test</title>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div class="text-white bg-[#0d0d0d]">
        <div class="flex flex-row items-center justify-center mx-auto p-3">
            <div id="count" class="text-[16px]"></div>
            <div class="flex flex-row items-left px-3 ml-3">
                <a class="text-[16px] w-[40px] hover:font-bold" href="javascript:setDuration(0);">5M</a>
                <a class="text-[16px] w-[40px] hover:font-bold" href="javascript:setDuration(1);">1H</a>
                <a class="text-[16px] w-[40px] hover:font-bold" href="javascript:setDuration(2);">6H</a>
                <a class="text-[16px] w-[40px] hover:font-bold" href="javascript:setDuration(3);">24H</a>
            </div>
        </div>
        <div class="flex items-center justify-center px-3">
            <div id="data-table" class="flex flex-col"></div>
        </div>
    </div>
</body>
<script type="text/javascript">
      var count = 0;
      var duration = 0;
      var sort = 'score';
      var skip = 0;
      var limit = 20;
      var pair = '';
      var txsort = 'blockTime';
      var curPage = 1;
      
      var idle = true;
      
      function formatString(num) {
        const numStr = num.toString();
        const length = numStr.length;
        const maxDigits = 8; // Adjust this value to change the number of digits shown

        if (length <= maxDigits) {
            return numStr; // Return the original number if it's short enough
        }

        const leadingDigits = numStr.slice(0, 4);
        const trailingDigits = numStr.slice(length - 4);

        return `${leadingDigits}...${trailingDigits}`; // Concatenate the leading and trailing digits with '...' in between
      }
     
      function formatDate(num) {
        const options = {
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        return new Date(num).toLocaleString('en-US', options).replace(',', '');
      }
      function setDuration(v) {
          duration = v;
          fetchStatistics();
      }
      function setSort(v) {
          sort = v;
          fetchStatistics();
      }
      
      function setPair(v) {
          pair = v;
          curPage = 2;
          fetchTransactions()
      }
      function setTxSort(v) {
          txsort= v;
          curPage = 2;
          fetchTransactions()
      }
      
      function setSkip(v) {
          skip = v;
          fetchStatistics();
      }
      function setLimit(v){
          limit = v;
          fetchStatistics()
      }
      function f(num) {
        // Convert number to string and split into integer and fractional parts
        num = Number(Number(num).toPrecision(4))

        if (Math.abs(num) >= 1e9) {
            return (num / 1e9).toFixed(1) + "B"; // Brillion
        } else if (Math.abs(num) >= 1e6) {
            return (num / 1e6).toFixed(1) + "M"; // Millions
        } else if (Math.abs(num) >= 1e3) {
            return (num / 1e3).toFixed(1) + "K"; // Thousands
        } else if (Math.abs(num) >= 0.1) {
            return num;
            //return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
        else if (num < 0.1) {
            diff = 0;
            if (num < 0.000001) {
                num *= 1e5;
                diff = 5;
            }
            let [integerPart, fractionalPart] = num.toFixed(12).toString().split('.');
            match = fractionalPart.match(/^0+/);
            let leadingZeros = match[0].length + diff;
            let subscriptChar = leadingZeros.toString().split('').map(char => String.fromCharCode(char.charCodeAt(0) + 8272)).join('');
            return `${integerPart}.0${subscriptChar}${fractionalPart.slice(leadingZeros)}`;
        }
        return num;
    };

      
      function togglePage() {
          curPage = 3 - curPage;
      }
      function fetchTransactions() {
          if (!idle || pair == undefined || pair == '') return;
          idle = false;
          count ++;
        document.getElementById('count').innerHTML = 'request: ' + count;
        fetch('/tx/query?pool='+pair +'&sort='+txsort +'&skip='+skip +'&limit='+limit +'')
          .then(response => response.json())
          .then(data => {
            idle = true;
            var html = '';
            html += '<button class="flex items-center justify-center text-[15px] ml-4" onclick="togglePage()">Back...</button>\\
                    <div class="data_row flex mx-auto w-full bg-[#39393E] text-[18px] font-bold">\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[220px] h-[40px] text-center" href="javascript:setTxSort(\\'blockTime\\');"> DATE(GMT) </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[120px] h-[40px] text-center" href="javascript:setTxSort(\\'type\\');"> TYPE </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[220px] h-[40px] text-center" href="javascript:setTxSort(\\'volume\\');"> USD </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[220px] h-[40px] text-center" href="javascript:setTxSort(\\'baseAmount\\');"> '+ formatString(data['baseName']) +' </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[220px] h-[40px] text-center" href="javascript:setTxSort(\\'quoteAmount\\');"> '+ formatString(data['quoteName']) +' </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[250px] h-[40px] text-center" href="javascript:setTxSort(\\'price\\');"> PRICE </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[180px] h-[40px] text-center" href="javascript:setTxSort(\\'signer\\');"> MAKER </a>\\
                        </div>';
            for(var i = 0; i < data["data"].length; i++) {
                row = data["data"][i]
                html += '<div class="data_row hover:bg-[#555] cursor-pointer flex mx-auto w-full text-[16px] bg-[#1D1D22]">'+
                            '<div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[220px] h-[35px] pr-2 justify-center text-[#848489] text-right"> '+ formatDate(row['date']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[120px] h-[35px] pr-2 justify-center '+ (row['type'] == 'Buy' ? 'text-[#48BB78]' : 'text-[#F56565]') +' text-right">'+ row['type'] +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[220px] h-[35px] pr-2 justify-end '+ (row['type'] == 'Buy' ? 'text-[#48BB78]' : 'text-[#F56565]') +' text-right"> '+ f(row['usd']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[220px] h-[35px] pr-2 justify-end '+ (row['type'] == 'Buy' ? 'text-[#48BB78]' : 'text-[#F56565]') +' text-right">'+ f(row['baseAmount']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[220px] h-[35px] pr-2 justify-end '+ (row['type'] == 'Buy' ? 'text-[#48BB78]' : 'text-[#F56565]') +' text-center">'+ f(row['quoteAmount']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[250px] h-[35px] pr-2 justify-end '+ (row['type'] == 'Buy' ? 'text-[#48BB78]' : 'text-[#F56565]') +' text-right">$ '+ f(row['price']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[180px] h-[35px] pr-2 justify-end '+ (row['type'] == 'Buy' ? 'text-[#48BB78]' : 'text-[#F56565]') +' text-right"> '+ (row['txId']) +'</div>\\
                        </div>';
                
            }
            document.getElementById('data-table').innerHTML = html;
          })
          .catch(error => {
              idle = true;
              console.error('Error:', error);
          });
      }
      function fetchStatistics() {
          if (!idle) return;
          idle = false;
        count ++;
        document.getElementById('count').innerHTML = 'request: ' + count;
        fetch('/st/query?duration='+duration +'&sort='+sort +'&skip='+skip +'&limit='+limit +'')
          .then(response => response.json())
          .then(data => {
            idle = true;
            var html = '';
            html += '<div class="data_row flex mx-auto w-full bg-[#39393E] text-[18px]">\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[330px] h-[40px] text-center font-bold" href="javascript:setSort(\\'score\\');"> pair </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[250px] h-[40px] text-center font-bold" href="javascript:setSort(\\'price\\');"> price </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[110px] h-[40px] text-center font-bold" href="javascript:setSort(\\'txns\\');"> txns </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[170px] h-[40px] text-center font-bold" href="javascript:setSort(\\'volume\\');"> volume </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[110px] h-[40px] text-center font-bold" href="javascript:setSort(\\'makers\\');"> makers </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[130px] h-[40px] text-center font-bold" href="javascript:setSort(\\'d_price\\');"> price ratio </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[150px] h-[40px] text-center font-bold" href="javascript:setSort(\\'liquidity\\');"> liquidity </a>\\
                            <a class="data_cell flex items-center justify-center border border-solid border-[white] w-[150px] h-[40px] text-center font-bold" href="javascript:setSort(\\'mcap\\');"> market cap </a>\\
                        </div>';
            for(var i = 0; i < data.length; i++) {
                row = data[i]
                st = row['st'+duration];
                html += '<div class="data_row flex hover:bg-[#888] cursor-pointer mx-auto w-full text-[16px] bg-[#1D1D22]" onclick="setPair(\\''+ row['poolAddress']  +'\\')">'+
                            '<div class="data_cell flex items-center border border-solid border-t-[transparent] pl-3 border-[white] w-[330px] h-[35px] pr-2 justify-start text-center">'+
                                '<div class="font-bold">'+ (row['baseSymbol'] == '' ? formatString(row['baseMint']) : row['baseSymbol']) +'</div>'+
                                '<div class="mr-3 text-[#888]"> / '+ (row['quoteSymbol'] == '' ? formatString(row['quoteMint']) : row['quoteSymbol']) +'</div>'+
                                '<div class="flex flex-row items-center justify-center text-[14px] text-[#AAA]">'+
                                    '<img src="'+ row['baseImage'] + '" style="width:20px; margin-right: 5px;">' + row['baseName'] +
                                '</div>'+
                            '</div>'+
                            '<div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[250px] h-[35px] pr-2 justify-end text-right">$ '+ f(row['price']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[110px] h-[35px] pr-2 justify-end text-right">'+ f(st['txns']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[170px] h-[35px] pr-2 justify-end text-right">$ '+ f(st['volume']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[110px] h-[35px] pr-2 justify-end text-right">'+ f(st['makers']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[130px] h-[35px] pr-2 justify-center text-center">'+ f(Number(st['d_price']).toFixed(3) * 100) +'%</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[150px] h-[35px] pr-2 justify-end text-right">$ '+ f(row['liq']) +'</div>\\
                            <div class="data_cell flex items-center border border-solid border-t-[transparent] border-[white] w-[150px] h-[35px] pr-2 justify-end text-right">$ '+ f(row['mcap']) +'</div>\\
                        </div>';
                
            }
            document.getElementById('data-table').innerHTML = html;
          })
          .catch(error => {
              idle = true;
              console.error('Error:', error);
          });
      }

      function fetchData() {
          if (curPage == 1)
            fetchStatistics();
          else
            fetchTransactions();
      }
      
      fetchStatistics();
      setInterval(fetchData, 1000);
    </script>
</html>
"""
