import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning) 
from cwarp_defs import *
from io import BytesIO
import datetime
import seaborn as sns
import streamlit as st
from streamlit import caching
caching.clear_cache()
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

def retrieve_yhoo_data(ticker='spy', start_date = '2007-07-01', end_date = '2020-12-31'):
    try:
        data_hold=yf.Ticker(ticker)
        price_df=data_hold.history(start=start_date,  end=end_date).Close.pct_change()
        price_df.name=ticker
        if price_df.shape[0] < 100:
            raise Exception('no prices.')
        return price_df
    except Exception as Ex:
        st.write(f"Sorry, Data not available for {ticker} please refresh the app.")

def main():
    st.sidebar.image('Artemis.png')
    st.header("CWARP\u2122 Calculator")

    st.markdown("""
    <style>
    .small-font {
        font-size:8px;
    }
    </style>
    """, unsafe_allow_html=True)

    body = """<p class="small-font">ANY AND ALL CONTENTS OF THIS STREAMLIT APPLICATION ARE FOR INFORMATIONAL PURPOSES ONLY. NEITHER THE INFORMATION PROVIDED HEREIN NOR ANY OTHER DATA OR RESOURCES RELATED TO CWARP\u2122 SHOULD BE CONSTRUED AS A GUARANTEE OF ANY PORTFOLIO PERFORMANCE USING CWARPTM OR ANY OTHER METRIC DEVELOPED OR DISCUSSED HEREIN. ANY INDIVIDUAL WHO USES, REFERENCES OR OTHERWISE ACCESSES THE WEBPAGE OR ANY OTHER DATA, THEORY, FORMULA, OR ANY OTHER INFORMATION CREATED, USED, OR REFERENCED BY ARTEMIS DOES SO AT THEIR OWN RISK AND, BY ACCESSING ANY SUCH INFORMATION, INDEMNIFIES AND HOLDS HARMLESS ARTEMIS CAPITAL MANAGEMENT LP, ARTEMIS CAPITAL ADVISERS LP, AND ALL OF ITS AFFILIATES (TOGETHER, “ARTEMIS”) AGAINST ANY LOSS OF CAPITAL THEY MAY OR MAY NOT INCUR BY UTILIZING SUCH DATA. ARTEMIS DOES NOT BEAR ANY RESPONSIBILITY FOR THE OUTCOME OF ANY PORTFOLIO NOT DIRECTLY OWNED AND/OR MANAGED BY ARTEMIS.</p>

CWARP\u2122, like the Sharpe or Sortino Ratios, is a number that quantifies the attractiveness of a prospective asset.
Like the Sharpe Ratio, the more positive the CWARP\u2122 the more attractive an asset.

Sharpe Ratios have the problem that the best portfolio isn't always built from a combination of assets which have the best Sortino ratios.
In fact it is possible that between assets with three Sortino Ratios $S_a < S_b < S_c$, the best portfolio is built from
the two weaker assets $S_a, S_b$. Reliance on this simple number has lead to underdiversified, fragile portfolios.
The whole is not the sum of the parts.

To improve the situation, CWARP\u2122 $\chi$ measures the attractiveness of a portfolio after an asset is added.
Here RMDD is the Return to Max-Drawdown Ratio, and n and p represent the new and old portfolio respectively :
"""
    st.markdown(body,unsafe_allow_html=True)
    formula = render_latex(r'\chi/100 = \sqrt{ \left( \frac{S_n}{S_p} \right) \left(  \frac{ RMDD_n }{ RMDD_p}  \right) }-1.')
    st.markdown("""Using the boxes below, you can calculate CWARP\u2122 based on your own portfolio for prospective assets,
    so long as a data provider has history on your holdings. Just edit the example entries.""")

    try:
        start_date = st.sidebar.date_input("Start Date", datetime.date(2007,7,1)).strftime("%Y-%m-%d")
        end_date = st.sidebar.date_input("End Date", datetime.date(2020,12,31)).strftime("%Y-%m-%d")
        weight_asset = st.sidebar.slider('Diversifier Weight', min_value=0.0001, max_value=0.9999, value=.25, step=0.01)
        weight_replace_port = st.sidebar.slider('Replacement Portfolio Weight', min_value=0.0001, max_value=1.0000, value=1.00, step=0.01)
        risk_free_rate = st.sidebar.slider('Risk-Free Rate (annualized)', min_value=0.0, max_value=0.2, value=0.005, step=0.001, format='%.3f')
        financing_rate = st.sidebar.slider('Financing Rate (annualized)', min_value=0.0, max_value=0.2, value=0.01)
        replacement_port_name = st.sidebar.text_input("Replacement Portfolio Name", "Plain 60/40")

        ticker_string_ = "qqq, lqd, hyg, tlt, ief, shy, gld, slv, efa, eem, iyr, xle, xlk, xlf"
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

        replacement_port = replacement_port_list[0]*(replacement_port_w[0]/sum(replacement_port_w))
        for k in range(1,len(replacement_port_list)):
            replacement_port += replacement_port_list[k]*(replacement_port_w[k]/sum(replacement_port_w))
        # with st.spinner("Pulling data..."):
        #     replacement_port=sum([retrieve_yhoo_data(sym, start_date, end_date)*replacement_port_w[i] for i, sym in enumerate(replacement_port_tik)])

        replacement_port.name=replacement_port_name
        risk_ret_df=pd.DataFrame(index=['Start_Date','End_Date','CWARP','+Sortino','+Ret_To_MaxDD','Sharpe','Sortino','Max_DD'],columns=ticker_list)
        new_risk_ret_df=pd.DataFrame(index=['Return','Vol','Sharpe','Sortino','Max_DD','Ret_To_MaxDD',f'CWARP_{round(100*weight_asset)}%_asset'],columns=ticker_list)
        new_risk_ret_df=new_risk_ret_df.add_suffix(f'@{round(100*weight_asset)}% | '+replacement_port.name+f'{round(100*weight_replace_port)}%')
        new_risk_ret_df[replacement_port.name]=np.nan
        prices_df=pd.DataFrame(index=retrieve_yhoo_data(ticker_list[0], start_date, end_date).index)

        # Save these for later plotting...
        new_ports = {}
        for i in range(0,len(ticker_list)):
            temp_data=retrieve_yhoo_data(ticker_list[i], start_date, end_date)
            prices_df=pd.merge(prices_df,temp_data, left_index=True, right_index=True)
            risk_ret_df.loc['Start_Date',ticker_list[i]]=min(temp_data.index).date()
            risk_ret_df.loc['End_Date',ticker_list[i]]=max(temp_data.index).date()
            risk_ret_df.loc['CWARP',ticker_list[i]]=cole_win_above_replace_port(new_asset=temp_data, replace_port=replacement_port,
                                                                                    risk_free_rate = risk_free_rate,
                                                                                    financing_rate = financing_rate,
                                                                                    weight_asset = weight_asset,
                                                                                    weight_replace_port = weight_replace_port,
                                                                                    periodicity=252)
            risk_ret_df.loc['+Sortino',ticker_list[i]]=cwarp_additive_sortino(new_asset=temp_data, replace_port=replacement_port,
                                                                                            risk_free_rate = risk_free_rate,
                                                                                            financing_rate = financing_rate,
                                                                                            weight_asset = weight_asset,
                                                                                            weight_replace_port = weight_replace_port,
                                                                                            periodicity=252)
            risk_ret_df.loc['+Ret_To_MaxDD',ticker_list[i]]=cwarp_additive_ret_maxdd(new_asset=temp_data, replace_port=replacement_port,
                                                                                            risk_free_rate = risk_free_rate,
                                                                                            financing_rate = financing_rate,
                                                                                            weight_asset = weight_asset,
                                                                                            weight_replace_port = weight_replace_port,
                                                                                            periodicity=252)
            risk_ret_df.loc['Sharpe',ticker_list[i]]=sharpe_ratio(temp_data, risk_free = risk_free_rate, periodicity=252)
            risk_ret_df.loc['Sortino',ticker_list[i]]=sortino_ratio(temp_data, risk_free = risk_free_rate, periodicity=252)
            risk_ret_df.loc['Max_DD',ticker_list[i]]=max_dd(temp_data)
            new_risk_ret_df.loc['Return',new_risk_ret_df.columns[i]]=cwarp_port_return(new_asset=temp_data,replace_port=replacement_port,
                                                                                                    risk_free_rate = risk_free_rate,
                                                                                                    financing_rate = financing_rate,
                                                                                                    weight_asset = weight_asset,
                                                                                                    weight_replace_port = weight_replace_port,
                                                                                                    periodicity = 252)
            new_risk_ret_df.loc['Vol',new_risk_ret_df.columns[i]]=cwarp_port_risk(new_asset=temp_data,replace_port=replacement_port,
                                                                                                    risk_free_rate = risk_free_rate,
                                                                                                    financing_rate = financing_rate,
                                                                                                    weight_asset = weight_asset,
                                                                                                    weight_replace_port = weight_replace_port,
                                                                                                    periodicity=252)
            cnpd = cwarp_new_port_data(new_asset=temp_data,replace_port=replacement_port, risk_free_rate = risk_free_rate,
                                                                                                    financing_rate = financing_rate,
                                                                                                    weight_asset = weight_asset,
                                                                                                    weight_replace_port = weight_replace_port,
                                                                                                    periodicity = 252)
            new_ports[ticker_list[i]] = cnpd
            new_risk_ret_df.loc['Sharpe',new_risk_ret_df.columns[i]]=sharpe_ratio(cnpd.copy(), risk_free = risk_free_rate, periodicity=252)
            new_risk_ret_df.loc['Sortino',new_risk_ret_df.columns[i]]=sortino_ratio(cnpd.copy(), risk_free = risk_free_rate, periodicity=252)
            new_risk_ret_df.loc['Max_DD',new_risk_ret_df.columns[i]]=max_dd(cnpd.copy())
            new_risk_ret_df.loc['Ret_To_MaxDD',new_risk_ret_df.columns[i]]=return_maxdd_ratio(cnpd.copy(), risk_free = risk_free_rate, periodicity=252)
            new_risk_ret_df.loc[f'CWARP_{round(100*weight_asset)}%_asset',new_risk_ret_df.columns[i]]=risk_ret_df.loc['CWARP',ticker_list[i]]

        new_risk_ret_df.loc['Return',[replacement_port_name]]=annualized_return(replacement_port, periodicity=252)
        new_risk_ret_df.loc['Vol',[replacement_port_name]]=target_downside_deviation(replacement_port, MAR=0)*np.sqrt(252)
        new_risk_ret_df.loc['Sharpe',[replacement_port_name]]=sharpe_ratio(replacement_port, risk_free = risk_free_rate, periodicity=252)
        new_risk_ret_df.loc['Sortino',[replacement_port_name]]=sortino_ratio(replacement_port, risk_free = risk_free_rate, periodicity=252)
        new_risk_ret_df.loc['Max_DD',[replacement_port_name]]=max_dd(replacement_port)
        new_risk_ret_df.loc['Ret_To_MaxDD',[replacement_port_name]]=return_maxdd_ratio(replacement_port, risk_free = risk_free_rate, periodicity=252)
        new_risk_ret_df.loc[f'CWARP_{round(100*weight_asset)}%_asset',[replacement_port_name]] = cole_win_above_replace_port(new_asset=replacement_port, replace_port=replacement_port, risk_free_rate=risk_free_rate, financing_rate=financing_rate,
                            weight_asset=weight_asset, weight_replace_port=weight_replace_port, periodicity=252)
        first_col = new_risk_ret_df.pop(replacement_port_name)
        new_risk_ret_df.insert(0, replacement_port_name, first_col)
        # display dataframes
        st.write(risk_ret_df.sort_values(by='CWARP', axis=1, ascending=False).style.set_precision(3))
        st.write(new_risk_ret_df.sort_values(by='Sharpe', axis=1, ascending=False).style.set_precision(3))
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
    except Exception as Ex:
        st.write("There Has been an error:", Ex)
        st.write("Please refresh this app.")
    # plt.colorbar(label='Cole Win Above Replacement Portfolio')
    # plt.title('Efficient Frontier using CWARP', fontsize=15)
    # plt.xlabel('Downside Volatility',fontsize=15)
    # plt.ylabel('Return',fontsize=15)
    # plt.scatter(max_sr_vol, max_sr_ret,c='red', s=200) # red dot
    # st.write(f)


main()
