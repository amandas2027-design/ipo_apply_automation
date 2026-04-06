🚀 MeroShare IPO Auto Apply

This is a Python script that automatically applies for IPOs on MeroShare for multiple users using Playwright.

It logs in, selects the IPO, fills the form, and submits — all automatically in the background.

📄 Setup
1. Create virtual environment (recommended)
python -m venv venv
2. Activate environment

Mac/Linux:
source venv/bin/activate
Windows:
venv\Scripts\activate

3. Install dependencies
pip install playwright
playwright install
4. Create users.csv
dp,username,password,bank,account,kitta,crn,Pin
12300,user1,pass1,NIC Asia Bank,12345678901234,10,12345678,1234
▶️ Run
python apply_ipo.py
⚠️ Note
IPO must be open on MeroShare
Make sure all user details are correct
Runs in background (headless mode)
