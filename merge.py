import os

from PyPDF2 import PdfWriter, PdfReader

files = [f for f in os.listdir('./output/') if os.path.isfile(os.path.join('./output/',f))] # Get all files in the output directory
pdf_files = []

# Loop through all files in the output directory and only keep pdf files (also skip the output OFP.pdf)
for i, f in enumerate(files):
    if not f.endswith('.pdf'): continue
    if f == "OPF.pdf": continue
    pdf_files.append(f)

if len(pdf_files) >= 1:
    writer = PdfWriter()

    for pdf in pdf_files:
        reader = PdfReader("output/" + pdf)
        fields = reader.get_form_text_fields()

        print(fields)

        page = reader.pages[0]
        writer.add_page(page)
        writer.update_page_form_field_values(page, fields)
        
        os.remove("output/" + pdf)# Delete the file now that we have copied it
        
    with open("output/OPF.pdf", "wb") as output_stream:
        writer.write(output_stream)