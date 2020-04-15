PROTOCOL_DESCRIPTION = b"\x13BitTorrent protocol"


class MessageTypes(object):
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    Bitfield = 5
    Request = 6
    Piece = 7
    Cancel = 8
    Port = 9

    # BEP 6 - Fast extension
    Suggest = 13
    HaveAll = 14
    HaveNone = 15
    Reject = 16
    AllowedFast = 17
    # BEP 10
    Extended = 20
