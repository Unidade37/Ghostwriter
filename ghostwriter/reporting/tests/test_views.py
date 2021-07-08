# Standard Libraries
import logging
import random
from datetime import datetime

# Django Imports
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_text

# Ghostwriter Libraries
from ghostwriter.factories import (
    ClientContactFactory,
    ClientFactory,
    EvidenceFactory,
    FindingFactory,
    FindingTypeFactory,
    ObjectivePriorityFactory,
    ObjectiveStatusFactory,
    ProjectAssignmentFactory,
    ProjectFactory,
    ProjectObjectiveFactory,
    ProjectScopeFactory,
    ProjectSubtaskFactory,
    ProjectTargetFactory,
    ReportDocxTemplateFactory,
    ReportFactory,
    ReportFindingLinkFactory,
    ReportPptxTemplateFactory,
    ReportTemplateFactory,
    SeverityFactory,
    UserFactory,
)

logging.disable(logging.INFO)

PASSWORD = "SuperNaturalReporting!"

# Tests related to report modification actions


class AssignBlankFindingTests(TestCase):
    """Collection of tests for :view:`reporting.AssignBlankFinding`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory()
        cls.user = UserFactory(password=PASSWORD)

        # These must exist for the view to function
        cls.high_severity = SeverityFactory(severity="High", weight=1)
        cls.med_severity = SeverityFactory(severity="Medium", weight=2)
        cls.low_severity = SeverityFactory(severity="Low", weight=3)
        cls.info_severity = SeverityFactory(severity="Informational", weight=4)
        cls.finding_type = FindingTypeFactory(finding_type="Network")

        cls.uri = reverse("reporting:assign_blank_finding", kwargs={"pk": cls.report.pk})
        cls.redirect_uri = reverse(
            "reporting:report_detail", kwargs={"pk": cls.report.pk}
        )

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertRedirects(response, self.redirect_uri)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)


class ConvertFindingTests(TestCase):
    """Collection of tests for :view:`reporting.ConvertFinding`."""

    @classmethod
    def setUpTestData(cls):
        cls.finding = ReportFindingLinkFactory()
        cls.user = UserFactory(password=PASSWORD)

        cls.uri = reverse("reporting:convert_finding", kwargs={"pk": cls.finding.pk})
        cls.redirect_uri = reverse(
            "reporting:finding_detail", kwargs={"pk": cls.finding.pk}
        )

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/finding_form.html")


class AssignFindingTests(TestCase):
    """Collection of tests for :view:`reporting.AssignFinding`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory()
        cls.finding = FindingFactory()
        cls.user = UserFactory(password=PASSWORD)

        cls.uri = reverse("reporting:ajax_assign_finding", kwargs={"pk": cls.finding.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.post(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.post(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_response_with_session_vars(self):
        self.session = self.client_auth.session
        self.session["active_report"] = {}
        self.session["active_report"]["id"] = self.report.id
        self.session["active_report"]["title"] = self.report.title
        self.session.save()

        self.assertEqual(
            self.session["active_report"],
            {"id": self.report.id, "title": self.report.title},
        )

        response = self.client_auth.post(self.uri)
        message = "{} successfully added to your active report".format(self.finding)
        data = {"result": "success", "message": message}

        self.assertJSONEqual(force_text(response.content), data)

    def test_view_response_without_session_vars(self):
        self.session = self.client_auth.session
        self.session["active_report"] = None
        self.session.save()

        self.assertEqual(self.session["active_report"], None)

        response = self.client_auth.post(self.uri)
        message = "Please select a report to edit before trying to assign a finding"
        data = {"result": "error", "message": message}

        self.assertJSONEqual(force_text(response.content), data)


class CloneReportTests(TestCase):
    """Collection of tests for :view:`reporting.ReportClone`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory()
        cls.ReportFindingLink = ReportFindingLinkFactory._meta.model
        cls.user = UserFactory(password=PASSWORD)

        cls.num_of_findings = 10
        cls.findings = []
        for finding_id in range(cls.num_of_findings):
            title = f"Finding {finding_id}"
            cls.findings.append(ReportFindingLinkFactory(title=title, report=cls.report))

        cls.uri = reverse("reporting:report_clone", kwargs={"pk": cls.report.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("reporting/reports/", response.url)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_nonexistent_report(self):
        uri = reverse("reporting:report_clone", kwargs={"pk": 100})
        response = self.client_auth.get(uri)
        self.assertEqual(response.status_code, 404)

    def test_clone_with_zero_findings(self):
        self.ReportFindingLink.objects.all().delete()
        response = self.client_auth.get(self.uri)
        self.assertIn("reporting/reports/", response.url)


# Tests related to :model:`reporting.Finding`


class FindingsListViewTests(TestCase):
    """Collection of tests for :view:`reporting.findings_list`."""

    @classmethod
    def setUpTestData(cls):
        cls.Finding = FindingFactory._meta.model
        cls.user = UserFactory(password=PASSWORD)

        cls.num_of_findings = 10
        cls.findings = []
        for finding_id in range(cls.num_of_findings):
            title = f"Finding {finding_id}"
            cls.findings.append(FindingFactory(title=title))

        cls.uri = reverse("reporting:findings")

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/finding_list.html")

    def test_lists_all_findings(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["filter"].qs) == len(self.findings))

    def test_search_findings(self):
        response = self.client_auth.get(self.uri + "?finding_search=Finding+2")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["filter"].qs) == 1)

    def test_filter_findings(self):
        response = self.client_auth.get(self.uri + "?title=Finding+2&submit=Filter")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["filter"].qs) == 1)


class FindingDetailViewTests(TestCase):
    """Collection of tests for :view:`reporting.FindingDetailView`."""

    @classmethod
    def setUpTestData(cls):
        cls.finding = FindingFactory()
        cls.user = UserFactory(password=PASSWORD)

        cls.uri = reverse("reporting:finding_detail", kwargs={"pk": cls.finding.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/finding_detail.html")


class FindingCreateViewTests(TestCase):
    """Collection of tests for :view:`reporting.FindingCreate`."""

    @classmethod
    def setUpTestData(cls):
        cls.finding = FindingFactory()
        cls.Finding = FindingFactory._meta.model
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:finding_create")

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/finding_form.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(response.context["cancel_link"], reverse("reporting:findings"))


class FindingUpdateViewTests(TestCase):
    """Collection of tests for :view:`reporting.FindingUpdate`."""

    @classmethod
    def setUpTestData(cls):
        cls.finding = FindingFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:finding_update", kwargs={"pk": cls.finding.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/finding_form.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:finding_detail", kwargs={"pk": self.finding.pk}),
        )


class FindingDeleteViewTests(TestCase):
    """Collection of tests for :view:`reporting.FindingDelete`."""

    @classmethod
    def setUpTestData(cls):
        cls.finding = FindingFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:finding_delete", kwargs={"pk": cls.finding.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "confirm_delete.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertIn("object_type", response.context)
        self.assertIn("object_to_be_deleted", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:findings"),
        )
        self.assertEqual(
            response.context["object_type"],
            "finding master record",
        )
        self.assertEqual(response.context["object_to_be_deleted"], self.finding.title)


# Tests related to :model:`reporting.Report`


class ReportsListViewTests(TestCase):
    """Collection of tests for :view:`reporting.reports_list`."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(password=PASSWORD)

        cls.num_of_reports = 10
        cls.reports = []
        for report_id in range(cls.num_of_reports):
            title = f"Report {report_id}"
            cls.reports.append(ReportFactory(title=title))

        cls.uri = reverse("reporting:reports")

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_list.html")

    def test_lists_all_reports(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["filter"].qs) == len(self.reports))


class ReportDetailViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportDetailView`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:report_detail", kwargs={"pk": cls.report.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_detail.html")


class ReportCreateViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportCreate`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory()
        cls.project = ProjectFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:report_create_no_project")
        cls.project_uri = reverse(
            "reporting:report_create", kwargs={"pk": cls.project.pk}
        )

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_form.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(response.context["cancel_link"], reverse("reporting:reports"))

    def test_view_uri_with_project_exists_at_desired_location(self):
        response = self.client_auth.get(self.project_uri)
        self.assertEqual(response.status_code, 200)

    def test_custom_context_changes_for_project(self):
        response = self.client_auth.get(self.project_uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("rolodex:project_detail", kwargs={"pk": self.project.pk}),
        )


class ReportUpdateViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportUpdate`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:report_update", kwargs={"pk": cls.report.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_form.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:report_detail", kwargs={"pk": self.report.pk}),
        )


class ReportDeleteViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportDelete`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:report_delete", kwargs={"pk": cls.report.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "confirm_delete.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertIn("object_type", response.context)
        self.assertIn("object_to_be_deleted", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("rolodex:project_detail", kwargs={"pk": self.report.project.pk}),
        )
        self.assertEqual(
            response.context["object_type"],
            "entire report, evidence and all",
        )
        self.assertEqual(response.context["object_to_be_deleted"], self.report.title)


# Tests related to :model:`reporting.ReportFindingLink`


class ReportFindingLinkUpdateViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportFindingLinkUpdate`."""

    @classmethod
    def setUpTestData(cls):
        cls.report = ReportFactory(
            docx_template=ReportDocxTemplateFactory(),
            pptx_template=ReportPptxTemplateFactory(),
        )

        cls.high_severity = SeverityFactory(severity="High", weight=1)
        cls.critical_severity = SeverityFactory(severity="Critical", weight=0)

        cls.user = UserFactory(password=PASSWORD)
        cls.new_user = UserFactory(password=PASSWORD)

        cls.num_of_findings = 10
        cls.findings = []
        for finding_id in range(cls.num_of_findings):
            title = f"Finding {finding_id}"
            cls.findings.append(ReportFindingLinkFactory(title=title, report=cls.report))

        cls.uri = reverse("reporting:local_edit", kwargs={"pk": cls.findings[0].pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/local_edit.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:report_detail", kwargs={"pk": self.report.pk}),
        )


# Tests related to :model:`reporting.Evidence`


class EvidenceDetailViewTests(TestCase):
    """
    Collection of tests for :view:`reporting.EvidenceDetailView` and the related
    :view:`reporting.upload_evidence_modal_success`.
    """

    @classmethod
    def setUpTestData(cls):
        cls.evidence = EvidenceFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:evidence_detail", kwargs={"pk": cls.evidence.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/evidence_detail.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("filetype", response.context)
        self.assertIn("evidence", response.context)
        self.assertIn("file_content", response.context)
        self.assertEqual(
            response.context["filetype"],
            "image",
        )
        self.assertEqual(
            response.context["evidence"],
            self.evidence,
        )


class EvidenceCreateViewTests(TestCase):
    """Collection of tests for :view:`reporting.EvidenceCreate`."""

    @classmethod
    def setUpTestData(cls):
        cls.finding = ReportFindingLinkFactory()
        cls.evidence = EvidenceFactory(finding=cls.finding)
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:upload_evidence", kwargs={"pk": cls.finding.pk})
        cls.modal_uri = reverse(
            "reporting:upload_evidence_modal",
            kwargs={"pk": cls.finding.pk, "modal": "modal"},
        )
        cls.success_uri = reverse(
            "reporting:report_detail", args=(cls.finding.report.pk,)
        )
        cls.modal_success_uri = reverse("reporting:upload_evidence_modal_success")

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    # Testing regular form view
    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/evidence_form.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:report_detail", kwargs={"pk": self.finding.report.pk}),
        )

    # Testing modal form view
    def test_view_modal_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.modal_uri)
        self.assertEqual(response.status_code, 200)

    def test_view_modal_requires_login(self):
        response = self.client.get(self.modal_uri)
        self.assertEqual(response.status_code, 302)

    def test_view_modal_uses_correct_template(self):
        response = self.client_auth.get(self.modal_uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/evidence_form_modal.html")

    def test_custom_modal_context_exists(self):
        response = self.client_auth.get(self.modal_uri)
        self.assertIn("cancel_link", response.context)
        self.assertIn("used_friendly_names", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:report_detail", kwargs={"pk": self.finding.report.pk}),
        )

    # Testing modal success view
    def test_view_modal_success_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.modal_success_uri)
        self.assertEqual(response.status_code, 200)

    def test_view_modal_success_requires_login(self):
        response = self.client.get(self.modal_success_uri)
        self.assertEqual(response.status_code, 302)

    def test_view_modal_success_uses_correct_template(self):
        response = self.client_auth.get(self.modal_success_uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/evidence_modal_success.html")


class EvidenceUpdateViewTests(TestCase):
    """Collection of tests for :view:`reporting.EvidenceUpdate`."""

    @classmethod
    def setUpTestData(cls):
        cls.evidence = EvidenceFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:evidence_update", kwargs={"pk": cls.evidence.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/evidence_form.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:evidence_detail", kwargs={"pk": self.evidence.pk}),
        )


class EvidenceDeleteViewTests(TestCase):
    """Collection of tests for :view:`reporting.EvidenceDelete`."""

    @classmethod
    def setUpTestData(cls):
        cls.evidence = EvidenceFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:evidence_delete", kwargs={"pk": cls.evidence.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "confirm_delete.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertIn("object_type", response.context)
        self.assertIn("object_to_be_deleted", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:evidence_detail", kwargs={"pk": self.evidence.pk}),
        )
        self.assertEqual(
            response.context["object_type"],
            "evidence file (and associated file on disk)",
        )
        self.assertEqual(
            response.context["object_to_be_deleted"], self.evidence.friendly_name
        )


# Tests related to :model:`reporting.ReportTemplate`


class ReportTemplateListViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportTemplateListView`."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(password=PASSWORD)

        cls.num_of_templates = 10
        cls.templates = []
        for template_id in range(cls.num_of_templates):
            cls.templates.append(ReportTemplateFactory())

        cls.uri = reverse("reporting:templates")

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_templates_list.html")


class ReportTemplateDownloadTests(TestCase):
    """Collection of tests for :view:`reporting.ReportTemplateDownload`."""

    @classmethod
    def setUpTestData(cls):
        cls.template = ReportTemplateFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:template_download", kwargs={"pk": cls.template.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)


class ReportTemplateDetailViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportTemplateDetailView`."""

    @classmethod
    def setUpTestData(cls):
        cls.template = ReportTemplateFactory(protected=True)
        cls.user = UserFactory(password=PASSWORD)
        cls.admin_user = UserFactory(password=PASSWORD, is_staff=True)
        cls.uri = reverse("reporting:template_detail", kwargs={"pk": cls.template.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_admin = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )
        self.client_admin.login(username=self.admin_user.username, password=PASSWORD)
        self.assertTrue(
            self.client_admin.login(username=self.admin_user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_template_detail.html")

    def test_view_for_protected_template(self):
        response = self.client_auth.get(self.uri)
        self.assertInHTML(
            '<div class="alert alert-danger icon lock-icon" role="alert">This template is protected – only admins may edit it</div>',
            response.content.decode(),
        )

        response = self.client_admin.get(self.uri)
        self.assertInHTML(
            '<div class="alert alert-secondary icon unlock-icon" role="alert">You may edit this template as an admin</div>',
            response.content.decode(),
        )


class ReportTemplateCreateViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportTemplateCreate`."""

    @classmethod
    def setUpTestData(cls):
        cls.template = ReportTemplateFactory()
        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:template_create")

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_template_form.html")

    def test_custom_context_exists(self):
        response = self.client_auth.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(response.context["cancel_link"], reverse("reporting:templates"))

    def test_initial_form_values(self):
        response = self.client_auth.get(self.uri)

        date = datetime.now().strftime("%d %B %Y")
        initial_upload = f'<p><span class="bold">{date}</span></p><p>Initial upload</p>'

        self.assertEqual(response.context["form"].initial["changelog"], initial_upload)


class ReportTemplateUpdateViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportTemplateUpdate`."""

    @classmethod
    def setUpTestData(cls):
        cls.template = ReportTemplateFactory(protected=True)
        cls.user = UserFactory(password=PASSWORD)
        cls.admin_user = UserFactory(password=PASSWORD, is_staff=True)
        cls.uri = reverse("reporting:template_update", kwargs={"pk": cls.template.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_admin = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )
        self.client_admin.login(username=self.admin_user.username, password=PASSWORD)
        self.assertTrue(
            self.client_admin.login(username=self.admin_user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_admin.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_admin.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reporting/report_template_form.html")

    def test_custom_context_exists(self):
        response = self.client_admin.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertEqual(response.context["cancel_link"], reverse("reporting:templates"))

    def test_view_permissions(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 302)


class ReportTemplateDeleteViewTests(TestCase):
    """Collection of tests for :view:`reporting.ReportTemplateDelete`."""

    @classmethod
    def setUpTestData(cls):
        cls.template = ReportTemplateFactory(protected=True)
        cls.user = UserFactory(password=PASSWORD)
        cls.admin_user = UserFactory(password=PASSWORD, is_staff=True)
        cls.uri = reverse("reporting:template_delete", kwargs={"pk": cls.template.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_admin = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )
        self.client_admin.login(username=self.admin_user.username, password=PASSWORD)
        self.assertTrue(
            self.client_admin.login(username=self.admin_user.username, password=PASSWORD)
        )

    def test_view_uri_exists_at_desired_location(self):
        response = self.client_admin.get(self.uri)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client_admin.get(self.uri)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "confirm_delete.html")

    def test_custom_context_exists(self):
        response = self.client_admin.get(self.uri)
        self.assertIn("cancel_link", response.context)
        self.assertIn("object_type", response.context)
        self.assertIn("object_to_be_deleted", response.context)
        self.assertEqual(
            response.context["cancel_link"],
            reverse("reporting:template_detail", kwargs={"pk": self.template.pk}),
        )
        self.assertEqual(
            response.context["object_type"],
            "report template file (and associated file on disk)",
        )
        self.assertEqual(response.context["object_to_be_deleted"], self.template.filename)

    def test_view_permissions(self):
        response = self.client_auth.get(self.uri)
        self.assertEqual(response.status_code, 302)


# Tests related to generating report types


class GenerateReportTests(TestCase):
    """Collection of tests for all :view:`reporting.GenerateReport*`."""

    @classmethod
    def setUpTestData(cls):
        cls.client = ClientFactory()
        cls.project = ProjectFactory(client=cls.client)

        cls.report = ReportFactory(
            docx_template=ReportDocxTemplateFactory(),
            pptx_template=ReportPptxTemplateFactory(),
        )

        cls.num_of_contacts = 3
        cls.contacts = []
        for contact_id in range(cls.num_of_contacts):
            cls.contacts.append(ClientContactFactory(client=cls.client))

        cls.num_of_assignments = 3
        cls.assignments = []
        for assignment_id in range(cls.num_of_assignments):
            cls.assignments.append(ProjectAssignmentFactory(project=cls.project))

        cls.severities = []
        cls.severities.append(SeverityFactory(severity="Critical", weight=0))
        cls.severities.append(SeverityFactory(severity="High", weight=1))
        cls.severities.append(SeverityFactory(severity="Medium", weight=2))
        cls.severities.append(SeverityFactory(severity="Low", weight=3))

        cls.num_of_findings = 10
        cls.findings = []
        for finding_id in range(cls.num_of_findings):
            title = f"Finding {finding_id}"
            cls.findings.append(
                ReportFindingLinkFactory(
                    title=title, report=cls.report, severity=random.choice(cls.severities)
                )
            )

        cls.open_scope = ProjectScopeFactory(project=cls.project)
        cls.disallowed_scope = ProjectScopeFactory(project=cls.project, disallowed=True)
        cls.cautious_scope = ProjectScopeFactory(
            project=cls.project, requires_caution=True
        )
        cls.combined_scope = ProjectScopeFactory(
            project=cls.project, requires_caution=True, disallowed=True
        )

        cls.num_of_targets = 5
        cls.targets = []
        for target in range(cls.num_of_targets):
            cls.targets.append(ProjectTargetFactory(project=cls.project))
        for target in range(cls.num_of_targets):
            cls.targets.append(
                ProjectTargetFactory(project=cls.project, compromised=True)
            )

        cls.obj_priorities = []
        cls.obj_priorities.append(ObjectivePriorityFactory(priority="Primary", weight=0))
        cls.obj_priorities.append(
            ObjectivePriorityFactory(priority="Secondary", weight=1)
        )
        cls.obj_priorities.append(ObjectivePriorityFactory(priority="Tertiary", weight=2))

        cls.obj_status = []
        cls.obj_status.append(ObjectiveStatusFactory(objective_status="Done"))
        cls.obj_status.append(ObjectiveStatusFactory(objective_status="Missed"))
        cls.obj_status.append(ObjectiveStatusFactory(objective_status="In Progress"))

        cls.objective_first = ProjectObjectiveFactory(
            project=cls.project,
            priority=random.choice(cls.obj_priorities),
            status=random.choice(cls.obj_status),
        )
        cls.objective_second = ProjectObjectiveFactory(
            project=cls.project,
            priority=random.choice(cls.obj_priorities),
            status=random.choice(cls.obj_status),
        )
        cls.objective_third = ProjectObjectiveFactory(
            project=cls.project,
            complete=True,
            priority=random.choice(cls.obj_priorities),
            status=random.choice(cls.obj_status),
        )

        cls.num_of_subtasks = 5
        cls.subtasks = []
        for subtask in range(cls.num_of_subtasks):
            cls.subtasks.append(
                ProjectSubtaskFactory(
                    parent=cls.objective_first, status=random.choice(cls.obj_status)
                )
            )
        for subtask in range(cls.num_of_subtasks):
            cls.subtasks.append(
                ProjectSubtaskFactory(
                    parent=cls.objective_second, status=random.choice(cls.obj_status)
                )
            )
        for subtask in range(cls.num_of_subtasks):
            cls.subtasks.append(
                ProjectSubtaskFactory(
                    parent=cls.objective_third, status=random.choice(cls.obj_status)
                )
            )

        # TODO: Infrastructure additions once unit tests & factories are done for Shepherd

        # cls.num_of_servers = 3
        # cls.servers = []
        # for server_id in range(cls.num_of_servers):
        #     cls.servers.append(ServerHistoryFactory())

        # cls.num_of_domains = 5
        # cls.domains = []
        # for domain_id in range(cls.num_of_domains):
        #     cls.domains.append(DomainHistoryFactory())

        # cls.num_of_vps = cls.num_of_domains
        # cls.cloud_servers = []
        # for server_id in range(cls.num_of_vps):
        #     cls.cloud_servers.append(TransientServerFactory())

        # cls.dns = []
        # for x in range(cls.num_of_domains):
        #     cls.dns.append(DomainServerConnectionFactory())

        cls.user = UserFactory(password=PASSWORD)
        cls.uri = reverse("reporting:report_delete", kwargs={"pk": cls.report.pk})
        cls.redirect_uri = reverse(
            "reporting:report_detail", kwargs={"pk": cls.report.pk}
        )
        cls.docx_uri = reverse("reporting:generate_docx", kwargs={"pk": cls.report.pk})
        cls.xlsx_uri = reverse("reporting:generate_xlsx", kwargs={"pk": cls.report.pk})
        cls.pptx_uri = reverse("reporting:generate_pptx", kwargs={"pk": cls.report.pk})
        cls.json_uri = reverse("reporting:generate_json", kwargs={"pk": cls.report.pk})
        cls.all_uri = reverse("reporting:generate_all", kwargs={"pk": cls.report.pk})

    def setUp(self):
        self.client = Client()
        self.client_auth = Client()
        self.client_auth.login(username=self.user.username, password=PASSWORD)
        self.assertTrue(
            self.client_auth.login(username=self.user.username, password=PASSWORD)
        )

    def test_view_json_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.json_uri)
        self.assertEqual(response.status_code, 200)

    def test_view_docx_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.docx_uri)
        self.assertEquals(
            response.get("Content-Type"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def test_view_xlsx_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.xlsx_uri)
        self.assertEquals(
            response.get("Content-Type"),
            "application/application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_view_pptx_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.pptx_uri)
        self.assertEquals(
            response.get("Content-Type"),
            "application/application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    def test_view_all_uri_exists_at_desired_location(self):
        response = self.client_auth.get(self.all_uri)
        self.assertEquals(
            response.get("Content-Type"),
            "application/x-zip-compressed",
        )

    def test_view_json_requires_login(self):
        response = self.client.get(self.json_uri)
        self.assertEqual(response.status_code, 302)

    def test_view_docx_requires_login(self):
        response = self.client.get(self.docx_uri)
        self.assertEqual(response.status_code, 302)

    def test_view_xlsx_requires_login(self):
        response = self.client.get(self.xlsx_uri)
        self.assertEqual(response.status_code, 302)

    def test_view_pptxx_requires_login(self):
        response = self.client.get(self.pptx_uri)
        self.assertEqual(response.status_code, 302)

    def test_view_all_requires_login(self):
        response = self.client.get(self.all_uri)
        self.assertEqual(response.status_code, 302)
