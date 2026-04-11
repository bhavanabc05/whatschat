import os
from fpdf import FPDF
from datetime import datetime

# Ensure the directory exists so the app doesn't crash
if not os.path.exists("invoices"):
    os.makedirs("invoices")

def generate_invoice(order):
    """Draws a PDF invoice and saves it locally."""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 15, txt="AdaShop.24", ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 8, txt="Official Order Invoice", ln=True, align='C')
    pdf.cell(200, 8, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Order Info
    order_id = str(order['_id'])[-6:].upper()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt=f"Order ID: {order_id}", ln=True)
    pdf.cell(200, 8, txt=f"Customer: {order['sender']}", ln=True)
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, txt=" Item Name", border=1)
    pdf.cell(50, 10, txt=" Price", border=1, align='R', ln=True)
    
    # Table Rows
    pdf.set_font("Arial", '', 12)
    for item in order['items']:
        # Removing non-ascii chars just in case (like ₹) which FPDF struggles with natively
        clean_name = item['name'].encode('ascii', 'ignore').decode('ascii')
        pdf.cell(140, 10, txt=f" {clean_name}", border=1)
        pdf.cell(50, 10, txt=f" INR {item['price']} ", border=1, align='R', ln=True)
        
    # Total
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, txt=" TOTAL", border=1)
    pdf.cell(50, 10, txt=f" INR {order['total']} ", border=1, align='R', ln=True)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(200, 10, txt="Thank you for shopping with us! ✨", ln=True, align='C')
    
    # Save the file
    file_name = f"invoice_{order_id}.pdf"
    file_path = f"invoices/{file_name}"
    pdf.output(file_path)
    
    return file_name