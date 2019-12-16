# MyFinanceManager

<p align="center">
  <img src="https://i.ibb.co/tzPkVrw/Capture.png">
</p>

#### My Finance Manager (MFM) - to manage all your money in one place, from bank account and investment house.
- Update stocks prices from yahoo finance or from Tel Aviv stock Exchange-TASE (with BizPortal API or using requests_html).
- Get statistics about portfolio history changes, including profit.
- View graphs and receive email report with weekly summery of your portfolio.
- Use built in Currency Converter.

### Notes:
1. Included scrappers are only for Bank Otsar Hahayal and Meitav Dash sites (Israeli companies).
2. Supported stocks are which in Yahoo Finance and TASE.

## Experience Installation:
1. install requirements.txt
2. Run gui.py
3. File -> Import Portfolio -> use Example_data.json 
4. Press Ctrl+U or Edit -> Update Stocks Prices
5. Press Ctrl+P or Graphs -> Show Profit
6. Tools -> Change Email Address and then Ctrl+E or Tools -> Send Email Report -> Fancy Style
7. Tools -> Currency Converter

--------------------------------------------------------------------
Get account info with scrapers (meitav_dash_scraper.py , otsar_haayal_scraper.py):

## Meitav Dash scraper:
```
{
    "Account Number": "999999",
    "Date": "01/11/19",
    "Time": "21:19:29",
    "Balance": "150,548.64",
    "Gain and Loss": "-674.58",
    "Change in Percentage": "-5.5%",
    "Cash": "4555.68",
    "Income": "264.21",
    "Profit": "-2,534.68",
    "Profit in Percentage": "-2.5%",
    "Collateral": "13,554"
}
```

## Otsar Haayal scraper:
```
{
    "Branch": "999",
    "Account Number": "66666",
    "Date": "01/11/2019",
    "Time": "21:15",
    "Current Amount": "21544.78",
    "Foreign Currency": "9854.25",
    "Total Current Account": "31399.03",
    "Charged Amount": "-5587.00",
    "Total Balance": "25812.03"
}
```

## Email report example:
--------------------------------------------------------------------

<html>
<center><h2><b>MyFinanceManager Weekly Report</b></h2><h3><table><thead><tr><th style="text-align: center;"> Portfolio Assets </th><th style="text-align: center;"> Bank CF  </th><th style="text-align: center;"> Trader CF </th><th style="text-align: center;"> Total Assets </th><th style="text-align: center;"> Total Profit </th><th style="text-align: center;"> Total Profit </th></tr><</thead><tbody><tr><td style="text-align: center;">   111,181.21₪    </td><td style="text-align: center;">12,549.00₪</td><td style="text-align: center;"> 5,348.00₪ </td><td style="text-align: center;"> 129,078.21₪  </td><td style="text-align: center;">  13,599.23₪  </td><td style="text-align: center;">    8.16%     </td></tr></tbody></table></h3></center> <a href="https://ibb.co/RDSGZqk"><img src="https://i.ibb.co/W23NqL4/01-11-2019-Profit-Nums.png" alt="01-11-2019-Profit-Nums" border="0"></a> <center><h3><u>Portfolio History Stats</u></h3><table><thead><tr><th style="text-align: center;">  Day  </th><th style="text-align: center;"> Portfolio ILS </th><th style="text-align: center;"> Bank CF </th><th style="text-align: center;"> Trader CF </th><th style="text-align: center;"> Total ILS </th><th style="text-align: center;"> Profit % </th><th style="text-align: center;"> Profit ILS </th></tr></thead><tbody><tr><td style="text-align: center;">Friday </td><td style="text-align: center;">  111,145.27   </td><td style="text-align: center;">12,549.00</td><td style="text-align: center;"> 5,348.00  </td><td style="text-align: center;">129,042.27 </td><td style="text-align: center;">   8.12   </td><td style="text-align: center;"> 13,563.29  </td></tr><tr><td style="text-align: center;">Tuesday</td><td style="text-align: center;">   43,481.31   </td><td style="text-align: center;">12,549.00</td><td style="text-align: center;"> 5,348.00  </td><td style="text-align: center;"> 61,378.31 </td><td style="text-align: center;">  -2.01   </td><td style="text-align: center;">  -534.85   </td></tr></tbody></table></center> <center><h3><u>Current Holdings</u></h3><table><thead><tr><th style="text-align: center;">  </th><th style="text-align: center;"> Symbol </th><th style="text-align: center;"> Lot </th><th style="text-align: center;">   Date   </th><th style="text-align: center;"> Amount </th><th style="text-align: center;"> Buy Price </th><th style="text-align: center;"> Currency </th><th style="text-align: center;"> Market Value USD </th><th style="text-align: center;"> Market Value ILS </th><th style="text-align: center;"> Profit % </th></tr></thead><tbody><tr><td style="text-align: center;">1 </td><td style="text-align: center;">  VTI   </td><td style="text-align: center;">Lot 1</td><td style="text-align: center;">22.10.2019</td><td style="text-align: center;">   57   </td><td style="text-align: center;">   152.6   </td><td style="text-align: center;">   USD    </td><td style="text-align: center;">     8,860.1      </td><td style="text-align: center;">     31,251.0     </td><td style="text-align: center;">   1.9    </td></tr><tr><td style="text-align: center;">2 </td><td style="text-align: center;">  AAPL  </td><td style="text-align: center;">Lot 2</td><td style="text-align: center;">01.11.2019</td><td style="text-align: center;">   29   </td><td style="text-align: center;">   130.2   </td><td style="text-align: center;">   USD    </td><td style="text-align: center;">     7,336.1      </td><td style="text-align: center;">     25,875.7     </td><td style="text-align: center;">   94.4   </td></tr><tr><td style="text-align: center;">3 </td><td style="text-align: center;">  IHF   </td><td style="text-align: center;">Lot 1</td><td style="text-align: center;">01.11.2019</td><td style="text-align: center;">   35   </td><td style="text-align: center;">   145.0   </td><td style="text-align: center;">   USD    </td><td style="text-align: center;">     6,262.7      </td><td style="text-align: center;">     22,089.4     </td><td style="text-align: center;">   23.4   </td></tr><tr><td style="text-align: center;">4 </td><td style="text-align: center;">  NKE   </td><td style="text-align: center;">Lot 1</td><td style="text-align: center;">01.11.2019</td><td style="text-align: center;">   70   </td><td style="text-align: center;">   70.0    </td><td style="text-align: center;">   USD    </td><td style="text-align: center;">     6,248.9      </td><td style="text-align: center;">     22,040.9     </td><td style="text-align: center;">   27.5   </td></tr><tr><td style="text-align: center;">5 </td><td style="text-align: center;">  IAU   </td><td style="text-align: center;">Lot 1</td><td style="text-align: center;">01.11.2019</td><td style="text-align: center;">  150   </td><td style="text-align: center;">   25.0    </td><td style="text-align: center;">   USD    </td><td style="text-align: center;">     2,167.5      </td><td style="text-align: center;">     7,645.1      </td><td style="text-align: center;">  -42.2   </td></tr><tr><td style="text-align: center;">6 </td><td style="text-align: center;">  VXUS  </td><td style="text-align: center;">Lot 1</td><td style="text-align: center;">01.11.2019</td><td style="text-align: center;">   12   </td><td style="text-align: center;">   122.5   </td><td style="text-align: center;">   USD    </td><td style="text-align: center;">      646.1       </td><td style="text-align: center;">     2,279.0      </td><td style="text-align: center;">  -56.0   </td></tr></tbody></table></center><br><big>End of report.</big><br><small>Sent by MyFinanceManager.</small>
</html>
