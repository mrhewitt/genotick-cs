//+------------------------------------------------------------------+
//|                                          GenotickWalkForward.mq4 |
//|                                      Copyright 2019, Mark Hewitt |
//|                                     https://www.markhewitt.co.za |
//|                                                                  |
//| Given a Genotick predictions output file, this EA will execute   |
//| the prections in the actual market								 |
//|                                                                  |
//| Provides an option to instead of trade at the open price of the  |
//| bar to rather offset the entry by a limit order of few ticks,    |
//| relying on the fact that markets don't often show an open-drive	 |
//|  (moving in one direction immediatly without any retracement)    |
//| This allows better fills and solves the end of day problem       |
//|																	 |			
//| End of day problem:  Note when using tools like Genotick real    |
//| trading conditions are not taken into account, and in FX when a  |
//| new daily bar is opened, all major sessions are closed, and many |
//| brokers are closed for 5-10 minutes for maintenance, making 	 |
//| spreads very wide, and hence hard to place a trade filled at the |
//| daily open as assumed by tools like Genotick				     |
//|																	 |
//| One solution is to offset your order as a limit order with the   |
//| limit price the daily open, this means you will always be filled |
//| at the price assumed by Genotick, but might sometimes miss a 	 |
//| on days the present as an open drice, meaning you miss 			 |
//| potentially the best days, and always catch the loosers.		 |	
//|																	 |
//| Experiement with what works best on your market  			   	 |
//|																	 |
//| By default this script assumes market with mostly retrace by 10% |
//| of currently daily ATR, the additonal gain by the offset 		 |
//| compenstates for occasioanl missed entry by increasing other 	 |
//| winners and decreasing every loosing day						 |
//|																	 |	
//| #TODO: Flesh out to be a more complete tester					 | 
//+------------------------------------------------------------------+
#property copyright "Copyright 2019, Mark Hewitt"
#property link      "https://www.markhewitt.co.za"
#property version   "1.00"
#property strict

//--- input parameters
input double   Lots=0.01;
input double   ATRRatio = 0.1;
input double   SLRatioOfATR = 0;
input bool     UseLimitOffset = true;
input string   sINVERT = "--- If Invert is true then EA will trade opposite to Genotick ---";
input bool     Invert=false;
input int      Magic = 20190606;
input string   PFILE = "--- Put your file in tester/files folder ---";
input string   PredictionsFile = "walkforward.csv";	 
input string   Comment = "GTWF-EA";

datetime previousBar ;
// max 2000 bars of walk forawrd
string action_data[3][2000];
// is the given data daily or intra day , day data is genotick format YYYYDDMM
// intraday data is time format  YYYYDDMMHHmmSS
bool day_format = true;
int days = 0;


//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
      previousBar = iTime(Symbol(),Period(),0);
      if ( !loadCSV() ) { return (INIT_FAILED); }
      day_format = (StringLen(action_data[0][0]) == 8);    
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---
   
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---
      // we only make a new trading decision once a new bar opens
      if ( newBar(previousBar,Symbol(),Period()) ) {
         
         // remove any unfilled orders
         flatten(OP_BUYLIMIT);
         flatten(OP_SELLLIMIT);
         
         int yesterday;
         
         // we get "yesterdays" bar date, as this is the bar that Genotick used to make the
         // prediction for what is now today in MT4 time
         string date = TimeToString(Time[1], ( day_format ? TIME_DATE : TIME_DATE|TIME_MINUTES|TIME_SECONDS) );
         StringReplace(date, ".", "" );
         StringReplace(date," ", "");
         StringReplace(date, ":", "");
         for ( yesterday = 0; yesterday < days; yesterday++ ) {
            if ( date == action_data[0][yesterday] ) {
               Print("Row ", yesterday, " is yesterday, ", date , " on MT4 matching ", action_data[0][yesterday], " in data");
               break;
            }
         }
               
         string prediction = action_data[2][yesterday];
         Print( date, " On " , action_data[0][yesterday], " we predicted ", prediction);
         
         // check to see if we are currently in a position, if it is the same as the prediction, we do nothing
         // and just stay in, if its not, we cut and reverse
         int pos = currentPosition();
         if ( pos == -1 || (pos == OP_BUY && prediction != "UP") || (pos == OP_SELL && prediction != "DOWN") ) {
            flatten();
            if ( prediction == "UP" ) {
               buy();
            } else if ( prediction == "DOWN" ) {
               sell();
            }
         }
      }
  }
//+------------------------------------------------------------------+



void buy() {
   while(IsTradeContextBusy()) Sleep(50);
   RefreshRates();
   
   if ( !Invert ) {
      if ( !UseLimitOffset ) {
         OrderSend(Symbol(), OP_BUY, Lots, Ask, 0, 0, 0/*Bid - (TPPips/10)*/, Comment, Magic);
      } else {
      //   Print("Bid at ", Bid, ", buy limit at ", Bid - getOffset());
         double price = Open[0] - getOffset();
         OrderSend(Symbol(), OP_BUYLIMIT, Lots, price, 0, SLRatioOfATR ? price - getSL() : 0, 0/*Bid - (TPPips/10)*/, Comment, Magic);
      }
   } else {
      // we are fading the strategy, so go long when strategy says go short, with TP where stratgy stop was and SL when target was
      OrderSend(Symbol(), OP_SELL, Lots, Bid, 0, 0, 0, "", Magic);
   }
}


void sell() {
   while(IsTradeContextBusy()) Sleep(50);
   RefreshRates();
    
   if ( !Invert ) {
     if ( !UseLimitOffset ) {
         OrderSend(Symbol(), OP_SELL, Lots, Bid, 0, 0, 0/*Bid - (TPPips/10)*/, Comment, Magic);
     } else {
      //   Print("Bid at ", Bid, ", sell limit at ", Bid + getOffset());
         double price  = Open[0] + getOffset();         
         OrderSend(Symbol(), OP_SELLLIMIT, Lots, price, 0, SLRatioOfATR ? price + getSL() : 0, 0/*Bid - (TPPips/10)*/, Comment, Magic);
     }
   } else {
      // we are fading the strategy, so go long when strategy says go short, with TP where stratgy stop was and SL when target was
      OrderSend(Symbol(), OP_BUY, Lots, Ask, 0, 0, 0, "", Magic);
   }
}

double getOffset() {
   double atr = iATR(Symbol(),Period(),20,1);
   double offset = NormalizeDouble(atr * ATRRatio,Digits());
   return offset;
}

double getSL() {
   return ( SLRatioOfATR ? NormalizeDouble(iATR(Symbol(),Period(),20,1) * SLRatioOfATR,Digits()) : 0 );
}

void flatten( int onlyTradesOf = -1, bool wholePosition = true ) {

   RefreshRates();
   for (int cc = OrdersTotal() - 1; cc >= 0; cc--)
   {
      if (!OrderSelect(cc, SELECT_BY_POS) ) continue;
      if ( OrderMagicNumber() == Magic && OrderSymbol() == Symbol() && (onlyTradesOf == -1 || OrderType() == onlyTradesOf) ) {
         if ( OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT ) {
            OrderDelete(OrderTicket());
         } else { 
            OrderClose(OrderTicket(),OrderLots(),(OrderType() == OP_BUY ? Bid : Ask),0);
         }
         if ( !wholePosition ) { break; }
      }
   }
 
   
}

/**
 * Returns true if there are active positions placed by this EA on this symbol, false otherwise
 */
bool isFlat() {
   for (int cc = OrdersTotal() - 1; cc >= 0; cc--) {
      if (!OrderSelect(cc, SELECT_BY_POS) ) continue;      
      if ( OrderMagicNumber() == Magic && OrderSymbol() == Symbol() ) {
         return (false);     // found an active position in our EA
      }
   }
   
   return (true);   // no open orders for our EA
}

/**
 * finds an open order for this EA and returns its type
 */ 
int currentPosition() {
   for (int cc = OrdersTotal() - 1; cc >= 0; cc--) {
      if (!OrderSelect(cc, SELECT_BY_POS) ) continue;      
      if ( OrderMagicNumber() == Magic && OrderSymbol() == Symbol() ) {
         return OrderType();     // found an active position in our EA
      }
   }
   return -1;     // no positions
}

// This function returns the value true if the current bar/candle was just formed
bool newBar(datetime& pBar,string symbol,int timeframe)
{
   if ( pBar < iTime(symbol,timeframe,0) )
   {
      pBar = iTime(symbol,timeframe,0);
      return(true);
   }
   else
   {
      return(false);
   }
}


bool loadCSV() {
   int row=0,col=0; //column and row pointer for the array
   string filename = PredictionsFile;
   int handle = FileOpen(filename,FILE_CSV|FILE_READ,","); //comma delimiter
   if ( handle != INVALID_HANDLE ) {
     while( True ) {
       string temp = FileReadString(handle); //read csv cell
       if ( FileIsEnding(handle) ) break; 
       // skip oddrows, this has this reverse data in it
       if ( true || row % 2 == 0 )  { action_data[col][row] = temp; } 
       if ( FileIsLineEnding(handle) ) {
         col = 0; //reset col = 0 for the next row
         row++; //next row
       } else {
         col++; //next col of the same row
       }
     }
     FileClose(handle);
     days = row;
     Print("Loaded ", days, " of walk-forward predictions");
     return true;
   } else {
     Print("File "+filename+" not found, the last error is ", GetLastError());
     return false;
   }
 }  