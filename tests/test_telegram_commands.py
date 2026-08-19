from .telegram_bot import detect_symbol, detect_language


def test_detect_symbol_simple():
    assert detect_symbol('BTCUSDT') == 'BTCUSDT'
    assert detect_symbol('please analyze btc') == 'BTCUSDT'
    assert detect_symbol('Analyze ETH') == 'ETHUSDT'
    assert detect_symbol('BTC का analysis करो') == 'BTCUSDT'
    assert detect_symbol('please buy btc') == 'BTCUSDT'
    assert detect_symbol('what is the price of eth') == 'ETHUSDT'
    assert detect_symbol('please') is None
    assert detect_symbol('analyze please') is None


def test_detect_language():
    assert detect_language('BTC का analysis करो') == 'hi'
    assert detect_language('Bitcoin buy करना चाहिए?') == 'hi'
    assert detect_language('How is BTC doing?') == 'en'
