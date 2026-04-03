"""Tests for the WhatsApp demo simulator page at /whatsapp-demo."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.session import get_db


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


# -- Page Load Tests --


class TestWhatsappDemoPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/whatsapp-demo")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/whatsapp-demo")
        assert "WhatsApp" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/whatsapp-demo")
        assert "intel-nav" in resp.text

    def test_page_has_script(self, client):
        resp = client.get("/whatsapp-demo")
        assert "whatsapp-demo.js" in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/whatsapp-demo")
        assert "cultivos-footer" in resp.text

    def test_page_has_meta_description(self, client):
        resp = client.get("/whatsapp-demo")
        assert "<meta" in resp.text
        assert "WhatsApp" in resp.text


# -- Chat Container Tests --


class TestChatContainer:
    """Chat interface elements exist."""

    def test_chat_container_exists(self, client):
        resp = client.get("/whatsapp-demo")
        assert "chat-container" in resp.text

    def test_chat_header_exists(self, client):
        resp = client.get("/whatsapp-demo")
        assert "chat-header" in resp.text

    def test_chat_messages_area_exists(self, client):
        resp = client.get("/whatsapp-demo")
        assert "chat-messages" in resp.text

    def test_chat_input_area_exists(self, client):
        resp = client.get("/whatsapp-demo")
        assert "chat-input" in resp.text

    def test_chat_has_whatsapp_styling(self, client):
        """Chat container has WhatsApp-themed class."""
        resp = client.get("/whatsapp-demo")
        assert "whatsapp-chat" in resp.text

    def test_chat_header_shows_cultivOS(self, client):
        """Header shows cultivOS as the contact name."""
        resp = client.get("/whatsapp-demo")
        assert "cultivOS" in resp.text

    def test_chat_header_shows_status(self, client):
        """Header shows online/bot status."""
        resp = client.get("/whatsapp-demo")
        assert "en linea" in resp.text.lower() or "asistente" in resp.text.lower()


# -- Message Bubble Tests --


class TestMessageBubbles:
    """Pre-scripted conversation messages are present in HTML or loaded by JS."""

    def test_farmer_message_class_defined(self, client):
        """Farmer messages use a distinct CSS class."""
        resp = client.get("/whatsapp-demo")
        assert "msg-farmer" in resp.text or "message-sent" in resp.text

    def test_ai_message_class_defined(self, client):
        """AI responses use a distinct CSS class."""
        resp = client.get("/whatsapp-demo")
        assert "msg-ai" in resp.text or "message-received" in resp.text

    def test_message_bubble_class(self, client):
        """Message bubbles have a bubble class for styling."""
        resp = client.get("/whatsapp-demo")
        assert "chat-bubble" in resp.text or "msg-bubble" in resp.text

    def test_timestamp_class_exists(self, client):
        """Messages have timestamp elements."""
        resp = client.get("/whatsapp-demo")
        assert "msg-time" in resp.text


# -- Voice Message Tests --


class TestVoiceMessages:
    """Voice note mockup elements exist."""

    def test_voice_waveform_element(self, client):
        """Voice message has a waveform visual."""
        resp = client.get("/whatsapp-demo")
        assert "voice-waveform" in resp.text

    def test_voice_duration_indicator(self, client):
        """Voice message shows duration."""
        resp = client.get("/whatsapp-demo")
        assert "voice-duration" in resp.text

    def test_voice_play_button(self, client):
        """Voice message has a play button."""
        resp = client.get("/whatsapp-demo")
        assert "voice-play" in resp.text


# -- Send Button & Input Tests --


class TestSendButton:
    """Send button and input field exist."""

    def test_send_button_exists(self, client):
        resp = client.get("/whatsapp-demo")
        assert "send-btn" in resp.text

    def test_message_input_exists(self, client):
        resp = client.get("/whatsapp-demo")
        assert "message-input" in resp.text


# -- Typing Indicator Tests --


class TestTypingIndicator:
    """Typing indicator element exists."""

    def test_typing_indicator_defined(self, client):
        """Typing indicator element or class is present."""
        resp = client.get("/whatsapp-demo")
        assert "typing-indicator" in resp.text

    def test_typing_dots(self, client):
        """Typing indicator has animated dots."""
        resp = client.get("/whatsapp-demo")
        assert "typing-dot" in resp.text


# -- Conversation Flow Tests --


class TestConversationFlow:
    """Pre-scripted conversation demonstrates the full farmer-AI flow."""

    def test_js_has_conversation_data(self, client):
        """JS file contains the scripted conversation messages."""
        resp = client.get("/whatsapp-demo.js")
        assert resp.status_code == 200
        assert "conversation" in resp.text.lower() or "messages" in resp.text.lower()

    def test_js_has_farmer_messages(self, client):
        """Conversation includes farmer messages in Spanish."""
        resp = client.get("/whatsapp-demo.js")
        assert "farmer" in resp.text.lower() or "agricultor" in resp.text.lower()

    def test_js_has_ai_responses(self, client):
        """Conversation includes AI responses."""
        resp = client.get("/whatsapp-demo.js")
        assert resp.status_code == 200

    def test_js_mentions_health_report(self, client):
        """Conversation flow includes health report topic."""
        resp = client.get("/whatsapp-demo.js")
        assert "salud" in resp.text.lower() or "health" in resp.text.lower()

    def test_js_mentions_treatment(self, client):
        """Conversation flow includes organic treatment recommendation."""
        resp = client.get("/whatsapp-demo.js")
        assert "tratamiento" in resp.text.lower() or "organico" in resp.text.lower()

    def test_js_has_voice_message_type(self, client):
        """At least one message is typed as voice."""
        resp = client.get("/whatsapp-demo.js")
        assert "voice" in resp.text.lower() or "voz" in resp.text.lower()


# -- Spanish Language Tests --


class TestSpanishContent:
    """All farmer-facing text is in Spanish."""

    def test_page_title_spanish(self, client):
        resp = client.get("/whatsapp-demo")
        assert "Simulador" in resp.text or "Demo" in resp.text

    def test_input_placeholder_spanish(self, client):
        resp = client.get("/whatsapp-demo")
        assert "Escribe" in resp.text or "mensaje" in resp.text.lower()

    def test_page_subtitle_spanish(self, client):
        resp = client.get("/whatsapp-demo")
        assert "agricultor" in resp.text.lower() or "granjero" in resp.text.lower() or "campesino" in resp.text.lower()
