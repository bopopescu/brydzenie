# Copyright 2015 Google Inc. All Rights Reserved.

"""Utilities for making requests using a given client and handling errors.
"""

import cStringIO
import json

import httplib2

from apitools.base import py as apitools_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import resource_printer


def ExtractErrorMessage(error_details):
  """Extracts error details from an apitools_base.HttpError."""
  error_message = cStringIO.StringIO()
  error_message.write('Error Response: [{code}] {message}'.format(
      code=error_details.get('code', 'UNKNOWN'),
      message=error_details.get('message', '')))
  if 'url' in error_details:
    error_message.write('\n{url}'.format(url=error_details['url']))

  if error_details.get('details'):
    error_message.write('\nDetails: ')
    resource_printer.Print(
        resources=[error_details['details']],
        print_format='json',
        out=error_message)

  return error_message.getvalue()


def MakeRequest(service_method, request_message):
  """Makes a request using the given client method and handles HTTP errors."""
  try:
    return service_method(request_message)
  except apitools_base.HttpError as error:
    error_json = _ExtractErrorJsonFromHttpError(error)
    raise exceptions.HttpException(ExtractErrorMessage(error_json))
  except httplib2.HttpLib2Error as error:
    raise exceptions.HttpException('Response error: %s' % error.message)


def _ExtractErrorJsonFromHttpError(error):
  try:
    return json.loads(error.content)['error']
  except (ValueError, KeyError):
    return {'code': error.response['status'], 'message': error.content,
            'url': error.url}
