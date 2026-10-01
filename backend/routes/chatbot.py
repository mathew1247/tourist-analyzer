import json
import urllib.request
import urllib.error
from flask import Blueprint, request, jsonify
from backend.config import Config

chatbot_bp = Blueprint('chatbot', __name__)

GROQ_ENDPOINT = 'https://api.groq.com/openai/v1/chat/completions'

# Primary and fallback models known to be active on Groq
FALLBACK_MODELS = [
    Config.GROQ_MODEL,
    'openai/gpt-oss-120b',
    'openai/gpt-oss-20b',
    'qwen/qwen3.8-27b',
    'allam-2-7b'
]

def build_system_context(page_context=None):
    """Build platform-aware system prompt including key domain knowledge."""
    summary_stats = ""
    try:
        from backend.services.analytics_service import get_analytics_data
        data = get_analytics_data(year=2025)
        if data and 'summary' in data:
            s = data['summary']
            summary_stats = (
                f"\nPlatform Current Analytics Snapshot (2025):\n"
                f"- Total Recorded Visitors: {s.get('total_visitors', 'N/A'):,}\n"
                f"- Gross Tourism Revenue: ₹{s.get('total_revenue', 0):,.2f}\n"
                f"- Average Yield per Visitor: ₹{s.get('avg_revenue_per_visitor', 0):,.2f}\n"
                f"- Peak Season: {s.get('peak_month', 'October - December')}\n"
            )
    except Exception:
        # Fallback if DB connection is offline
        pass

    prompt = (
        "You are XploreAI, the intelligent copilot and data specialist for XploreElite — "
        "the enterprise Tourism Footfall & Revenue Analytics Platform.\n\n"
        "Your role:\n"
        "- Assist tourism administrators, destination managers, and company analysts with visitor trends, "
        "revenue insights, seasonal forecasting, peak analysis, and destination strategies.\n"
        "- Explain features of XploreElite: Dashboard (KPI cards & charts), Add Tourism Data (monthly records & Firestore sync), "
        "Records (tabular view & export), Analytics (category & monthly breakdown), Prediction (AI footfall & revenue forecasting), "
        "Reports (downloadable summaries), and Profile (system user settings).\n"
        "- When asked about travel trends or destination planning, provide expert, data-driven, practical recommendations.\n"
        "- Maintain a professional, encouraging, and executive tone. Use formatted markdown (bullet points, bold text, short paragraphs).\n"
    )

    if page_context:
        prompt += f"\nThe user is currently viewing the page: '{page_context}'. Tailor your advice to be relevant to this section if appropriate.\n"

    if summary_stats:
        prompt += summary_stats

    return prompt

@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chat():
    """
    Handle chat conversation requests.
    Expects JSON: { "message": "...", "history": [...], "page": "dashboard.html" }
    """
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get('message', '').strip()
        history = data.get('history', [])
        page_name = data.get('page', '')

        if not user_message and not history:
            return jsonify({'success': False, 'message': 'Message cannot be empty.'}), 400

        api_key = Config.GROQ_API_KEY
        if not api_key:
            return jsonify({'success': False, 'message': 'Groq API Key not configured on server.'}), 500

        # Construct messages payload with system prompt
        system_prompt = build_system_context(page_name)
        messages_payload = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history (last 10 turns max)
        for turn in history[-10:]:
            role = turn.get('role', 'user')
            content = turn.get('content', '')
            if role in ('user', 'assistant') and content:
                messages_payload.append({"role": role, "content": content})

        if user_message:
            # If user message not already appended in history
            if not history or history[-1].get('content') != user_message:
                messages_payload.append({"role": "user", "content": user_message})

        last_error = None
        # Deduplicate models list while keeping order
        models_to_try = list(dict.fromkeys(FALLBACK_MODELS))

        for model in models_to_try:
            try:
                body = json.dumps({
                    "model": model,
                    "messages": messages_payload,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }).encode('utf-8')

                req = urllib.request.Request(
                    GROQ_ENDPOINT,
                    data=body,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "XploreElite-Chatbot/1.0"
                    }
                )

                with urllib.request.urlopen(req, timeout=15) as res:
                    res_body = json.loads(res.read().decode('utf-8'))
                    choices = res_body.get('choices', [])
                    if choices:
                        reply_text = choices[0].get('message', {}).get('content', '')
                        return jsonify({
                            'success': True,
                            'reply': reply_text,
                            'model': model
                        }), 200

            except urllib.error.HTTPError as he:
                error_body = he.read().decode('utf-8', errors='ignore')
                last_error = f"HTTP {he.code}: {error_body}"
                # If model not found or forbidden, try next fallback model
                if he.code in (404, 400):
                    continue
                else:
                    break
            except Exception as e:
                last_error = str(e)
                continue

        return jsonify({
            'success': False,
            'message': f"AI processing error: {last_error or 'Unable to get response from Groq API.'}"
        }), 502

    except Exception as ex:
        return jsonify({'success': False, 'message': f"Server error: {str(ex)}"}), 500
