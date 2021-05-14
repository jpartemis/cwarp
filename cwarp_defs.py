import pandas as pd
import numpy as np
from datetime import date
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import yfinance as yf
yf.pdr_override()
import pandas as pd

#Risk and Reward Functions##################################################################
def sharpe_ratio(df,risk_free_rate=0,periodicity=252):
    risk_free_rate=(1+risk_free_rate)**(1/periodicity)-1
    dfMean=np.mean(df)-risk_free_rate
    dfSTD=np.std(df)
    dfSharpe=dfMean/dfSTD*np.sqrt(periodicity)
    return dfSharpe

def sortino_ratio(df,risk_free_rate=0,periodicity=252):
    neg_ndx = np.where(df<0)[0]
    dfSTD= np.std(df[neg_ndx])
    risk_free_rate=(1+risk_free_rate)**(1/periodicity)-1
    dfMean=np.mean(df)-risk_free_rate
    dfSortino=(dfMean/dfSTD)*np.sqrt(periodicity)
    return dfSortino

def return_maxdd_ratio(df,risk_free_rate=0,periodicity=252):
    #drop zero means you will drop all zero values from the calculation
    risk_free_rate=(1+risk_free_rate)**(1/periodicity)-1
    dfMean=(1+np.mean(df)-risk_free_rate)**(periodicity)-1
    maxDD=max_dd(df,use_window=False,window=252,return_data=False)
    return dfMean/abs(maxDD)

def annualized_return(returns,periodicity=252):
    """Assumes returns is a pandas Series"""
    #start_date=returns.index[0]
    #end_date=returns.index[-1]
    #difference_in_years = (end_date-start_date).days/days_in_year
    difference_in_years = len(returns)/periodicity
    r = np.cumprod(returns+1.)
    start_NAV=1
    end_NAV=r[-1]
    AnnualReturn = (1 + (end_NAV - 1) / 1)** (1 / difference_in_years) - 1
    return AnnualReturn

def avg_positive(ret,dropzero=1):
    if dropzero>0:
        positives = ret > 0
    else:
        positives = ret >= 0
    if positives.any():
        return np.mean(ret[positives])
    else:
        return 0.000000000000000000000000000001

def avg_neg(ret):
    negatives = ret < 0
    if negatives.any():
        return np.mean(ret[negatives])
    else:
        return -1*0.000000000000000000000000000001

def win_pct(ret,dropzero=1):
    if dropzero>0:
        win=len(np.where(ret>0)[0])
        total=len(ret)
    else:
        win=len(np.where(ret>=0)[0])
        total=len(ret)
    return (win/total)

def max_dd(pct_df,use_window=False,window=252,return_data=False):
    #calculates the maximum drawdown for the strategy cumulatively or over a rolling window period
    #use_window initiates rolling period, otherwise is cumulative
    #return data provides the raw datastream rather than the min
    if use_window==False:
        out=((((pct_df + 1).cumprod()-(pct_df + 1).cumprod().cummax())/(pct_df + 1).cumprod().cummax()).dropna())
    else:
        out=(((pct_df + 1).cumprod()-(pct_df + 1).cumprod().rolling(window).max())/(pct_df + 1).cumprod().rolling(window).max()).dropna()
    if return_data==True:
        out = out
    else:
        out = min(out)
    return out

def kelly(df,dropzero=0):
    if dropzero==1: df = df[(df!= 0)]
    avg_pos=df[df>=0].mean()
    avg_neg=df[df<0].mean()
    win_pct=df[df>=0].count()/df.count()
    loss_pct=(1-win_pct)
    return ((avg_pos/abs(avg_neg))*win_pct-(loss_pct))/(avg_pos/abs(loss_pct))

def return_analyz(df_pct,bck_test_name='BackTest',bop=None,eop=None):
    df_pct=df_pct.copy()
    if bop==None: bop=min(df_pct.index)
    if eop==None: eop=max(df_pct.index)

    sharpe=SharpeAdj(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)].to_numpy(),dropzero=1, periodicity=252)
    sortino=SortinoAdj(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)].to_numpy(),dropzero=1, periodicity=252)
    annret=annualized_return(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)].to_numpy(),periodicity=252)
    maxdd=max_dd(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)],use_window=False,return_data=False)
    calmar=annret/abs(maxdd)
    #calmar=annualized_return(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)].to_numpy(),days_in_year=252)/abs(max_dd(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)]))
    vol=np.std(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)])*((252)**.5)
    worst_day=min(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)])
    best_day=min(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)])
    win_pct=df_pct[df_pct>=0].count()/df_pct.count()
    avg_positive=df_pct[df_pct>=0].mean()
    avg_neg=df_pct[df_pct<0].mean()
    kelly1=kelly(df_pct[(df_pct.index>=bop)&(df_pct.index<=eop)],dropzero=0)
    data=[annret,vol,sharpe,sortino,maxdd,calmar,kelly,bop,eop]
    arr= pd.DataFrame({'AnnRet': annret, 'Vol': vol, 'Sharpe': sharpe, 'Sortino': sortino, 'MaxDD': maxdd, 'Calmar': calmar,
                       'Kelly': kelly1, 'bop': bop, 'eop': eop},index=[bck_test_name])
    return arr

def monthly_ret_matrix(daily_nav_df):
    return_df=daily_nav_df.iloc[:,0]
    return_df=pd.DataFrame(return_df.resample('M').last())
    return_df['Monthly%']=return_df.pct_change()
    return_df['month']=pd.DatetimeIndex(return_df.index).month
    return_df['year']=pd.DatetimeIndex(return_df.index).year
    return_table=pd.pivot_table(return_df,index=["month"],
                   values=["Monthly%"],
                   aggfunc='sum',fill_value=None,
                   columns=["year"])
    return_table=return_table.append(pd.DataFrame(((return_table+1).cumprod()-1).iloc[-1,:]).rename(columns={12: "Annual"}).T)
    return return_table

def ReturnTable(daily_nav_df,freq='1M'):
    return_df=daily_pct_df.resample('1M').last()
    return_df


def cole_win_above_replace_port(new_asset, replace_port,
                                risk_free_rate=0,
                                financing_rate=0,
                                weight_asset=0.25,
                                weight_replace_port=1,
                                periodicity=252):
    # Cole Win Above Replacement Portolio: Calculate additive return to unit of risk for a new asset on an existing portfolio
    # new_asset = returns of the asset you are thinking of adding to your portfolio
    # replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    # risk_free_rate = Tbill rate
    # financing_rate = portfolio margin/borrowing cost to layer new asset on top of prevailing portfolio
    # weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    # weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    # periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count

    risk_free_rate=(1+risk_free_rate)**(1/periodicity)-1
    financing_rate=(1+financing_rate)**(1/periodicity)-1

    replace_port_ex_rf=replace_port-risk_free_rate
    new_port_returns_ex_rf=(new_asset-financing_rate)*weight_asset+(replace_port*weight_replace_port)-risk_free_rate
    new_port=(new_asset-financing_rate)*weight_asset+(replace_port*weight_replace_port)

    #Calculate Replacement Portfolio Sortino Ratio
    neg_ndx = np.where(replace_port<0)[0]
    replace_port_sortino=np.mean(replace_port_ex_rf)/(np.std(replace_port[neg_ndx]))*np.sqrt(periodicity)

    #Calculate Replacement Portfolio Return to Max Drawdown
    maxdd_replace_port=min((((replace_port + 1).cumprod()-(replace_port + 1).cumprod().cummax())/(replace_port + 1).cumprod().cummax()).dropna())
    replace_port_return_maxdd= ((1+np.mean(replace_port_ex_rf))**(periodicity)-1)/abs(maxdd_replace_port)

    #Calculate New Portfolio Sortino Ratio
    neg_ndx_new = np.where(new_port<0)[0]
    new_port_sortino=np.mean(new_port_returns_ex_rf)/(np.std(new_port[neg_ndx_new]))*np.sqrt(periodicity)

    #Calculate New Portfolio Return to Max Drawdown
    maxdd_new_port=min((((new_port + 1).cumprod()-(new_port + 1).cumprod().cummax())/(new_port + 1).cumprod().cummax()).dropna())
    new_port_return_maxdd= ((1+np.mean(new_port_returns_ex_rf))**(periodicity)-1)/abs(maxdd_new_port)

    #Final CWARP calculation
    CWARP=(((new_port_return_maxdd/replace_port_return_maxdd)*(new_port_sortino/replace_port_sortino))**(1/2)-1)*100
    return CWARP

def cwarp_additive_sortino(new_asset,replace_port,
                                risk_free_rate=0,
                                financing_rate=0,
                                weight_asset=0.25,
                                weight_replace_port=1,
                                periodicity=252):
    # new_asset = returns of the asset you are thinking of adding to your portfolio
    # replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    # risk_free_rate = Tbill rate
    # financing_rate = portfolio margin/borrowing cost to layer new asset on top of prevailing portfolio
    # weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    # weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    # periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count

    risk_free_rate=(1+risk_free_rate)**(1/periodicity)-1
    financing_rate=(1+financing_rate)**(1/periodicity)-1

    replace_port_ex_rf=replace_port-risk_free_rate
    new_port_returns_ex_rf=(new_asset-financing_rate)*weight_asset+(replace_port*weight_replace_port)-risk_free_rate
    new_port=(new_asset-financing_rate)*weight_asset+(replace_port*weight_replace_port)

    #Calculate Replacement Portfolio Sortino Ratio
    neg_ndx = np.where(replace_port<0)[0]
    replace_port_sortino=np.mean(replace_port_ex_rf)/(np.std(replace_port[neg_ndx]))*np.sqrt(periodicity)

    #Calculate Replacement Portfolio Return to Max Drawdown
    maxdd_replace_port=min((((replace_port + 1).cumprod()-(replace_port + 1).cumprod().cummax())/(replace_port + 1).cumprod().cummax()).dropna())
    replace_port_return_maxdd= ((1+np.mean(replace_port_ex_rf))**(periodicity)-1)/abs(maxdd_replace_port)

    #Calculate New Portfolio Sortino Ratio
    neg_ndx_new = np.where(new_port<0)[0]
    new_port_sortino=np.mean(new_port_returns_ex_rf)/(np.std(new_port[neg_ndx_new]))*np.sqrt(periodicity)

    #Calculate New Portfolio Return to Max Drawdown
    maxdd_new_port=min((((new_port + 1).cumprod()-(new_port + 1).cumprod().cummax())/(new_port + 1).cumprod().cummax()).dropna())
    new_port_return_maxdd= ((1+np.mean(new_port_returns_ex_rf))**(periodicity)-1)/abs(maxdd_new_port)

    #Final calculation
    CWARP_add_sortino=((new_port_sortino/replace_port_sortino)-1)*100

    return CWARP_add_sortino

def cwarp_additive_ret_maxdd(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    # new_asset = returns of the asset you are thinking of adding to your portfolio
    # replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    # risk_free_rate = Tbill rate
    # financing_rate = portfolio margin/borrowing cost to layer new asset on top of prevailing portfolio
    # weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    # weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    # periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count

    risk_free_rate=(1+risk_free_rate)**(1/periodicity)-1
    financing_rate=(1+financing_rate)**(1/periodicity)-1

    replace_port_ex_rf=replace_port-risk_free_rate
    new_port_returns_ex_rf=(new_asset-financing_rate)*weight_asset+(replace_port*weight_replace_port)-risk_free_rate
    new_port=(new_asset-financing_rate)*weight_asset+(replace_port*weight_replace_port)

    #Calculate Replacement Portfolio Sortino Ratio
    neg_ndx = np.where(replace_port<0)[0]
    replace_port_sortino=np.mean(replace_port_ex_rf)/(np.std(replace_port[neg_ndx]))*np.sqrt(periodicity)

    #Calculate Replacement Portfolio Return to Max Drawdown
    maxdd_replace_port=min((((replace_port + 1).cumprod()-(replace_port + 1).cumprod().cummax())/(replace_port + 1).cumprod().cummax()).dropna())
    replace_port_return_maxdd= ((1+np.mean(replace_port_ex_rf))**(periodicity)-1)/abs(maxdd_replace_port)

    #Calculate New Portfolio Sortino Ratio
    neg_ndx_new = np.where(new_port<0)[0]
    new_port_sortino=np.mean(new_port_returns_ex_rf)/(np.std(new_port[neg_ndx_new]))*np.sqrt(periodicity)

    #Calculate New Portfolio Return to Max Drawdown
    maxdd_new_port=min((((new_port + 1).cumprod()-(new_port + 1).cumprod().cummax())/(new_port + 1).cumprod().cummax()).dropna())
    new_port_return_maxdd= ((1+np.mean(new_port_returns_ex_rf))**(periodicity)-1)/abs(maxdd_new_port)

    #Final calculation
    CWARP_add_ret_maxdd=((new_port_return_maxdd/replace_port_return_maxdd)-1)*100
    return CWARP_add_ret_maxdd

def cwarp_port_return(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    financing_rate=((financing_rate+1)**(1/periodicity)-1)
    risk_free_rate=((risk_free_rate+1)**(1/periodicity)-1)
    new_port=(new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port-risk_free_rate
    out=(np.mean(new_port)+1)**(periodicity)-1
    return out

def cwarp_port_risk(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    financing_rate=((financing_rate+1)**(1/periodicity)-1)
    risk_free_rate=((risk_free_rate+1)**(1/periodicity)-1)
    new_port=(new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port
    neg_ndx = np.where(new_port<0)[0]
    out=np.std(new_port[neg_ndx])*np.sqrt(periodicity)
    return out

def cwarp_new_port_data(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    financing_rate=((financing_rate+1)**(1/periodicity)-1)
    risk_free_rate=((risk_free_rate+1)**(1/periodicity)-1)
    new_port=(new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port
    return new_port

def retrieve_yhoo_data(ticker='spy', start_date = '2007-07-01', end_date = '2020-12-31'):
    data_hold=yf.Ticker(ticker)
    price_df=data_hold.history(start=start_date,  end=end_date).Close.pct_change()
    price_df.name=ticker
    return price_df
