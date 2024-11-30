from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
import time
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import base64
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure Gemini API
try:
    genai.configure(api_key='AIzaSyBHCq884aLX91g0_4p7LcEiWVT8QRye2rc')
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini API configured successfully")
except Exception as e:
    logger.error(f"Error configuring Gemini: {str(e)}")
    model = None

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'pdf'}

def safe_delete_file(filepath, max_attempts=5, delay=1):
    for attempt in range(max_attempts):
        try:
            if os.path.exists(filepath):
                os.close(os.open(filepath, os.O_RDONLY))
                os.remove(filepath)
            return True
        except Exception as e:
            if attempt == max_attempts - 1:
                logger.error(f"Failed to delete {filepath} after {max_attempts} attempts: {str(e)}")
                return False
            time.sleep(delay)
    return False

def extract_invoice_data(image_path):
    try:
        logger.info(f"Processing invoice: {image_path}")
        
        # Load and prepare the image for Gemini
        img = Image.open(image_path)
        
        # Prepare the prompt for Gemini
        prompt = """
        استخرج المعلومات التالية من صورة الفاتورة. قم بإرجاع البيانات بتنسيق JSON. يجب أن تكون جميع القيم العددية أرقاماً وليست نصوصاً:
        {
            "items": [
                {
                    "ITEM_REFERENCE": "رقم المنتج أو وصفه",
                    "UNIT_NAME": "وحدة القياس (كرتون، صندوق، كجم)",
                    "QUANTITY": "عدد الوحدات (رقم فقط، مثال: اذا كان العدد ٢ يجب ان يكون 2)",
                    "UNIT_PRICE": "سعر الوحدة (رقم فقط)",
                    "DISCOUNT": "قيمة الخصم (رقم فقط، اذا لم يوجد اكتب 0)",
                    "EXCISE_TAX_AMOUNT": "قيمة الضريبة (رقم فقط، اذا لم يوجد اكتب 0)",
                    "TOTAL": "المجموع الكلي للمنتج (رقم فقط)"
                }
            ],
            "invoice_total": "إجمالي الفاتورة قبل الضريبة (رقم فقط، يجب ادخال قيمة)",
            "invoice_date": "تاريخ الفاتورة",
            "invoice_number": "رقم الفاتورة",
            "seller_name": "اسم البائع",
            "seller_tax_number": "الرقم الضريبي للبائع"
        }
        
        ملاحظات مهمة:
        - قم بتحويل جميع الأرقام العربية (٠١٢٣٤٥٦٧٨٩) إلى أرقام إنجليزية (0123456789)
        - يجب أن تكون جميع القيم العددية أرقاماً وليست نصوصاً
        - يجب أن تكون QUANTITY دائماً رقماً صحيحاً
        - قم بإدراج جميع المنتجات الموجودة في الفاتورة
        - تأكد من صحة تنسيق JSON
        - يجب ادخال قيمة رقمية في invoice_total
        """
        
        # Generate content using Gemini
        response = model.generate_content([prompt, img])
        
        try:
            # Extract JSON from the response
            json_str = response.text
            # Find the JSON part (between curly braces)
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = json_str[start:end]
            
            # Parse the JSON
            extracted_data = json.loads(json_str)
            
            # Calculate total from items if invoice_total is missing
            if not extracted_data.get('invoice_total'):
                total = 0
                for item in extracted_data.get('items', []):
                    item_total = float(item.get('TOTAL', 0))
                    total += item_total
                extracted_data['invoice_total'] = total
            
            # Ensure invoice_total is a number
            try:
                subtotal = float(extracted_data['invoice_total'])
            except (TypeError, ValueError):
                # If conversion fails, calculate from items
                subtotal = sum(float(item.get('TOTAL', 0)) for item in extracted_data.get('items', []))
                extracted_data['invoice_total'] = subtotal
            
            # Calculate VAT (15%) and total with VAT
            vat_amount = subtotal * 0.15
            total_with_vat = subtotal + vat_amount
            
            # Add VAT calculations to the response
            extracted_data['vat_rate'] = 15
            extracted_data['vat_amount'] = round(vat_amount, 2)
            extracted_data['total_with_vat'] = round(total_with_vat, 2)
            
            logger.info("Successfully extracted and parsed invoice data")
            return {
                'success': True,
                'data': extracted_data
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to parse extracted data',
                'raw_text': response.text
            }
            
    except Exception as e:
        logger.error(f"Error in invoice data extraction: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Save uploaded file
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        logger.info(f"File saved: {filename}")
        
        # Process the file
        result = extract_invoice_data(filename)
        
        # Clean up
        safe_delete_file(filename)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
