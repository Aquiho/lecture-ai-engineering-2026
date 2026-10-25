from types import SimpleNamespace

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
        text="回答",
    )

    class FakeClient:
        def __init__(self, api_key):
            self.models = SimpleNamespace(generate_content=lambda **kwargs: response)

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out.strip() == "[トークン] 入力: 12 / 出力: 34"