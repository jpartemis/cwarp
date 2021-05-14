from cwarp_defs import *
from io import BytesIO
import datetime
import seaborn as sns

import streamlit as st

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

def render_latex(formula, fontsize=12, dpi=300):
    """Renders LaTeX formula into Streamlit."""
    fig = plt.figure()
    text = fig.text(0, 0, '$%s$' % formula, fontsize=fontsize)
    fig.savefig(BytesIO(), dpi=dpi)  # triggers rendering
    bbox = text.get_window_extent()
    width, height = bbox.size / float(dpi) + 0.05
    fig.set_size_inches((width, height))
    dy = (bbox.ymin / float(dpi)) / height
    text.set_position((0, -dy))
    buffer = BytesIO()
    fig.savefig(buffer, dpi=dpi, format='jpg')
    plt.close(fig)
    st.image(buffer)

def main():
    st.sidebar.image('Artemis.png')
    st.header("CWarp Calculator")

    body = """CWARP, like Sharpe or Sortino ratio, is a number that quantifies the attractiveness of of a prospective asset.
Like the Sharpe ratio, the more positive the CWARP the more attractive an asset.

Sharpe ratios have the problem that the best portfolio isn't built from assets which have the best Sharpe ratios.
In fact it is possible that between assets with three sortino ratios $S_a < S_b < S_c$, the best portfolio is built from
the two weaker assets $S_a, S_b$. Reliance on this simple number has lead to underdiversified, fragile portfolios.
The whole is not the sum of the parts.

To improve the situation, CWARP $\chi$ measures the attractiveness of a portfolio after an asset is added.
Here RMDD is the return to max-drawdown ratio, and n and p represent the new and old portfolio respectively :
"""
    st.markdown(body)
    formula = render_latex(r'\chi/100 = \sqrt{ \left( \frac{S_n}{S_p} \right) \left(  \frac{ RMDD_n }{ RMDD_p}  \right) }-1.')
    st.markdown("""Using the boxes below, you can calculate CWARP based on your own portfolio for prospective assets,
    so long as a data provider has history on your holdings. Just edit the example entries.""")

    start_date = st.sidebar.date_input("Start Date", datetime.date(2007,7,1)).strftime("%Y-%m-%d")
    end_date = st.sidebar.date_input("End Date", datetime.date(2020,12,31)).strftime("%Y-%m-%d")
    weight_asset = st.sidebar.slider('Diversifier Weight', min_value=0.0001, max_value=0.9999, value=.25)
    risk_free_rate = st.sidebar.slider('Risk-Free Rate (annualized)', min_value=0.0, max_value=0.2, value=0.027)
    financing_rate = st.sidebar.slider('Financing Rate (annualized)', min_value=0.0, max_value=0.2, value=0.0)
    replacement_port_name = st.sidebar.text_input("Replacement Portfolio Name", "Plain 60/40")

    ticker_string_ = "qqq, lqd, hyg, tlt, ief, shy, gld, efa, eem, iyr, xle, xlf"
    ticker_string = st.text_input("Prospective Portfolio Diversifiers (comma separated)", ticker_string_)
    ticker_list=ticker_string.replace(' ','').split(',')

    port_string_ = ".6, spy, .4, ief"
    port_string = st.text_input("Portfolio (comma separated, fraction_1, symbol_1, fraction_2, symbol_2... )", port_string_)
    port_list=port_string.replace(' ','').split(',')
    replacement_port_tik=[]
    replacement_port_w=[]
    replacement_port_list = []
    for i in range(len(port_list)//2):
        replacement_port_w.append(float(port_list[2*i]))
        replacement_port_tik.append(port_list[2*i+1])
        with st.spinner("Pulling data..."):
            D = retrieve_yhoo_data(replacement_port_tik[-1], start_date, end_date)
            replacement_port_list.append(D)

    replacement_port = replacement_port_list[0]
    for k in range(1,len(replacement_port_list)):
        replacement_port += replacement_port_list[k]*(replacement_port_w[k]/sum(replacement_port_w))

    replacement_port.name=replacement_port_name
    risk_ret_df=pd.DataFrame(index=['Start_Date','End_Date','CWARP','+Sortino','+Ret_To_MaxDD','Sharpe','Sortino','Max_DD'],columns=ticker_list)
    new_risk_ret_df=pd.DataFrame(index=['Return','Vol','Sharpe','Sortino','Max_DD','Ret_To_MaxDD',f'CWARP_{round(100*weight_asset)}%_asset'],columns=ticker_list)
    new_risk_ret_df=new_risk_ret_df.add_suffix(f'@{round(100*weight_asset)}% | '+replacement_port.name+'@100%')
    new_risk_ret_df[replacement_port.name]=np.nan
    prices_df=pd.DataFrame(index=retrieve_yhoo_data(ticker_list[0], start_date, end_date).index)

    # Save these for later plotting...
    new_ports = {}
    for i in range(0,len(ticker_list)):
        temp_data=retrieve_yhoo_data(ticker_list[i], start_date, end_date)
        prices_df=pd.merge(prices_df,temp_data, left_index=True, right_index=True)
        risk_ret_df.loc['Start_Date',ticker_list[i]]=min(temp_data.index)
        risk_ret_df.loc['End_Date',ticker_list[i]]=max(temp_data.index)
        risk_ret_df.loc['CWARP',ticker_list[i]]=cole_win_above_replace_port(new_asset=temp_data, replace_port=replacement_port,
                                                                                risk_free_rate = risk_free_rate,
                                                                                financing_rate = financing_rate,
                                                                                weight_asset = weight_asset
                                                                                )
        risk_ret_df.loc['+Sortino',ticker_list[i]]=cwarp_additive_sortino(new_asset=temp_data, replace_port=replacement_port,
                                                                                        risk_free_rate = risk_free_rate,
                                                                                        financing_rate = financing_rate,
                                                                                        weight_asset = weight_asset)
        risk_ret_df.loc['+Ret_To_MaxDD',ticker_list[i]]=cwarp_additive_ret_maxdd(new_asset=temp_data, replace_port=replacement_port,
                                                                                        risk_free_rate = risk_free_rate,
                                                                                        financing_rate = financing_rate,
                                                                                        weight_asset = weight_asset)
        risk_ret_df.loc['Sharpe',ticker_list[i]]=sharpe_ratio(temp_data, risk_free_rate = risk_free_rate)
        risk_ret_df.loc['Sortino',ticker_list[i]]=sortino_ratio(temp_data, risk_free_rate = risk_free_rate)
        risk_ret_df.loc['Max_DD',ticker_list[i]]=max_dd(temp_data)
        new_risk_ret_df.loc['Return',new_risk_ret_df.columns[i]]=cwarp_port_return(new_asset=temp_data,replace_port=replacement_port,
                                                                                                risk_free_rate = risk_free_rate,
                                                                                                financing_rate = financing_rate,
                                                                                                weight_asset = weight_asset)
        new_risk_ret_df.loc['Vol',new_risk_ret_df.columns[i]]=cwarp_port_risk(new_asset=temp_data,replace_port=replacement_port,
                                                                                                risk_free_rate = risk_free_rate,
                                                                                                financing_rate = financing_rate,
                                                                                                weight_asset = weight_asset)
        cnpd = cwarp_new_port_data(new_asset=temp_data,replace_port=replacement_port, risk_free_rate = risk_free_rate,
                                                                                                financing_rate = financing_rate,
                                                                                                weight_asset = weight_asset)
        new_ports[ticker_list[i]] = cnpd
        new_risk_ret_df.loc['Sharpe',new_risk_ret_df.columns[i]]=sharpe_ratio(cnpd.copy(), risk_free_rate = risk_free_rate)
        new_risk_ret_df.loc['Sortino',new_risk_ret_df.columns[i]]=sortino_ratio(cnpd.copy(), risk_free_rate = risk_free_rate)
        new_risk_ret_df.loc['Max_DD',new_risk_ret_df.columns[i]]=max_dd(cnpd.copy())
        new_risk_ret_df.loc['Ret_To_MaxDD',new_risk_ret_df.columns[i]]=return_maxdd_ratio(cnpd.copy(), risk_free_rate = risk_free_rate)
        new_risk_ret_df.loc[f'CWARP_{round(100*weight_asset)}%_asset',new_risk_ret_df.columns[i]]=risk_ret_df.loc['CWARP',ticker_list[i]]

    new_risk_ret_df.loc['Return',[replacement_port_name]]=(replacement_port.mean()+1)**252-1
    new_risk_ret_df.loc['Vol',[replacement_port_name]]=replacement_port.std()*np.sqrt(252)
    new_risk_ret_df.loc['Sharpe',[replacement_port_name]]=sharpe_ratio(replacement_port, risk_free_rate = risk_free_rate)
    new_risk_ret_df.loc['Sortino',[replacement_port_name]]=sortino_ratio(replacement_port, risk_free_rate = risk_free_rate)
    new_risk_ret_df.loc['Max_DD',[replacement_port_name]]=max_dd(replacement_port)
    new_risk_ret_df.loc['Ret_To_MaxDD',[replacement_port_name]]=return_maxdd_ratio(replacement_port, risk_free_rate = risk_free_rate)
    first_col = new_risk_ret_df.pop(replacement_port_name)
    new_risk_ret_df.insert(0, replacement_port_name, first_col)
    st.write(risk_ret_df)
    st.write(new_risk_ret_df)
    vol_arr=new_risk_ret_df.loc['Vol',new_risk_ret_df.columns[1:]]
    ret_arr=new_risk_ret_df.loc['Return',new_risk_ret_df.columns[1:]]
    sharpe_arr=new_risk_ret_df.loc['Sharpe',new_risk_ret_df.columns[1:]]
    cwarp_arr=risk_ret_df.loc['CWARP',:]
    #labels_arr=new_risk_ret_df.columns
    max_sr_vol=new_risk_ret_df.loc['Vol',replacement_port_name]
    max_sr_ret=new_risk_ret_df.loc['Vol',replacement_port_name]

    # f = plt.figure(figsize=(10,6))
    # plt.scatter(vol_arr, ret_arr, c=cwarp_arr, cmap='winter',label=new_risk_ret_df.columns,alpha=.9)
    # plt.colorbar(label='Cole Win Above Replacement Portfolio')
    # plt.title('Efficient Frontier using CWARP', fontsize=15)
    # plt.xlabel('Downside Volatility',fontsize=15)
    # plt.ylabel('Return',fontsize=15)
    # plt.scatter(max_sr_vol, max_sr_ret,c='red', s=200) # red dot
    # st.write(f)

    sns.set_theme(style="white")
    sns.set(rc={'figure.figsize':(125,10)})
    #Load Data
    adjust_new_risk = new_risk_ret_df.transpose()
    adjust_new_risk['Portfolio']=adjust_new_risk.index
    #Plot Seaborn
    p=sns.relplot(x="Vol", y="Return", hue="Portfolio", size=f"CWARP_{round(100*weight_asset)}%_asset",
                sizes=(50, 400), alpha=.9, palette="muted",
                height=6, data=adjust_new_risk)
    plt.title('Efficient Frontier with CWARP')
    st.pyplot(p)

    #plot the putative returns of the best CWARP asset, and the worst.
    best_div = risk_ret_df.loc['CWARP'].astype(float).idxmax(axis='columns')
    worst_div = risk_ret_df.loc['CWARP'].astype(float).idxmin(axis='columns')
    st.write(f"Best CWarp: {best_div.upper()} Worst CWarp {worst_div.upper()}")

    f = plt.figure(figsize=(8,6))
    plt.plot((new_ports[best_div].astype(float)+1).cumprod(), label=best_div)
    plt.plot((new_ports[worst_div].astype(float)+1).cumprod(), label=worst_div)
    plt.title('Cumulative Returns With Best/Worst Diversifier')
    plt.legend()
    plt.xlabel('Date',fontsize=15)
    plt.ylabel('Return',fontsize=15)
    st.write(f)

    # plt.colorbar(label='Cole Win Above Replacement Portfolio')
    # plt.title('Efficient Frontier using CWARP', fontsize=15)
    # plt.xlabel('Downside Volatility',fontsize=15)
    # plt.ylabel('Return',fontsize=15)
    # plt.scatter(max_sr_vol, max_sr_ret,c='red', s=200) # red dot
    # st.write(f)


main()
