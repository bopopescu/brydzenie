# Copyright 2015 Google Inc. All Rights Reserved.
# Copyright 2002, Google Inc.
# Author: Keith Randall


import array
import httplib
import re
import struct
try:
  # NOTE(user): Using non-google-style import to workaround a zipimport_tinypar
  import googlecloudsdk.appengine.lib.external.proto.proto1 as proto1
except ImportError:
  # Protect in case of missing deps / strange env (GAE?) / etc.
  class ProtocolBufferDecodeError(Exception): pass
  class ProtocolBufferEncodeError(Exception): pass
  class ProtocolBufferReturnError(Exception): pass
else:
  ProtocolBufferDecodeError = proto1.ProtocolBufferDecodeError
  ProtocolBufferEncodeError = proto1.ProtocolBufferEncodeError
  ProtocolBufferReturnError = proto1.ProtocolBufferReturnError

__all__ = ['ProtocolMessage', 'Encoder', 'Decoder',
           'ExtendableProtocolMessage',
           'ProtocolBufferDecodeError',
           'ProtocolBufferEncodeError',
           'ProtocolBufferReturnError']

URL_RE = re.compile('^(https?)://([^/]+)(/.*)$')


class ProtocolMessage:
  """
  The parent class of all protocol buffers.
  NOTE: the methods that unconditionally raise NotImplementedError are
  reimplemented by the subclasses of this class.
  Subclasses are automatically generated by tools/protocol_converter.
  Encoding methods can raise ProtocolBufferEncodeError if a value for an
  integer or long field is too large, or if any required field is not set.
  Decoding methods can raise ProtocolBufferDecodeError if they couldn't
  decode correctly, or the decoded message doesn't have all required fields.
  """

  #####################################
  # methods you should use            #
  #####################################

  def __init__(self, contents=None):
    """Construct a new protocol buffer, with optional starting contents
    in binary protocol buffer format."""
    raise NotImplementedError

  def Clear(self):
    """Erases all fields of protocol buffer (& resets to defaults
    if fields have defaults)."""
    raise NotImplementedError

  def IsInitialized(self, debug_strs=None):
    """returns true iff all required fields have been set."""
    raise NotImplementedError

  def Encode(self):
    """Returns a string representing the protocol buffer object."""
    try:
      return self._CEncode()
    except (NotImplementedError, AttributeError):
      e = Encoder()
      self.Output(e)
      return e.buffer().tostring()

  def SerializeToString(self):
    """Same as Encode(), but has same name as proto2's serialize function."""
    return self.Encode()

  def SerializePartialToString(self):
    """Returns a string representing the protocol buffer object.
    Same as SerializeToString() but does not enforce required fields are set.
    """
    try:
      return self._CEncodePartial()
    except (NotImplementedError, AttributeError):
      e = Encoder()
      self.OutputPartial(e)
      return e.buffer().tostring()

  def _CEncode(self):
    """Call into C++ encode code.

    Generated protocol buffer classes will override this method to
    provide C++-based serialization. If a subclass does not
    implement this method, Encode() will fall back to
    using pure-Python encoding.
    """
    raise NotImplementedError

  def _CEncodePartial(self):
    """Same as _CEncode, except does not encode missing required fields."""
    raise NotImplementedError

  def ParseFromString(self, s):
    """Reads data from the string 's'.
    Raises a ProtocolBufferDecodeError if, after successfully reading
    in the contents of 's', this protocol message is still not initialized."""
    self.Clear()
    self.MergeFromString(s)

  def ParsePartialFromString(self, s):
    """Reads data from the string 's'.
    Does not enforce required fields are set."""
    self.Clear()
    self.MergePartialFromString(s)

  def MergeFromString(self, s):
    """Adds in data from the string 's'.
    Raises a ProtocolBufferDecodeError if, after successfully merging
    in the contents of 's', this protocol message is still not initialized."""
    self.MergePartialFromString(s)
    dbg = []
    if not self.IsInitialized(dbg):
      raise ProtocolBufferDecodeError, '\n\t'.join(dbg)

  def MergePartialFromString(self, s):
    """Merges in data from the string 's'.
    Does not enforce required fields are set."""
    try:
      self._CMergeFromString(s)
    except (NotImplementedError, AttributeError):
      # If we can't call into C++ to deserialize the string, use
      # the (much slower) pure-Python implementation.
      a = array.array('B')
      a.fromstring(s)
      d = Decoder(a, 0, len(a))
      self.TryMerge(d)

  def _CMergeFromString(self, s):
    """Call into C++ parsing code to merge from a string.

    Does *not* check IsInitialized() before returning.

    Generated protocol buffer classes will override this method to
    provide C++-based deserialization.  If a subclass does not
    implement this method, MergeFromString() will fall back to
    using pure-Python parsing.
    """
    raise NotImplementedError

  def __getstate__(self):
    """Return the pickled representation of the data inside protocol buffer,
    which is the same as its binary-encoded representation (as a string)."""
    return self.Encode()

  def __setstate__(self, contents_):
    """Restore the pickled representation of the data inside protocol buffer.
    Note that the mechanism underlying pickle.load() does not call __init__."""
    self.__init__(contents=contents_)

  def sendCommand(self, server, url, response, follow_redirects=1,
                  secure=0, keyfile=None, certfile=None):
    """posts the protocol buffer to the desired url on the server
    and puts the return data into the protocol buffer 'response'

    NOTE: The underlying socket raises the 'error' exception
    for all I/O related errors (can't connect, etc.).

    If 'response' is None, the server's PB response will be ignored.

    The optional 'follow_redirects' argument indicates the number
    of HTTP redirects that are followed before giving up and raising an
    exception.  The default is 1.

    If 'secure' is true, HTTPS will be used instead of HTTP.  Also,
    'keyfile' and 'certfile' may be set for client authentication.
    """
    data = self.Encode()
    if secure:
      if keyfile and certfile:
        conn = httplib.HTTPSConnection(server, key_file=keyfile,
                                       cert_file=certfile)
      else:
        conn = httplib.HTTPSConnection(server)
    else:
      conn = httplib.HTTPConnection(server)
    conn.putrequest("POST", url)
    conn.putheader("Content-Length", "%d" %len(data))
    conn.endheaders()
    conn.send(data)
    resp = conn.getresponse()
    if follow_redirects > 0 and resp.status == 302:
      m = URL_RE.match(resp.getheader('Location'))
      if m:
        protocol, server, url = m.groups()
        return self.sendCommand(server, url, response,
                                follow_redirects=follow_redirects - 1,
                                secure=(protocol == 'https'),
                                keyfile=keyfile,
                                certfile=certfile)
    if resp.status != 200:
      raise ProtocolBufferReturnError(resp.status)
    if response is not None:
      response.ParseFromString(resp.read())
    return response

  def sendSecureCommand(self, server, keyfile, certfile, url, response,
                        follow_redirects=1):
    """posts the protocol buffer via https to the desired url on the server,
    using the specified key and certificate files, and puts the return
    data int othe protocol buffer 'response'.

    See caveats in sendCommand.

    You need an SSL-aware build of the Python2 interpreter to use this command.
    (Python1 is not supported).  An SSL build of python2.2 is in
    /home/build/buildtools/python-ssl-2.2 . An SSL build of python is
    standard on all prod machines.

    keyfile: Contains our private RSA key
    certfile: Contains SSL certificate for remote host
    Specify None for keyfile/certfile if you don't want to do client auth.
    """
    return self.sendCommand(server, url, response,
                            follow_redirects=follow_redirects,
                            secure=1, keyfile=keyfile, certfile=certfile)

  def __str__(self, prefix="", printElemNumber=0):
    """Returns nicely formatted contents of this protocol buffer."""
    raise NotImplementedError

  def ToASCII(self):
    """Returns the protocol buffer as a human-readable string."""
    return self._CToASCII(ProtocolMessage._SYMBOLIC_FULL_ASCII)

  def ToCompactASCII(self):
    """Returns the protocol buffer as an ASCII string.
    Tag numbers are used instead of field names.
    Defers to the C++ ProtocolPrinter class in NUMERIC mode.
    """
    return self._CToASCII(ProtocolMessage._NUMERIC_ASCII)

  def ToShortASCII(self):
    """Returns the protocol buffer as an ASCII string.
    The output is short, leaving out newlines and some other niceties.
    Defers to the C++ ProtocolPrinter class in SYMBOLIC_SHORT mode.
    """
    return self._CToASCII(ProtocolMessage._SYMBOLIC_SHORT_ASCII)

  # Note that these must be consistent with the ProtocolPrinter::Level C++
  # enum.
  _NUMERIC_ASCII = 0
  _SYMBOLIC_SHORT_ASCII = 1
  _SYMBOLIC_FULL_ASCII = 2

  def _CToASCII(self, output_format):
    """Calls into C++ ASCII-generating code.

    Generated protocol buffer classes will override this method to provide
    C++-based ASCII output.
    """
    raise NotImplementedError

  def ParseASCII(self, ascii_string):
    """Parses a string generated by ToASCII() or by the C++ DebugString()
    method, initializing this protocol buffer with its contents. This method
    raises a ValueError if it encounters an unknown field.
    """
    raise NotImplementedError

  def ParseASCIIIgnoreUnknown(self, ascii_string):
    """Parses a string generated by ToASCII() or by the C++ DebugString()
    method, initializing this protocol buffer with its contents.  Ignores
    unknown fields.
    """
    raise NotImplementedError

  def Equals(self, other):
    """Returns whether or not this protocol buffer is equivalent to another.

    This assumes that self and other are of the same type.
    """
    raise NotImplementedError

  def __eq__(self, other):
    """Implementation of operator ==."""
    # If self and other are of different types we return NotImplemented, which
    # tells the Python interpreter to try some other methods of measuring
    # equality before finally performing an identity comparison.  This allows
    # other classes to implement custom __eq__ or __ne__ methods.
    # See http://docs.sympy.org/_sources/python-comparisons.txt
    if other.__class__ is self.__class__:
      return self.Equals(other)
    return NotImplemented

  def __ne__(self, other):
    """Implementation of operator !=."""
    # We repeat code for __ne__ instead of returning "not (self == other)"
    # so that we can return NotImplemented when comparing against an object of
    # a different type.
    # See http://bugs.python.org/msg76374 for an example of when __ne__ might
    # return something other than the Boolean opposite of __eq__.
    if other.__class__ is self.__class__:
      return not self.Equals(other)
    return NotImplemented

  #####################################
  # methods power-users might want    #
  #####################################

  def Output(self, e):
    """write self to the encoder 'e'."""
    dbg = []
    if not self.IsInitialized(dbg):
      raise ProtocolBufferEncodeError, '\n\t'.join(dbg)
    self.OutputUnchecked(e)
    return

  def OutputUnchecked(self, e):
    """write self to the encoder 'e', don't check for initialization."""
    raise NotImplementedError

  def OutputPartial(self, e):
    """write self to the encoder 'e', don't check for initialization and
    don't assume required fields exist."""
    raise NotImplementedError

  def Parse(self, d):
    """reads data from the Decoder 'd'."""
    self.Clear()
    self.Merge(d)
    return

  def Merge(self, d):
    """merges data from the Decoder 'd'."""
    self.TryMerge(d)
    dbg = []
    if not self.IsInitialized(dbg):
      raise ProtocolBufferDecodeError, '\n\t'.join(dbg)
    return

  def TryMerge(self, d):
    """merges data from the Decoder 'd'."""
    raise NotImplementedError

  def CopyFrom(self, pb):
    """copy data from another protocol buffer"""
    if (pb == self): return
    self.Clear()
    self.MergeFrom(pb)

  def MergeFrom(self, pb):
    """merge data from another protocol buffer"""
    raise NotImplementedError

  #####################################
  # helper methods for subclasses     #
  #####################################

  def lengthVarInt32(self, n):
    return self.lengthVarInt64(n)

  def lengthVarInt64(self, n):
    if n < 0:
      return 10 # ceil(64/7)
    result = 0
    while 1:
      result += 1
      n >>= 7
      if n == 0:
        break
    return result

  def lengthString(self, n):
    return self.lengthVarInt32(n) + n

  def DebugFormat(self, value):
    return "%s" % value
  def DebugFormatInt32(self, value):
    if (value <= -2000000000 or value >= 2000000000):
      return self.DebugFormatFixed32(value)
    return "%d" % value
  def DebugFormatInt64(self, value):
    if (value <= -20000000000000 or value >= 20000000000000):
      return self.DebugFormatFixed64(value)
    return "%d" % value
  def DebugFormatString(self, value):
    # For now we only escape the bare minimum to insure interoperability
    # and redability. In the future we may want to mimick the c++ behavior
    # more closely, but this will make the code a lot more messy.
    def escape(c):
      o = ord(c)
      if o == 10: return r"\n"   # optional escape
      if o == 39: return r"\'"   # optional escape

      if o == 34: return r'\"'   # necessary escape
      if o == 92: return r"\\"   # necessary escape

      if o >= 127 or o < 32: return "\\%03o" % o # necessary escapes
      return c
    return '"' + "".join([escape(c) for c in value]) + '"'
  def DebugFormatFloat(self, value):
    return "%ff" % value
  def DebugFormatFixed32(self, value):
    if (value < 0): value += (1L<<32)
    return "0x%x" % value
  def DebugFormatFixed64(self, value):
    if (value < 0): value += (1L<<64)
    return "0x%x" % value
  def DebugFormatBool(self, value):
    if value:
      return "true"
    else:
      return "false"

# types of fields, must match Proto::Type and net/proto/protocoltype.proto
TYPE_DOUBLE  = 1
TYPE_FLOAT   = 2
TYPE_INT64   = 3
TYPE_UINT64  = 4
TYPE_INT32   = 5
TYPE_FIXED64 = 6
TYPE_FIXED32 = 7
TYPE_BOOL    = 8
TYPE_STRING  = 9
TYPE_GROUP   = 10
TYPE_FOREIGN = 11

# debug string for extensions
_TYPE_TO_DEBUG_STRING = {
    TYPE_INT32:   ProtocolMessage.DebugFormatInt32,
    TYPE_INT64:   ProtocolMessage.DebugFormatInt64,
    TYPE_UINT64:  ProtocolMessage.DebugFormatInt64,
    TYPE_FLOAT:   ProtocolMessage.DebugFormatFloat,
    TYPE_STRING:  ProtocolMessage.DebugFormatString,
    TYPE_FIXED32: ProtocolMessage.DebugFormatFixed32,
    TYPE_FIXED64: ProtocolMessage.DebugFormatFixed64,
    TYPE_BOOL:    ProtocolMessage.DebugFormatBool }

# users of protocol buffers usually won't need to concern themselves
# with either Encoders or Decoders.
class Encoder:

  # types of data
  NUMERIC     = 0
  DOUBLE      = 1
  STRING      = 2
  STARTGROUP  = 3
  ENDGROUP    = 4
  FLOAT       = 5
  MAX_TYPE    = 6

  def __init__(self):
    self.buf = array.array('B')
    return

  def buffer(self):
    return self.buf

  def put8(self, v):
    if v < 0 or v >= (1<<8): raise ProtocolBufferEncodeError, "u8 too big"
    self.buf.append(v & 255)
    return

  def put16(self, v):
    if v < 0 or v >= (1<<16): raise ProtocolBufferEncodeError, "u16 too big"
    self.buf.append((v >> 0) & 255)
    self.buf.append((v >> 8) & 255)
    return

  def put32(self, v):
    if v < 0 or v >= (1L<<32): raise ProtocolBufferEncodeError, "u32 too big"
    self.buf.append((v >> 0) & 255)
    self.buf.append((v >> 8) & 255)
    self.buf.append((v >> 16) & 255)
    self.buf.append((v >> 24) & 255)
    return

  def put64(self, v):
    if v < 0 or v >= (1L<<64): raise ProtocolBufferEncodeError, "u64 too big"
    self.buf.append((v >> 0) & 255)
    self.buf.append((v >> 8) & 255)
    self.buf.append((v >> 16) & 255)
    self.buf.append((v >> 24) & 255)
    self.buf.append((v >> 32) & 255)
    self.buf.append((v >> 40) & 255)
    self.buf.append((v >> 48) & 255)
    self.buf.append((v >> 56) & 255)
    return

  def putVarInt32(self, v):
    # Profiling has shown this code to be very performance critical
    # so we duplicate code, go for early exits when possible, etc.
    # VarInt32 gets more unrolling because VarInt32s are far and away
    # the most common element in protobufs (field tags and string
    # lengths), so they get more attention.  They're also more
    # likely to fit in one byte (string lengths again), so we
    # check and bail out early if possible.

    buf_append = self.buf.append  # cache attribute lookup
    if v & 127 == v:
      buf_append(v)
      return
    if v >= 0x80000000 or v < -0x80000000:  # python2.4 doesn't fold constants
      raise ProtocolBufferEncodeError, "int32 too big"
    if v < 0:
      v += 0x10000000000000000
    while True:
      bits = v & 127
      v >>= 7
      if v:
        bits |= 128
      buf_append(bits)
      if not v:
        break
    return

  def putVarInt64(self, v):
    buf_append = self.buf.append
    if v >= 0x8000000000000000 or v < -0x8000000000000000:
      raise ProtocolBufferEncodeError, "int64 too big"
    if v < 0:
      v += 0x10000000000000000
    while True:
      bits = v & 127
      v >>= 7
      if v:
        bits |= 128
      buf_append(bits)
      if not v:
        break
    return

  def putVarUint64(self, v):
    buf_append = self.buf.append
    if v < 0 or v >= 0x10000000000000000:
      raise ProtocolBufferEncodeError, "uint64 too big"
    while True:
      bits = v & 127
      v >>= 7
      if v:
        bits |= 128
      buf_append(bits)
      if not v:
        break
    return


  # TODO: should we make sure that v actually has no more precision than
  #       float (so it comes out exactly as it goes in)?  Probably not -
  #       users expect their value to be rounded, and they would be
  #       annoyed if we forced them do it themselves.
  def putFloat(self, v):
    a = array.array('B')
    a.fromstring(struct.pack("<f", v))
    self.buf.extend(a)
    return

  def putDouble(self, v):
    a = array.array('B')
    a.fromstring(struct.pack("<d", v))
    self.buf.extend(a)
    return

  def putBoolean(self, v):
    if v:
      self.buf.append(1)
    else:
      self.buf.append(0)
    return

  def putPrefixedString(self, v):
    # This change prevents corrupted encoding an YouTube, where
    # our default encoding is utf-8 and unicode strings may occasionally be
    # passed into ProtocolBuffers.
    v = str(v)
    self.putVarInt32(len(v))
    self.buf.fromstring(v)
    return

  def putRawString(self, v):
    self.buf.fromstring(v)

  _TYPE_TO_METHOD = {
      TYPE_DOUBLE:   putDouble,
      TYPE_FLOAT:    putFloat,
      TYPE_FIXED64:  put64,
      TYPE_FIXED32:  put32,
      TYPE_INT32:    putVarInt32,
      TYPE_INT64:    putVarInt64,
      TYPE_UINT64:   putVarUint64,
      TYPE_BOOL:     putBoolean,
      TYPE_STRING:   putPrefixedString }

  _TYPE_TO_BYTE_SIZE = {
      TYPE_DOUBLE:  8,
      TYPE_FLOAT:   4,
      TYPE_FIXED64: 8,
      TYPE_FIXED32: 4,
      TYPE_BOOL:    1 }

class Decoder:
  def __init__(self, buf, idx, limit):
    self.buf = buf
    self.idx = idx
    self.limit = limit
    return

  def avail(self):
    return self.limit - self.idx

  def buffer(self):
    return self.buf

  def pos(self):
    return self.idx

  def skip(self, n):
    if self.idx + n > self.limit: raise ProtocolBufferDecodeError, "truncated"
    self.idx += n
    return

  def skipData(self, tag):
    t = tag & 7               # tag format type
    if t == Encoder.NUMERIC:
      self.getVarInt64()
    elif t == Encoder.DOUBLE:
      self.skip(8)
    elif t == Encoder.STRING:
      n = self.getVarInt32()
      self.skip(n)
    elif t == Encoder.STARTGROUP:
      while 1:
        t = self.getVarInt32()
        if (t & 7) == Encoder.ENDGROUP:
          break
        else:
          self.skipData(t)
      if (t - Encoder.ENDGROUP) != (tag - Encoder.STARTGROUP):
        raise ProtocolBufferDecodeError, "corrupted"
    elif t == Encoder.ENDGROUP:
      raise ProtocolBufferDecodeError, "corrupted"
    elif t == Encoder.FLOAT:
      self.skip(4)
    else:
      raise ProtocolBufferDecodeError, "corrupted"

  # these are all unsigned gets
  def get8(self):
    if self.idx >= self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    self.idx += 1
    return c

  def get16(self):
    if self.idx + 2 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    d = self.buf[self.idx + 1]
    self.idx += 2
    return (d << 8) | c

  def get32(self):
    if self.idx + 4 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    d = self.buf[self.idx + 1]
    e = self.buf[self.idx + 2]
    f = long(self.buf[self.idx + 3])
    self.idx += 4
    return (f << 24) | (e << 16) | (d << 8) | c

  def get64(self):
    if self.idx + 8 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    c = self.buf[self.idx]
    d = self.buf[self.idx + 1]
    e = self.buf[self.idx + 2]
    f = long(self.buf[self.idx + 3])
    g = long(self.buf[self.idx + 4])
    h = long(self.buf[self.idx + 5])
    i = long(self.buf[self.idx + 6])
    j = long(self.buf[self.idx + 7])
    self.idx += 8
    return ((j << 56) | (i << 48) | (h << 40) | (g << 32) | (f << 24)
            | (e << 16) | (d << 8) | c)

  def getVarInt32(self):
    # getVarInt32 gets different treatment than other integer getter
    # functions due to the much larger number of varInt32s and also
    # varInt32s that fit in one byte.  See the comment at putVarInt32.
    b = self.get8()
    if not (b & 128):
      return b

    result = long(0)
    shift = 0

    while 1:
      result |= (long(b & 127) << shift)
      shift += 7
      if not (b & 128):
        if result >= 0x10000000000000000L:  # (1L << 64):
          raise ProtocolBufferDecodeError, "corrupted"
        break
      if shift >= 64: raise ProtocolBufferDecodeError, "corrupted"
      b = self.get8()

    if result >= 0x8000000000000000L:  # (1L << 63)
      result -= 0x10000000000000000L  # (1L << 64)
    if result >= 0x80000000L or result < -0x80000000L:  # (1L << 31)
      raise ProtocolBufferDecodeError, "corrupted"
    return result

  def getVarInt64(self):
    result = self.getVarUint64()
    if result >= (1L << 63):
      result -= (1L << 64)
    return result

  def getVarUint64(self):
    result = long(0)
    shift = 0
    while 1:
      if shift >= 64: raise ProtocolBufferDecodeError, "corrupted"
      b = self.get8()
      result |= (long(b & 127) << shift)
      shift += 7
      if not (b & 128):
        if result >= (1L << 64): raise ProtocolBufferDecodeError, "corrupted"
        return result
    return result             # make pychecker happy

  def getFloat(self):
    if self.idx + 4 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    a = self.buf[self.idx:self.idx+4]
    self.idx += 4
    return struct.unpack("<f", a)[0]

  def getDouble(self):
    if self.idx + 8 > self.limit: raise ProtocolBufferDecodeError, "truncated"
    a = self.buf[self.idx:self.idx+8]
    self.idx += 8
    return struct.unpack("<d", a)[0]

  def getBoolean(self):
    b = self.get8()
    if b != 0 and b != 1: raise ProtocolBufferDecodeError, "corrupted"
    return b

  def getPrefixedString(self):
    length = self.getVarInt32()
    if self.idx + length > self.limit:
      raise ProtocolBufferDecodeError, "truncated"
    r = self.buf[self.idx : self.idx + length]
    self.idx += length
    return r.tostring()

  def getRawString(self):
    r = self.buf[self.idx:self.limit]
    self.idx = self.limit
    return r.tostring()

  _TYPE_TO_METHOD = {
      TYPE_DOUBLE:   getDouble,
      TYPE_FLOAT:    getFloat,
      TYPE_FIXED64:  get64,
      TYPE_FIXED32:  get32,
      TYPE_INT32:    getVarInt32,
      TYPE_INT64:    getVarInt64,
      TYPE_UINT64:   getVarUint64,
      TYPE_BOOL:     getBoolean,
      TYPE_STRING:   getPrefixedString }

#####################################
# extensions                        #
#####################################

class ExtensionIdentifier(object):
  __slots__ = ('full_name', 'number', 'field_type', 'wire_tag', 'is_repeated',
               'default', 'containing_cls', 'composite_cls', 'message_name')
  def __init__(self, full_name, number, field_type, wire_tag, is_repeated,
               default):
    self.full_name = full_name
    self.number = number
    self.field_type = field_type
    self.wire_tag = wire_tag
    self.is_repeated = is_repeated
    self.default = default

class ExtendableProtocolMessage(ProtocolMessage):
  def HasExtension(self, extension):
    """Checks if the message contains a certain non-repeated extension."""
    self._VerifyExtensionIdentifier(extension)
    return extension in self._extension_fields

  def ClearExtension(self, extension):
    """Clears the value of extension, so that HasExtension() returns false or
    ExtensionSize() returns 0."""
    self._VerifyExtensionIdentifier(extension)
    if extension in self._extension_fields:
      del self._extension_fields[extension]

  def GetExtension(self, extension, index=None):
    """Gets the extension value for a certain extension.

    Args:
      extension: The ExtensionIdentifier for the extension.
      index: The index of element to get in a repeated field. Only needed if
          the extension is repeated.

    Returns:
      The value of the extension if exists, otherwise the default value of the
      extension will be returned.
    """
    self._VerifyExtensionIdentifier(extension)
    if extension in self._extension_fields:
      result = self._extension_fields[extension]
    else:
      if extension.is_repeated:
        result = []
      elif extension.composite_cls:
        result = extension.composite_cls()
      else:
        result = extension.default
    if extension.is_repeated:
      result = result[index]
    return result

  def SetExtension(self, extension, *args):
    """Sets the extension value for a certain scalar type extension.

    Arg varies according to extension type:
    - Singular:
      message.SetExtension(extension, value)
    - Repeated:
      message.SetExtension(extension, index, value)
    where
      extension: The ExtensionIdentifier for the extension.
      index: The index of element to set in a repeated field. Only needed if
          the extension is repeated.
      value: The value to set.

    Raises:
      TypeError if a message type extension is given.
    """
    self._VerifyExtensionIdentifier(extension)
    if extension.composite_cls:
      raise TypeError(
          'Cannot assign to extension "%s" because it is a composite type.' %
          extension.full_name)
    if extension.is_repeated:
      if (len(args) != 2):
        raise TypeError(
            'SetExtension(extension, index, value) for repeated extension '
            'takes exactly 3 arguments: (%d given)' % len(args))
      index = args[0]
      value = args[1]
      self._extension_fields[extension][index] = value
    else:
      if (len(args) != 1):
        raise TypeError(
            'SetExtension(extension, value) for singular extension '
            'takes exactly 3 arguments: (%d given)' % len(args))
      value = args[0]
      self._extension_fields[extension] = value

  def MutableExtension(self, extension, index=None):
    """Gets a mutable reference of a message type extension.

    For repeated extension, index must be specified, and only one element will
    be returned. For optional extension, if the extension does not exist, a new
    message will be created and set in parent message.

    Args:
      extension: The ExtensionIdentifier for the extension.
      index: The index of element to mutate in a repeated field. Only needed if
          the extension is repeated.

    Returns:
      The mutable message reference.

    Raises:
      TypeError if non-message type extension is given.
    """
    self._VerifyExtensionIdentifier(extension)
    if extension.composite_cls is None:
      raise TypeError(
          'MutableExtension() cannot be applied to "%s", because it is not a '
          'composite type.' % extension.full_name)
    if extension.is_repeated:
      if index is None:
        raise TypeError(
            'MutableExtension(extension, index) for repeated extension '
            'takes exactly 2 arguments: (1 given)')
      return self.GetExtension(extension, index)
    if extension in self._extension_fields:
      return self._extension_fields[extension]
    else:
      result = extension.composite_cls()
      self._extension_fields[extension] = result
      return result

  def ExtensionList(self, extension):
    """Returns a mutable list of extensions.

    Raises:
      TypeError if the extension is not repeated.
    """
    self._VerifyExtensionIdentifier(extension)
    if not extension.is_repeated:
      raise TypeError(
          'ExtensionList() cannot be applied to "%s", because it is not a '
          'repeated extension.' % extension.full_name)
    if extension in self._extension_fields:
      return self._extension_fields[extension]
    result = []
    self._extension_fields[extension] = result
    return result

  def ExtensionSize(self, extension):
    """Returns the size of a repeated extension.

    Raises:
      TypeError if the extension is not repeated.
    """
    self._VerifyExtensionIdentifier(extension)
    if not extension.is_repeated:
      raise TypeError(
          'ExtensionSize() cannot be applied to "%s", because it is not a '
          'repeated extension.' % extension.full_name)
    if extension in self._extension_fields:
      return len(self._extension_fields[extension])
    return 0

  def AddExtension(self, extension, value=None):
    """Appends a new element into a repeated extension.

    Arg varies according to the extension field type:
    - Scalar/String:
      message.AddExtension(extension, value)
    - Message:
      mutable_message = AddExtension(extension)

    Args:
      extension: The ExtensionIdentifier for the extension.
      value: The value of the extension if the extension is scalar/string type.
          The value must NOT be set for message type extensions; set values on
          the returned message object instead.

    Returns:
      A mutable new message if it's a message type extension, or None otherwise.

    Raises:
      TypeError if the extension is not repeated, or value is given for message
      type extensions.
    """
    self._VerifyExtensionIdentifier(extension)
    if not extension.is_repeated:
      raise TypeError(
          'AddExtension() cannot be applied to "%s", because it is not a '
          'repeated extension.' % extension.full_name)
    if extension in self._extension_fields:
      field = self._extension_fields[extension]
    else:
      field = []
      self._extension_fields[extension] = field
    # Composite field
    if extension.composite_cls:
      if value is not None:
        raise TypeError(
            'value must not be set in AddExtension() for "%s", because it is '
            'a message type extension. Set values on the returned message '
            'instead.' % extension.full_name)
      msg = extension.composite_cls()
      field.append(msg)
      return msg
    # Scalar and string field
    field.append(value)

  def _VerifyExtensionIdentifier(self, extension):
    if extension.containing_cls != self.__class__:
      raise TypeError("Containing type of %s is %s, but not %s."
                      % (extension.full_name,
                         extension.containing_cls.__name__,
                         self.__class__.__name__))

  def _MergeExtensionFields(self, x):
    for ext, val in x._extension_fields.items():
      if ext.is_repeated:
        for i in xrange(len(val)):
          if ext.composite_cls is None:
            self.AddExtension(ext, val[i])
          else:
            self.AddExtension(ext).MergeFrom(val[i])
      else:
        if ext.composite_cls is None:
          self.SetExtension(ext, val)
        else:
          self.MutableExtension(ext).MergeFrom(val)

  def _ListExtensions(self):
    result = [ext for ext in self._extension_fields.keys()
              if (not ext.is_repeated) or self.ExtensionSize(ext) > 0]
    result.sort(key = lambda item: item.number)
    return result

  def _ExtensionEquals(self, x):
    extensions = self._ListExtensions()
    if extensions != x._ListExtensions():
      return False
    for ext in extensions:
      if ext.is_repeated:
        if self.ExtensionSize(ext) != x.ExtensionSize(ext): return False
        for e1, e2 in zip(self.ExtensionList(ext),
                          x.ExtensionList(ext)):
          if e1 != e2: return False
      else:
        if self.GetExtension(ext) != x.GetExtension(ext): return False
    return True

  def _OutputExtensionFields(self, out, partial, extensions, start_index,
                             end_field_number):
    """Serialize a range of extensions.

    To generate canonical output when encoding, we interleave fields and
    extensions to preserve tag order.

    Generated code will prepare a list of ExtensionIdentifier sorted in field
    number order and call this method to serialize a specific range of
    extensions. The range is specified by the two arguments, start_index and
    end_field_number.

    The method will serialize all extensions[i] with i >= start_index and
    extensions[i].number < end_field_number. Since extensions argument is sorted
    by field_number, this is a contiguous range; the first index j not included
    in that range is returned. The return value can be used as the start_index
    in the next call to serialize the next range of extensions.

    Args:
      extensions: A list of ExtensionIdentifier sorted in field number order.
      start_index: The start index in the extensions list.
      end_field_number: The end field number of the extension range.

    Returns:
      The first index that is not in the range. Or the size of extensions if all
      the extensions are within the range.
    """
    def OutputSingleField(ext, value):
      out.putVarInt32(ext.wire_tag)
      if ext.field_type == TYPE_GROUP:
        if partial:
          value.OutputPartial(out)
        else:
          value.OutputUnchecked(out)
        out.putVarInt32(ext.wire_tag + 1)  # End the group
      elif ext.field_type == TYPE_FOREIGN:
        if partial:
          out.putVarInt32(value.ByteSizePartial())
          value.OutputPartial(out)
        else:
          out.putVarInt32(value.ByteSize())
          value.OutputUnchecked(out)
      else:
        Encoder._TYPE_TO_METHOD[ext.field_type](out, value)

    size = len(extensions)
    for ext_index in xrange(start_index, size):
      ext = extensions[ext_index]
      if ext.number >= end_field_number:
        # exceeding extension range end.
        return ext_index
      if ext.is_repeated:
        for i in xrange(len(self._extension_fields[ext])):
          OutputSingleField(ext, self._extension_fields[ext][i])
      else:
        OutputSingleField(ext, self._extension_fields[ext])
    return size

  def _ParseOneExtensionField(self, wire_tag, d):
    number = wire_tag >> 3
    if number in self._extensions_by_field_number:
      ext = self._extensions_by_field_number[number]
      if wire_tag != ext.wire_tag:
        # wire_tag doesn't match; discard as unknown field.
        return
      if ext.field_type == TYPE_FOREIGN:
        length = d.getVarInt32()
        tmp = Decoder(d.buffer(), d.pos(), d.pos() + length)
        if ext.is_repeated:
          self.AddExtension(ext).TryMerge(tmp)
        else:
          self.MutableExtension(ext).TryMerge(tmp)
        d.skip(length)
      elif ext.field_type == TYPE_GROUP:
        if ext.is_repeated:
          self.AddExtension(ext).TryMerge(d)
        else:
          self.MutableExtension(ext).TryMerge(d)
      else:
        value = Decoder._TYPE_TO_METHOD[ext.field_type](d)
        if ext.is_repeated:
          self.AddExtension(ext, value)
        else:
          self.SetExtension(ext, value)
    else:
      # discard unknown extensions.
      d.skipData(wire_tag)

  def _ExtensionByteSize(self, partial):
    size = 0
    for extension, value in self._extension_fields.items():
      ftype = extension.field_type
      tag_size = self.lengthVarInt64(extension.wire_tag)
      if ftype == TYPE_GROUP:
        tag_size *= 2  # end tag
      if extension.is_repeated:
        size += tag_size * len(value)
        for single_value in value:
          size += self._FieldByteSize(ftype, single_value, partial)
      else:
        size += tag_size + self._FieldByteSize(ftype, value, partial)
    return size

  def _FieldByteSize(self, ftype, value, partial):
    size = 0
    if ftype == TYPE_STRING:
      size = self.lengthString(len(value))
    elif ftype == TYPE_FOREIGN or ftype == TYPE_GROUP:
      if partial:
        size = self.lengthString(value.ByteSizePartial())
      else:
        size = self.lengthString(value.ByteSize())
    elif ftype == TYPE_INT64 or  \
         ftype == TYPE_UINT64 or \
         ftype == TYPE_INT32:
      size = self.lengthVarInt64(value)
    else:
      if ftype in Encoder._TYPE_TO_BYTE_SIZE:
        size = Encoder._TYPE_TO_BYTE_SIZE[ftype]
      else:
        raise AssertionError(
            'Extension type %d is not recognized.' % ftype)
    return size

  def _ExtensionDebugString(self, prefix, printElemNumber):
    res = ''
    extensions = self._ListExtensions()
    for extension in extensions:
      value = self._extension_fields[extension]
      if extension.is_repeated:
        cnt = 0
        for e in value:
          elm=""
          if printElemNumber: elm = "(%d)" % cnt
          if extension.composite_cls is not None:
            res += prefix + "[%s%s] {\n" % \
                (extension.full_name, elm)
            res += e.__str__(prefix + "  ", printElemNumber)
            res += prefix + "}\n"
      else:
        if extension.composite_cls is not None:
          res += prefix + "[%s] {\n" % extension.full_name
          res += value.__str__(
              prefix + "  ", printElemNumber)
          res += prefix + "}\n"
        else:
          if extension.field_type in _TYPE_TO_DEBUG_STRING:
            text_value = _TYPE_TO_DEBUG_STRING[
                extension.field_type](self, value)
          else:
            text_value = self.DebugFormat(value)
          res += prefix + "[%s]: %s\n" % (extension.full_name, text_value)
    return res

  @staticmethod
  def _RegisterExtension(cls, extension, composite_cls=None):
    extension.containing_cls = cls
    extension.composite_cls = composite_cls
    if composite_cls is not None:
      extension.message_name = composite_cls._PROTO_DESCRIPTOR_NAME
    actual_handle = cls._extensions_by_field_number.setdefault(
        extension.number, extension)
    if actual_handle is not extension:
      raise AssertionError(
          'Extensions "%s" and "%s" both try to extend message type "%s" with '
          'field number %d.' %
          (extension.full_name, actual_handle.full_name,
           cls.__name__, extension.number))
