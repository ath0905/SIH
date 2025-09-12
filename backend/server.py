from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import asyncio
import uuid
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Digital Krishi Officer API",
    description="Multi-agent system for agricultural support in Malayalam",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.krishi_officer

# Pydantic Models
class FarmerQuery(BaseModel):
    text: str = Field(..., description="Malayalam text from farmer")
    query_type: Optional[str] = Field("general", description="Type of query")
    location: Optional[str] = Field(None, description="Farm location")
    farmer_id: Optional[str] = Field(None, description="Farmer identifier")

class QueryResponse(BaseModel):
    id: str
    original_text: str
    translated_text: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    agent_responses: Dict[str, Any] = {}
    recommendations: List[str] = []
    timestamp: datetime
    status: str = "processing"

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "ml"
    target_lang: str = "en"

class TranslationResponse(BaseModel):
    success: bool
    original_text: str
    translated_text: Optional[str] = None
    error: Optional[str] = None

# Agent Classes
class QueryUnderstandingAgent:
    def __init__(self):
        self.agent_name = "Query Understanding Agent"
        self.llm_key = os.getenv("EMERGENT_LLM_KEY")
        
    async def analyze_query(self, text: str, translated_text: str) -> Dict[str, Any]:
        """Analyze farmer query to understand intent and extract information"""
        try:
            # Import here to avoid startup issues if library not installed
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            session_id = str(uuid.uuid4())
            system_message = """You are an agricultural expert AI that analyzes farmer queries. 
            Given a Malayalam farmer's query (and its English translation), analyze and extract:
            1. Intent: crop_query, pest_disease, weather, finance_scheme, market_info, general
            2. Crop mentioned (if any)
            3. Location context (if mentioned)
            4. Urgency level (1-5, 5 being emergency)
            5. Key agricultural concepts
            
            Respond only in JSON format with these fields:
            {
                "intent": "string",
                "crop": "string or null",
                "location": "string or null", 
                "urgency": number,
                "concepts": ["list of key concepts"],
                "confidence": number (0-1)
            }"""
            
            chat = LlmChat(
                api_key=self.llm_key,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-4o-mini")
            
            user_message = UserMessage(
                text=f"Malayalam Query: {text}\nEnglish Translation: {translated_text}\n\nAnalyze this agricultural query:"
            )
            
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # Fallback parsing
                return {
                    "intent": "general",
                    "crop": None,
                    "location": None,
                    "urgency": 3,
                    "concepts": [],
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Query analysis error: {str(e)}")
            return {
                "intent": "general",
                "crop": None,
                "location": None,
                "urgency": 3,
                "concepts": [],
                "confidence": 0.0,
                "error": str(e)
            }

class TranslationAgent:
    def __init__(self):
        self.agent_name = "Translation Agent"
        
    async def translate_malayalam(self, text: str) -> Dict[str, Any]:
        """Translate Malayalam to English - using Google Translate free tier"""
        try:
            # For now, implementing a simple keyword-based translation for common agricultural terms
            # This will be replaced with actual Google Translate API integration
            
            malayalam_to_english = {
                "നെല്ല്": "rice",
                "കപ്പ": "tapioca", 
                "തെങ്ങ്": "coconut",
                "കുരുമുളക്": "pepper",
                "ഏലം": "cardamom",
                "റബ്ബർ": "rubber",
                "പയർ": "beans",
                "വിത്ത്": "seed",
                "നടുക": "plant",
                "കൊയ്ത്ത്": "harvest",
                "വളം": "fertilizer",
                "രോഗം": "disease",
                "കീടം": "pest",
                "പുഴു": "worm",
                "മഴ": "rain",
                "വരൾച്ച": "drought",
                "എന്താണ്": "what is",
                "എങ്ങനെ": "how",
                "എപ്പോൾ": "when",
                "എവിടെ": "where",
                "സഹായം": "help",
                "ചികിത്സ": "treatment",
                "മരുന്ന്": "medicine"
            }
            
            # Simple translation by replacing known terms
            translated = text
            for malayalam, english in malayalam_to_english.items():
                translated = translated.replace(malayalam, english)
            
            # If no translation occurred, use a generic approach
            if translated == text:
                translated = f"Agricultural query: {text}"
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated,
                "method": "keyword_based"
            }
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return {
                "success": False,
                "original_text": text,
                "translated_text": None,
                "error": str(e)
            }

class AgricultureAdvisorAgent:
    def __init__(self):
        self.agent_name = "Agriculture Advisor Agent"
        self.llm_key = os.getenv("EMERGENT_LLM_KEY")
        
    async def provide_advice(self, query_analysis: Dict[str, Any], translated_text: str) -> Dict[str, Any]:
        """Provide agricultural advice based on query analysis"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            session_id = str(uuid.uuid4())
            system_message = """You are an expert agricultural advisor specializing in Kerala and South Indian farming practices. 
            Provide practical, actionable advice for farmers. Consider local climate, crops, and farming methods.
            
            Focus on:
            1. Organic and sustainable practices when possible
            2. Cost-effective solutions for small farmers
            3. Local resources and materials
            4. Seasonal considerations
            5. Traditional knowledge combined with modern techniques
            
            Keep advice simple, practical, and culturally appropriate for Malayalam-speaking farmers."""
            
            chat = LlmChat(
                api_key=self.llm_key,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-4o-mini")
            
            intent = query_analysis.get("intent", "general")
            crop = query_analysis.get("crop", "")
            urgency = query_analysis.get("urgency", 3)
            
            prompt = f"""
            Farmer's Query: {translated_text}
            Detected Intent: {intent}
            Crop: {crop or "Not specified"}
            Urgency Level: {urgency}/5
            
            Provide specific agricultural advice for this farmer's situation. Include:
            1. Immediate actions (if urgent)
            2. Practical solutions
            3. Resources needed
            4. Timeline for implementation
            5. Expected outcomes
            """
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {
                "success": True,
                "advice": response,
                "agent": self.agent_name,
                "intent_handled": intent
            }
            
        except Exception as e:
            logger.error(f"Agriculture advisor error: {str(e)}")
            return {
                "success": False,
                "advice": "Unable to provide advice at this time. Please try again later.",
                "error": str(e)
            }

class AgentOrchestrator:
    def __init__(self):
        self.translation_agent = TranslationAgent()
        self.query_agent = QueryUnderstandingAgent()
        self.advisor_agent = AgricultureAdvisorAgent()
        
    async def process_farmer_query(self, query: FarmerQuery) -> QueryResponse:
        """Process farmer query through multiple agents"""
        query_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        # Store initial query
        query_doc = {
            "id": query_id,
            "original_text": query.text,
            "query_type": query.query_type,
            "location": query.location,
            "farmer_id": query.farmer_id,
            "timestamp": timestamp,
            "status": "processing"
        }
        
        try:
            await db.queries.insert_one(query_doc)
            
            # Step 1: Translate Malayalam to English
            translation_result = await self.translation_agent.translate_malayalam(query.text)
            translated_text = translation_result.get("translated_text", query.text)
            
            # Step 2: Analyze query intent
            query_analysis = await self.query_agent.analyze_query(query.text, translated_text)
            
            # Step 3: Get agricultural advice
            advice_result = await self.advisor_agent.provide_advice(query_analysis, translated_text)
            
            # Compile response
            agent_responses = {
                "translation": translation_result,
                "analysis": query_analysis,
                "advice": advice_result
            }
            
            # Extract recommendations
            recommendations = []
            if advice_result.get("success"):
                recommendations.append(advice_result.get("advice", ""))
            
            # Update database
            update_doc = {
                "translated_text": translated_text,
                "intent": query_analysis.get("intent"),
                "confidence": query_analysis.get("confidence"),
                "agent_responses": agent_responses,
                "recommendations": recommendations,
                "status": "completed"
            }
            
            await db.queries.update_one(
                {"id": query_id},
                {"$set": update_doc}
            )
            
            return QueryResponse(
                id=query_id,
                original_text=query.text,
                translated_text=translated_text,
                intent=query_analysis.get("intent"),
                confidence=query_analysis.get("confidence"),
                agent_responses=agent_responses,
                recommendations=recommendations,
                timestamp=timestamp,
                status="completed"
            )
            
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            
            # Update status to error
            await db.queries.update_one(
                {"id": query_id},
                {"$set": {"status": "error", "error": str(e)}}
            )
            
            return QueryResponse(
                id=query_id,
                original_text=query.text,
                timestamp=timestamp,
                status="error"
            )

# Initialize orchestrator
orchestrator = AgentOrchestrator()

# API Endpoints
@app.post("/api/farmer-query", response_model=QueryResponse)
async def process_farmer_query(query: FarmerQuery):
    """Process a farmer's query through the multi-agent system"""
    try:
        response = await orchestrator.process_farmer_query(query)
        return response
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )

@app.post("/api/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Direct translation endpoint"""
    try:
        translation_agent = TranslationAgent()
        result = await translation_agent.translate_malayalam(request.text)
        
        return TranslationResponse(
            success=result["success"],
            original_text=result["original_text"],
            translated_text=result.get("translated_text"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Translation API error: {str(e)}")
        return TranslationResponse(
            success=False,
            original_text=request.text,
            error=str(e)
        )

@app.get("/api/queries/{query_id}")
async def get_query(query_id: str):
    """Get query by ID"""
    try:
        query = await db.queries.find_one({"id": query_id})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Remove MongoDB _id field
        query.pop("_id", None)
        return query
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving query: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Digital Krishi Officer API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": {
            "translation": "active",
            "query_understanding": "active", 
            "agriculture_advisor": "active"
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Digital Krishi Officer - Multi-Agent Agricultural Support System",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)