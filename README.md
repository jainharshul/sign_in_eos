# EOS Fitness Automation

This script automates form filling for EOS Fitness guest registration using Selenium.

## Setup

Prerequisites:
- Python 3.8+

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Web Interface (Recommended)

A simple web interface is available to trigger the automation:

```bash
python app.py
```

Then open your browser to `http://localhost:5000` and click "Start Automation".

## Running via Command Line

```bash
python main.py
```

Or specify a custom URL:
```bash
python main.py https://your-custom-url.com
```

## Default Values

The script fills the following information from defaults (edit in `main.py` to customize):

- Name: Michael Tse
- Phone: 626-367-8923
- Email: mmtse12@gmail.com
- Gender: Male
- Address: 38 east forest ave, Arcadia, CA 91006
- Birthday: 02/05/2004
- Fitness Goal: Gain Muscle/Weight

## How It Works

The script:
1. Opens the fitness registration page
2. Intelligently finds form fields by analyzing labels, names, and placeholders
3. Fills in personal information
4. Selects radio buttons and dropdowns
5. Clicks Next/Submit buttons
6. Checks consent checkboxes and submits the final form

