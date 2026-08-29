import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.units import mm

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
INVOICE_DIR = BASE_DIR / "invoices"
INVOICE_DIR.mkdir(exist_ok=True)


def money(value):
    return f"₹{Decimal(str(value)):,.2f}"


def generate_invoice(booking):
    filename = f"{booking['booking_code']}-invoice.pdf"
    output = INVOICE_DIR / filename

    hotel_name = os.getenv("HOTEL_NAME", "DeskFlow Hotel")
    hotel_address = os.getenv("HOTEL_ADDRESS", "")
    hotel_phone = os.getenv("HOTEL_PHONE", "")
    hotel_email = os.getenv("HOTEL_EMAIL", "")

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {booking['booking_code']}",
        author=hotel_name,
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=5 * mm,
    )
    right = ParagraphStyle(
        "Right",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )

    story = []

    story.append(Paragraph(hotel_name, title))
    story.append(Paragraph(hotel_address, styles["Normal"]))
    story.append(Paragraph(
        f"{hotel_phone} | {hotel_email}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("BOOKING INVOICE", styles["Heading2"]))
    story.append(Spacer(1, 3 * mm))

    booking_info = [
        ["Booking ID", booking["booking_code"]],
        ["Guest", booking["customer_name"]],
        ["Email", booking["customer_email"]],
        ["Phone", booking["customer_phone"]],
        ["Room", f"{booking['room_number']} - {booking['room_type']}"],
        ["Check-in", booking["check_in"]],
        ["Check-out", booking["check_out"]],
        ["Guests", str(booking["number_of_guests"])],
        ["Nights", str(booking["nights"])],
        ["Booking status", booking["booking_status"]],
    ]

    info_table = Table(booking_info, colWidths=[42 * mm, 125 * mm])
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8 * mm))

    subtotal = Decimal(str(booking["total_amount"]))
    invoice_rows = [
        ["Description", "Qty", "Rate", "Amount"],
        [
            f"{booking['room_type']} Room",
            str(booking["nights"]),
            money(booking["room_price"]),
            money(subtotal),
        ],
        ["", "", "Grand Total", money(subtotal)],
    ]

    invoice_table = Table(
        invoice_rows,
        colWidths=[75 * mm, 20 * mm, 35 * mm, 35 * mm],
    )
    invoice_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 12 * mm))

    story.append(Paragraph(
        "Thank you for choosing our hotel.",
        styles["Normal"],
    ))

    doc.build(story)
    return str(output)
