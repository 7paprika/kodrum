# kodrum

Vertical KO drum rating helper built with Streamlit.

This app now performs two checks:
- vapor disengagement check (`Uv < Ut`)
- liquid holdup / residence-time check using vessel diameter, tangent height, liquid flow, and operating liquid level fraction

## What changed
- Added structured calculation engine in `modules/rating.py`
- Added explicit input validation for nonphysical cases
- Added residence-time / liquid holdup logic so `H` and `W_L` affect the result
- Added auto/manual conclusion mode so conclusion text does not silently go stale
- Replaced base64 link download with `st.download_button`
- Added HTML report generator module and automated tests

## Quick start
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

## Run tests
```bash
python3 -m pip install pytest
PYTHONPATH=. pytest tests -q
```

## Scope note
This tool is a practical rating aid, not a full separator design package.
It does not replace detailed process/mechanical design review.
