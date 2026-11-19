import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image
from src.modules.extraction.adapters.outbound.ai.provider_factory import ModelConfig, create_chat_model
from src.modules.extraction.adapters.outbound.ai.vision_transcriber import LangChainVisionTranscriber
from src.modules.extraction.config.module import build_process_job
from src.modules.extraction.adapters.outbound.ai.ocr_cleaner import LangChainOCRCleaner


class TestProviderFactory(unittest.TestCase):
    def test_provider_defaults_and_credentials(self):
        self.assertEqual(ModelConfig("openai", "").resolved_model, "gpt-4.1-mini")
        self.assertEqual(ModelConfig("anthropic", "").resolved_model, "claude-haiku-4-5-20251001")
        self.assertEqual(ModelConfig("ollama", "").resolved_model, "gemma3:4b")
        self.assertEqual(ModelConfig("google", "").resolved_model, "gemini-2.5-flash")
        self.assertFalse(ModelConfig("anthropic", "").ready)
        self.assertTrue(ModelConfig("anthropic", "", anthropic_api_key="test-key").ready)
        self.assertTrue(ModelConfig("ollama", "").ready)
        self.assertFalse(ModelConfig("google", "").ready)
        self.assertTrue(ModelConfig("google", "", google_api_key="test-key").ready)

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_google_uses_one_provider_key(self, constructor):
        create_chat_model(ModelConfig("google", "gemini-test", google_api_key="test-key"))
        self.assertEqual(constructor.call_args.kwargs["model"], "gemini-test")
        self.assertEqual(constructor.call_args.kwargs["google_api_key"], "test-key")

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
        for provider, expected_type in (("openai", "image_url"), ("anthropic", "image"), ("ollama", "image_url"), ("google", "image_url")):
            model = Mock()
            model.invoke.return_value.content = "TOTAL 10"
            result = LangChainVisionTranscriber(model, provider).transcribe(image)
            self.assertEqual(result, "TOTAL 10")
            block = model.invoke.call_args.args[0][0].content[1]
            self.assertEqual(block["type"], expected_type)
            if provider == "ollama":
                self.assertIsInstance(block["image_url"], str)

    def test_ocr_cleaner_preserves_model_text_as_candidate(self):
        model = Mock()
        model.invoke.return_value.content = "Total 100.00"
        self.assertEqual(LangChainOCRCleaner(model).clean("Tota1 100.00"), "Total 100.00")

    @patch("src.modules.extraction.config.module.create_chat_model")
    @patch("src.modules.extraction.config.module.settings")
    def test_vision_can_use_a_different_provider_and_key(self, settings, create_model):
        settings.LLM_PROVIDER = "anthropic"
        settings.EXTRACTION_MODEL = "claude-test"
        settings.VISION_PROVIDER = "openai"
        settings.VISION_MODEL = "gpt-vision-test"
        settings.ANTHROPIC_API_KEY = "claude-key"
        settings.GOOGLE_API_KEY = ""
        settings.OPENAI_API_KEY = "vision-key"
        settings.OLLAMA_BASE_URL = "http://ollama:11434"
        settings.ENABLE_VISION_FALLBACK = True
        settings.OCR_CLEANUP_PROVIDER = ""
        settings.OCR_CLEANUP_MODEL = ""
        settings.ENABLE_OCR_CLEANUP = False
        settings.OCR_LANGUAGES = "eng"
        settings.MAX_IMAGE_PIXELS = 40_000_000
        settings.MAX_PDF_PAGES = 20
        settings.ARTIFACT_DIR = Path("/tmp/artifacts")
        extraction_model, vision_model = Mock(), Mock()
        create_model.side_effect = [extraction_model, vision_model]

        processor = build_process_job()

        extraction_config = create_model.call_args_list[0].args[0]
        vision_config = create_model.call_args_list[1].args[0]
        self.assertEqual((extraction_config.provider, extraction_config.resolved_model), ("anthropic", "claude-test"))
        self.assertEqual((vision_config.provider, vision_config.resolved_model), ("openai", "gpt-vision-test"))
        self.assertEqual(vision_config.openai_api_key, "vision-key")
        self.assertIs(processor.readers[".png"].ocr.vision.model, vision_model)
        self.assertEqual(processor.readers[".png"].ocr.vision.provider, "openai")
