# Copyright 2015 Google Inc. All Rights Reserved.
#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Define the DeadlineExceededError exception."""




# Python 2.4 doesn't have BaseException; in that case alias it to Exception.
try:
  BaseException
except NameError:
  BaseException = Exception


class DeadlineExceededError(BaseException):
  """Exception raised when the request reaches its overall time limit.

  Not to be confused with runtime.apiproxy_errors.DeadlineExceededError.
  That one is raised when individual API calls take too long.
  """
