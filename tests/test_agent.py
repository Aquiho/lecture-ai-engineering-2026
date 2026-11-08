"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent, request_tool_approvals

BASE_TOOLS = {"search_glossary", "get_lecture_summary", "make_quiz", "save_learning_log"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # 承認が必要なツール（requires_approval=True）は、実行されずに承認待ちになるので戻り値が無い
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output
    assert isinstance(result.output, DeferredToolRequests)
    assert result.output.approvals


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_request_tool_approvals_accepts_explicit_yes(monkeypatch):
    call = ToolCallPart(
        tool_name="save_learning_log",
        args={"topic": "LoRA", "note": "理解した"},
        tool_call_id="save-1",
    )
    monkeypatch.setattr("builtins.input", lambda _: "はい")

    result = request_tool_approvals(DeferredToolRequests(approvals=[call]))

    assert isinstance(result, DeferredToolResults)
    assert result.approvals == {"save-1": True}


def test_request_tool_approvals_defaults_to_reject(monkeypatch):
    call = ToolCallPart(
        tool_name="save_learning_log",
        args={"topic": "LoRA", "note": "理解した"},
        tool_call_id="save-2",
    )
    monkeypatch.setattr("builtins.input", lambda _: "")

    result = request_tool_approvals(DeferredToolRequests(approvals=[call]))

    assert result.approvals == {"save-2": False}
