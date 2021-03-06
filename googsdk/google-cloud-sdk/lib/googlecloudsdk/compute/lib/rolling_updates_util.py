# Copyright 2014 Google Inc. All Rights Reserved.
"""Common utility functions for Updater."""

import json
import sys

from googlecloudsdk.core import log

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import time_utils
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import resource_printer


def WaitForOperation(client, operation_ref, message):
  """Waits until the given operation finishes.

  Wait loop terminates when the operation's status becomes 'DONE'.

  Args:
    client: interface to the Cloud Updater API
    operation_ref: operation to poll
    message: message to be displayed by progress tracker

  Returns:
    True iff the operation finishes with success
  """
  with console_io.ProgressTracker(message, autotick=False) as pt:
    while True:
      operation = client.zoneOperations.Get(operation_ref.Request())
      if operation.error:
        return False
      if operation.status == 'DONE':
        return True
      pt.Tick()
      time_utils.Sleep(2)


def GetError(error, verbose=False):
  """Returns a ready-to-print string representation from the http response.

  Args:
    error: A string representing the raw json of the Http error response.
    verbose: Whether or not to print verbose messages [default false]

  Returns:
    A ready-to-print string representation of the error.
  """
  data = json.loads(error.content)
  if verbose:
    PrettyPrint(data)
  code = data['error']['code']
  message = data['error']['message']
  return 'ResponseError: code={0}, message={1}'.format(code, message)


def SanitizeLimitFlag(limit):
  """Sanitizes and returns a limit flag value.

  Args:
    limit: the limit flag value to sanitize.
  Returns:
    Sanitized limit flag value.
  Raises:
    ToolException: if the provided limit flag value is not a positive integer
  """
  if limit is None:
    limit = sys.maxint
  else:
    if limit > sys.maxint:
      limit = sys.maxint
    elif limit <= 0:
      raise exceptions.ToolException(
          '--limit must be a positive integer; received: {0}'
          .format(limit))
  return limit


def PrettyPrint(resource, print_format='json'):
  """Prints the given resource."""
  resource_printer.Print(
      resources=[resource],
      print_format=print_format,
      out=log.out)
