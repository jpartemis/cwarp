from cwarp_defs import *
from io import BytesIO
import datetime
import seaborn as sns

import streamlit as st

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

    start_date = st.sidebar.date_input("Start Date", datetime.date(2007,7,1)).strftime("%Y-%m-%d")
    end_date = st.sidebar.date_input("End Date", datetime.date(2020,12,31)).strftime("%Y-%m-%d")

    ticker_string_ = "qqq, lqd, hyg, tlt, ief, shy, gld, slv, efa, eem, iyr, xle, xlk, xlf"
    ticker_string = st.text_input("Prospects (comma separated)", ticker_string_)
    ticker_list=ticker_string.replace(' ','').split(',')

    replacement_port_tik=['spy','ief']
    replacement_port_w=[.60,.40]

    formula = render_latex(r'\chi = \sqrt{ \left( \frac{S_n}{S_p} \right) \left(  \frac{ RMDD_n }{ RMDD_p}  \right) }')

    replacement_port=(retrieve_yhoo_data('spy')*.60+retrieve_yhoo_data('ief')*.40)
    replacement_port_name='Classic 60/40'
    replacement_port.name=replacement_port_name
    risk_ret_df=pd.DataFrame(index=['Start_Date','End_Date','CWARP','+Sortino','+Ret_To_MaxDD','Sharpe','Sortino','Max_DD'],columns=ticker_list)
    new_risk_ret_df=pd.DataFrame(index=['Return','Vol','Sharpe','Sortino','Max_DD','Ret_To_MaxDD','CWARP_25%_asset'],columns=ticker_list)
    new_risk_ret_df=new_risk_ret_df.add_suffix('@25% | '+replacement_port.name+'@100%')
    new_risk_ret_df[replacement_port.name]=np.nan
    prices_df=pd.DataFrame(index=retrieve_yhoo_data(ticker_list[0]).index)
    for i in range(0,len(ticker_list)):
        temp_data=retrieve_yhoo_data(ticker_list[i])
        prices_df=pd.merge(prices_df,temp_data, left_index=True, right_index=True)
        risk_ret_df.loc['Start_Date',ticker_list[i]]=min(temp_data.index)
        risk_ret_df.loc['End_Date',ticker_list[i]]=max(temp_data.index)
        risk_ret_df.loc['CWARP',ticker_list[i]]=cole_win_above_replace_port(new_asset=temp_data,replace_port=replacement_port)
        risk_ret_df.loc['+Sortino',ticker_list[i]]=cwarp_additive_sortino(new_asset=temp_data,replace_port=replacement_port)
        risk_ret_df.loc['+Ret_To_MaxDD',ticker_list[i]]=cwarp_additive_ret_maxdd(new_asset=temp_data,replace_port=replacement_port)
        risk_ret_df.loc['Sharpe',ticker_list[i]]=sharpe_ratio(temp_data)
        risk_ret_df.loc['Sortino',ticker_list[i]]=sortino_ratio(temp_data)
        risk_ret_df.loc['Max_DD',ticker_list[i]]=max_dd(temp_data)

        new_risk_ret_df.loc['Return',new_risk_ret_df.columns[i]]=cwarp_port_return(new_asset=temp_data,replace_port=replacement_port,risk_free_rate=0,financing_rate=0,periodicity=252)
        new_risk_ret_df.loc['Vol',new_risk_ret_df.columns[i]]=cwarp_port_risk(new_asset=temp_data,replace_port=replacement_port,risk_free_rate=0,financing_rate=0,periodicity=252)
        new_risk_ret_df.loc['Sharpe',new_risk_ret_df.columns[i]]=sharpe_ratio(cwarp_new_port_data(new_asset=temp_data,replace_port=replacement_port,risk_free_rate=0,financing_rate=0,periodicity=252))
        new_risk_ret_df.loc['Sortino',new_risk_ret_df.columns[i]]=sortino_ratio(cwarp_new_port_data(new_asset=temp_data,replace_port=replacement_port,risk_free_rate=0,financing_rate=0,periodicity=252))
        new_risk_ret_df.loc['Max_DD',new_risk_ret_df.columns[i]]=max_dd(cwarp_new_port_data(new_asset=temp_data,replace_port=replacement_port,risk_free_rate=0,financing_rate=0,periodicity=252))
        new_risk_ret_df.loc['Ret_To_MaxDD',new_risk_ret_df.columns[i]]=return_maxdd_ratio(cwarp_new_port_data(new_asset=temp_data,replace_port=replacement_port,risk_free_rate=0,financing_rate=0,periodicity=252))
        new_risk_ret_df.loc['CWARP_25%_asset',new_risk_ret_df.columns[i]]=risk_ret_df.loc['CWARP',ticker_list[i]]

    new_risk_ret_df.loc['Return',[replacement_port_name]]=(replacement_port.mean()+1)**252-1
    new_risk_ret_df.loc['Vol',[replacement_port_name]]=replacement_port.std()*np.sqrt(252)
    new_risk_ret_df.loc['Sharpe',[replacement_port_name]]=sharpe_ratio(replacement_port)
    new_risk_ret_df.loc['Sortino',[replacement_port_name]]=sortino_ratio(replacement_port)
    new_risk_ret_df.loc['Max_DD',[replacement_port_name]]=max_dd(replacement_port)
    new_risk_ret_df.loc['Ret_To_MaxDD',[replacement_port_name]]=return_maxdd_ratio(replacement_port)
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

    f = plt.figure(figsize=(10,6))
    plt.scatter(vol_arr, ret_arr, c=cwarp_arr, cmap='winter',label=new_risk_ret_df.columns,alpha=.9)
    plt.colorbar(label='Cole Win Above Replacement Portfolio')
    plt.title('Efficient Frontier using CWAP', fontsize=15)
    plt.xlabel('Downside Volatility',fontsize=15)
    plt.ylabel('Return',fontsize=15)
    plt.scatter(max_sr_vol, max_sr_ret,c='red', s=200) # red dot
    st.write(f)

    sns.set_theme(style="white")
    sns.set(rc={'figure.figsize':(125,10)})
    #Load Data
    adjust_new_risk = new_risk_ret_df.transpose()
    adjust_new_risk['Portfolio']=adjust_new_risk.index
    #Plot Seaborn
    p=sns.relplot(x="Vol", y="Return", hue="Portfolio", size="CWARP_25%_asset",
                sizes=(50, 400), alpha=.9, palette="muted",
                height=6, data=adjust_new_risk)
    plt.title('Efficient Frontier with CWARP')
    st.pyplot(p)

main()
