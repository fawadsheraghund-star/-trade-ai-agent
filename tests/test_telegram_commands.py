from .telegram_bot import detect_symbol, detect_language


def test_detect_symbol_simple():
    assert detect_symbol('BTCUSDT') == 'BTCUSDT'
    assert detect_symbol('please analyze btc') == 'BTCUSDT'
    assert detect_symbol('Analyze ETH') == 'ETHUSDT'


def test_detect_language():
    assert detect_language('BTC का analysis करो') == 'hi'
    assert detect_language('Bitcoin buy करना चाहिए?') == 'hi'
    assert detect_language('How is BTC doing?') == 'en'
