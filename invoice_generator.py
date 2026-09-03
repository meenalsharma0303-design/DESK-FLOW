from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from datetime import datetime

def create_invoice_pdf(b):
    out_dir = Path("generated_invoices")
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"invoice_{b['booking_id']}.pdf"

    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            rightMargin=18*mm,leftMargin=18*mm,
                            topMargin=18*mm,bottomMargin=18*mm)
    styles=getSampleStyleSheet()
    title=ParagraphStyle("Title2", parent=styles["Title"], fontSize=24, spaceAfter=8)
    small=ParagraphStyle("Small", parent=styles["Normal"], fontSize=9)
    right=ParagraphStyle("Right", parent=styles["Normal"], alignment=TA_RIGHT)
    story=[]
    story += [Paragraph("DESKFLOW", title),
              Paragraph("HOTEL • STAY • EXPERIENCE", small),
              Spacer(1,10)]
    code=f"DF-{b['booking_id']:04d}"
    story += [Paragraph(f"<b>INVOICE</b> &nbsp;&nbsp; {code}", styles["Heading2"]),
              Paragraph(f"Issued: {datetime.now():%d %B %Y}", small),
              Spacer(1,15)]
    guest = f"{b['full_name']}<br/>{b['email']}<br/>{b['phone']}"
    story.append(Table([[Paragraph("<b>Bill To</b><br/>"+guest, styles["Normal"]),
                         Paragraph("<b>Stay Details</b><br/>"+b["room_name"]+
                                   f"<br/>{b['check_in']} → {b['check_out']}"+
                                   f"<br/>{b['guests_count']} guest(s)", styles["Normal"])]],
                       colWidths=[85*mm,85*mm],
                       style=[("VALIGN",(0,0),(-1,-1),"TOP"),
                              ("BOX",(0,0),(-1,-1),0.5,colors.grey),
                              ("INNERGRID",(0,0),(-1,-1),0.25,colors.lightgrey),
                              ("PADDING",(0,0),(-1,-1),8)]))
    story.append(Spacer(1,15))
    nights=(b["check_out"]-b["check_in"]).days
    subtotal=float(b["total_amount"])
    data=[["Description","Qty","Rate","Amount"],
          [b["room_name"], str(nights), f"₹{float(b['price_per_night']):,.2f}", f"₹{subtotal:,.2f}"],
          ["","", "TOTAL", f"₹{subtotal:,.2f}"]]
    t=Table(data,colWidths=[80*mm,20*mm,35*mm,35*mm],hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eeeeee")),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("ALIGN",(1,1),(-1,-1),"RIGHT"),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTNAME",(2,-1),(-1,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("PADDING",(0,0),(-1,-1),7),
    ]))
    story += [t, Spacer(1,20),
              Paragraph("Thank you for choosing DESKFLOW. We look forward to welcoming you.", styles["Normal"])]
    doc.build(story)
    return str(path)
