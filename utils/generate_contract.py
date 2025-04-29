print("✅ generate_contract.py is being read!")

from docx import Document
from datetime import datetime
import os
import sys
import uuid
import shutil
from docx.oxml import parse_xml

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db
from models.provider import Provider
from models.standard_rates import StandardRates  # We'll need to create this model

# Standard Imaging Rates (replace or load from DB as needed)
IMAGING_RATES = {
    "MRI w/o": 300,
    "MRI w/": 400,
    "MRI w/ & w/o": 450,
    "CT w/o": 200,
    "CT w/": 275,
    "CT w/ & w/o": 350,
    "XRAY": 25,
    "Arthrograms": 570
}

# Imaging categories for selection
IMAGING_CATEGORIES = [
    "MRI w/o",
    "MRI w/",
    "MRI w/ & w/o",
    "CT w/o",
    "CT w/",
    "CT w/ & w/o",
    "XRAY",
    "Arthrograms"
]

def get_rates_by_method(provider_id, method, custom_rates=None, wcfs_percentages=None):
    """
    Get rates based on the selected reimbursement method.
    
    Args:
        provider_id: The ID of the provider
        method: The reimbursement method ('standard', 'wcfs', or 'custom')
        custom_rates: Dictionary of custom rates for each category (for 'custom' method)
        wcfs_percentages: Dictionary of WCFS percentages for each category (for 'wcfs' method)
    
    Returns:
        Dictionary of rates for each imaging category
    """
    provider = Provider.query.get(provider_id)
    if not provider:
        raise ValueError("Provider not found")
    
    # Get states from provider
    if provider.states_in_contract:
        states = [s.strip() for s in provider.states_in_contract.split(",") if s.strip()]
    else:
        states = ["CA"]  # Default to California if no states specified
    
    rates = {}
    
    # Map form field names to category names
    category_mapping = {
        'mri_without': 'MRI w/o',
        'mri_with': 'MRI w/',
        'mri_both': 'MRI w/ & w/o',
        'ct_without': 'CT w/o',
        'ct_with': 'CT w/',
        'ct_both': 'CT w/ & w/o',
        'xray': 'XRAY',
        'arthrogram': 'Arthrograms'
    }
    
    if method == 'standard':
        # Get rates from standard_rates table for each category
        state = states[0]  # Use first state's rates
        for category in IMAGING_CATEGORIES:
            standard_rate = StandardRates.query.filter_by(
                state=state,
                category=category
            ).first()
            
            if standard_rate:
                rates[category] = standard_rate.rate
            else:
                # Fallback to default rates if not found in DB
                rates[category] = IMAGING_RATES.get(category, 0)
    
    elif method == 'wcfs':
        # Apply WCFS percentages to standard rates
        if not wcfs_percentages:
            raise ValueError("WCFS percentages must be provided for WCFS method")
        
        # Store the WCFS percentages in the rates dictionary
        for form_field, category in category_mapping.items():
            if form_field in wcfs_percentages:
                # Store the percentage as an integer
                rates[category] = int(wcfs_percentages[form_field])
            else:
                # Use 0 if no percentage provided
                rates[category] = 0
    
    elif method == 'custom':
        # Use custom rates provided by the user
        if not custom_rates:
            raise ValueError("Custom rates must be provided for custom method")
        
        for form_field, category in category_mapping.items():
            if form_field in custom_rates:
                rates[category] = custom_rates[form_field]
            else:
                # Use default rate if no custom rate provided
                rates[category] = IMAGING_RATES.get(category, 0)
    
    else:
        raise ValueError(f"Invalid reimbursement method: {method}")
    
    return rates

def create_rates_table(doc, states, rates, method='standard', wcfs_percentages=None):
    # Create table without relying on named styles
    table = doc.add_table(rows=1, cols=3)
    
    # Make sure the table has borders using direct XML
    for row in table.rows:
        for cell in row.cells:
            # Add borders to the cell
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            
            # Add borders using direct XML
            for key in ['top', 'left', 'bottom', 'right']:
                element = parse_xml(f'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:{key} w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tcBorders>')
                tcPr.append(element)
            
            # Make header text bold
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True

    # Header
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "State"
    hdr_cells[1].text = "Procedure"
    hdr_cells[2].text = "Rate" if method != 'wcfs' else "WCFS %"

    for state in states:
        for procedure in IMAGING_CATEGORIES:
            row_cells = table.add_row().cells
            
            # Add borders to each new cell
            for cell in row_cells:
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                
                # Add borders using direct XML
                for key in ['top', 'left', 'bottom', 'right']:
                    element = parse_xml(f'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:{key} w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tcBorders>')
                    tcPr.append(element)
            
            row_cells[0].text = state
            row_cells[1].text = procedure
            
            if method == 'wcfs':
                # Get the percentage from the rates dictionary
                percentage = rates.get(procedure, 0)
                row_cells[2].text = f"{percentage}% of WCFS"
            else:
                rate = rates.get(procedure, 0)
                row_cells[2].text = f"${rate:.2f}"
            
    return table

def generate_contract(provider_id, method='standard', custom_rates=None, wcfs_percentages=None):
    provider = Provider.query.get(provider_id)
    if not provider:
        raise ValueError("Provider not found")

    # Split state list - handle None case
    if provider.states_in_contract:
        states = [s.strip() for s in provider.states_in_contract.split(",") if s.strip()]
    else:
        states = ["CA"]  # Default to California if no states specified

    # Get rates based on the selected method
    rates = get_rates_by_method(provider_id, method, custom_rates, wcfs_percentages)

    # Load template - ensure we use the exact path specified
    template_path = "templates/contracts/IMAGING_TEMPLATE.docx"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")

    # Create output paths
    output_folder = "contracts"
    os.makedirs(output_folder, exist_ok=True)
    
    # Create filename using DBA name or provider name if DBA is not available
    filename = f"{provider.dba_name or provider.name}_Agreement"
    # Replace any characters that might be invalid in filenames
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
    
    docx_path = os.path.join(output_folder, f"{filename}.docx")
    pdf_path = os.path.join(output_folder, f"{filename}.pdf")

    # Create a copy of the template for this contract
    shutil.copy2(template_path, docx_path)
    
    # Open the copy for editing
    doc = Document(docx_path)

    # Import XML parser for table formatting
    from docx.oxml import parse_xml
    
    # Replace all placeholders in paragraphs
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text
        if "{{provider_name}}" in text:
            text = text.replace("{{provider_name}}", provider.name)
            paragraph.text = text
        elif "{{dba_name}}" in text:
            text = text.replace("{{dba_name}}", provider.dba_name or "")
            paragraph.text = text
        elif "{{address}}" in text:
            text = text.replace("{{address}}", provider.address or "")
            paragraph.text = text
        elif "{{provider_type}}" in text:
            text = text.replace("{{provider_type}}", provider.provider_type or "")
            paragraph.text = text
        elif "{{npi}}" in text:
            text = text.replace("{{npi}}", provider.npi or "")
            paragraph.text = text
        elif "{{specialty}}" in text:
            text = text.replace("{{specialty}}", provider.specialty or "")
            paragraph.text = text
        elif "{{rate_type}}" in text:
            text = text.replace("{{rate_type}}", method)
            paragraph.text = text
        elif "{{wcfs_percentage}}" in text:
            if method == 'wcfs' and wcfs_percentages:
                # For WCFS method, show the average percentage
                avg_percentage = sum(wcfs_percentages.values()) / len(wcfs_percentages)
                text = text.replace("{{wcfs_percentage}}", f"{avg_percentage:.1f}")
            else:
                text = text.replace("{{wcfs_percentage}}", "0")
            paragraph.text = text
        elif "{{states}}" in text:
            text = text.replace("{{states}}", ", ".join(states))
            paragraph.text = text
        elif "{{date}}" in text:
            text = text.replace("{{date}}", datetime.now().strftime("%B %d, %Y"))
            paragraph.text = text
        elif "{{exhibit_a}}" in text:
            # Create the rates table
            table = create_rates_table(doc, states, rates, method, wcfs_percentages)
            
            # Insert the table after the current paragraph
            p = paragraph._element
            p.getparent().insert(p.getparent().index(p) + 1, table._element)
            
            # Remove the placeholder paragraph
            p.getparent().remove(p)
            
            # Add a small paragraph after the table for spacing
            doc.add_paragraph()

    # Save the modified copy
    doc.save(docx_path)

    # Convert to PDF (optional)
    try:
        from docx2pdf import convert
        convert(docx_path, pdf_path)
    except Exception as e:
        print(f"[WARN] PDF conversion failed: {e}")

    return docx_path, pdf_path

# Test section - can be run directly
if __name__ == "__main__":
    with app.app_context():
        # Create a test provider
        provider = Provider(
            id=str(uuid.uuid4()),
            name="Test Imaging Center",
            dba_name="TIC Medical Group",
            address="123 Test St, Los Angeles, CA 90001",
            provider_type="Imaging",
            states_in_contract="CA, NY, TX",
            npi="1234567890",
            specialty="Radiology",
            rate_type="wcfs",
            wcfs_percentage=80.0,
            status="active"
        )
        
        # Add to database
        db.session.add(provider)
        db.session.commit()
        
        print(f"Created test provider with ID: {provider.id}")
        
        # Generate contract
        try:
            docx_path, pdf_path = generate_contract(provider.id)
            print(f"Contract generated successfully!")
            print(f"DOCX path: {docx_path}")
            print(f"PDF path: {pdf_path}")
        except Exception as e:
            print(f"Error generating contract: {e}")