from unittest.mock import MagicMock, patch

from django.test import TestCase

from coldfront.plugins.qumulo.hooks import notify_on_call_on_failure_hook

ON_CALL = ["oncall@example.edu"]


def _task(success, result):
    task = MagicMock()
    task.success = success
    task.result = result
    task.name = "Generate Storage3 Monthly Usage Report for Test Condo"
    task.func = "some.module.func"
    return task


@patch("coldfront.plugins.qumulo.hooks.send_email")
class NotifyOnCallOnFailureHookTests(TestCase):
    @patch("coldfront.plugins.qumulo.hooks.EMAIL_ON_CALL_LIST", ON_CALL)
    def test_failure_emails_on_call_with_stack_trace(self, mock_send_email):
        trace = 'boom : Traceback (most recent call last):\n  File "x.py", line 1\nValueError: boom'

        notify_on_call_on_failure_hook(_task(False, trace))

        mock_send_email.assert_called_once()
        subject, body, _sender, recipients = mock_send_email.call_args.args
        self.assertIn("Generate Storage3 Monthly Usage Report for Test Condo", subject)
        self.assertIn(trace, body)
        self.assertEqual(recipients, ON_CALL)

    @patch("coldfront.plugins.qumulo.hooks.EMAIL_ON_CALL_LIST", ON_CALL)
    def test_success_sends_nothing(self, mock_send_email):
        notify_on_call_on_failure_hook(_task(True, None))

        mock_send_email.assert_not_called()

    @patch("coldfront.plugins.qumulo.hooks.EMAIL_ON_CALL_LIST", [])
    def test_failure_without_on_call_list_sends_nothing(self, mock_send_email):
        with self.assertLogs("coldfront.plugins.qumulo.hooks", level="ERROR"):
            notify_on_call_on_failure_hook(_task(False, "boom : Traceback"))

        mock_send_email.assert_not_called()

    @patch("coldfront.plugins.qumulo.hooks.EMAIL_ON_CALL_LIST", ON_CALL)
    def test_django_q_calls_hook_when_failed_task_is_saved(self, mock_send_email):
        from django.utils import timezone
        from django_q.models import Task
        from django_q.humanhash import uuid

        Task.objects.create(
            id=uuid()[1],
            name="Generate Storage3 Monthly Usage Report for Test Condo",
            func="some.module.func",
            hook="coldfront.plugins.qumulo.hooks.notify_on_call_on_failure_hook",
            started=timezone.now(),
            stopped=timezone.now(),
            success=False,
            result="boom : Traceback (most recent call last): ...",
        )

        mock_send_email.assert_called_once()
        self.assertIn("boom : Traceback", mock_send_email.call_args.args[1])
