"""
Automated invoice generation
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
from django.core.files.base import ContentFile


class InvoiceGenerator:
    """Generate professional PDF invoices"""
    
    @staticmethod
    def generate_invoice(payment):
        """
        Generate invoice PDF for a payment
        
        Args:
            payment: Payment object
        
        Returns:
            BytesIO buffer with PDF data
        """
        from .models import Invoice
        
        # Create or get invoice
        invoice, created = Invoice.objects.get_or_create(
            payment=payment,
            defaults={
                'student_name': payment.student.full_name,
                'student_email': payment.student.email,
                'subtotal': payment.amount,
                'tax_amount': 0,  # Add GST calculation if needed
                'total_amount': payment.amount,
                'items': InvoiceGenerator._build_invoice_items(payment)
            }
        )
        
        if created:
            invoice.generate_invoice_number()
            invoice.save()
        
        # Generate PDF
        buffer = InvoiceGenerator._create_pdf(invoice)
        
        # Save PDF file
        filename = f"{invoice.invoice_number}.pdf"
        invoice.pdf_file.save(filename, ContentFile(buffer.read()))
        invoice.save()
        
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def _build_invoice_items(payment):
        """Build invoice line items"""
        items = []
        
        if payment.session:
            items.append({
                'description': f"Tutoring Session - {payment.session.title}",
                'teacher': payment.session.teacher.full_name,
                'date': payment.session.scheduled_date.strftime('%Y-%m-%d'),
                'duration': f"{payment.session.duration_minutes} minutes",
                'amount': float(payment.amount)
            })
        elif payment.course:
            items.append({
                'description': f"Course Enrollment - {payment.course.title}",
                'teacher': payment.course.teacher.full_name,
                'duration': f"{payment.course.duration_weeks} weeks",
                'amount': float(payment.amount)
            })
        
        return items
    
    @staticmethod
    def _create_pdf(invoice):
        """Create PDF invoice"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Header
        story.append(Paragraph("ELITE CLASSROOM", title_style))
        story.append(Paragraph("Invoice", styles['Heading1']))
        story.append(Spacer(1, 0.3*inch))
        
        # Invoice details
        invoice_data = [
            ['Invoice Number:', invoice.invoice_number],
            ['Invoice Date:', invoice.invoice_date.strftime('%B %d, %Y')],
            ['Payment Status:', invoice.payment.status],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(invoice_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Bill to
        story.append(Paragraph("Bill To:", styles['Heading3']))
        story.append(Paragraph(invoice.student_name, styles['Normal']))
        story.append(Paragraph(invoice.student_email, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Items
        story.append(Paragraph("Items:", styles['Heading3']))
        
        items_data = [['Description', 'Teacher', 'Date', 'Amount']]
        for item in invoice.items:
            items_data.append([
                item['description'],
                item.get('teacher', 'N/A'),
                item.get('date', 'N/A'),
                f"₹{item['amount']:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"₹{invoice.subtotal:.2f}"],
            ['Platform Fee (included):', f"₹{invoice.payment.platform_fee:.2f}"],
            ['Total:', f"₹{invoice.total_amount:.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[4.5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer_text = "Thank you for your business!<br/>Elite Classroom - Empowering Education"
        story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
