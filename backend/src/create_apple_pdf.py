import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf():
    pdf_dir = "data/pdf/Apple/Q3-2024"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, "aapl-q324-10q.pdf")
    
    # Setup document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=12
    )

    story = []
    
    # Title
    story.append(Paragraph("Apple Inc. Form 10-Q - Q3 2024", title_style))
    story.append(Spacer(1, 12))
    
    # Page 1 content (Operating Margins)
    story.append(Paragraph("Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations", section_style))
    story.append(Paragraph("Our operating results can vary significantly from quarter to quarter. During the third quarter, we observed fluctuations in component procurement costs and supply-chain logistics pricing.", body_style))
    story.append(Paragraph("Operating margin for the quarter contracted to 25.2%, down 180 basis points, primarily due to elevated supply chain costs and raw material inflation. We continue to monitor operational expenses closely, though external cost pressures remain volatile.", body_style))
    
    story.append(Spacer(1, 30))
    
    # Page 2 content (Debt Capacity and Risks)
    story.append(Paragraph("Item 1A. Risk Factors & Financial Obligations", section_style))
    story.append(Paragraph("We maintain a capital structure composed of both short-term commercial papers and long-term notes.", body_style))
    story.append(Paragraph("The company faces near-term liquidity constraints due to higher-than-expected yields on newly issued long-term notes. We cannot guarantee that future cash flows will be sufficient to cover debt maturities scheduled for the upcoming fiscal year, raising potential liquidity or default risks if refinancing conditions deteriorate.", body_style))
    story.append(Paragraph("Interest expenses for the quarter ended June 30, 2026, increased by 14% compared to the prior year period, driven by higher interest rates on newly issued debt instruments. These risks could negatively impact our credit rating and refinancing capabilities.", body_style))
    
    doc.build(story)
    print(f"✓ Generated PDF successfully at: {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
