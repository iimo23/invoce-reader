# Arabic Invoice Data Extraction

A Flask-based web application that extracts data from Arabic invoices using Google's Gemini AI Vision API.

## Features

- Upload and process Arabic invoices (PNG, JPG, JPEG, PDF)
- Extract detailed invoice information including:
  - Line items with quantities, prices, and totals
  - Invoice totals with VAT calculations
  - Seller information and tax numbers
- Automatic 15% VAT calculation
- Support for both Arabic and English text
- Clean JSON output format

## Requirements

- Python 3.7+
- Google Gemini API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Gemini API key:
   - Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Set it in your code or environment variables

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and go to `http://localhost:5000`

3. Upload an invoice image (supported formats: PNG, JPG, JPEG, PDF)

4. The application will return a JSON response containing:
   - Extracted line items
   - Invoice totals
   - VAT calculations (15%)
   - Seller information

## API Response Format

```json
{
    "success": true,
    "data": {
        "items": [
            {
                "ITEM_REFERENCE": "Product ID or description",
                "UNIT_NAME": "Unit type (carton, box, kg)",
                "QUANTITY": "Number of units",
                "UNIT_PRICE": "Price per unit",
                "DISCOUNT": "Applied discount",
                "EXCISE_TAX_AMOUNT": "Tax amount",
                "TOTAL": "Total item amount"
            }
        ],
        "invoice_total": "Pre-tax total",
        "vat_rate": 15,
        "vat_amount": "Calculated VAT",
        "total_with_vat": "Final total with VAT",
        "invoice_date": "Invoice date",
        "invoice_number": "Invoice number",
        "seller_name": "Seller name",
        "seller_tax_number": "Seller tax number"
    }
}
```

## Error Handling

The application includes comprehensive error handling for:
- Invalid file types
- Missing or corrupt images
- Failed text extraction
- Invalid numeric values
- Missing required fields

## License

MIT License
