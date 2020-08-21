# pylint: disable=redefined-outer-name
import base64
import glob
import pytest
import mock

from bentoml.types import HTTPRequest
from bentoml.adapters import FileInput


@pytest.fixture()
def input_adapter():
    return FileInput()


def test_file_input_cli(input_adapter, bin_file):
    test_args = ["--input-file", bin_file]
    for task in input_adapter.from_cli(test_args):
        assert b'\x810\x899' == task.data.read()


def test_file_input_cli_list(input_adapter, bin_files):
    test_args = ["--input-file"] + sorted(glob.glob(bin_files))
    tasks = input_adapter.from_cli(test_args)
    for i, task in enumerate(tasks):
        assert b'\x810\x899' + f'{i}'.encode() == task.data.read()


def test_file_input_aws_lambda_event(input_adapter, bin_file):
    with open(str(bin_file), "rb") as file_file:
        content = file_file.read()
        try:
            file_bytes_encoded = base64.encodebytes(content)
        except AttributeError:
            file_bytes_encoded = base64.encodebytes(str(bin_file))

    aws_lambda_event = {
        "body": file_bytes_encoded,
    }

    for task in input_adapter.from_aws_lambda_event([aws_lambda_event]):
        assert b'\x810\x899' == task.data.read()


def test_file_input_http_request_post_binary(input_adapter, bin_file):
    request = mock.MagicMock(spec=HTTPRequest)
    request.headers = tuple()
    request.body = open(str(bin_file), 'rb').read()

    for task in input_adapter.from_http_request([request]):
        assert b'\x810\x899' == task.data.read()


def test_file_input_http_request_multipart_form(input_adapter, bin_file):
    file_bytes = open(str(bin_file), 'rb').read()

    headers = (("Content-Type", "multipart/form-data; boundary=123456"),)
    body = (
        b'--123456\n'
        + b'Content-Disposition: form-data; name="file"; filename="text.png"\n'
        + b'Content-Type: application/octet-stream\n\n'
        + file_bytes
        + b'\n--123456--\n'
    )
    request = HTTPRequest(headers=headers, body=body)
    for task in input_adapter.from_http_request([request]):
        assert b'\x810\x899' == task.data.read()


def test_file_input_http_request_single_file_different_name(input_adapter, bin_file):
    file_bytes = open(str(bin_file), 'rb').read()

    headers = (("Content-Type", "multipart/form-data; boundary=123456"),)
    body = (
        b'--123456\n'
        + b'Content-Disposition: form-data; name="different_name"; filename="text.png"\n'
        + b'Content-Type: application/octet-stream\n\n'
        + file_bytes
        + b'\n--123456--\n'
    )
    request = HTTPRequest(headers=headers, body=body)

    for task in input_adapter.from_http_request([request]):
        assert b'\x810\x899' == task.data.read()


def test_file_input_http_request_malformatted_input_missing_file_file(input_adapter):
    request = mock.MagicMock(spec=HTTPRequest)

    request.files = {}
    request.headers = {}
    request.body = None

    for task in input_adapter.from_http_request([request]):
        assert task.is_discarded
