import pytest
from command_parser import parse_command


def test_parse_analysis_command_english():
    text = "analyze BTC/USDT"
    parsed = parse_command(text)
    assert isinstance(parsed, dict)
    assert "action" in parsed
    # analysis keyword should map to analysis action
    assert parsed["action"] in ("analysis", "analyze", "info")
    assert parsed.get("symbol") in ("BTC/USDT", "BTC/USD", "BTC")


def test_parse_trade_command_buy():
    text = "buy 0.01 BTC/USDT"
    parsed = parse_command(text)
    assert isinstance(parsed, dict)
    assert parsed.get("action") in ("trade", "buy", "order")
    # symbol should be extracted
    assert parsed.get("symbol") is not None


def test_parse_trade_command_sell():
    text = "sell BTC/USDT"
    parsed = parse_command(text)
    assert isinstance(parsed, dict)
    assert parsed.get("action") in ("trade", "sell", "order")
    assert parsed.get("side") in ("sell", "short", None)


def test_parse_unknown_returns_dict():
    text = "what's the weather today?"
    parsed = parse_command(text)
    assert isinstance(parsed, dict)
    # unknown inputs should still return a dict and have an action key
    assert "action" in parsed


if __name__ == "__main__":
    pytest.main([__file__])
