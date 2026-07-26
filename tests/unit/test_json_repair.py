import pytest
from src.utils.json_repair import JSONParsingError, clean_markdown_fences, parse_and_repair_json, repair_json_string


def test_valid_json():
    raw = '{"gaps": [{"skill": "Python", "severity": "high"}], "priority_skills": ["Python"]}'
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["gaps"][0]["skill"] == "Python"
    assert res["priority_skills"] == ["Python"]


def test_extra_markdown_fences():
    raw = """
    ```json
    {
        "status": "success",
        "value": 100
    }
    ```
    """
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["status"] == "success"
    assert res["value"] == 100


def test_markdown_tilde_fences():
    raw = """
    ~~~json
    {
        "status": "ok"
    }
    ~~~
    """
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["status"] == "ok"


def test_trailing_commas():
    raw = '{"items": ["a", "b",], "data": {"x": 1, "y": 2,},}'
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["items"] == ["a", "b"]
    assert res["data"] == {"x": 1, "y": 2}


def test_missing_commas():
    raw = '{"key1": "val1" "key2": "val2", "list": ["item1" "item2"]}'
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["key1"] == "val1"
    assert res["key2"] == "val2"


def test_missing_quotes_unquoted_keys():
    raw = '{key: "val", priority: "high"}'
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["key"] == "val"
    assert res["priority"] == "high"


def test_single_quoted_strings_and_keys():
    raw = "{'key': 'val', 'priority': 'high'}"
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["key"] == "val"
    assert res["priority"] == "high"


def test_leading_and_trailing_explanations():
    raw = """
    Here is the requested career strategy JSON analysis:
    {
        "gaps": [{"skill": "FastAPI", "severity": "high"}],
        "priority_skills": ["FastAPI"]
    }
    Hope this helps you with your career goals!
    """
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["gaps"][0]["skill"] == "FastAPI"
    assert res["priority_skills"] == ["FastAPI"]


def test_partial_json_unclosed_braces():
    raw = '{"gaps": [{"skill": "Docker", "severity": "high"}], "summary": {"status": "ok"'
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["gaps"][0]["skill"] == "Docker"
    assert res["summary"]["status"] == "ok"


def test_bom_and_control_characters():
    raw = '\ufeff{\x00"gaps"\x07: [{"skill": "Python"}]}'
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["gaps"][0]["skill"] == "Python"


def test_js_comments_in_json():
    raw = """
    {
        // This is a comment
        "skill": "Python",
        /* Multi line
           comment */
        "level": "expert"
    }
    """
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert res["skill"] == "Python"
    assert res["level"] == "expert"


def test_list_response_wrapping():
    raw = '[{"skill": "Python"}, {"skill": "Go"}]'
    res = parse_and_repair_json(raw, agent_name="TestAgent")
    assert "data" in res
    assert len(res["data"]) == 2


def test_truncation_recovery():
    raw = '{"user_id": "123", "gaps": [{"skill": "Python"}], "projects": [{"title": "API Build", "desc": "Truncated content'
    res = parse_and_repair_json(raw, agent_name="TestAgent", finish_reason="length")
    assert "user_id" in res
    assert res["gaps"][0]["skill"] == "Python"


def test_unrepairable_json_raises_descriptive_error():
    raw = 'this is completely invalid garbage payload that cannot be parsed as json'
    with pytest.raises(JSONParsingError) as exc_info:
        parse_and_repair_json(raw, agent_name="TestAgent")

    err = exc_info.value
    assert err.agent_name == "TestAgent"
    assert "Original error" in str(err)
    assert "Repaired error" in str(err)


def test_empty_response_raises_error():
    with pytest.raises(JSONParsingError) as exc_info:
        parse_and_repair_json("", agent_name="TestAgent")
    assert exc_info.value.agent_name == "TestAgent"
