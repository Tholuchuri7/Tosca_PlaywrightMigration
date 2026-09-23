# Tosca → Playwright Converter V5

Converts Tosca Test Case JSON + Tosca Modules `.tsu` into Playwright automation.

## Targets
- Playwright TypeScript (`playwright.spec.ts`)
- Playwright Python (`test_tosca_migration.py`)

The Tosca parsing, mapping, BusinessType-driven locator strategy, dropdown handling, checkbox/radio handling, and table mapping are shared. Only the final code generator changes by target language.

## Run
```cmd
python -m streamlit run app.py
```
