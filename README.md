# cwarp

Streamlit App and Notebook For CWARP

## DISCLAIMER

ANY AND ALL CONTENTS OF THIS STREAMLIT APPLICATION ARE FOR INFORMATIONAL PURPOSES ONLY. NEITHER THE INFORMATION PROVIDED HEREIN NOR ANY OTHER DATA OR RESOURCES RELATED TO CWARP(TM) SHOULD BE CONSTRUED AS A GUARANTEE OF ANY PORTFOLIO PERFORMANCE USING CWARPTM OR ANY OTHER METRIC DEVELOPED OR DISCUSSED HEREIN. ANY INDIVIDUAL WHO USES, REFERENCES OR OTHERWISE ACCESSES THE WEBPAGE OR ANY OTHER DATA, THEORY, FORMULA, OR ANY OTHER INFORMATION CREATED, USED, OR REFERENCED BY ARTEMIS DOES SO AT THEIR OWN RISK AND, BY ACCESSING ANY SUCH INFORMATION, INDEMNIFIES AND HOLDS HARMLESS ARTEMIS CAPITAL MANAGEMENT LP, ARTEMIS CAPITAL ADVISERS LP, AND ALL OF ITS AFFILIATES (TOGETHER, “ARTEMIS”) AGAINST ANY LOSS OF CAPITAL THEY MAY OR MAY NOT INCUR BY UTILIZING SUCH DATA. ARTEMIS DOES NOT BEAR ANY RESPONSIBILITY FOR THE OUTCOME OF ANY PORTFOLIO NOT DIRECTLY OWNED AND/OR MANAGED BY ARTEMIS.

## Where

The project is live and hosted [here](https://share.streamlit.io/jpartemis/cwarp/main/cwarp_app.py), although it is quite unstable.

We will keep monitoring and reboot the app when it fails. We are looking into this issue for longer term maintenance.
If the app is not working when you try to access it, we welcome you to run the streamlit app locally.

## How

Most fool proof way to run the project locally is to either download the `.zip` or 
```
git clone https://github.com/jpartemis/cwarp.git
```
from this repo, make sure you have both `python3` and `pip`  installed and set in your system PATH.

### Install

```
pip install pandas matplotlib seaborn yfinance streamlit
```
### Run

Hopefully just running `streamlit run cwarp_app.py` from the command line just launches the script and opens your browser on `localhost:8501`.
In some cases it might not work.
You might find that installing [Anaconda](https://www.anaconda.com/products/individual) and using its command prompt does the trick. Probably overkill but hey, it works.
