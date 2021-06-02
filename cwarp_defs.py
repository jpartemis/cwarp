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
def sharpe_ratio(df,risk_free=0,periodicity=252):
    """df - asset return series, e.g. daily returns based on daily close prices of asset
   risk_free - annualized risk free rate (default is assumed to be 0)
   periodicity - number of periods at desired frequency in one year
                e.g. 252 business days in 1 year (default),
                12 months in 1 year,
                52 weeks in 1 year etc."""
    # convert return series to numpy array (in case Pandas series is provided)
    df = np.asarray(df)
    # convert annualized risk free rate into appropriate value for provided frequency of asset return series (df)
    risk_free=(1+risk_free)**(1/periodicity)-1
    # calculate mean excess return based on return series provided
    dfMean=np.nanmean(df)-risk_free
    # calculate standard deviation of return series
    dfSTD=np.nanstd(df)
    # calculate Sharpe Ratio = Mean excess return / Std of returns * sqrt(periodicity)
    dfSharpe=dfMean/dfSTD*np.sqrt(periodicity)
    return dfSharpe

def target_downside_deviation(df, MAR=0, periodicity=252):
    """df - asset return series, e.g. daily returns based on daily close prices of asset
    minimum acceptable return (MAR) - value is subtracted from returns before root-mean-square calculation to obtain target downside deviation (TDD)"""
    # convert return series to numpy array (in case Pandas series is provided)
    df = np.asarray(df)
    # TDD step 1: subtract mininum acceptable return (MAR) from period returns provided in df
    df_ = df - MAR
    # TDD step 2: zero out positive excess returns and calculate root-mean-square for resulting values
    df2 = np.where(df_<0, df_, 0)
    tdd = np.sqrt(np.nanmean(df2**2))
    return tdd

def sortino_ratio(df,risk_free=0, periodicity=252, include_risk_free_in_vol=False):
    """df - asset return series, e.g. daily returns based on daily close prices of asset
   risk_free - annualized risk free rate (default is assumed to be 0). Note: risk free rate is assumed to be the target return/minimum acceptable return (MAR)
               used in calculating both the mean excess return (numerator of Sortino ratio) and determining target downside deviation (TDD, the denominator of Sortino)
   periodicity - number of periods at desired frequency in one year
                e.g. 252 business days in 1 year (default),
                12 months in 1 year,
                52 weeks in 1 year etc."""
    # convert return series to numpy array (in case Pandas series is provided)
    df = np.asarray(df)
    # convert annualized risk free rate into appropriate value for provided frequency of asset return series (df)
    risk_free=(1+risk_free)**(1/periodicity)-1
    # calculate mean excess return based on return series provided
    dfMean=np.nanmean(df)-risk_free
    # calculate target downside deviation (TDD)
    # assume risk free rate is MAR
    if include_risk_free_in_vol==True: MAR=risk_free
    else: MAR=0
    tdd = target_downside_deviation(df, MAR=MAR)
    # calculate Sortino Ratio = Mean excess return / TDD * sqrt(periodicity)
    dfSortino=(dfMean/tdd)*np.sqrt(periodicity)
    return dfSortino

def annualized_return(df,periodicity=252):
    """df - asset return series, e.g. returns based on daily close prices of asset
   periodicity - number of periods at desired frequency in one year
                e.g. 252 business days in 1 year (default),
                12 months in 1 year,
                52 weeks in 1 year etc."""
    # convert return series to numpy array (in case Pandas series is provided)
    df = np.asarray(df)
    # how many years of returns data is provided in df
    difference_in_years = len(df)/periodicity
    # starting net asset value / NAV (assumed to be 1) and cumulative returns (r) over time period provided in returns data
    start_NAV=1.0
    r = np.nancumprod(df+start_NAV)
    # end NAV based on final cumulative return
    end_NAV=r[-1]
    # determine annualized return
    AnnualReturn = end_NAV**(1 / difference_in_years) - 1
    return AnnualReturn

def max_dd(df, return_data=False):
    """df - asset return series, e.g. returns based on daily close prices of asset
    return_data - boolean value to determine if drawdown values over the return data time period should be return, instead of max DD"""
    # convert return series to numpy array (in case Pandas series is provided)
    df = np.asarray(df)
    # calculate cumulative returns
    start_NAV = 1
    r = np.nancumprod(df+start_NAV)
    # calculate cumulative max returns (i.e. keep track of peak cumulative return up to that point in time, despite actual cumulative return at that point in time)
    peak_r = np.maximum.accumulate(r)
    # determine drawdowns relative to peak cumulative return achieved up to each point in time
    dd = (r - peak_r) / peak_r
    # return drawdown values over time period if return_data is set to True, otherwise return max drawdown which will be a positive number
    if return_data==True:
        out = dd
    else:
        out = np.abs(np.nanmin(dd))
    return out

def return_maxdd_ratio(df,risk_free=0,periodicity=252):
    """df - asset return series, e.g. returns based on daily close prices of asset
   risk_free - annualized risk free rate (default is assumed to be 0)
   periodicity - number of periods at desired frequency in one year
                e.g. 252 business days in 1 year (default),
                12 months in 1 year,
                52 weeks in 1 year etc."""
    # convert return series to numpy array (in case Pandas series is provided)
    df = np.asarray(df)
    # convert annualized risk free rate into appropriate value for provided frequency of asset return series (df)
    risk_free=(1+risk_free)**(1/periodicity)-1
    # determine annualized return to be used in numerator of return to max drawdown (RMDD) calculation
    AnnualReturn = annualized_return(df, periodicity=periodicity)
    # determine max drawdown to be used in the denominator of RMDD calculation
    maxDD=max_dd(df,return_data=False)
    return (AnnualReturn-risk_free)/abs(maxDD)

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


def cole_win_above_replace_port(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    """Cole Win Above Replacement Portolio (CWARP): Total score to evaluate whether any new investment improves or hurts the return to risk of your total portfolio.
    new_asset = returns of the asset you are thinking of adding to your portfolio
    replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    risk_free_rate = Tbill rate (annualized)
    financing_rate = portfolio margin/borrowing cost (annualized) to layer new asset on top of prevailing portfolio (e.g. LIBOR + 60bps). No financing rate is reasonable for derivate overlay products.
    weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count"""
    # convert annualized financing rate into appropriate value for provided periodicity
    # risk_free_rate will be converted appropriately in respective Sortino and RMDD calcs
    financing_rate=(1+financing_rate)**(1/periodicity)-1

    #Calculate Replacement Portfolio Sortino Ratio
    replace_port_sortino = sortino_ratio(replace_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Calculate Replacement Portfolio Return to Max Drawdown
    replace_port_return_maxdd = return_maxdd_ratio(replace_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Calculate New Portfolio Sortino Ratio
    new_port = (new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port
    new_port_sortino = sortino_ratio(new_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Calculate New Portfolio Return to Max Drawdown
    new_port_return_maxdd = return_maxdd_ratio(new_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Final CWARP calculation
    CWARP = ((new_port_return_maxdd/replace_port_return_maxdd*new_port_sortino/replace_port_sortino)**(1/2)-1)*100

    return CWARP

def cwarp_additive_sortino(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    """Cole Win Above Replacement Portolio (CWARP) Sortino +: Isolates new investment effect on total portfolio Sortino Ratio, which is a portion of the holistic CWARP score.
    new_asset = returns of the asset you are thinking of adding to your portfolio
    replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    risk_free_rate = Tbill rate (annualized)
    financing_rate = portfolio margin/borrowing cost (annualized) to layer new asset on top of prevailing portfolio (e.g. LIBOR + 60bps). No financing rate is reasonable for derivate overlay products.
    weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count"""
    # convert annualized financing rate into appropriate value for provided periodicity
    # risk_free_rate will be converted appropriately in respective Sortino and RMDD calcs
    financing_rate=(1+financing_rate)**(1/periodicity)-1

    #Calculate Replacement Portfolio Sortino Ratio
    replace_port_sortino = sortino_ratio(replace_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Calculate New Portfolio Sortino Ratio
    new_port = (new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port
    new_port_sortino = sortino_ratio(new_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Final calculation
    CWARP_add_sortino=((new_port_sortino/replace_port_sortino)-1)*100

    return CWARP_add_sortino

def cwarp_additive_ret_maxdd(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    """Cole Win Above Replacement Portolio (CWARP) Ret to Max DD +: Isolates new investment effect on total portfolio Return to MAXDD, which is a portion of the holistic CWARP score.
    new_asset = returns of the asset you are thinking of adding to your portfolio
    replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    risk_free_rate = Tbill rate (annualized)
    financing_rate = portfolio margin/borrowing cost (annualized) to layer new asset on top of prevailing portfolio (e.g. LIBOR + 60bps). No financing rate is reasonable for derivate overlay products.
    weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count"""
    # convert annualized financing rate into appropriate value for provided periodicity
    # risk_free_rate will be converted appropriately in respective Sortino and RMDD calcs
    financing_rate=(1+financing_rate)**(1/periodicity)-1

    #Calculate Replacement Portfolio Return to Max Drawdown
    replace_port_return_maxdd = return_maxdd_ratio(replace_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Calculate New Portfolio Return to Max Drawdown
    new_port = (new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port
    new_port_return_maxdd = return_maxdd_ratio(new_port, risk_free=risk_free_rate, periodicity=periodicity)

    #Final calculation
    CWARP_add_ret_maxdd=((new_port_return_maxdd/replace_port_return_maxdd)-1)*100

    return CWARP_add_ret_maxdd

def cwarp_port_return(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    """Cole Win Above Replacement Portolio (CWARP) Portfolio Return: Returns of the aggregate portfolio after a new asset is financed and layered on top of the replacement portfolio.
    new_asset = returns of the asset you are thinking of adding to your portfolio
    replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    risk_free_rate = Tbill rate (annualized)
    financing_rate = portfolio margin/borrowing cost (annualized) to layer new asset on top of prevailing portfolio (e.g. LIBOR + 60bps). No financing rate is reasonable for derivate overlay products.
    weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count"""
    # convert annual financing based on periodicity
    financing_rate=((financing_rate+1)**(1/periodicity)-1)

    # compose new portfolio
    new_port=(new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port

    # calculate annualized return of new portfolio and subtract risk-free rate
    out = annualized_return(new_port, periodicity=periodicity) - risk_free_rate
    return out

def cwarp_port_risk(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    """Cole Win Above Replacement Portolio (CWARP) Portfolio Risk: Volatility of the aggregate portfolio after a new asset is financed and layered on top of the replacement portfolio.
    new_asset = returns of the asset you are thinking of adding to your portfolio
    replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    risk_free_rate = Tbill rate (annualized)
    financing_rate = portfolio margin/borrowing cost (annualized) to layer new asset on top of prevailing portfolio (e.g. LIBOR + 60bps). No financing rate is reasonable for derivate overlay products.
    weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count"""
    # convert annual financing and risk free rates based on periodicity
    financing_rate=((financing_rate+1)**(1/periodicity)-1)
    risk_free_rate=((risk_free_rate+1)**(1/periodicity)-1)
    # compose new portfolio
    new_port=(new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port
    # calculated target downside deviation (TDD)
    tdd = target_downside_deviation(new_port, MAR=0)*np.sqrt(periodicity)
    return tdd

def cwarp_new_port_data(new_asset,replace_port,risk_free_rate=0,financing_rate=0,weight_asset=0.25,weight_replace_port=1,periodicity=252):
    """Cole Win Above Replacement Portolio (CWARP) return stream: Return series after a new asset is financed and layered on top of the replacement portfolio.
    new_asset = returns of the asset you are thinking of adding to your portfolio
    replace_port = returns of your pre-existing portfolio (e.g. S&P 500 Index, 60/40 Stock-Bond Portfolio)
    risk_free_rate = Tbill rate
    financing_rate = portfolio margin/borrowing cost to layer new asset on top of prevailing portfolio (e.g. LIBOR + 60bps). No financing rate is reasonable for derivate overlay products.
    weight_asset = % weight you wish to overlay for the new asset on top of the previous portfolio, 25% overlay allocation is standard
    weight_replace_port = % weight of the replacement portfolio, 100% pre-existing portfolio value is standard
    periodicity = the frequency of the data you are sampling, typically 12 for monthly or 252 for trading day count"""
    # convert annual financing based on periodicity
    financing_rate=((financing_rate+1)**(1/periodicity)-1)
    new_port=(new_asset-financing_rate)*weight_asset+replace_port*weight_replace_port
    return new_port
