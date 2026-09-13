import sys
from io import StringIO
import pytest
from leo_greeting import main, GREETING_MESSAGE


def test_main_prints_expected_greeting(capsys):
    """
    Test that the main function prints the correct greeting message to stdout
    under normal operating conditions.
    """
    main()
    captured = capsys.readouterr()
    assert captured.out == f"{GREETING_MESSAGE}\n"


def test_main_no_stderr_output(capsys):
    """
    Test that executing the main function does not produce any error output
    on standard error.
    """
    main()
    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_exit_code_success():
    """
    Test that executing the main function completes successfully with a
    standard successful execution flow (implicit return None).
    """
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an unexpected exception: {e}")


def test_main_multiple_independent_calls(capsys):
    """
    Test that calling main multiple times produces consistent, independent
    results without side effects bleeding between executions.
    """
    main()
    first_capture = capsys.readouterr().out

    main()
    second_capture = capsys.readouterr().out

    assert first_capture == second_capture
    assert first_capture == f"{GREETING_MESSAGE}\n"


def test_greeting_message_constant_integrity():
    """
    Integration-style test ensuring the module-level GREETING_MESSAGE constant
    matches the string actually consumed and printed by the main function workflow.
    """
    fake_stdout = StringIO()
    sys.stdout = fake_stdout
    try:
        main()
        output = fake_stdout.getvalue().strip()
        assert output == GREETING_MESSAGE
    finally:
        sys.stdout = sys.__stdout__