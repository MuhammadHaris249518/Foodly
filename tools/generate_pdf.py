import markdown2
from xhtml2pdf import pisa

def convert_md_to_pdf(md_file, pdf_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    html_text = markdown2.markdown(md_text, extras=["tables"])
    
    # Add some basic CSS for better rendering
    styled_html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #eee; }}
        h2 {{ color: #34495e; margin-top: 20px; }}
        h3 {{ color: #16a085; }}
        p, li {{ font-size: 14px; color: #333; }}
        strong {{ color: #000; }}
        ul {{ margin-bottom: 15px; }}
    </style>
    </head>
    <body>
    {html_text}
    </body>
    </html>
    """

    with open(pdf_file, "wb") as result_file:
        pisa_status = pisa.CreatePDF(
            styled_html,
            dest=result_file
        )

    return pisa_status.err

if __name__ == "__main__":
    convert_md_to_pdf("Architecture_Issues_Report.md", "Foodly_Architecture_Issues.pdf")
    print("PDF generated successfully.")
