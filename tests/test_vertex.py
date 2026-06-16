from unittest.mock import MagicMock

from gateway import vertex


def test_build_contents_function_call_roundtrip():
    raw = [
        {"role": "user", "parts": [{"text": "What's the weather?"}]},
        {
            "role": "model",
            "parts": [{"functionCall": {"name": "get_weather", "args": {"city": "Tokyo"}}}],
        },
        {
            "role": "user",
            "parts": [
                {"functionResponse": {"name": "get_weather", "response": {"temp": 22}}}
            ],
        },
    ]
    contents = vertex.build_contents(raw)

    assert contents[1].parts[0].function_call.name == "get_weather"
    assert contents[1].parts[0].function_call.args == {"city": "Tokyo"}
    assert contents[2].parts[0].function_response.name == "get_weather"
    assert contents[2].parts[0].function_response.response == {"temp": 22}


def test_build_config_passes_tools():
    request_body = {
        "tools": [{"functionDeclarations": [{"name": "get_weather"}]}],
        "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
    }
    config = vertex.build_config(request_body)

    assert config is not None
    assert config.tools is not None
    assert config.tool_config is not None


def test_build_config_wraps_single_tool_object():
    request_body = {
        "tools": {"functionDeclarations": [{"name": "get_weather"}]},
    }
    config = vertex.build_config(request_body)

    assert config is not None
    assert config.tools is not None
    assert len(config.tools) == 1


def test_build_config_sanitizes_nullable_anyof():
    request_body = {
        "tools": {
            "functionDeclarations": [
                {
                    "name": "task_update",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                                "description": "current status",
                            }
                        },
                    },
                }
            ]
        }
    }
    config = vertex.build_config(request_body)

    status = config.tools[0].function_declarations[0].parameters.properties["status"]
    # anyOf collapsed into a plain nullable string, description preserved.
    assert status.any_of is None
    assert status.description == "current status"
    assert status.nullable is True


def test_sanitize_schema_keeps_anyof_alone_for_multiple_variants():
    schema = {
        "anyOf": [{"type": "string"}, {"type": "integer"}],
        "description": "id",
    }
    result = vertex._sanitize_schema(schema)

    assert set(result.keys()) == {"anyOf"}
    assert len(result["anyOf"]) == 2


def test_response_to_dict_includes_function_call():
    part = MagicMock()
    part.text = None
    part.function_call.name = "get_weather"
    part.function_call.args = {"city": "Tokyo"}
    content = MagicMock()
    content.role = "model"
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    candidate.finish_reason = None
    response = MagicMock()
    response.candidates = [candidate]
    response.usage_metadata = None

    result = vertex.response_to_dict(response)

    fc = result["candidates"][0]["content"]["parts"][0]["functionCall"]
    assert fc == {"name": "get_weather", "args": {"city": "Tokyo"}}
