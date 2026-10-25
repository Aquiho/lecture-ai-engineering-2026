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
    times = iter([10.0, 11.234])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(times))

    assert ask_module.ask("質問") == "回答"
    assert capsys.readouterr().out.splitlines() == [
        "[応答時間] 1.23 秒",
        "[トークン] 入力: 12 / 出力: 34",
    ]


def test_interactive_chat_reuses_conversation(monkeypatch, capsys):
    responses = iter(
        [
            SimpleNamespace(
                usage_metadata=None,
                text="最初の回答",
            ),
            SimpleNamespace(
                usage_metadata=None,
                text="続きの回答",
            ),
        ]
    )
    conversations = []

    class FakeConversation:
        def __init__(self):
            self.messages = []

        def send_message(self, message):
            self.messages.append(message)
            return next(responses)

    class FakeClient:
        def __init__(self, api_key):
            def create_chat(**kwargs):
                conversation = FakeConversation()
                conversations.append(conversation)
                return conversation

            self.chats = SimpleNamespace(
                create=create_chat
            )

    inputs = iter(["最初の質問", "続きの質問", "exit"])
    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    times = iter([5.0, 5.5, 6.0, 8.25])
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(times))

    ask_module.chat()

    assert len(conversations) == 1
    assert conversations[0].messages == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "[応答時間] 0.50 秒" in output
    assert "[応答時間] 2.25 秒" in output
    assert "最初の回答" in output