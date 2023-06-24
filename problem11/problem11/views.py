import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from .models import Student
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile


def get_student(request):
    student_id = request.GET.get('student_id')
    if student_id:
        try:
            student = Student.objects.get(AdmissionionID=student_id)

            # Set up the PDF document
            doc = SimpleDocTemplate(tempfile.NamedTemporaryFile(suffix='.pdf').name, pagesize=letter)
            elements = []

            # Define custom styles for the PDF content
            styles = getSampleStyleSheet()
            header_style = styles['Heading1']
            name_style = styles['Heading2']
            field_style = styles['Normal']

            # Add content to the PDF
            elements.append(Paragraph('Student Details', header_style))
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(f'Name: {student.Name}', name_style))
            elements.append(Paragraph(f'Date of Birth: {student.DataOfBirth}', field_style))
            elements.append(Paragraph(f'Gender: {student.Gender}', field_style))
            elements.append(Paragraph(f'Address: {student.Address}', field_style))
            elements.append(Paragraph(f'Admission Date: {student.AdmissionDate}', field_style))

            doc.build(elements)

            # Upload the PDF file to S3
            s3 = boto3.client('s3',
                              aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            bucket_name = 'aitech11'  # Replace with your S3 bucket name
            s3_filepath = f"problem11/all_pdf's/student_{student_id}.pdf"
            with open(doc.filename, 'rb') as file_obj:
                s3.upload_fileobj(file_obj, bucket_name, s3_filepath)

            # Generate the S3 URL for the uploaded file
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_filepath}"

            # Redirect to the S3 URL or display it as a download link
            return HttpResponse(f"PDF uploaded successfully")

        except Student.DoesNotExist:
            error_message = f"No student found with ID: {student_id}"
            return HttpResponse(error_message)

    else:
        return render(request, 'problem11/student_details.html')
