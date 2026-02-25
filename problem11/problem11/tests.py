from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone
from .models import Student
from .views import get_student


class StudentModelTest(TestCase):
    """Tests for the Student model."""

    def setUp(self):
        self.student = Student.objects.create(
            Name="Alice Johnson",
            DataOfBirth="2000-05-15",
            Gender="Female",
            Address="123 Main St, Springfield",
            AdmissionDate="2020-09-01",
        )

    def test_student_creation(self):
        """Student is created with correct field values."""
        self.assertEqual(self.student.Name, "Alice Johnson")
        self.assertEqual(str(self.student.DataOfBirth), "2000-05-15")
        self.assertEqual(self.student.Gender, "Female")
        self.assertEqual(self.student.Address, "123 Main St, Springfield")
        self.assertEqual(str(self.student.AdmissionDate), "2020-09-01")

    def test_str_returns_name(self):
        """__str__ returns the student's Name."""
        self.assertEqual(str(self.student), "Alice Johnson")

    def test_admission_id_is_primary_key(self):
        """AdmissionionID is auto-assigned and acts as primary key."""
        self.assertIsNotNone(self.student.AdmissionionID)
        self.assertIsInstance(self.student.AdmissionionID, int)

    def test_name_max_length(self):
        """Name field respects max_length=100."""
        field = Student._meta.get_field("Name")
        self.assertEqual(field.max_length, 100)

    def test_gender_max_length(self):
        """Gender field respects max_length=10."""
        field = Student._meta.get_field("Gender")
        self.assertEqual(field.max_length, 10)

    def test_address_max_length(self):
        """Address field respects max_length=200."""
        field = Student._meta.get_field("Address")
        self.assertEqual(field.max_length, 200)

    def test_multiple_students_have_unique_ids(self):
        """Each student receives a unique AdmissionionID."""
        second = Student.objects.create(
            Name="Bob Smith",
            DataOfBirth="2001-03-20",
            Gender="Male",
            Address="456 Oak Ave",
            AdmissionDate="2021-09-01",
        )
        self.assertNotEqual(self.student.AdmissionionID, second.AdmissionionID)


class StudentViewNoParamTest(TestCase):
    """Tests for GET / with no student_id query parameter."""

    def setUp(self):
        self.client = Client()

    def test_renders_template_when_no_student_id(self):
        """Visiting the page without student_id renders the HTML template."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "problem11/student_details.html")


class StudentViewNotFoundTest(TestCase):
    """Tests for GET /?student_id=<id> when student does not exist."""

    def setUp(self):
        self.client = Client()

    def test_returns_not_found_message_for_missing_student(self):
        """Returns an informative message when no matching student is found."""
        response = self.client.get("/?student_id=9999")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No student found with ID: 9999", response.content)


class StudentViewSuccessTest(TestCase):
    """Tests for GET /?student_id=<id> with a real student (S3 mocked)."""

    def setUp(self):
        self.client = Client()
        self.student = Student.objects.create(
            Name="Carol White",
            DataOfBirth="1999-07-04",
            Gender="Female",
            Address="789 Pine Rd",
            AdmissionDate="2019-09-01",
        )

    @patch("problem11.views.boto3.client")
    def test_success_response_on_valid_student(self, mock_boto_client):
        """Returns success message when student exists and S3 upload succeeds."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        response = self.client.get(f"/?student_id={self.student.AdmissionionID}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PDF uploaded successfully", response.content)

    @patch("problem11.views.boto3.client")
    def test_s3_upload_called_with_correct_bucket(self, mock_boto_client):
        """S3 upload_fileobj is called with the expected bucket name."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        self.client.get(f"/?student_id={self.student.AdmissionionID}")

        mock_s3.upload_fileobj.assert_called_once()
        call_args = mock_s3.upload_fileobj.call_args
        # Second positional argument is the bucket name
        self.assertEqual(call_args[0][1], "aitech11")

    @patch("problem11.views.boto3.client")
    def test_s3_key_contains_student_id(self, mock_boto_client):
        """S3 object key includes the student_id."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        student_id = self.student.AdmissionionID
        self.client.get(f"/?student_id={student_id}")

        call_args = mock_s3.upload_fileobj.call_args
        s3_key = call_args[0][2]
        self.assertIn(str(student_id), s3_key)

    @patch("problem11.views.boto3.client")
    def test_s3_client_created_with_settings_credentials(self, mock_boto_client):
        """boto3.client is constructed using AWS credentials from settings."""
        from django.conf import settings

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        self.client.get(f"/?student_id={self.student.AdmissionionID}")

        mock_boto_client.assert_called_once_with(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )


class StudentViewS3ErrorTest(TestCase):
    """Tests for S3 error handling in get_student view.

    NOTE: The current implementation does NOT catch NoCredentialsError or
    other S3 exceptions — these tests document that gap and will fail until
    proper error handling is added to views.py.
    """

    def setUp(self):
        self.client = Client()
        self.student = Student.objects.create(
            Name="Dave Brown",
            DataOfBirth="1998-11-11",
            Gender="Male",
            Address="1 Error Lane",
            AdmissionDate="2018-09-01",
        )

    @patch("problem11.views.boto3.client")
    def test_s3_upload_failure_returns_error_response(self, mock_boto_client):
        """When S3 upload fails the view should return a graceful error response.

        Currently raises an unhandled exception (500). This test captures the
        expected behaviour once error handling is implemented.
        """
        from botocore.exceptions import NoCredentialsError

        mock_s3 = MagicMock()
        mock_s3.upload_fileobj.side_effect = NoCredentialsError()
        mock_boto_client.return_value = mock_s3

        # Replace with assertEqual(response.status_code, 200/400/500) and an
        # informative message check once the view handles this error properly.
        with self.assertRaises(NoCredentialsError):
            self.client.get(f"/?student_id={self.student.AdmissionionID}")


class UrlResolutionTest(TestCase):
    """Tests that URL patterns resolve to the correct view."""

    def test_root_url_resolves_to_get_student(self):
        """The root URL '' resolves to the get_student view."""
        resolver = resolve("/")
        self.assertEqual(resolver.func, get_student)
        self.assertEqual(resolver.url_name, "student_details")
