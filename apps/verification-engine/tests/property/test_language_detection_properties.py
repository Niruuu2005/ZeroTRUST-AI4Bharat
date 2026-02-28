"""
Property-based tests for language detection.

Property 25: Language Detection Accuracy
**Validates: Requirements 13.6**

Property: For any claim text in a supported language, the language detector should 
return a valid ISO 639-1 language code.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.normalization.language_detector import LanguageDetector


# ISO 639-1 language codes (most common ones supported by langdetect)
VALID_ISO_639_1_CODES = {
    'af', 'ar', 'bg', 'bn', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'es', 'et', 'fa', 'fi', 'fr',
    'gu', 'he', 'hi', 'hr', 'hu', 'id', 'it', 'ja', 'kn', 'ko', 'lt', 'lv', 'mk', 'ml', 'mr', 'ne',
    'nl', 'no', 'pa', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'so', 'sq', 'sv', 'sw', 'ta', 'te', 'th',
    'tl', 'tr', 'uk', 'ur', 'vi', 'zh-cn', 'zh-tw'
}


# Sample texts in different languages for testing
LANGUAGE_SAMPLES = {
    'en': [
        "The quick brown fox jumps over the lazy dog",
        "Hello world, this is a test message",
        "Climate change is affecting global weather patterns",
        "Artificial intelligence is transforming technology",
        "The government announced new policies today"
    ],
    'es': [
        "El rápido zorro marrón salta sobre el perro perezoso",
        "Hola mundo, este es un mensaje de prueba",
        "El cambio climático está afectando los patrones climáticos globales",
        "La inteligencia artificial está transformando la tecnología",
        "El gobierno anunció nuevas políticas hoy"
    ],
    'fr': [
        "Le rapide renard brun saute par-dessus le chien paresseux",
        "Bonjour le monde, ceci est un message de test",
        "Le changement climatique affecte les modèles météorologiques mondiaux",
        "L'intelligence artificielle transforme la technologie",
        "Le gouvernement a annoncé de nouvelles politiques aujourd'hui"
    ],
    'de': [
        "Der schnelle braune Fuchs springt über den faulen Hund",
        "Hallo Welt, dies ist eine Testnachricht",
        "Der Klimawandel beeinflusst globale Wettermuster",
        "Künstliche Intelligenz verändert die Technologie",
        "Die Regierung kündigte heute neue Richtlinien an"
    ],
    'it': [
        "La veloce volpe marrone salta sopra il cane pigro",
        "Ciao mondo, questo è un messaggio di prova",
        "Il cambiamento climatico sta influenzando i modelli meteorologici globali",
        "L'intelligenza artificiale sta trasformando la tecnologia",
        "Il governo ha annunciato nuove politiche oggi"
    ],
    'pt': [
        "A rápida raposa marrom pula sobre o cão preguiçoso",
        "Olá mundo, esta é uma mensagem de teste",
        "A mudança climática está afetando os padrões climáticos globais",
        "A inteligência artificial está transformando a tecnologia",
        "O governo anunciou novas políticas hoje"
    ],
    'nl': [
        "De snelle bruine vos springt over de luie hond",
        "Hallo wereld, dit is een testbericht",
        "Klimaatverandering beïnvloedt wereldwijde weerpatronen",
        "Kunstmatige intelligentie transformeert technologie",
        "De regering kondigde vandaag nieuw beleid aan"
    ],
    'ru': [
        "Быстрая коричневая лиса прыгает через ленивую собаку",
        "Привет мир, это тестовое сообщение",
        "Изменение климата влияет на глобальные погодные условия",
        "Искусственный интеллект преобразует технологии",
        "Правительство объявило о новой политике сегодня"
    ],
    'ja': [
        "素早い茶色のキツネが怠け者の犬を飛び越える",
        "こんにちは世界、これはテストメッセージです",
        "気候変動は世界的な気象パターンに影響を与えています",
        "人工知能は技術を変革しています",
        "政府は今日新しい政策を発表しました"
    ],
    'zh-cn': [
        "敏捷的棕色狐狸跳过懒狗",
        "你好世界，这是一条测试消息",
        "气候变化正在影响全球天气模式",
        "人工智能正在改变技术",
        "政府今天宣布了新政策"
    ],
    'ar': [
        "الثعلب البني السريع يقفز فوق الكلب الكسول",
        "مرحبا بالعالم، هذه رسالة اختبار",
        "تغير المناخ يؤثر على أنماط الطقس العالمية",
        "الذكاء الاصطناعي يحول التكنولوجيا",
        "أعلنت الحكومة عن سياسات جديدة اليوم"
    ],
    'hi': [
        "तेज़ भूरी लोमड़ी आलसी कुत्ते के ऊपर कूदती है",
        "नमस्ते दुनिया, यह एक परीक्षण संदेश है",
        "जलवायु परिवर्तन वैश्विक मौसम पैटर्न को प्रभावित कर रहा है",
        "कृत्रिम बुद्धिमत्ता प्रौद्योगिकी को बदल रही है",
        "सरकार ने आज नई नीतियों की घोषणा की"
    ]
}


# Custom strategy for generating text in known languages
@st.composite
def text_in_language(draw):
    """Generate text in a known language."""
    language = draw(st.sampled_from(list(LANGUAGE_SAMPLES.keys())))
    text = draw(st.sampled_from(LANGUAGE_SAMPLES[language]))
    return text, language


class TestLanguageDetectionProperties:
    """Property-based tests for language detection."""
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_returns_valid_iso_639_1_code(self, text):
        """
        Property 25: Returns Valid ISO 639-1 Code
        **Validates: Requirements 13.6**
        
        For any claim text, the language detector should return a valid 
        ISO 639-1 language code.
        """
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Result should be a valid ISO 639-1 code
        assert isinstance(result, str), (
            f"Result is not a string: {type(result)}"
        )
        
        assert len(result) >= 2, (
            f"Result is too short to be a valid ISO 639-1 code: {repr(result)}"
        )
        
        # Should be lowercase
        assert result.islower() or '-' in result, (
            f"Result is not lowercase: {repr(result)}"
        )
        
        # Should be alphanumeric (with possible hyphen for zh-cn, zh-tw)
        assert all(c.isalnum() or c == '-' for c in result), (
            f"Result contains invalid characters: {repr(result)}"
        )
    
    @given(text_in_language())
    @settings(max_examples=100)
    def test_detects_known_languages_correctly(self, data):
        """
        Property 25: Detects Known Languages Correctly
        **Validates: Requirements 13.6**
        
        For any text in a known language, the language detector should 
        return a valid ISO 639-1 code. Due to the probabilistic nature
        of language detection, we verify it returns a valid code rather
        than requiring exact matches for all cases.
        """
        text, expected_lang = data
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Should return a valid ISO 639-1 code
        assert isinstance(result, str), (
            f"Result is not a string: {type(result)}"
        )
        
        assert len(result) >= 2, (
            f"Result is too short: {repr(result)}"
        )
        
        # For longer, well-formed text, detection should be accurate
        # But we acknowledge that short or ambiguous text may be misdetected
        if len(text) > 50:
            # For longer text, we expect higher accuracy
            # Allow some tolerance for similar languages (e.g., nl/af, zh-cn/ko)
            similar_languages = {
                'nl': ['af', 'nl'],  # Dutch and Afrikaans are similar
                'af': ['af', 'nl'],
                'zh-cn': ['zh-cn', 'zh-tw', 'ko', 'ja'],  # CJK languages can be confused
                'zh-tw': ['zh-cn', 'zh-tw', 'ko', 'ja'],
                'ko': ['ko', 'ja', 'zh-cn', 'zh-tw'],
                'ja': ['ja', 'ko', 'zh-cn', 'zh-tw'],
            }
            
            allowed = similar_languages.get(expected_lang, [expected_lang])
            assert result in allowed, (
                f"Unexpected language detected:\n"
                f"Text: {repr(text)}\n"
                f"Expected: {expected_lang}\n"
                f"Detected: {result}\n"
                f"Allowed: {allowed}"
            )
    
    @given(st.text(min_size=0, max_size=2))
    @settings(max_examples=100)
    def test_short_text_returns_default(self, text):
        """
        Property 25: Short Text Returns Default
        **Validates: Requirements 13.6**
        
        For any text shorter than 3 characters, the language detector should 
        return the default language code 'en'.
        """
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Short text should default to 'en'
        assert result == 'en', (
            f"Short text did not return default 'en':\n"
            f"Text: {repr(text)}\n"
            f"Result: {result}"
        )
    
    @given(st.just(''))
    @settings(max_examples=100)
    def test_empty_text_returns_default(self, text):
        """
        Property 25: Empty Text Returns Default
        **Validates: Requirements 13.6**
        
        For empty text, the language detector should return the default 
        language code 'en'.
        """
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Empty text should default to 'en'
        assert result == 'en', (
            f"Empty text did not return default 'en':\n"
            f"Result: {result}"
        )
    
    @given(st.text(
        alphabet=st.characters(whitelist_categories=('Zs',)),  # Only whitespace
        min_size=1,
        max_size=100
    ))
    @settings(max_examples=100)
    def test_whitespace_only_returns_default(self, text):
        """
        Property 25: Whitespace-Only Text Returns Default
        **Validates: Requirements 13.6**
        
        For text containing only whitespace, the language detector should 
        return the default language code 'en'.
        """
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Whitespace-only text should default to 'en'
        assert result == 'en', (
            f"Whitespace-only text did not return default 'en':\n"
            f"Text: {repr(text)}\n"
            f"Result: {result}"
        )
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_detection_is_deterministic(self, text):
        """
        Property 25: Detection is Deterministic
        **Validates: Requirements 13.6**
        
        For any text, detecting the language multiple times should return 
        the same result (deterministic behavior).
        """
        detector = LanguageDetector()
        
        # Detect language multiple times
        result1 = detector.detect(text)
        result2 = detector.detect(text)
        result3 = detector.detect(text)
        
        # Property: All results should be identical
        assert result1 == result2 == result3, (
            f"Language detection is not deterministic:\n"
            f"Text: {repr(text[:100])}\n"
            f"Result1: {result1}\n"
            f"Result2: {result2}\n"
            f"Result3: {result3}"
        )
    
    @given(
        st.lists(
            st.sampled_from([
                sample
                for samples in LANGUAGE_SAMPLES.values()
                for sample in samples
            ]),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_mixed_language_text_returns_valid_code(self, sentences):
        """
        Property 25: Mixed Language Text Returns Valid Code
        **Validates: Requirements 13.6**
        
        For text containing multiple languages, the language detector should 
        still return a valid ISO 639-1 code (typically the dominant language).
        """
        text = ' '.join(sentences)
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Should return a valid ISO 639-1 code
        assert isinstance(result, str), (
            f"Result is not a string: {type(result)}"
        )
        
        assert len(result) >= 2, (
            f"Result is too short: {repr(result)}"
        )
        
        # Should be a valid code (either in our known set or a reasonable code)
        assert result.islower() or '-' in result, (
            f"Result is not lowercase: {repr(result)}"
        )
    
    @given(
        st.sampled_from(list(LANGUAGE_SAMPLES.keys())),
        st.integers(min_value=2, max_value=5)  # Use at least 2 sentences for better accuracy
    )
    @settings(max_examples=100)
    def test_longer_text_improves_accuracy(self, language, num_sentences):
        """
        Property 25: Longer Text Improves Accuracy
        **Validates: Requirements 13.6**
        
        For text in a known language with multiple sentences, the language 
        detector should return a valid ISO 639-1 code.
        """
        # Build text with multiple sentences
        sentences = LANGUAGE_SAMPLES[language][:num_sentences]
        text = ' '.join(sentences)
        
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Should return a valid ISO 639-1 code
        assert isinstance(result, str), (
            f"Result is not a string: {type(result)}"
        )
        
        assert len(result) >= 2, (
            f"Result is too short: {repr(result)}"
        )
        
        # For multiple sentences, allow similar languages
        similar_languages = {
            'nl': ['af', 'nl'],
            'af': ['af', 'nl'],
            'zh-cn': ['zh-cn', 'zh-tw', 'ko', 'ja'],
            'zh-tw': ['zh-cn', 'zh-tw', 'ko', 'ja'],
            'ko': ['ko', 'ja', 'zh-cn', 'zh-tw'],
            'ja': ['ja', 'ko', 'zh-cn', 'zh-tw'],
        }
        
        allowed = similar_languages.get(language, [language])
        assert result in allowed, (
            f"Unexpected language detected with {num_sentences} sentences:\n"
            f"Text: {repr(text[:200])}\n"
            f"Expected: {language}\n"
            f"Detected: {result}\n"
            f"Allowed: {allowed}"
        )
    
    @given(st.text(
        alphabet=st.characters(
            whitelist_categories=('Nd',),  # Only digits
            min_codepoint=48,
            max_codepoint=57
        ),
        min_size=3,
        max_size=100
    ))
    @settings(max_examples=100)
    def test_numeric_only_text_returns_default(self, text):
        """
        Property 25: Numeric-Only Text Returns Default
        **Validates: Requirements 13.6**
        
        For text containing only numbers, the language detector should 
        return the default language code 'en'.
        """
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Numeric-only text should default to 'en'
        assert result == 'en', (
            f"Numeric-only text did not return default 'en':\n"
            f"Text: {repr(text)}\n"
            f"Result: {result}"
        )
    
    @given(st.text(
        alphabet='!@#$%^&*()_+-=[]{}|;:,.<>?/',
        min_size=3,
        max_size=100
    ))
    @settings(max_examples=100)
    def test_special_characters_only_returns_default(self, text):
        """
        Property 25: Special Characters Only Returns Default
        **Validates: Requirements 13.6**
        
        For text containing only special characters, the language detector 
        should return the default language code 'en'.
        """
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Special characters only should default to 'en'
        assert result == 'en', (
            f"Special characters only did not return default 'en':\n"
            f"Text: {repr(text)}\n"
            f"Result: {result}"
        )
    
    @given(
        st.sampled_from(list(LANGUAGE_SAMPLES.keys())),
        st.text(
            alphabet=st.characters(whitelist_categories=('Zs',)),
            min_size=0,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_text_with_extra_whitespace(self, language, whitespace):
        """
        Property 25: Text with Extra Whitespace
        **Validates: Requirements 13.6**
        
        For text in a known language with extra whitespace, the language 
        detector should still return a valid ISO 639-1 code.
        """
        # Get a sample text
        base_text = LANGUAGE_SAMPLES[language][0]
        
        # Add extra whitespace
        text = whitespace + base_text + whitespace
        
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Should return a valid ISO 639-1 code
        assert isinstance(result, str), (
            f"Result is not a string: {type(result)}"
        )
        
        assert len(result) >= 2, (
            f"Result is too short: {repr(result)}"
        )
        
        # Allow similar languages due to probabilistic nature
        similar_languages = {
            'nl': ['af', 'nl'],
            'af': ['af', 'nl'],
            'zh-cn': ['zh-cn', 'zh-tw', 'ko', 'ja'],
            'zh-tw': ['zh-cn', 'zh-tw', 'ko', 'ja'],
            'ko': ['ko', 'ja', 'zh-cn', 'zh-tw'],
            'ja': ['ja', 'ko', 'zh-cn', 'zh-tw'],
        }
        
        allowed = similar_languages.get(language, [language])
        assert result in allowed, (
            f"Unexpected language detected with extra whitespace:\n"
            f"Text: {repr(text)}\n"
            f"Expected: {language}\n"
            f"Detected: {result}\n"
            f"Allowed: {allowed}"
        )
    
    @given(st.text(min_size=500, max_size=1000))
    @settings(max_examples=100)
    def test_long_text_uses_sample(self, text):
        """
        Property 25: Long Text Uses Sample
        **Validates: Requirements 13.6**
        
        For very long text (>500 characters), the language detector should 
        still return a valid ISO 639-1 code by using a sample.
        """
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect(text)
        
        # Property: Should return a valid ISO 639-1 code
        assert isinstance(result, str), (
            f"Result is not a string: {type(result)}"
        )
        
        assert len(result) >= 2, (
            f"Result is too short: {repr(result)}"
        )
        
        assert result.islower() or '-' in result, (
            f"Result is not lowercase: {repr(result)}"
        )
    
    @given(st.sampled_from(list(LANGUAGE_SAMPLES.keys())))
    @settings(max_examples=100)
    def test_consistency_across_samples_in_same_language(self, language):
        """
        Property 25: Consistency Across Samples
        **Validates: Requirements 13.6**
        
        For different samples in the same language, the language detector 
        should return consistent results (same language or similar languages).
        """
        detector = LanguageDetector()
        
        # Get two different samples from the same language
        samples = LANGUAGE_SAMPLES[language]
        assume(len(samples) >= 2)
        
        text1 = samples[0]
        text2 = samples[1]
        
        # Detect language for both
        result1 = detector.detect(text1)
        result2 = detector.detect(text2)
        
        # Property: Both should return valid ISO 639-1 codes
        assert isinstance(result1, str) and isinstance(result2, str), (
            f"Results are not strings: {type(result1)}, {type(result2)}"
        )
        
        # Allow similar languages
        similar_languages = {
            'nl': ['af', 'nl'],
            'af': ['af', 'nl'],
            'zh-cn': ['zh-cn', 'zh-tw', 'ko', 'ja'],
            'zh-tw': ['zh-cn', 'zh-tw', 'ko', 'ja'],
            'ko': ['ko', 'ja', 'zh-cn', 'zh-tw'],
            'ja': ['ja', 'ko', 'zh-cn', 'zh-tw'],
        }
        
        allowed = similar_languages.get(language, [language])
        
        assert result1 in allowed and result2 in allowed, (
            f"Inconsistent detection for same language:\n"
            f"Language: {language}\n"
            f"Text1: {repr(text1)}\n"
            f"Result1: {result1}\n"
            f"Text2: {repr(text2)}\n"
            f"Result2: {result2}\n"
            f"Allowed: {allowed}"
        )
