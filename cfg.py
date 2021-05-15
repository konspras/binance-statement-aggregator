# transaction history colulmns
trcols = {"account": "Account",
          "change": "Change",
          "coin": "Coin",
          "operation": "Operation",
          "remark": "Remark",
          "date": "UTC_Time",
          }

# trade history cols
tdcols_0 = {"amount": "Amount",
            "executed": "Executed",
            "fee": "Fee",
            "pair": "Pair",
            "price": "Price",
            "side": "Side",
            "date": "\ufeffDate(UTC)"}  # tf?

tdcols = {"amount": "Amount",
          "executed": "Total",
          "fee": "Fee",
          "fee coin": "Fee Coin",
          "pair": "Market",
          "price": "Price",
          "side": "Type",
          "date": "Date(UTC)"}

ethstcols = {"date": "Date",
             "out": "Coin",
             "in": "Token",
             "amount": "Amount",
             "status": "Status"}

bethdstrcols = {"date": "Date",
                "in": "Token",
                "amount": "Amount",
                "position": "Position"}

base_coins = ["EUR", "BUSD", "USDT", "USDC"]

default_coin = "BUSD"

coins_used = ['EGLD', 'HOT', 'BAT', 'BUSD', 'ETH', 'LINK', 'LDEUR', 'TLM',
              'EUR', 'BTC', 'ALICE', 'ENJ', 'DOT', 'ADA', 'BNB', 'BETH', 'ALPHA', 'SHIB']

considered_transaction_ops = ["Deposit", "Withdraw", "Fee", "Savings Interest", "Launchpool Interest",
                              "Buy", "POS savings interest", "Commission History", "Savings purchase",
                              "Transaction Related", "Savings Principal redemption", "POS savings purchase",
                              "IsolatedMargin loan", "BNB deducts fee", "POS savings redemption"]
