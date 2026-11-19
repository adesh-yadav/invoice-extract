import unittest
from unittest.mock import Mock, patch
from PIL import Image
from src.modules.extraction.adapters.outbound.ai.provider_factory import ModelConfig, create_chat_model
from src.modules.extraction.adapters.outbound.ai.vision_transcriber import LangChainVisionTranscriber


class TestProviderFactory(unittest.TestCase):
    def test_provider_defaults_and_credentials(self):
        self.assertEqual(ModelConfig("openai", "").resolved_model, "gpt-4.1-mini")
        self.assertEqual(ModelConfig("anthropic", "").resolved_model, "claude-haiku-4-5-20251001")
        self.assertEqual(ModelConfig("ollama", "").resolved_model, "gemma3:4b")
        self.assertFalse(ModelConfig("anthropic", "").ready)
        self.assertTrue(ModelConfig("anthropic", "", anthropic_api_key="test-key").ready)
        self.assertTrue(ModelConfig("ollama", "").ready)

    @patch("langchain_anthropic.ChatAnthropic")
    def test_claude_uses_anthropic_adapter(self, constructor):
        create_chat_model(ModelConfig("anthropic", "claude-test", anthropic_api_key="test-key"))
        self.assertEqual(constructor.call_args.kwargs["model"], "claude-test")
        self.assertEqual(constructor.call_args.kwargs["anthropic_api_key"], "test-key")

    @patch("langchain_ollama.ChatOllama")
    def test_ollama_uses_local_endpoint(self, constructor):
        create_chat_model(ModelConfig("ollama", "gemma3:4b", ollama_base_url="http://ollama:11434"))
        self.assertEqual(constructor.call_args.kwargs["base_url"], "http://ollama:11434")

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_still_supported(self, constructor):
        create_chat_model(ModelConfig("openai", "gpt-test", openai_api_key="test-key"))
        self.assertEqual(constructor.call_args.kwargs["model"], "gpt-test")

    def test_vision_image_block_matches_provider(self):
        image = Image.new("RGB", (8, 8), "white")
        for provider, expected_type in (("openai", "image_url"), ("anthropic", "image"), ("ollama", "image_url")):
            model = Mock()
            model.invoke.return_value.content = "TOTAL 10"
            result = LangChainVisionTranscriber(model, provider).transcribe(image)
            self.assertEqual(result, "TOTAL 10")
            block = model.invoke.call_args.args[0][0].content[1]
            self.assertEqual(block["type"], expected_type)
            if provider == "ollama":
                self.assertIsInstance(block["image_url"], str)
