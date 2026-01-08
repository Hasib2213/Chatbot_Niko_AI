# Mobile App Support Chatbot

A FastAPI-based AI chatbot powered by Groq API that provides 24/7 support for a mobile application with features like wallet, marketplace, live streaming, and more.

## 🎯 Features

- **24/7 Availability**: Always available to help users
- **Multi-Language Support**: Responds in user's language (Bengali, English, etc.)
- **Comprehensive Knowledge Base**: Detailed guides for:
  - Wallet and payment systems
  - Marketplace with escrow protection
  - CAP (Capture Evidence) feature
  - Live streaming functionality
  - Profile customization and security
  - Parental controls (Guardian)
  - Safety and reporting features
  - Troubleshooting common issues
- **Real-time Error Handling**: Proper error messages and logging
- **Fast Responses**: Powered by Groq's fast LLM inference
- **REST API**: Easy integration with frontend applications

## 📋 Requirements

- Python 3.8+
- Groq API Key (Get from https://console.groq.com)
- FastAPI
- Uvicorn
- Pydantic
- python-dotenv

## 🚀 Quick Start

### 1. Clone or Download the Project
```bash
cd ChatbotAI
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.3-70b-versatile
TEMPERATURE=0.7
MAX_TOKENS=1000
```

**Get your API Key:**
1. Go to https://console.groq.com
2. Sign up or log in
3. Create an API key
4. Copy and paste it in `.env` file

### 5. Run the Application
```bash
# Option 1: Direct Python
python main.py

# Option 2: Using Uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at: `http://127.0.0.1:8000`

## 📚 API Endpoints

### Health Check
```bash
GET /health
```
**Response:**
```json
{
  "status": "ok",
  "model": "llama-3.3-70b-versatile"
}
```

### Generate Response
```bash
POST /api/generate
```

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How do I add money to my wallet?"
    }
  ],
  "user_id": "user123"
}
```

**Response:**
```json
{
  "response": "To add money:\n- Go to Wallet → + Add Credits\n- Choose amount ($10, $25, $50, $100, $250, $500 or custom)\n- Pay with card → Balance added instantly.",
  "success": true,
  "error": null
}
```

## 📁 Project Structure

```
ChatbotAI/
├── main.py              # FastAPI application and routes
├── ai_service.py        # Groq service integration
├── config.py            # Configuration settings
├── system_prompt.py     # Chatbot system prompt and app info
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── chatbot.log         # Application logs (auto-generated)
```

## 🔧 Configuration

Edit the `.env` file to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | Required |
| `MODEL` | LLM model name | `llama-3.3-70b-versatile` |
| `TEMPERATURE` | Response creativity (0-1) | `0.7` |
| `MAX_TOKENS` | Maximum response length | `1000` |

### Available Groq Models:
- `llama-3.3-70b-versatile` (Recommended)
- `llama-3.2-70b-text`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

## 📝 Example Requests

### Using cURL

**Health Check:**
```bash
curl http://127.0.0.1:8000/health
```

**Chat Request:**
```bash
curl -X POST 'http://127.0.0.1:8000/api/generate' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "role": "user",
      "content": "How do I start a live stream?"
    }
  ],
  "user_id": "user123"
}'
```

### Using Python

```python
import requests

url = "http://127.0.0.1:8000/api/generate"
payload = {
    "messages": [
        {
            "role": "user",
            "content": "How do I use the Marketplace?"
        }
    ],
    "user_id": "user123"
}

response = requests.post(url, json=payload)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
const response = await fetch('http://127.0.0.1:8000/api/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    messages: [
      {
        role: "user",
        content: "What is CAP feature?"
      }
    ],
    user_id: "user123"
  })
});

const data = await response.json();
console.log(data);
```

## 🐛 Troubleshooting

### API Key Error
**Error:** `"GROQ_API_KEY is not configured"`
- Solution: Check `.env` file has valid API key
- Verify at: https://console.groq.com

### Model Not Found
**Error:** `"The model 'xxx' has been decommissioned"`
- Solution: Update `MODEL` in `.env` to a supported model
- Check: https://console.groq.com/docs/models

### Port Already in Use
**Error:** `"Address already in use"`
- Solution: Use different port
  ```bash
  uvicorn main:app --reload --port 8001
  ```

### Connection Refused
**Error:** `"Connection refused"`
- Solution: Ensure uvicorn is running
- Check internet connection to Groq API

### Empty Response
**Error:** `"response": ""`
- Check `max_tokens` is not too small
- Verify message content is not empty
- Check API rate limits

## 📊 Supported Features

### Wallet & Payments
- Adding credits to wallet
- Sending money/tips to users
- Payout/withdrawal process

### Marketplace
- Buying with escrow protection
- Selling items
- Delivery proof submission
- Dispute resolution

### CAP (Capture Evidence)
- Step-by-step guide for recording
- Dual camera setup
- Metadata information
- Upload process

### Live Streaming
- Starting and ending streams
- Viewer interaction
- Tipping functionality
- Stream management

### Profile & Security
- Profile customization
- Privacy settings
- Biometric authentication
- Two-factor authentication

### Safety & Reporting
- Issue reporting
- SOS functionality
- Support tickets
- Safety tips

### Guardian (Parental Control)
- Child account setup
- App management
- Browser controls
- Time scheduling
- Activity monitoring

## 🔐 Security

- API keys are never committed (protected by `.gitignore`)
- Environment variables stored in `.env` (not in git)
- HTTPS support ready
- Input validation on all endpoints
- Error handling prevents information leakage

## 📈 Logging

Logs are saved to `chatbot.log`:
- Request/response logging
- Error tracking
- Service health monitoring
- Performance metrics

View logs:
```bash
tail -f chatbot.log
```

## 🤝 Support

For issues or questions:
- **App Support**: nikoo@app.com
- **API Issues**: Check `.gitignore` and `.env` configuration
- **Groq API Help**: https://console.groq.com/docs

## 📄 License

This project is for the Mobile App Support Platform.

## 🎓 Learning Resources

- FastAPI: https://fastapi.tiangolo.com
- Groq API: https://console.groq.com/docs
- Pydantic: https://docs.pydantic.dev
- Python: https://docs.python.org

## 📝 Version History

- **v1.0.0** (Jan 2026): Initial release
  - Groq API integration
  - Multi-language support
  - Comprehensive app documentation
  - Error handling and logging

## 🚀 Future Enhancements

- [ ] Database integration for chat history
- [ ] User authentication
- [ ] Rate limiting
- [ ] WebSocket support for real-time chat
- [ ] Admin dashboard
- [ ] Analytics tracking
- [ ] Multiple AI model support
- [ ] Conversation context persistence

---

**Happy Chatting! 🎉**
