"""
PDF scorecard generation for test results
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
from django.core.files.base import ContentFile


class ScorecardGenerator:
    """Generate professional PDF scorecards"""
    
    @staticmethod
    def generate_scorecard(attempt) -> BytesIO:
        """
        Generate PDF scorecard for a mock test attempt
        
        Args:
            attempt: MockTestAttempt instance
        
        Returns:
            BytesIO buffer with PDF data
        """
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
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("Mock Test Scorecard", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Student info
        student_data = [
            ['Student:', attempt.student.full_name],
            ['Test:', attempt.mock_test.title],
            ['Subject:', attempt.mock_test.subject],
            ['Date:', attempt.started_at.strftime('%B %d, %Y')],
            ['Duration:', f"{attempt.time_taken_minutes} minutes"],
        ]
        
        student_table = Table(student_data, colWidths=[2*inch, 4*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(student_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Score summary
        story.append(Paragraph("Score Summary", heading_style))
        
        passed_text = "PASSED ✓" if attempt.passed else "NEEDS IMPROVEMENT"
        passed_color = colors.HexColor('#10b981') if attempt.passed else colors.HexColor('#ef4444')
        
        score_data = [
            ['Score', f"{attempt.total_score}/{attempt.max_score}"],
            ['Percentage', f"{attempt.percentage}%"],
            ['Status', passed_text],
            ['Passing Score', f"{attempt.mock_test.passing_score}%"],
        ]
        
        score_table = Table(score_data, colWidths=[3*inch, 3*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (1, 2), (1, 2), passed_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (1, 2), (1, 2), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(score_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Question-by-question breakdown
        story.append(Paragraph("Question Breakdown", heading_style))
        
        answers = attempt.answers.select_related('question').order_by('question__order')
        
        question_data = [['Q#', 'Correct?', 'Points', 'Topic']]
        for answer in answers:
            q = answer.question
            check = '✓' if answer.is_correct else '✗'
            question_data.append([
                str(q.order + 1),
                check,
                f"{answer.points_earned}/{q.points}",
                q.bloom_level or 'General'
            ])
        
        question_table = Table(question_data, colWidths=[0.75*inch, 1*inch, 1.25*inch, 3*inch])
        question_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        
        story.append(question_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        story.append(Paragraph("Recommendations", heading_style))
        
        if attempt.percentage < 60:
            recommendation = "Focus on reviewing the material and retake the test. Consider scheduling additional tutoring sessions."
        elif attempt.percentage < 80:
            recommendation = "Good effort! Review the questions you missed and practice similar problems."
        else:
            recommendation = "Excellent work! You've demonstrated strong understanding. Ready to move to advanced topics."
        
        story.append(Paragraph(recommendation, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Footer
        footer = Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Elite Classroom",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
        )
        story.append(Spacer(1, 0.3*inch))
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def save_scorecard_to_attempt(attempt):
        """Generate and save PDF to attempt instance"""
        pdf_buffer = ScorecardGenerator.generate_scorecard(attempt)
        filename = f"scorecard_{attempt.id}_{attempt.student.id}.pdf"
        attempt.scorecard_pdf.save(filename, ContentFile(pdf_buffer.read()))
        attempt.save()
