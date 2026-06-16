#!/bin/bash

set -e

# Run tests against existing gateway
echo "Running tests..."

# 1. List models
curl -s -X GET http://localhost:12080/v1beta/models > test-20260617/list_models.json

# 2. Generate content (gemini-2.5-flash)
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/generate_flash.json

# 3. Generate content (gemini-2.5-pro)
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-pro:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/generate_pro.json

# 4. Stream generate content (gemini-2.5-flash)
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:streamGenerateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/stream_flash.json

# 5. Stream generate content (gemini-2.5-pro)
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-pro:streamGenerateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/stream_pro.json

# 6. Generate content with system instruction
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"systemInstruction":{"parts":[{"text":"You are a helpful assistant."}]},"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/generate_system_instruction.json

# 7. Generate content with generation config
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"generationConfig":{"temperature":0.5,"topP":0.9,"topK":40,"maxOutputTokens":100},"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/generate_generation_config.json

# 8. Generate content with safety settings
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"safetySettings":[{"category":"HARM_CATEGORY_HATE_SPEECH","threshold":"BLOCK_LOW_AND_ABOVE"}],"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/generate_safety_settings.json

# 9. Generate content with tools
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"tools":[{"functionDeclarations":[{"name":"get_weather","description":"Get the current weather in a given location","parameters":{"type":"OBJECT","properties":{"location":{"type":"STRING","description":"The city and state, e.g. San Francisco, CA"}},"required":["location"]}}]}],"contents":[{"parts":[{"text":"What is the weather like in Boston?"}]}]}' > test-20260617/generate_tools.json

# 10. Generate content with tool choice
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"toolConfig":{"functionCallingConfig":{"mode":"ANY","allowedFunctionNames":["get_weather"]}},"tools":[{"functionDeclarations":[{"name":"get_weather","description":"Get the current weather in a given location","parameters":{"type":"OBJECT","properties":{"location":{"type":"STRING","description":"The city and state, e.g. San Francisco, CA"}},"required":["location"]}}]}],"contents":[{"parts":[{"text":"What is the weather like in Boston?"}]}]}' > test-20260617/generate_tool_choice.json

# 11. Generate content with multiple parts
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"},{"text":"World"}]}]}' > test-20260617/generate_multiple_parts.json

# 12. Generate content with multiple contents
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Hello"}]},{"role":"model","parts":[{"text":"Hi there!"}]},{"role":"user","parts":[{"text":"How are you?"}]}]}' > test-20260617/generate_multiple_contents.json

# 13. Generate content with invalid model
curl -s -X POST http://localhost:12080/v1beta/models/invalid-model:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' > test-20260617/generate_invalid_model.json

# 14. Generate content with invalid request body
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"invalid":"body"}' > test-20260617/generate_invalid_body.json

# 15. Generate content with missing contents
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{}' > test-20260617/generate_missing_contents.json

# 16. Generate content with empty contents
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[]}' > test-20260617/generate_empty_contents.json

# 17. Generate content with missing parts
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{}]}' > test-20260617/generate_missing_parts.json

# 18. Generate content with empty parts
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[]}]}' > test-20260617/generate_empty_parts.json

# 19. Generate content with missing text
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{}]}]}' > test-20260617/generate_missing_text.json

# 20. Generate content with empty text
curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":""}]}]}' > test-20260617/generate_empty_text.json

# 21. Create cached content
# Generate a long text to meet the 1024 token requirement
LONG_TEXT=$(python3 -c "print('This is a cached content. ' * 500)")
curl -s -X POST http://localhost:12080/v1beta/cachedContents \
  -H "Content-Type: application/json" \
  -d '{"model":"models/gemini-2.5-flash","contents":[{"parts":[{"text":"'"$LONG_TEXT"'"}]}]}' > test-20260617/create_cached_content.json

# Extract cached content name
CACHED_CONTENT_NAME=$(cat test-20260617/create_cached_content.json | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4 | awk -F'/' '{print $NF}')

# 22. List cached contents
curl -s -X GET http://localhost:12080/v1beta/cachedContents > test-20260617/list_cached_contents.json

# 23. Get cached content
if [ -n "$CACHED_CONTENT_NAME" ]; then
  curl -s -X GET http://localhost:12080/v1beta/cachedContents/$CACHED_CONTENT_NAME > test-20260617/get_cached_content.json
fi

# 24. Update cached content
if [ -n "$CACHED_CONTENT_NAME" ]; then
  curl -s -X PATCH http://localhost:12080/v1beta/cachedContents/$CACHED_CONTENT_NAME \
    -H "Content-Type: application/json" \
    -d '{"ttl":"3600s"}' > test-20260617/update_cached_content.json
fi

# 25. Generate content with cached content
if [ -n "$CACHED_CONTENT_NAME" ]; then
  sleep 5 # Wait a bit to avoid rate limits
  curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
    -H "Content-Type: application/json" \
    -d '{"cachedContent":"cachedContents/'$CACHED_CONTENT_NAME'","contents":[{"parts":[{"text":"What is the cached content?"}]}]}' > test-20260617/generate_cached_content.json
fi

# 26. Delete cached content
if [ -n "$CACHED_CONTENT_NAME" ]; then
  curl -s -X DELETE http://localhost:12080/v1beta/cachedContents/$CACHED_CONTENT_NAME > test-20260617/delete_cached_content.json
fi

# 27. Get deleted cached content
if [ -n "$CACHED_CONTENT_NAME" ]; then
  curl -s -X GET http://localhost:12080/v1beta/cachedContents/$CACHED_CONTENT_NAME > test-20260617/get_deleted_cached_content.json
fi

# 28. Generate content with deleted cached content
if [ -n "$CACHED_CONTENT_NAME" ]; then
  sleep 5 # Wait a bit to avoid rate limits
  curl -s -X POST http://localhost:12080/v1beta/models/gemini-2.5-flash:generateContent \
    -H "Content-Type: application/json" \
    -d '{"cachedContent":"cachedContents/'$CACHED_CONTENT_NAME'","contents":[{"parts":[{"text":"What is the cached content?"}]}]}' > test-20260617/generate_deleted_cached_content.json
fi

# 29. Create cached content with invalid model
curl -s -X POST http://localhost:12080/v1beta/cachedContents \
  -H "Content-Type: application/json" \
  -d '{"model":"models/invalid-model","contents":[{"parts":[{"text":"This is a cached content."}]}]}' > test-20260617/create_cached_content_invalid_model.json

# 30. Create cached content with missing contents
curl -s -X POST http://localhost:12080/v1beta/cachedContents \
  -H "Content-Type: application/json" \
  -d '{"model":"models/gemini-2.5-flash"}' > test-20260617/create_cached_content_missing_contents.json

echo "Tests completed."
