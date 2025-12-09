
# ########################################################################################

# #Final Code

# ########################################################################################

# import os
# import logging
# import psycopg2
# import threading
# import json
# import re
# import requests
# import traceback
# from concurrent.futures import ThreadPoolExecutor
# from psycopg2 import pool
# from psycopg2.extras import RealDictCursor
# from datetime import datetime, timedelta, date
# from flask import Flask, request
# import openai
# from twilio.rest import Client as TwilioClient 
# from twilio.twiml.messaging_response import MessagingResponse 
# from dotenv import load_dotenv
# from typing import List, Dict, Any, Optional

# # 1. Load Environment Variables
# load_dotenv()

# app = Flask(__name__)

# # --- CONFIGURATION ---
# DB_URI = os.getenv("DATABASE_URL")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# openai.api_key = OPENAI_API_KEY

# TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") 

# # Milvus Configuration
# MILVUS_ENDPOINT = os.getenv("MILVUS_ENDPOINT")
# MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")

# # Initialize OpenAI client for embeddings
# from openai import OpenAI
# client = OpenAI(api_key=OPENAI_API_KEY)

# # Try to import Milvus, but don't fail if not available
# try:
#     from pymilvus import connections, Collection, utility
#     MILVUS_AVAILABLE = True
# except ImportError:
#     MILVUS_AVAILABLE = False
#     print("⚠️ pymilvus not installed. Install with: pip install pymilvus")

# # Initialize Twilio Client
# twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# # Logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # --- GLOBAL THREAD POOL ---
# executor = ThreadPoolExecutor(max_workers=5) 

# # --- DATABASE POOL ---
# try:
#     postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(
#         1, 50, DB_URI, cursor_factory=RealDictCursor, connect_timeout=10
#     )
#     print("✅ Database Connection Pool Created")
# except (Exception, psycopg2.DatabaseError) as error:
#     print("❌ Error connecting to PostgreSQL", error)

# # ==============================================================================
# # 🚀 DIRECT MILVUS RAG EVENT RETRIEVAL (EMBEDDED)
# # ==============================================================================

# # Initialize Milvus if available
# milvus_collection = None
# if MILVUS_AVAILABLE and MILVUS_ENDPOINT and MILVUS_TOKEN:
#     try:
#         connections.connect(uri=MILVUS_ENDPOINT, token=MILVUS_TOKEN)
#         COLLECTION_NAME = "events"
#         if utility.has_collection(COLLECTION_NAME):
#             milvus_collection = Collection(COLLECTION_NAME)
#             milvus_collection.load()
#             logger.info("✅ Milvus connected and collection loaded")
#         else:
#             logger.warning("⚠️ Milvus collection 'events' not found")
#     except Exception as e:
#         logger.error(f"❌ Error connecting to Milvus: {e}")
#         milvus_collection = None
# else:
#     logger.warning("⚠️ Milvus not configured or unavailable")

# def create_embedding(text: str) -> List[float]:
#     """Create embedding for a single text"""
#     try:
#         response = client.embeddings.create(
#             model="text-embedding-3-small",
#             input=text
#         )
#         return response.data[0].embedding
#     except Exception as e:
#         logger.error(f"❌ Error creating embedding: {e}")
#         return []

# def get_date_context() -> Dict[str, str]:
#     """Generate current date context"""
#     now = datetime.now()
#     today = now.date()
    
#     tomorrow = today + timedelta(days=1)
#     yesterday = today - timedelta(days=1)
    
#     # Calculate this week's dates
#     days_until_monday = (today.weekday() - 0) % 7  # Monday is 0
#     this_monday = today - timedelta(days=days_until_monday)
#     this_sunday = this_monday + timedelta(days=6)
    
#     # Calculate next week's dates
#     next_monday = this_monday + timedelta(days=7)
#     next_sunday = next_monday + timedelta(days=6)
    
#     # Calculate weekends
#     days_until_friday = (4 - today.weekday()) % 7
#     this_friday = today + timedelta(days=days_until_friday)
#     this_saturday = this_friday + timedelta(days=1)
#     this_weekend_sunday = this_friday + timedelta(days=2)
    
#     next_friday = this_friday + timedelta(days=7)
#     next_saturday = next_friday + timedelta(days=1)
#     next_weekend_sunday = next_friday + timedelta(days=2)
    
#     return {
#         "today": today.strftime("%Y-%m-%d, %A"),
#         "tomorrow": tomorrow.strftime("%Y-%m-%d, %A"),
#         "yesterday": yesterday.strftime("%Y-%m-%d, %A"),
#         "this_week_start": this_monday.strftime("%Y-%m-%d"),
#         "this_week_end": this_sunday.strftime("%Y-%m-%d"),
#         "next_week_start": next_monday.strftime("%Y-%m-%d"),
#         "next_week_end": next_sunday.strftime("%Y-%m-%d"),
#         "this_weekend_start": this_friday.strftime("%Y-%m-%d"),
#         "this_weekend_middle": this_saturday.strftime("%Y-%m-%d"),
#         "this_weekend_end": this_weekend_sunday.strftime("%Y-%m-%d"),
#         "next_weekend_start": next_friday.strftime("%Y-%m-%d"),
#         "next_weekend_middle": next_saturday.strftime("%Y-%m-%d"),
#         "next_weekend_end": next_weekend_sunday.strftime("%Y-%m-%d"),
#         "current_date_iso": today.strftime("%Y-%m-%d"),
#         "current_day_name": today.strftime("%A"),
#         "current_week_number": today.strftime("%W")
#     }

# def extract_event_fields(event_data: Dict, metadata: Dict) -> Dict:
#     """Extract and merge all relevant fields from event data and metadata"""
#     merged = {}
#     merged.update(event_data)
#     merged.update(metadata)
    
#     result = {
#         "title": merged.get("title") or merged.get("name") or "Untitled Event",
#         "description": merged.get("description") or merged.get("details") or merged.get("summary") or "",
#         "event_date": merged.get("event_date") or merged.get("date") or "Date not specified",
#         "mood": merged.get("mood"),
#         "music_type": merged.get("music_type") or merged.get("genre") or merged.get("music_genre"),
#         "location": merged.get("location") or merged.get("venue") or merged.get("address") or "",
#         "address": merged.get("address") or merged.get("venue_address") or "",
#         "price": merged.get("price") or merged.get("ticket_price") or "",
#         "recurring_day": merged.get("recurring_day") or merged.get("recurring") or merged.get("day"),
#         "image_url": merged.get("image_url") or merged.get("photo_url") or merged.get("image") or merged.get("photo"),
#         "instagram_link": merged.get("instagram_link") or merged.get("instagram") or merged.get("instagram_url"),
#         "organizer": merged.get("organizer") or merged.get("host"),
#         "capacity": merged.get("capacity"),
#         "age_restriction": merged.get("age_restriction") or merged.get("age_limit"),
#     }
    
#     return result

# def search_milvus_events(query_embedding: List[float], limit: int = 25) -> List[Dict]:
#     """Search for similar events in Milvus"""
#     if not milvus_collection:
#         return []
    
#     try:
#         search_params = {
#             "data": [query_embedding],
#             "anns_field": "embedding",
#             "param": {"metric_type": "COSINE", "params": {"nprobe": 10}},
#             "limit": limit,
#             "output_fields": ["id", "title", "text", "metadata"]
#         }
        
#         results = milvus_collection.search(**search_params)
        
#         events = []
#         for hits in results:
#             for hit in hits:
#                 try:
#                     event_data = json.loads(hit.entity.get("text", "{}"))
#                     metadata_str = hit.entity.get("metadata", "{}")
                    
#                     if isinstance(metadata_str, str):
#                         try:
#                             metadata = json.loads(metadata_str)
#                         except json.JSONDecodeError:
#                             metadata = {}
#                     else:
#                         metadata = metadata_str or {}
                    
#                     event = extract_event_fields(event_data, metadata)
#                     event["similarity_score"] = float(hit.score)
                    
#                     events.append(event)
#                 except Exception as e:
#                     logger.error(f"Error processing hit: {e}")
#                     continue
        
#         return events
#     except Exception as e:
#         logger.error(f"Milvus search error: {e}")
#         return []

# def llm_filter_events(query: str, events: List[Dict], date_context: Dict) -> List[Dict]:
#     """Use LLM to filter and format recommendations"""
#     if not events:
#         return []
    
#     try:
#         events_context = []
#         for i, event in enumerate(events):
#             events_context.append(f"""
# Event {i+1} (Similarity: {event.get('similarity_score', 0):.3f}):
# Title: {event.get('title', 'N/A')}
# Description: {event.get('description', '')}
# Date: {event.get('event_date', 'N/A')}
# Recurring Day: {event.get('recurring_day', 'None')}
# Music Type: {event.get('music_type', '')}
# Mood: {event.get('mood', '')}
# Location: {event.get('location', '')}
# Image URL: {event.get('image_url', '')}
# Instagram: {event.get('instagram_link', '')}
# """)
        
#         prompt = f"""
# # TASK: Recommend relevant events based on user query

# ## DATE CONTEXT:
# - TODAY: {date_context['today']}
# - TOMORROW: {date_context['tomorrow']}
# - THIS WEEK: {date_context['this_week_start']} to {date_context['this_week_end']}
# - NEXT WEEK: {date_context['next_week_start']} to {date_context['next_week_end']}
# - THIS WEEKEND: {date_context['this_weekend_start']} (Friday) to {date_context['this_weekend_end']} (Sunday)
# - NEXT WEEKEND: {date_context['next_weekend_start']} (Friday) to {date_context['next_weekend_end']} (Sunday)

# ## USER QUERY:
# "{query}"

# ## AVAILABLE EVENTS:
# {chr(10).join(events_context)}

# ## INSTRUCTIONS:
# 1. Select only the most relevant events for the user query.
# 2. Prioritize events that match the date/time context from the user query.
# 3. **CRITICAL: For recurring events, ALWAYS include the 'recurring_day' field in your response.**
# 4. When user asks for "this week" or "next week", include recurring events that happen on weekdays within that week.
# 5. When user asks for "weekend" events, include recurring events that happen on Saturday or Sunday.
# 6. **If an event has a 'recurring_day', include it in your response even if it also has a specific date.**

# Return ONLY a JSON array with this structure:
# [
#   {{
#     "title": "string",
#     "description": "string",
#     "event_date": "string",
#     "recurring_day": "string or null",  # IMPORTANT: Include if available in event data
#     "mood": "string or null",
#     "music_type": "string or null",
#     "image_url": "string or null",
#     "instagram_link": "string or null"
#   }}
# ]

# ## EXAMPLES OF PROPER RECURRING EVENT HANDLING:
# - If event shows "Recurring Day: Friday" and user asks "events this week", include it with "recurring_day": "Friday"
# - If event shows "Recurring Day: Saturday" and user asks "weekend events", include it with "recurring_day": "Saturday"
# - If event shows both "Date: 2024-12-20" and "Recurring Day: Friday", include both fields

# IMPORTANT: Include image_url and instagram_link if available in event data.
# """

#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are an event recommendation expert. Always include recurring_day if present in event data. Return ONLY valid JSON."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.0,
#             max_tokens=2000,
#             response_format={"type": "json_object"}
#         )
        
#         content = response.choices[0].message.content.strip()
#         data = json.loads(content)
#         recommendations = data.get("recommendations", data.get("events", []))
        
#         if not isinstance(recommendations, list):
#             return events[:5]  # Fallback to top 5 events
        
#         validated_recommendations = []
#         for rec in recommendations:
#             cleaned_rec = {
#                 "title": rec.get("title") or "Untitled Event",
#                 "description": rec.get("description") or "",
#                 "event_date": rec.get("event_date") or "Date not specified",
#                 "recurring_day": rec.get("recurring_day"),
#                 "mood": rec.get("mood"),
#                 "music_type": rec.get("music_type"),
#                 "image_url": rec.get("image_url"),
#                 "instagram_link": rec.get("instagram_link")
#             }
#             validated_recommendations.append(cleaned_rec)
        
#         return validated_recommendations[:6]
        
#     except Exception as e:
#         logger.error(f"LLM filtering error: {e}")
#         return events[:6]

# def build_milvus_query(user_query: str, ai_data: Dict) -> str:
#     """
#     Enhance user query with AI analysis for better Milvus retrieval
#     """
#     date_range = ai_data.get('date_range') or {}
#     category = ai_data.get('category')
#     target_mood = ai_data.get('target_mood')
#     social_context = ai_data.get('social_context')
    
#     # SAFE extraction with default empty lists
#     specific_keywords = ai_data.get('specific_keywords')
#     inferred_keywords = ai_data.get('inferred_keywords')
    
#     # Ensure they are lists
#     if specific_keywords is None:
#         specific_keywords = []
#     if inferred_keywords is None:
#         inferred_keywords = []
    
#     query_parts = [user_query]
    
#     # Add date context if available
#     if date_range and isinstance(date_range, dict):
#         start_date = date_range.get('start')
#         if start_date:
#             end_date = date_range.get('end', start_date)
#             if start_date == end_date:
#                 query_parts.append(f"on {start_date}")
#             else:
#                 query_parts.append(f"from {start_date} to {end_date}")
    
#     # Add mood context
#     if target_mood and isinstance(target_mood, str):
#         query_parts.append(f"{target_mood} vibe")
    
#     # Add category context
#     if category and isinstance(category, str):
#         query_parts.append(f"{category} events")
    
#     # Add social context
#     if social_context and isinstance(social_context, str):
#         social_context_map = {
#             'date': 'romantic date night',
#             'friends': 'with friends',
#             'solo': 'solo',
#             'family': 'family friendly',
#             'business': 'business networking'
#         }
#         social_text = social_context_map.get(social_context, social_context)
#         if social_text:
#             query_parts.append(social_text)
    
#     # Add keywords - SAFE CONCATENATION
#     all_keywords = []
#     if specific_keywords and isinstance(specific_keywords, list):
#         all_keywords.extend([k for k in specific_keywords if isinstance(k, str)])
#     if inferred_keywords and isinstance(inferred_keywords, list):
#         all_keywords.extend([k for k in inferred_keywords if isinstance(k, str)])
    
#     # Clean keywords
#     all_keywords = [k.strip() for k in all_keywords if k and len(str(k).strip()) > 2]
#     if all_keywords:
#         unique_keywords = list(set(all_keywords))
#         query_parts.append(" ".join(unique_keywords))
    
#     enhanced_query = " ".join(query_parts)
#     logger.info(f"🔍 Enhanced query for Milvus: {enhanced_query}")
    
#     return enhanced_query

# def retrieve_events_direct(user_query: str, ai_data: Dict, user_language: str = 'en') -> List[Dict]:
#     """
#     Direct Milvus RAG event retrieval embedded in main code
#     """
#     try:
#         # Check if Milvus is available
#         if not milvus_collection:
#             logger.info("⚠️ Milvus not available - skipping RAG retrieval")
#             return []
        
#         # Build enhanced query with safe handling
#         try:
#             enhanced_query = build_milvus_query(user_query, ai_data)
#         except Exception as e:
#             logger.error(f"❌ Error building Milvus query: {e}")
#             enhanced_query = user_query  # Fallback to original query
        
#         logger.info(f"🔍 Direct Milvus search with query: {enhanced_query}")
        
#         # Create embedding
#         query_embedding = create_embedding(enhanced_query)
#         if not query_embedding:
#             logger.error("❌ Failed to create embedding")
#             return []
        
#         # Search in Milvus
#         raw_events = search_milvus_events(query_embedding, limit=25)
#         logger.info(f"✅ Found {len(raw_events)} potential events in Milvus")
        
#         if not raw_events:
#             return []
        
#         # Get date context
#         date_context = get_date_context()
        
#         # Use LLM to filter and format
#         recommendations = llm_filter_events(user_query, raw_events, date_context)
#         logger.info(f"✅ LLM filtered to {len(recommendations)} events")
        
#         # Check if recommendations have recurring_day
#         for i, rec in enumerate(recommendations):
#             if rec.get('recurring_day'):
#                 logger.info(f"🔁 Event {i+1} has recurring_day: {rec.get('recurring_day')}")
        
#         # Convert to expected format
#         formatted_events = []
#         for event in recommendations:
#             if not isinstance(event, dict):
#                 continue
            
#             # Try to find matching original event to get location if missing
#             location = event.get('location', '')
#             if not location:
#                 # Find matching event in raw_events by title
#                 for raw_event in raw_events:
#                     if raw_event.get('title') == event.get('title'):
#                         location = raw_event.get('location', '')
#                         break
            
#             # Extract recurring_day - ensure it's included
#             recurring_day = event.get('recurring_day')
#             if recurring_day:
#                 logger.info(f"📅 Including recurring event: {event.get('title')} on {recurring_day}")
            
#             formatted_event = {
#                 'title': event.get('title', 'Untitled Event'),
#                 'description': event.get('description', ''),
#                 'event_date': event.get('event_date', 'Date not specified'),
#                 'mood': event.get('mood'),
#                 'music_type': event.get('music_type'),
#                 'location': location,
#                 'event_time': '',  # Milvus might not have this
#                 'recurring_day': recurring_day,  # This should now be included
#                 'ticket_link': '',  # Milvus might not have this
#                 'instagram_link': event.get('instagram_link'),
#                 'image_url': event.get('image_url'),
#                 'category': 'event'
#             }
#             formatted_events.append(formatted_event)
        
#         logger.info(f"📊 Final formatted events: {len(formatted_events)}")
#         for i, ev in enumerate(formatted_events):
#             if ev.get('recurring_day'):
#                 logger.info(f"   Event {i+1}: {ev.get('title')} - Recurring: {ev.get('recurring_day')}")
        
#         return formatted_events
        
#     except Exception as e:
#         logger.error(f"❌ Direct Milvus retrieval error: {e}")
#         traceback.print_exc()
#         return []

# # ==============================================================================
# # 🧠 ENHANCED AI & UTILS (UNCHANGED - KEEP YOUR EXISTING CODE)
# # ==============================================================================

# def analyze_user_intent(user_text):
#     """
#     UPDATED: Added 'is_out_of_scope' detection + reduced temperature for consistency
#     """
#     today_str = date.today().strftime("%Y-%m-%d")
#     weekday_str = date.today().strftime("%A")
#     tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
#     system_prompt = (
#         f"Current Date: {today_str} ({weekday_str}). Tomorrow is: {tomorrow_str}. "
#         "You are a multilingual AI that understands ALL languages (English, Spanish, Portuguese, French, German, Italian, Russian, Arabic, Hebrew, Hindi, Telugu, Tamil, Chinese, Japanese, Korean, and ALL others). "
#         "Your job is to analyze a user's request for events or businesses in Buenos Aires and extract structured data."
#         "Withou user asking anythin do not give the recommendations "
#         "EXTRACT THE FOLLOWING (return as JSON):\n"
        
#         "1. 'is_greeting': boolean (true ONLY if message is JUST 'hi', 'hello', 'hola', 'hey', 'salut', 'ciao', 'नमस्ते', 'నమస్కారం', '你好', 'こんにちは', '안녕하세요' etc. with ABSOLUTELY NO OTHER REQUEST. If user says 'hi' AND asks for anything else, return FALSE)\n"
#         "   Examples:\n"
#         "   - 'hi' → is_greeting: true ✅\n"
#         "   - 'hello' → is_greeting: true ✅\n"
#         "   - 'hi any events on Dec 6' → is_greeting: FALSE ❌ (has request!)\n"
#         "   - 'hello where can I find bars' → is_greeting: FALSE ❌ (has request!)\n"
#         "   - 'hey whats up' → is_greeting: True \n-"
        
#         "2. 'is_identity_question': boolean. \n"
#         "   - TRUE ONLY if user asks about THEIR OWN identity: 'Who am I?', 'Do you know me?', 'What is my name?' - Any language \n"
#         "   - FALSE if user asks about YOUR identity: 'Who are you?', 'What is your name?'. (This goes to general chat) - Any language \n"
        
#         "3. 'wants_to_upload': boolean. CRITICAL - Detect this intent in ANY language:\n"
#         "   True if user expresses intent to:\n"
#         "   - Upload/Submit/Add/Post/Share/Promote an event\n"
#         "   - Recommend their own event/party/venue/business\n"
#         "   - List their event or ask how to add/submit it\n"
#         "   - Say 'I have an event', 'I'm organizing', 'I want to promote', 'I want to list'\n"
#         "   Examples across languages:\n"
#         "   - English: 'upload event', 'add my party', 'how can I submit', 'I want to recommend my event'\n"
#         "   - Spanish: 'subir evento', 'agregar mi fiesta', 'cómo puedo enviar', 'quiero recomendar'\n"
#         "   - Portuguese: 'enviar evento', 'adicionar minha festa', 'quero recomendar'\n"
#         "   - French: 'ajouter événement', 'télécharger mon événement', 'je veux recommender'\n"
#         "   - German: 'Veranstaltung hochladen', 'meine Party hinzufügen', 'ich möchte empfehlen'\n"
#         "   - Italian: 'caricare evento', 'aggiungere la minha festa', 'voglio raccomandare'\n"
#         "   - Russian: 'загрузить событие', 'добавить мою вечеринку', 'я хочу порекомендовать'\n"
#         "   - Arabic: 'إضافة حدث', 'رفع حدثي', 'كيف أضيف', 'أريد أن أوصي'\n"
#         "   - Hebrew: 'להעלות אירוע', 'להוסיף את המסיבה שלי', 'אני רוצה להמליץ'\n"
#         "   - Hindi: 'इवेंट अपलोड करें', 'मेरी पार्टी जोड़ें', 'मैं सिफारिश करना चाहता हूं'\n"
#         "   - Telugu: 'ఈవెంట్ అప్‌లోడ్ చేయండి', 'నా పార్టీని జోడించండి', 'నేను సిఫార్సు చేయాలనుకుంటున్నాను'\n"
#         "   - Chinese: '上传活动', '添加我的派对', '如何提交', '我想推荐'\n"
#         "   - Japanese: 'イベントをアップロード', 'パーティーを追加', '推薦したい'\n"
#         "   - Korean: 'イベント 업로드', '내 파티 추가', '제출 방법', '추천하고 싶어요'\n"
#         "   ANY similar phrase in ANY language should return true.\n"

#         "4. 'is_out_of_scope': boolean. **FOLLOW THIS EXACT PROCESS:**\n"
#         "   \n"
#         "   **STEP 1 - CHECK FOR ENTERTAINMENT KEYWORDS (if ANY found → return FALSE immediately):**\n"
#         "   Look for these words in the user's message (in ANY language):\n"
#         "   - Drinking: drink, drinks, bar, pub, cocktail, beer, wine, alcohol\n"
#         "   - Eating: eat, food, restaurant, cafe, coffee, dinner, lunch, brunch\n"
#         "   - Nightlife: club, party, dance, DJ, nightlife, night out\n"
#         "   - Events: event, concert, show, festival, happening, tonight, today\n"
#         "   - Entertainment: music, live, theater, cinema, movie, museum, gallery\n"
#         "   - IF user asks about: Eating, Drinking, Nightlife, Clubbing, Events, Art, Theater -> FALSE (In Scope)\n"
#         "   - IF user asks about: Social Groups, Women Communities, Meetups, Expats -> FALSE (In Scope)\n"
#         "   - IF user asks about: Buying items, Doctors, Real Estate, Jobs, Repairs -> TRUE (Out of Scope)\n"
#         "   - Example: 'Where can I adopt a dog?' -> TRUE (Out of Scope)\n"
#         "   - Example: 'Women communities' -> FALSE (In Scope)\n"
#         "   \n"
#         "   **IF ANY OF THESE WORDS APPEAR → IMMEDIATELY RETURN FALSE (in scope)**\n"
#         "   Do not analyze grammar or context. Just check if the word exists.\n"
#         "   \n"
#         "   Examples:\n"
#         "   - 'Where do i drink question' → contains 'drink' → FALSE ✅\n"
#         "   - 'drink' → contains 'drink' → FALSE ✅\n"
#         "   - 'bar question' → contains 'bar' → FALSE ✅\n"
#         "   - 'eat where' → contains 'eat' → FALSE ✅\n"
#         "   - 'event?' → contains 'event' → FALSE ✅\n"
#         "   \n"
#         "   **STEP 2 - IF NO ENTERTAINMENT KEYWORDS, CHECK IF OUT OF SCOPE:**\n"
#         "   Only return TRUE if asking about:\n"
#         "   - Shopping: buy, purchase, shop, store, mall, electronics\n"
#         "   - Services: doctor, hospital, dentist, lawyer, veterinarian, haircut\n"
#         "   - Transport: bus, taxi, uber, train, airport\n"
#         "   - Utilities: bills, internet, electricity, water\n"
#         "   - Real Estate: rent, apartment, house, real estate\n"
#         "   - Jobs: job, employment, hire, resume\n"
#         "   - Education: university, school, course, tutor\n"
#         "   - General: weather, news, Wikipedia, how to cook\n"
#         "   \n"
#         "   **DEFAULT: When uncertain → return FALSE**\n"
        
#         "5. 'date_range': {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'} or null\n"
#         "   CRITICAL DATE DETECTION RULES:\n"
#         "   - If user mentions ANY temporal word like 'tomorrow', 'tonight', 'today', 'this weekend', 'next week', 'happening', 'going on', 'what's on', YOU MUST extract date_range\n"
#         "   - Detect temporal words in ALL languages (e.g., 'mañana', 'demain', 'morgen', 'రేపు', 'غداً', 'מחר', '明日', '내일', etc.)\n"
#         "   - 'tomorrow' → date_range: {'start': tomorrow_date, 'end': tomorrow_date}\n"
#         "   - 'today' → date_range: {'start': today_date, 'end': today_date}\n"
#         "   - 'tonight' → date_range: {'start': today_date, 'end': today_date}\n"
#         "   - 'this weekend' → date_range: {'start': next_saturday, 'end': next_sunday}\n"
#         "   - 'this week' → date_range: {'start': this_monday, 'end': this_sunday}\n"
#         "   - 'next week' → date_range: {'start': next_monday, 'end': next_sunday}\n"
#         "   - 'next weekend' → date_range: {'start': next_saturday, 'end': next_sunday}\n"
#         "   - 'what happening' / 'what's on' / 'show me' + temporal word → ALWAYS means they want events with dates\n"
#         "   EXAMPLES:\n"
#         "   - 'what happening tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
#         "   - 'what's on tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
#         "   - 'anything tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
#         "   - 'show me tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
#         "   - 'events tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
#         "   - 'events this week' → date_range: {'start': this_monday, 'end': this_sunday} ✅\n"
#         "   - 'events next week' → date_range: {'start': next_monday, 'end': next_sunday} ✅\n"
#         "   - 'weekend events' → date_range: {'start': next_saturday, 'end': next_sunday} ✅\n"
        
#         "6. 'target_mood': string (romantic, chill, energetic, party, relaxed, upscale, casual)\n"
        
#         "7. 'social_context': string (date, friends, solo, family, business)\n"
        
#         "8. 'category': string (event, concert, show, bar, restaurant, cafe, theater, club, etc.)\n"
#         "   CRITICAL DETECTION RULES:\n"
#         "   - If user mentions DRINKING (drink, drinks, wine, beer, cocktail, alcohol) → category: 'bar'\n"
#         "   - If user mentions EATING (eat, food, dinner, lunch, brunch) → category: 'restaurant' or 'cafe'\n"
#         "   - If user mentions DANCING/CLUBBING (dance, DJ, club, party) → category: 'club'\n"
#         "   - 'theater' (if mentions play, movie, cinema, show, film)\n"  
#         "   - If user asks temporal questions ('what's happening', 'what's on', 'tonight') → category: 'event'\n"
#         "   - If user mentions GROUPS/MEETUPS (women group, community, circle) → category: 'communities'\n"
#         "   - If user mentions cultural centers it should go to the cultural centers so remember this\n"
#         " - 'cultural_center' (cultural center, art, museum, gallery, exhibition)\n" 
#         "   - May be there will be any category so please analyze the user thing"
#         "   EXAMPLES:\n"
#         "   - 'want to drink wine' → category: 'bar' ✅\n"
#         "   - 'where to drink coffee' → category: 'cafe' ✅\n"
#         "   - 'eat pizza' → category: 'restaurant' ✅\n"
#         "   - 'dance tonight' → category: 'club' ✅\n"
#         "   - 'what's happening tomorrow' → category: 'event' ✅\n"
        
#         "9. 'specific_keywords': List of DIRECT and SPECIFIC keywords from the user's text. "
#         "   - Examples: 'Salsa', 'Techno', 'Jazz', 'Rooftop', 'Live music', 'Coffee', 'Pizza', 'Theater'.\n"
#         "   - **CRITICAL**: DO NOT include generic shopping terms like 'buy', 'shop', 'store' as keywords\n"
#         "   - **CRITICAL**: DO NOT include service terms like 'adopt', 'service', 'appointment' as keywords\n"
        
#         "10. 'user_language': detected ISO 639-1 language code (en, es, pt, fr, de, it, ru, ar, he, hi, te, ta, ko, ja, zh, etc.). Default to 'en' if uncertain.\n"

#         "11. 'inferred_keywords': List of related, searchable keywords if the user's request is abstract. "
#         "   - If the user asks for 'artistic' or 'cultural' things, infer related concrete terms.\n"
#         "   - If the user's request is already specific (e.g., 'techno'), this can be null.\n"
#         "   - **CRITICAL**: Only infer keywords related to nightlife, dining, or entertainment\n"
#         "   - Examples:\n"
#         "     * User says 'artistic events' → inferred_keywords: ['art', 'gallery', 'exhibition', 'museum', 'theatre', 'performance', 'cultural']\n"
#         "     * User says 'something intellectual' → inferred_keywords: ['lecture', 'talk', 'book', 'museum', 'cinema', 'art']\n"
#         "     * User says 'a place with a nice view' → inferred_keywords: ['rooftop', 'terrace', 'view', 'balcony']\n"
#         "     * User says 'buy earphones' → inferred_keywords: null (out of scope!)\n"
#         "     * User says 'adopt dogs' → inferred_keywords: null (out of scope!)\n"
        
#         "Return STRICT JSON only. Remember: You understand ALL languages naturally."
#     )
    
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             response_format={"type": "json_object"},
#             messages=[
#                 {"role": "system", "content": system_prompt}, 
#                 {"role": "user", "content": user_text}
#             ],
#             temperature=0
#         )
#         content = response.choices[0].message.content.strip()
#         data = json.loads(content)
        
#         if not isinstance(data, dict): 
#             return {"user_language": "en", "is_out_of_scope": False}
        
#         if not data.get('user_language') or data.get('user_language') == 'unknown':
#             data['user_language'] = 'en'
        
#         if 'is_out_of_scope' not in data:
#             data['is_out_of_scope'] = False
        
#         logger.info(f"🧠 AI Analysis: {data}")
#         return data
        
#     except Exception as e:
#         logger.error(f"AI Intent Error: {e}")
#         return {"user_language": "en", "is_out_of_scope": False}

# def generate_just_for_you(user_age, item_name, item_desc, item_mood, social_context=None, user_language='en'):
#     """
#     Enhanced: Now generates personalized recommendations in user's detected language
#     """
#     try:
#         context_msg = ""
#         if social_context == 'date':
#             context_msg = "Perfect for a romantic date night."
#         elif social_context == 'friends':
#             context_msg = "Great spot to hang out with friends."
#         elif social_context == 'solo':
#             context_msg = "Perfect for solo exploration."
#         elif social_context == 'business':
#             context_msg = "Ideal for business meetings."
        
#         # Language instruction
#         lang_instruction = f"Respond in the language code: {user_language}. "
#         if user_language == 'te':
#             lang_instruction += "Use Telugu script and language."
#         elif user_language == 'he':
#             lang_instruction += "Use Hebrew script and language."
#         elif user_language == 'ar':
#             lang_instruction += "Use Arabic script and language."
#         elif user_language == 'hi':
#             lang_instruction += "Use Hindi script and language."
#         elif user_language == 'es':
#             lang_instruction += "Use Spanish language."
#         elif user_language == 'pt':
#             lang_instruction += "Use Portuguese language."
#         elif user_language == 'fr':
#             lang_instruction += "Use French language."
#         else:
#             lang_instruction += "Use English language."
        
#         prompt = (
#             f"{lang_instruction} "
#             f"Write a 1-sentence recommendation for a {user_age} year old. "
#             f"Venue: {item_name}. Vibe: {item_mood}. {context_msg} "
#             "Start with '✨ Just for you:' or equivalent in the target language. Be enthusiastic and specific."
#         )
        
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.5,
#             timeout=5
#         )
#         return response.choices[0].message.content.replace('"', '')
#     except Exception as e:
#         logger.error(f"Just for you error: {e}")
#         if user_language == 'te':
#             return f"✨ మీ కోసం: ఇది {item_mood} వైబ్‌తో సరిపోతుంది! {context_msg}"
#         elif user_language == 'he':
#             return f"✨ בשבילך: זה מתאים ל{item_mood} אווירה! {context_msg}"
#         elif user_language == 'ar':
#             return f"✨ لك خصيصاً: זה يناسب الأجواء {item_mood}! {context_msg}"
#         elif user_language == 'es':
#             return f"✨ Just for you: ¡Esto coincide עם el ambiente {item_mood}! {context_msg}"
#         else:
#             return f"✨ Just for you: This matches the {item_mood} vibe! {context_msg}"

# def translate_text(text, target_language):
#     if not text:
#         return text
    
#     try:
#         lang_map = {
#             'es': 'Spanish', 'pt': 'Portuguese', 'fr': 'French', 'de': 'German', 
#             'it': 'Italian', 'ru': 'Russian', 'ar': 'Arabic', 'he': 'Hebrew', 
#             'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'ko': 'Korean', 
#             'ja': 'Japanese', 'zh': 'Chinese'
#         }
#         lang_name = lang_map.get(target_language, 'English')
        
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": f"Translate the following text to {lang_name}. Maintain original tone. Only return the translation."},
#                 {"role": "user", "content": text}
#             ],
#             temperature=0.2,
#             timeout=5
#         )
#         translated = response.choices[0].message.content.strip()
#         return translated if translated else text
#     except Exception as e:
#         logger.error(f"Translation error: {e}")
#         return text

# def generate_closing_message(user_query, user_language='en'):
#     try:
#         lang_instruction_map = {
#             'te': "Respond in Telugu using Telugu script.", 'he': "Respond in Hebrew using Hebrew script.",
#             'ar': "Respond in Arabic using Arabic script.", 'hi': "Respond in Hindi using Devanagari script.",
#             'es': "Respond in Spanish.", 'pt': "Respond in Portuguese.", 'fr': "Respond in French."
#         }
#         lang_instruction = lang_instruction_map.get(user_language, "Respond in English.")
        
#         prompt = (
#             f"User query: '{user_query}'. I sent recommendations. "
#             f"Write a SHORT closing message asking if they want more suggestions. "
#             f"Use 1 emoji. Be friendly. {lang_instruction}"
#         )
        
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "system", "content": "You are Yara, a friendly Buenos Aires guide. You know everything."}, {"role": "user", "content": prompt}],
#             temperature=0.5,
#             timeout=4
#         )
#         return response.choices[0].message.content.replace('"', '')
#     except:
#         fallback_map = {
#             'te': "మరిన్ని సూచనలు కావాలా? 🎉", 'he': "צריך עוד המלצות? 🎉",
#             'ar': "هل تحتاج المزيد من الاقتراحات؟ 🎉", 'es': "¿Te gustaría más sugerencias? 🎉",
#             'pt': "Gostaria de mais sugestões? 🎉"
#         }
#         return fallback_map.get(user_language, "Need more suggestions? 🎉")

# # --- DATABASE FUNCTIONS (UNCHANGED) ---

# def get_user(conn, phone):
#     with conn.cursor() as cur:
#         cur.execute("SELECT * FROM public.users WHERE phone = %s", (phone,))
#         return cur.fetchone()

# def create_user(conn, phone):
#     with conn.cursor() as cur:
#         cur.execute(
#             "INSERT INTO public.users (phone, conversation_step) VALUES (%s, 'welcome') ON CONFLICT (phone) DO NOTHING", (phone,)
#         )
#         conn.commit()
#         cur.execute("SELECT * FROM public.users WHERE phone = %s", (phone,))
#         return cur.fetchone()

# def update_user(conn, phone, data):
#     set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
#     values = list(data.values())
#     values.append(phone)
#     with conn.cursor() as cur:
#         cur.execute(f"UPDATE public.users SET {set_clause} WHERE phone = %s", values)
#         conn.commit()

# # --- ENHANCED SEARCH LOGIC FOR BUSINESSES (UNCHANGED) ---

# def build_search_query(table, ai_data, strictness_level):
#     query = f"SELECT * FROM public.{table} WHERE 1=1"
#     args = []

#     logger.info(f"🔍 AI_data: {ai_data}")
    
#     date_range = ai_data.get('date_range') or {}
#     category = ai_data.get('category')
    
#     # --- KEYWORD COLLECTION ---
#     search_terms = []
#     if ai_data.get('specific_keywords'):
#         search_terms.extend(ai_data.get('specific_keywords'))
#     if ai_data.get('inferred_keywords'):
#         search_terms.extend(ai_data.get('inferred_keywords'))
#     if ai_data.get('target_mood'):
#         search_terms.append(ai_data.get('target_mood'))
    
#     if strictness_level == 2 and category:
#         search_terms.append(category)

#     search_terms = list(set([t for t in search_terms if t and len(t) > 2]))
#     logger.info(f"🔍 Search Terms (Level {strictness_level}): {search_terms}")

#     # --- 1. STRICT CATEGORY FILTERING (Only applies in Strict Mode) ---
#     if strictness_level == 1 and category and table == 'businesses':
#         if category == 'club':
#             query += " AND (category ILIKE %s OR category ILIKE %s)"
#             args.extend(['%club%', '%nightclub%'])
#         elif category == 'bar':
#             query += " AND (category ILIKE %s OR category ILIKE %s)"
#             args.extend(['%bar%', '%pub%'])
#         elif category == 'cafe':
#             query += " AND (category ILIKE %s OR category ILIKE %s)"
#             args.extend(['%cafe%', '%coffee%'])
#         elif category == 'restaurant':
#             query += " AND (category ILIKE %s OR category ILIKE %s)"
#             args.extend(['%restaurant%', '%food%'])
#         elif category == 'communities':
#             query += " AND (category ILIKE %s OR category ILIKE %s OR category ILIKE %s)"
#             args.extend(['%communities%', '%community%', '%group%'])
#         else:
#             query += " AND category ILIKE %s"
#             args.append(f"%{category}%")

#     # --- 2. DATE LOGIC (for events - but events now use Milvus) ---
#     if table == 'events' and date_range:
#         start, end = date_range.get('start'), date_range.get('end')
#         if start and end:
#             start_obj = datetime.strptime(start, "%Y-%m-%d").date()
#             end_obj = datetime.strptime(end, "%Y-%m-%d").date()
            
#             # Calculate all days in the range
#             days_in_range = []
#             current_date = start_obj
#             while current_date <= end_obj:
#                 days_in_range.append(current_date.strftime('%A'))
#                 current_date += timedelta(days=1)
            
#             days_tuple = tuple(set(days_in_range))
#             query += " AND ((event_date >= %s::date AND event_date <= %s::date) OR (recurring_day = ANY(%s)))"
#             args.extend([start, end, list(days_tuple)])

#     # --- 3. DYNAMIC KEYWORD SEARCH ---
#     if search_terms:
#         join_operator = " AND " if strictness_level == 1 else " OR "
        
#         if table == 'events':
#             term_conditions = [f"(title ILIKE %s OR description ILIKE %s OR mood ILIKE %s OR music_type ILIKE %s OR category ILIKE %s)" for _ in search_terms]
#             for term in search_terms:
#                 term_wild = f"%{term}%"
#                 args.extend([term_wild] * 5) 
#         else:  # businesses
#             term_conditions = [f"(name ILIKE %s OR description ILIKE %s OR category ILIKE %s OR location ILIKE %s)" for _ in search_terms]
#             for term in search_terms:
#                 term_wild = f"%{term}%"
#                 args.extend([term_wild] * 4)
        
#         if term_conditions:
#             query += f" AND ({join_operator.join(term_conditions)})"

#     # --- 4. RANDOMIZE AND LIMIT ---
#     if table == 'events':
#         query += " ORDER BY event_date ASC LIMIT 6"
#     else:
#         query += " ORDER BY RANDOM() LIMIT 6" 

#     logger.info(f"📊 SQL Query: {query}")
#     return query, args

# def smart_search(conn, table, ai_data, user_text=''):
#     """
#     IMPORTANT: This function is now ONLY used for BUSINESSES
#     Events are handled by the Milvus RAG system, but we can still use database as fallback
#     """
#     results = []
#     seen_ids = set()
    
#     try:
#         # 1. Try STRICT search first
#         query, args = build_search_query(table, ai_data, strictness_level=1)
#         with conn.cursor() as cur:
#             cur.execute(query, tuple(args))
#             strict_results = cur.fetchall()
            
#             for r in strict_results:
#                 uid = r.get('id') or r.get('name')
#                 if uid not in seen_ids:
#                     results.append(r)
#                     seen_ids.add(uid)

#         # 2. If we have fewer than 3 results, try LOOSE search
#         if len(results) < 3:
#             logger.info(f"⚠️ Only found {len(results)} strict results. expanding to loose search...")
#             query, args = build_search_query(table, ai_data, strictness_level=2)
#             with conn.cursor() as cur:
#                 cur.execute(query, tuple(args))
#                 loose_results = cur.fetchall()
                
#                 if table == 'businesses':
#                     loose_results = filter_restricted_results(loose_results, user_query=user_text)
                
#                 for r in loose_results:
#                     uid = r.get('id') or r.get('name')
#                     if uid not in seen_ids:
#                         results.append(r)
#                         seen_ids.add(uid)
#                         if len(results) >= 6:
#                             break
        
#         logger.info(f"✅ Final Results Count: {len(results)}")
#         return results

#     except Exception as e:
#         logger.error(f"❌ Search error in {table}: {e}")
#         return []

# def filter_restricted_results(results, user_query=''):
#     """
#     Filter out gender/age-restricted results unless explicitly requested
#     """
#     excluded_keywords = [
#         'women only', 'for women', 'ladies only', 'women\'s group',
#         '18+','adults only'
#     ]
    
#     query_lower = user_query.lower()
#     user_wants_gendered = any(word in query_lower for word in ['women', 'ladies', 'girls', 'men', 'guys', 'boys'])
    
#     if user_wants_gendered:
#         return results
    
#     filtered = []
#     for result in results:
#         name = (result.get('name') or '').lower()
#         description = (result.get('description') or '').lower()
#         category = (result.get('category') or '').lower()
        
#         is_restricted = any(
#             keyword in name or keyword in description or keyword in category
#             for keyword in excluded_keywords
#         )
        
#         if not is_restricted:
#             filtered.append(result)
#         else:
#             logger.info(f"🚫 Filtered out restricted result: {result.get('name')}")
    
#     return filtered

# # ==============================================================================
# # 🚀 TWILIO TYPING INDICATOR (UNCHANGED)
# # ==============================================================================

# def send_typing_indicator(message_sid):
#     """
#     Sends a 'Typing' status to the WhatsApp user.
#     This also marks the user's message as Read (Blue Ticks).
#     """
#     if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN: 
#         return
    
#     try:
#         url = "https://messaging.twilio.com/v2/Indicators/Typing.json"
        
#         auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
#         data = {
#             "messageId": message_sid,
#             "channel": "whatsapp"
#         }
        
#         response = requests.post(url, auth=auth, data=data, timeout=2)
        
#         if response.status_code == 200:
#             logger.info("✅ Typing indicator sent (Blue Ticks triggered)")
#         else:
#             logger.warning(f"⚠️ Typing indicator failed: {response.text}")
            
#     except Exception as e:
#         logger.error(f"❌ Error sending typing indicator: {e}")

# def send_whatsapp_message(to, body, media_url=None):
#     if not TWILIO_WHATSAPP_NUMBER: 
#         return
    
#     try:
#         message_data = {
#             'from_': TWILIO_WHATSAPP_NUMBER,
#             'to': to,
#             'body': body
#         }
#         if media_url:
#             message_data['media_url'] = media_url
            
#         twilio_client.messages.create(**message_data)
#     except Exception as e:
#         logger.error(f"❌ Twilio Error: {e}")

# def ask_chatgpt_expert_fallback(user_input, ai_data, user_language='en'):
#     """
#     UPDATED: Prompt rewritten to be ALWAYS POSITIVE. Never says "not found" or "sorry"
#     """
#     category = ai_data.get('category')
#     mood = ai_data.get('target_mood')
#     social_context = ai_data.get('social_context')
#     keywords = ai_data.get('specific_keywords', [])
#     inferred_keywords = ai_data.get('inferred_keywords', [])
#     date_range = ai_data.get('date_range') or {}
#     date_str = date_range.get('start')
    
#     casual_patterns = [
#         'do you know', 'can you speak', 'what languages', 'hello', 'hi', 
#         'hey', 'thanks', 'thank you', 'how are you', 'who are you',
#         'what is', 'tell me about', 'explain'
#     ]
#     is_casual = any(pattern.lower() in user_input.lower() for pattern in casual_patterns)

#     context_parts = []
#     if not is_casual:
#         if social_context: 
#             context_parts.append(f"looking for {social_context} experience")
#         if mood: 
#             context_parts.append(f"wants {mood} vibe")
#         if keywords: 
#             context_parts.append(f"interested in: {', '.join(keywords)}")
#         if inferred_keywords:
#             context_parts.append(f"likes: {', '.join(inferred_keywords)}")
#         if category: 
#             context_parts.append(f"wants: {category}")
#         if date_str: 
#             context_parts.append(f"for date: {date_str}")
    
#     if context_parts:
#         context_description = ". ".join(context_parts)
#     elif is_casual:
#         context_description = "User is having a casual conversation"
#     else:
#         context_description = "User is exploring Buenos Aires"
    
#     lang_map = {
#         'te': "CRITICAL: Respond ENTIRELY in Telugu using Telugu script (తెలుగు).",
#         'he': "CRITICAL: Respond ENTIRELY in Hebrew using Hebrew script (עברית).",
#         'ar': "CRITICAL: Respond ENTIRELY in Arabic using Arabic script (العربية).",
#         'hi': "CRITICAL: Respond ENTIRELY in Hindi using Devanagari script (हिन्दी).",
#         'es': "IMPORTANT: Respond in Spanish.",
#         'pt': "IMPORTANT: Respond in Portuguese.",
#         'fr': "IMPORTANT: Respond in French.",
#     }
#     lang_instruction = lang_map.get(user_language, "IMPORTANT: Respond in English.")
    
#     expert_prompt = f"""You are Yara, the ULTIMATE Buenos Aires expert and local tour guide. 
#     You know EVERYTHING about Buenos Aires - every bar, every restaurant, every café, every hidden gem, every neighborhood.
    
#     USER'S REQUEST: "{user_input}"
#     USER CONTEXT: {context_description}
    
#     FIRST, analyze what the user wants:
#     Without the user aking anyu recommendations don't give any suggestions remember 
#     **TYPE A - Casual Chat/Questions:**
#     - "Who are you?", "What is your name?"
#     - "Do you know [Language]?", "Can you speak [Language]?"
#     - General info: "Weather", "Flights", "News"
#     - Greetings ("Hi", "Hello") or Thanks ("Thank you")
#     **INSTRUCTIONS FOR TYPE A:**
#     1. Answer the question naturally and enthusiastically.
#     2. **STOP.** Do NOT provide a list of specific venues/places unless the user explicitly asked for them.
#     3. If asking about language (e.g., "Do you know Hindi?"), reply **IN** that language.
#        - Example: "Namaste! Haan, main Hindi janti hoon. (Yes, I know Hindi). Main Buenos Aires mein aapki madad kaise kar sakti hoon? 😊"
#     FOR TYPE A RESPONSES:
#     1. **If asking Identity ("Who are you?"):** Say: "I'm Yara, your personal guide to the best of Buenos Aires! 💃✨ I'm here to help you find the coolest spots and events."
#     2. **If asking Language ("Do you know Telugu?"):** Reply **IN** that language. Example: "Avunu! Nenu Telugu matladagalanu. (Yes, I speak Telugu). How can I help? 😊"
#     3. **If asking General Info (Flights/Weather):** Be natural. Say: "I don't have live flight/weather info right now, but I hope everything goes smoothly! While you wait, do you want a recommendation for a nice cafe or bar? 🍷"
#     4. **Otherwise:** Respond naturally and conversationally in 1-2 sentences.
    
#     **TYPE B - Venue Recommendations:**
#     - "Where should I go for..."
#     - "I want to find..."
#     - "Recommend me..."
#     - "What are good places for..."
#     - Mentions specific categories (bars, restaurants, cafés, clubs, events)
    
#     FOR TYPE B: Give 2-3 PERFECT venue recommendations with the format below.
    
#     ---
    
#     **IF TYPE B (Venue Request), use this format:**
    
#     YOUR MISSION: Give them 2-3 PERFECT, SPECIFIC recommendations that match their request.
    
#     CRITICAL RULES - READ CAREFULLY:
#     1. ✅ BE POSITIVE AND CONFIDENT - You're an expert who knows the BEST places in Buenos Aires
#     2. ✅ Give 2-3 SPECIFIC place names with neighborhoods (Palermo, San Telmo, Recoleta, etc.)
#     3.But ther recommedantions should be accurate ask and recommend relavant answers
#     4. you know all the evetns happenining also remeber 
#     5. ✅ Explain WHY each place is perfect for their request
#     6. ✅ Be enthusiastic and use emojis (🎯, ✨, 🍸, 🎵, etc.)
#     7. ❌ NEVER EVER say negative things like:
#        - "sorry"
#        - "not found"
#        - "don't have"
#        - "couldn't find"
#        - "no matches"
#        - "unfortunately"
#     8. ✅ Instead, say positive things like:
#        - "I know the perfect spots!"
#        - "Great choice! Here are amazing places!"
#        - "You'll love these!"
#        - "Perfect! Buenos Aires has incredible options!"
    
#     FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
#     "[Enthusiastic intro acknowledging their request - NO negativity!]
    
#     🎯 **[Place Name]** in [Neighborhood]
#     [One sentence why it's perfect for them]
    
#     🎯 **[Place Name]** in [Neighborhood]
#     [One sentence why it's perfect for them]
    
#     🎯 **[Place Name]** in [Neighborhood]
#     [One sentence why it's perfect for them]
    
#     [Friendly closing with emoji]"
    
#     EXAMPLES OF GOOD INTROS (use similar tone):
#     - "Great choice! I know some incredible spots for that!" ✅
#     - "Perfect! Buenos Aires has amazing places for this!" ✅
#     - "Excellent! Here are some fantastic options!" ✅
    
#     EXAMPLES OF BAD INTROS (NEVER use these):
#     - "Sorry, I don't have information..." ❌
#     - "Unfortunately, I couldn't find..." ❌
    
#     {lang_instruction}
    
#     Remember: You're a confident expert. You ALWAYS have great recommendations!

# {lang_instruction}

# Remember: You're a confident expert. You ALWAYS have great recommendations!"""

#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are Yara, the ultimate Buenos Aires expert who knows EVERYTHING about the city. You're always positive, enthusiastic, and helpful. You NEVER say negative things. You always have great recommendations because you're a real expert."}, 
#                 {"role": "user", "content": expert_prompt}
#             ],
#             temperature=0.6,
#             timeout=10
#         )
#         expert_response = response.choices[0].message.content
#         logger.info(f"🎯 Expert Fallback Response Generated in {user_language}")
#         return expert_response
    
#     except Exception as e:
#         logger.error(f"Fallback Error: {e}")
#         fallback_map = {
#             'te': "బ్యూనస్ ఎయిర్స్‌లో మీ కోసం కొన్ని అద్భుతమైన ప్రదేశాలు ఉన్నాయి! మరిన్ని వివరాలు ఇవ్వండి, నేను ఉత్తమ ప్రదేశాలను సూచిస్తాను! 🎯",
#             'he': "יש כמה מקומות מדהימים בבואנוס איירס בשבילך! ספר לי עוד פרטים ואני אמליץ על המקומות הכי טובים! 🎯",
#             'ar': "لدي أماكن رائعة في بوينس آيريس لك! أخبرني المزيد من التفاصيل وسأوصي بأفضل الأماكن! 🎯",
#             'es': "¡Conozco lugares increíbles en Buenos Aires para ti! Cuéntame más detalles و te recomendaré los mejores sitios! 🎯",
#             'pt': "Conheço lugares incríveis em Buenos Aires para você! Me conte mais detalhes e recomendarei os melhores lugares! 🎯",
#         }
#         return fallback_map.get(user_language, "I know some amazing places in Buenos Aires for you! Tell me more details and I'll recommend the best spots! 🎯")

# # ==============================================================================
# # 🚀 PROCESS THREAD WITH DIRECT MILVUS INTEGRATION
# # ==============================================================================

# def process_message_thread(sender, text, message_sid=None):
#     """
#     UPDATED: Integrated Direct Milvus RAG for event retrieval
#     """
    
#     if message_sid:
#         send_typing_indicator(message_sid)
        
#     conn = None
#     try:
#         conn = postgreSQL_pool.getconn()
#         user = get_user(conn, sender)

#         if not user:
#             create_user(conn, sender)
#             send_whatsapp_message(sender, "Hey! Welcome to Yara ai , I'm your Buenos Aires guide for finding the best plans in the city ✨ what are you in the mood for?")
#             return

#         step, user_age = user.get('conversation_step'), user.get('age', '25')
#         user_name = user.get('name', 'Friend')
        
#         ai_data = executor.submit(analyze_user_intent, text).result() or {"user_language": "en", "is_out_of_scope": False}
#         user_language = ai_data.get('user_language', 'en')
#         social_context = ai_data.get('social_context')
#         is_out_of_scope = ai_data.get('is_out_of_scope', False)

#         logger.info(f"🌍 Detected Language: {user_language}")
#         logger.info(f"🎯 Out of Scope: {is_out_of_scope}")
#         category = (ai_data.get('category') or '').lower()

#         if not category and ai_data.get('specific_keywords'):
#             keywords = [k.lower() for k in ai_data.get('specific_keywords', [])]
    
#             if any(k in keywords for k in ['wine', 'beer', 'cocktail', 'drinks', 'alcohol']):
#                 category = 'bar'
#                 logger.info("🔧 Auto-corrected category to 'bar'")
#             elif any(k in keywords for k in ['coffee', 'cafe', 'espresso']):
#                 category = 'cafe'
#                 logger.info("🔧 Auto-corrected category to 'cafe'")
#             elif any(k in keywords for k in ['food', 'pizza', 'burger', 'eat']):
#                 category = 'restaurant'
#                 logger.info("🔧 Auto-corrected category to 'restaurant'")
#             elif any(k in keywords for k in ['dance', 'dj', 'techno', 'party']):
#                 category = 'club'
#                 logger.info("🔧 Auto-corrected category to 'club'")
        
#         # --- 1. HANDLE GREETINGS ---
#         if ai_data.get('is_greeting') and step != 'ask_name_age':
#             greetings = {
#                 'te': f"నమస్కారం {user_name}! మీరు ఏమి వెతుకుతున్నారు?", 
#                 'he': f"שלום {user_name}! מה אתה מחפש?", 
#                 'ar': f"مرحباً {user_name}! ماذا تبحث؟", 
#                 'es': f"¡Hola {user_name}! ¿Qué estás buscando hoy?", 
#                 'en': f"Hey {user_name}! What are you looking for today?"
#             }
#             send_whatsapp_message(sender, greetings.get(user_language, greetings['en']))
#             return

#         # --- 2. HANDLE IDENTITY QUESTIONS ("Who am I?") --- 
#         if ai_data.get('is_identity_question'):
#             logger.info("👤 Identity question detected.")
            
#             last_mood = user.get('last_mood', 'mystery')
            
#             identity_prompt = (
#                 f"The user asked 'Who am I?' or 'What do you know about me?'. "
#                 f"User Name: {user_name}. Age: {user_age}. Last thing they looked for: {last_mood}. "
#                 f"Respond in language code '{user_language}'. "
#                 f"Be friendly, witty, and confirm you know them as Yara, their local guide. "
#                 "Example: 'You are [Name], my favorite [Age]-year-old explorer! We were just looking for [last_mood].'"
#             )
            
#             try:
#                 response = openai.chat.completions.create(
#                     model="gpt-4o-mini",
#                     messages=[{"role": "system", "content": "You are Yara."}, {"role": "user", "content": identity_prompt}],
#                     temperature=0.6
#                 )
#                 answer = response.choices[0].message.content.replace('"', '')
#                 send_whatsapp_message(sender, answer)
#                 return
#             except Exception as e:
#                 logger.error(f"Identity AI Error: {e}")
#                 send_whatsapp_message(sender, f"You are {user_name}, {user_age} years young! And I'm Yara, your guide! ✨")
#                 return

#         # --- 3. HANDLE UPLOAD/SUBMIT EVENT REQUESTS ---
#         if ai_data.get('wants_to_upload'):
#             logger.info("📤 User wants to upload an event.")
            
#             upload_messages = {
#                 'en': "That's awesome! 🎉 We love new events.\n\nYou can upload your event details here:\n\nhttps://tally.so/r/EkqRYN",
#                 'es': "¡Genial! 🎉 Nos encantan los nuevos eventos.\n\nPuedes subir los detalles de tu evento aquí:\n\nhttps://tally.so/r/EkqRYN",
#                 'pt': "Isso é incrível! 🎉 Adoramos novos eventos.\n\nVocê pode enviar os detalhes do seu evento aqui:\n\nhttps://tally.so/r/EkqRYN",
#                 'fr': "C'est génial! 🎉 Nous adorons les nouveaux événements.\n\nVous pouvez télécharger les détails aqui:\n\nhttps://tally.so/r/EkqRYN",
#                 'de': "Das ist großartig! 🎉 Wir lieben neue Veranstaltungen.\n\nSie podem sua Veranstaltungsdetails aqui hochladen:\n\nhttps://tally.so/r/EkqRYN",
#                 'it': "Fantastico! 🎉 Amiamo i nuovi eventi.\n\nPuoi caricare i dettagli del tuo evento aquí:\n\nhttps://tally.so/r/EkqRYN",
#                 'ru': "Это здорово! 🎉 Мы любим новые события.\n\nВы можете загрузить детали вашего события здесь:\n\nhttps://tally.so/r/EkqRYN",
#                 'te': "అద్భుతం! 🎉 మాకు కొత్త ఈవెంట్‌లు చాలా ఇష్టం.\n\nమీరు మీ ఈవెంట్ వివరాలను ఇక్కడ అప్‌లోడ్ చేయవచ్చు:\n\nhttps://tally.so/r/EkqRYN",
#                 'he': "מדהים! 🎉 אנחנו אוהבים אירועים חדשים.\n\nאתה יכול להעלות את פרטי האירוע שלך כאן:\n\nhttps://tally.so/r/EkqRYN",
#                 'ar': "רائع! 🎉 نحب الأحداث الجديدة.\n\nيمكنك تحميل تفاصيل الحدث الخاص بك כאן:\n\nhttps://tally.so/r/EkqRYN",
#                 'hi': "बहुत बढ़िया! 🎉 हमें नए इवेंट्स पसंद हैं।\n\nआप अपने इवेंट की जानकारी यहाँ अपलोड कर सकते हैं:\n\nhttps://tally.so/r/EkqRYN",
#                 'zh': "太棒了！🎉 我们喜欢新活动。\n\n您可以在这里上传您的活动详情：\n\nhttps://tally.so/r/EkqRYN",
#                 'ja': "素晴らしい！🎉 新しいイベントが大好きです。\n\nイベントの詳細はこちらからアップロードできます：\n\nhttps://tally.so/r/EkqRYN",
#                 'ko': "멋지네요! 🎉 새로운 이벤트를 좋아합니다.\n\n여기에서 이벤트 세부정보를 업로드할 수 있습니다:\n\nhttps://tally.so/r/EkqRYN"
#             }
            
#             final_message = upload_messages.get(user_language, upload_messages['en'])
#             send_whatsapp_message(sender, final_message)
#             return

#         # --- 4. ✅ CHECK IF OUT OF SCOPE ---
#         if is_out_of_scope:
#             logger.info("🚫 OUT OF SCOPE REQUEST DETECTED - Skipping database, going straight to ChatGPT")
#             send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
#             return

#         # --- 5. HANDLE ONBOARDING ---
#         if step == 'welcome':
#             messages = {
#                 'te': "మొదట, మీకు ఉత్తమ సూచనలు ఇవ్వడానికి, మీ పేరు మరియు వయస్సు ఏమిటి?", 
#                 'he': "קודם כל, מה שמך וגילך?", 
#                 'ar': "أولاً، ما هو اسمك وعمرك؟", 
#                 'es': "Primero, ¿cuál es tu nombre y edad?", 
#                 'en': "First, what's your name and age?"
#             }
#             send_whatsapp_message(sender, messages.get(user_language, messages['en']))
#             update_user(conn, sender, {"conversation_step": "ask_name_age", "last_mood": text})
#             return

#         if step == 'ask_name_age':
#             last_mood = user.get('last_mood')
#             messages = {
#                 'te': f"సరే! '{last_mood}' కోసం చూపిస్తున్నాను:", 
#                 'he': f"מעולה! מראה אפשרויות עבור '{last_mood}':", 
#                 'ar': f"رائع! عرض الخيارات لـ '{last_mood}':", 
#                 'es': f"¡Perfecto! Buscando opciones para '{last_mood}':", 
#                 'en': f"Ok cool! Showing options for '{last_mood}':"
#             }
#             send_whatsapp_message(sender, messages.get(user_language, messages['en']))
            
#             clean_name = re.sub(r'[^\w]', '', text.split()[0]) if text.split() else "Friend"
#             age = "".join(filter(str.isdigit, text)) or "25"
            
#             update_user(conn, sender, {"name": clean_name, "age": age, "conversation_step": "ready"})
#             text = last_mood 
#             ai_data = analyze_user_intent(text) or {"user_language": "en", "is_out_of_scope": False}
#             user_language = ai_data.get('user_language', 'en')
#             social_context = ai_data.get('social_context')
#             is_out_of_scope = ai_data.get('is_out_of_scope', False)
            
#             # Check out of scope again after re-analysis
#             if is_out_of_scope:
#                 logger.info("🚫 OUT OF SCOPE (after onboarding) - Using ChatGPT")
#                 send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
#                 return

#         # ===================================================================
#         # 🚀 ENHANCED SEARCH LOGIC WITH DIRECT MILVUS INTEGRATION
#         # ===================================================================
        
#         found_something = False
        
#         # Determine what user is SPECIFICALLY asking for
#         wants_events = (
#             ai_data.get('date_range') or
#             category in ['event', 'concert', 'show', 'party', 'festival', 'exhibition']
#         )
        
#         wants_businesses = category in ['bar', 'restaurant', 'cafe', 'club', 'shop', 'mall', 'theater', 'theatre','communities','community','cultural_center']
        
#         logger.info(f"🎯 User wants - Events: {wants_events}, Businesses: {wants_businesses}")
        
#         # CASE 1: User SPECIFICALLY wants EVENTS - USE DIRECT MILVUS RAG
#         if wants_events and not wants_businesses:
#             logger.info("🚀 Searching EVENTS using Direct Milvus RAG...")
            
#             # Use Direct Milvus RAG for event retrieval
#             events = executor.submit(retrieve_events_direct, text, ai_data, user_language).result()
            
#             # If Milvus returns no results or fails, use database fallback
#             if not events:
#                 logger.info("⚠️ Direct Milvus RAG failed or returned no results - falling back to database")
#                 events = smart_search(conn, 'events', ai_data, text)
            
#             if events:
#                 found_something = True
#                 intro = translate_text(f"Here are some events matching your vibe:", user_language)
#                 if ai_data.get('date_range') and ai_data['date_range'].get('start'):
#                     date_start = ai_data['date_range'].get('start')
#                     date_end = ai_data['date_range'].get('end', date_start)
#                     if date_start == date_end:
#                         intro = translate_text(f"Here's what's happening on {date_start}:", user_language)
#                     else:
#                         intro = translate_text(f"Here's what's happening from {date_start} to {date_end}:", user_language)
#                 send_whatsapp_message(sender, intro)
                
#                 for e in events:
#                     futures = {
#                         'jfy': executor.submit(generate_just_for_you, user_age, e['title'], e['description'], e.get('mood', 'social'), social_context, user_language),
#                         'title': executor.submit(translate_text, e.get('title'), user_language),
#                         'desc': executor.submit(translate_text, e.get('description'), user_language),
#                         'location': executor.submit(translate_text, e.get('location', ''), user_language),
#                         'music': executor.submit(translate_text, e.get('music_type', ''), user_language)
#                     }
                    
#                     ticket_section = ""
#                     if e.get('ticket_link'):
#                         book_text_map = {
#                             'en': '🎟️ Book your slot',
#                             'es': '🎟️ Reserva tu lugar',
#                             'pt': '🎟️ Reserve seu lugar',
#                             'fr': '🎟️ Réservez votre place',
#                             'te': '🎟️ మీ స్లాట్‌ను బుక్ చేసుకోండి',
#                             'he': '🎟️ הזמן את המקום שלך',
#                             'ar': '🎟️ احجز مكانك',
#                             'hi': '🎟️ अपनी जगह बुक करें'
#                         }
#                         book_text = book_text_map.get(user_language, '🎟️ Book your slot')
#                         ticket_section = f"\n{book_text}: {e.get('ticket_link')}"
                    
#                     # Format date display - show recurring day if available
#                     display_date = ""
#                     if e.get('recurring_day'):
#                         if e.get('event_date') and e.get('event_date') != 'Date not specified':
#                             display_date = f"📅 {e.get('event_date')} (Every {e.get('recurring_day')})"
#                         else:
#                             display_date = f"📅 Every {e.get('recurring_day')}"
#                     else:
#                         display_date = f"📅 {e.get('event_date')}" if e.get('event_date') else "📅 Date not specified"
                    
#                     location_text = f"\n📍 {futures['location'].result()}" if e.get('location') else ""
#                     music_text = f"\n🎵 {futures['music'].result()}" if e.get('music_type') else ""
#                     time_text = f"\n🕒 {e.get('event_time')}" if e.get('event_time') else ""
                    
#                     caption = f"*{futures['title'].result()}*{location_text}{time_text}\n{display_date}{music_text}\n📝 {futures['desc'].result()}{ticket_section}"
                    
#                     if e.get('instagram_link'):
#                         caption += f"\n📸 {e.get('instagram_link')}"
                    
#                     caption += f"\n\n{futures['jfy'].result()}"
                    
#                     # Send with image if available
#                     media_url = e.get('image_url')
#                     if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
#                         send_whatsapp_message(sender, caption, media_url=media_url)
#                     else:
#                         send_whatsapp_message(sender, caption)
            
#             if not found_something:
#                 logger.info("🎯 No events found via Milvus or database - Using ChatGPT fallback")
#                 send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
#                 return
        
#         # CASE 2: User SPECIFICALLY wants BUSINESSES - USE DATABASE (UNCHANGED)
#         elif wants_businesses and not wants_events:
#             logger.info("🔍 Searching BUSINESSES only (using database)...")
#             businesses = smart_search(conn, 'businesses', ai_data, text)
            
#             if businesses:
#                 found_something = True
#                 intro = translate_text("Found these spots for you:", user_language)
#                 send_whatsapp_message(sender, intro)
                
#                 for b in businesses:
#                     futures = {
#                         'jfy': executor.submit(generate_just_for_you, user_age, b['name'], b['description'], ai_data.get('target_mood') or 'chill', social_context, user_language),
#                         'name': executor.submit(translate_text, b.get('name'), user_language),
#                         'desc': executor.submit(translate_text, b.get('description'), user_language),
#                         'location': executor.submit(translate_text, b.get('location'), user_language)
#                     }
#                     msg = f"*{futures['name'].result()}*\n📍 {futures['location'].result()}\n\n{futures['desc'].result()}\n\n📸 {b.get('instagram_link')}\n\n{futures['jfy'].result()}"
                    
#                     media_url = b.get('image_url')
#                     if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
#                         send_whatsapp_message(sender, msg, media_url=media_url)
#                     else:
#                         send_whatsapp_message(sender, msg)
            
#             if not found_something:
#                 logger.info("🎯 No businesses found - Using ChatGPT fallback for businesses")
#                 send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
#                 return
        
#         # CASE 3: Ambiguous query - search BOTH (EVENTS: MILVUS, BUSINESSES: DATABASE)
#         else:
#             logger.info("🔍 Ambiguous query - Searching both (Events: Milvus, Businesses: Database)...")
            
#             # Use Direct Milvus for events
#             events = executor.submit(retrieve_events_direct, text, ai_data, user_language).result()
#             if not events:  # Fallback to database if Milvus fails
#                 events = smart_search(conn, 'events', ai_data, text)
            
#             if events:
#                 found_something = True
#                 intro = translate_text(f"Here are some events matching your vibe:", user_language)
#                 send_whatsapp_message(sender, intro)
                
#                 for e in events:
#                     futures = {
#                         'jfy': executor.submit(generate_just_for_you, user_age, e['title'], e['description'], e.get('mood', 'social'), social_context, user_language),
#                         'title': executor.submit(translate_text, e.get('title'), user_language),
#                         'desc': executor.submit(translate_text, e.get('description'), user_language),
#                         'location': executor.submit(translate_text, e.get('location', ''), user_language),
#                         'music': executor.submit(translate_text, e.get('music_type', ''), user_language)
#                     }
                    
#                     ticket_section = ""
#                     if e.get('ticket_link'):
#                         book_text_map = {
#                             'en': '🎟️ Book your slot',
#                             'es': '🎟️ Reserva tu lugar',
#                             'pt': '🎟️ Reserve seu lugar',
#                             'fr': '🎟️ Réservez votre place',
#                             'te': '🎟️ మీ స్లాట్‌ను బుక్ చేసుకోండి',
#                             'he': '🎟️ הזמן את המקום שלך',
#                             'ar': '🎟️ احجز مكانك',
#                             'hi': '🎟️ अपनी जगह बुक करें'
#                         }
#                         book_text = book_text_map.get(user_language, '🎟️ Book your slot')
#                         ticket_section = f"\n{book_text}: {e.get('ticket_link')}"
                    
#                     # Format date display - show recurring day if available
#                     display_date = ""
#                     if e.get('recurring_day'):
#                         if e.get('event_date') and e.get('event_date') != 'Date not specified':
#                             display_date = f"📅 {e.get('event_date')} (Every {e.get('recurring_day')})"
#                         else:
#                             display_date = f"📅 Every {e.get('recurring_day')}"
#                     else:
#                         display_date = f"📅 {e.get('event_date')}" if e.get('event_date') else "📅 Date not specified"
                    
#                     location_text = f"\n📍 {futures['location'].result()}" if e.get('location') else ""
#                     music_text = f"\n🎵 {futures['music'].result()}" if e.get('music_type') else ""
#                     time_text = f"\n🕒 {e.get('event_time')}" if e.get('event_time') else ""
                    
#                     caption = f"*{futures['title'].result()}*{location_text}{time_text}\n{display_date}{music_text}\n📝 {futures['desc'].result()}{ticket_section}"
                    
#                     if e.get('instagram_link'):
#                         caption += f"\n📸 {e.get('instagram_link')}"
                    
#                     caption += f"\n\n{futures['jfy'].result()}"
                    
#                     media_url = e.get('image_url')
#                     if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
#                         send_whatsapp_message(sender, caption, media_url=media_url)
#                     else:
#                         send_whatsapp_message(sender, caption)
            
#             # Use database for businesses
#             businesses = smart_search(conn, 'businesses', ai_data, text)
#             if businesses:
#                 found_something = True
#                 intro = translate_text("Found these spots for you:", user_language)
#                 send_whatsapp_message(sender, intro)
                
#                 for b in businesses:
#                     futures = {
#                         'jfy': executor.submit(generate_just_for_you, user_age, b['name'], b['description'], ai_data.get('target_mood') or 'chill', social_context, user_language),
#                         'name': executor.submit(translate_text, b.get('name'), user_language),
#                         'desc': executor.submit(translate_text, b.get('description'), user_language),
#                         'location': executor.submit(translate_text, b.get('location'), user_language)
#                     }
#                     msg = f"*{futures['name'].result()}*\n📍 {futures['location'].result()}\n\n{futures['desc'].result()}\n\n📸 {b.get('instagram_link')}\n\n{futures['jfy'].result()}"
                    
#                     media_url = b.get('image_url')
#                     if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
#                         send_whatsapp_message(sender, msg, media_url=media_url)
#                     else:
#                         send_whatsapp_message(sender, msg)
            
#             if not found_something:
#                 logger.info("🎯 Nothing found in both tables - Using ChatGPT fallback")
#                 send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
#                 return
        
#         # Send closing message if something was found
#         if found_something:
#             send_whatsapp_message(sender, generate_closing_message(text, user_language))

#     except Exception as e:
#         logger.error(f"Logic Error: {e}", exc_info=True)
#         try:
#             ai_data = analyze_user_intent(text) or {"user_language": "en", "is_out_of_scope": False}
#             user_language = ai_data.get('user_language', 'en')
#             send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
#         except:
#             send_whatsapp_message(sender, "I know some amazing places in Buenos Aires for you! Tell me what you're looking for and I'll recommend the best spots! 🎯")
#     finally:
#         if conn: 
#             postgreSQL_pool.putconn(conn)

# # ==============================================================================
# # 🌐 WEBHOOK (UNCHANGED)
# # ==============================================================================

# @app.route("/webhook", methods=["POST"])
# def twilio_webhook():
#     incoming_msg = request.form.get('Body')
#     sender_id = request.form.get('From')
#     message_sid = request.form.get('MessageSid')
    
#     if not sender_id or not incoming_msg: return "" 
    
#     resp = MessagingResponse()
#     threading.Thread(target=process_message_thread, args=(sender_id, incoming_msg, message_sid)).start()
#     return str(resp)

# if __name__ == "__main__":
#     print("🚀 Twilio WhatsApp Bot Starting...")
#     print("✨ Features: Typing Indicators, Identity, Upload Link, Multilingual")
#     print("✅ DIRECT MILVUS RAG INTEGRATION: Events use embedded Milvus RAG")
#     print("✅ BUSINESSES: Still use PostgreSQL database (unchanged)")
#     print("✅ UPLOAD: Event upload feature preserved")
#     print("✅ LANGUAGE: Multilingual support preserved")
#     print("✅ OUT-OF-SCOPE: Detection preserved")
#     print("✅ ENHANCED DATE HANDLING: Proper support for 'this week', 'next week', 'weekends' with recurring events")
    
#     # Check Milvus configuration
#     if MILVUS_AVAILABLE and MILVUS_ENDPOINT and MILVUS_TOKEN:
#         print(f"✅ Milvus configured: {MILVUS_ENDPOINT}")
#     else:
#         print("⚠️ Milvus not fully configured - will use database fallback for events")
    
#     app.run(port=5000)\





########################################################################################

#Final Code

########################################################################################

import os
import logging
import psycopg2
import threading
import json
import re
import requests
import traceback
from concurrent.futures import ThreadPoolExecutor
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, date
from flask import Flask, request
import openai
from twilio.rest import Client as TwilioClient 
from twilio.twiml.messaging_response import MessagingResponse 
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# 1. Load Environment Variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
DB_URI = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") 

# Milvus Configuration
MILVUS_ENDPOINT = os.getenv("MILVUS_ENDPOINT")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")

# Initialize OpenAI client for embeddings
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Try to import Milvus, but don't fail if not available
try:
    from pymilvus import connections, Collection, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    print("⚠️ pymilvus not installed. Install with: pip install pymilvus")

# Initialize Twilio Client
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GLOBAL THREAD POOL ---
executor = ThreadPoolExecutor(max_workers=5) 

# --- DATABASE POOL ---
try:
    postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(
        1, 50, DB_URI, cursor_factory=RealDictCursor, connect_timeout=10
    )
    print("✅ Database Connection Pool Created")
except (Exception, psycopg2.DatabaseError) as error:
    print("❌ Error connecting to PostgreSQL", error)

# ==============================================================================
# 🚀 DIRECT MILVUS RAG EVENT RETRIEVAL (EMBEDDED)
# ==============================================================================

# Initialize Milvus if available
milvus_collection = None
if MILVUS_AVAILABLE and MILVUS_ENDPOINT and MILVUS_TOKEN:
    try:
        connections.connect(uri=MILVUS_ENDPOINT, token=MILVUS_TOKEN)
        COLLECTION_NAME = "events"
        if utility.has_collection(COLLECTION_NAME):
            milvus_collection = Collection(COLLECTION_NAME)
            milvus_collection.load()
            logger.info("✅ Milvus connected and collection loaded")
        else:
            logger.warning("⚠️ Milvus collection 'events' not found")
    except Exception as e:
        logger.error(f"❌ Error connecting to Milvus: {e}")
        milvus_collection = None
else:
    logger.warning("⚠️ Milvus not configured or unavailable")

def create_embedding(text: str) -> List[float]:
    """Create embedding for a single text"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"❌ Error creating embedding: {e}")
        return []

def get_date_context() -> Dict[str, str]:
    """Generate current date context"""
    now = datetime.now()
    today = now.date()
    
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    
    # Calculate this week's dates
    days_until_monday = (today.weekday() - 0) % 7  # Monday is 0
    this_monday = today - timedelta(days=days_until_monday)
    this_sunday = this_monday + timedelta(days=6)
    
    # Calculate next week's dates
    next_monday = this_monday + timedelta(days=7)
    next_sunday = next_monday + timedelta(days=6)
    
    # Calculate weekends
    days_until_friday = (4 - today.weekday()) % 7
    this_friday = today + timedelta(days=days_until_friday)
    this_saturday = this_friday + timedelta(days=1)
    this_weekend_sunday = this_friday + timedelta(days=2)
    
    next_friday = this_friday + timedelta(days=7)
    next_saturday = next_friday + timedelta(days=1)
    next_weekend_sunday = next_friday + timedelta(days=2)
    
    return {
        "today": today.strftime("%Y-%m-%d, %A"),
        "tomorrow": tomorrow.strftime("%Y-%m-%d, %A"),
        "yesterday": yesterday.strftime("%Y-%m-%d, %A"),
        "this_week_start": this_monday.strftime("%Y-%m-%d"),
        "this_week_end": this_sunday.strftime("%Y-%m-%d"),
        "next_week_start": next_monday.strftime("%Y-%m-%d"),
        "next_week_end": next_sunday.strftime("%Y-%m-%d"),
        "this_weekend_start": this_friday.strftime("%Y-%m-%d"),
        "this_weekend_middle": this_saturday.strftime("%Y-%m-%d"),
        "this_weekend_end": this_weekend_sunday.strftime("%Y-%m-%d"),
        "next_weekend_start": next_friday.strftime("%Y-%m-%d"),
        "next_weekend_middle": next_saturday.strftime("%Y-%m-%d"),
        "next_weekend_end": next_weekend_sunday.strftime("%Y-%m-%d"),
        "current_date_iso": today.strftime("%Y-%m-%d"),
        "current_day_name": today.strftime("%A"),
        "current_week_number": today.strftime("%W")
    }

def extract_event_fields(event_data: Dict, metadata: Dict) -> Dict:
    """Extract and merge all relevant fields from event data and metadata"""
    merged = {}
    merged.update(event_data)
    merged.update(metadata)
    
    result = {
        "title": merged.get("title") or merged.get("name") or "Untitled Event",
        "description": merged.get("description") or merged.get("details") or merged.get("summary") or "",
        "event_date": merged.get("event_date") or merged.get("date") or "Date not specified",
        "mood": merged.get("mood"),
        "music_type": merged.get("music_type") or merged.get("genre") or merged.get("music_genre"),
        "location": merged.get("location") or merged.get("venue") or merged.get("address") or "",
        "address": merged.get("address") or merged.get("venue_address") or "",
        "price": merged.get("price") or merged.get("ticket_price") or "",
        "recurring_day": merged.get("recurring_day") or merged.get("recurring") or merged.get("day"),
        "image_url": merged.get("image_url") or merged.get("photo_url") or merged.get("image") or merged.get("photo"),
        "instagram_link": merged.get("instagram_link") or merged.get("instagram") or merged.get("instagram_url"),
        "organizer": merged.get("organizer") or merged.get("host"),
        "capacity": merged.get("capacity"),
        "age_restriction": merged.get("age_restriction") or merged.get("age_limit"),
    }
    
    return result

def search_milvus_events(query_embedding: List[float], limit: int = 25) -> List[Dict]:
    """Search for similar events in Milvus"""
    if not milvus_collection:
        return []
    
    try:
        search_params = {
            "data": [query_embedding],
            "anns_field": "embedding",
            "param": {"metric_type": "COSINE", "params": {"nprobe": 10}},
            "limit": limit,
            "output_fields": ["id", "title", "text", "metadata"]
        }
        
        results = milvus_collection.search(**search_params)
        
        events = []
        for hits in results:
            for hit in hits:
                try:
                    event_data = json.loads(hit.entity.get("text", "{}"))
                    metadata_str = hit.entity.get("metadata", "{}")
                    
                    if isinstance(metadata_str, str):
                        try:
                            metadata = json.loads(metadata_str)
                        except json.JSONDecodeError:
                            metadata = {}
                    else:
                        metadata = metadata_str or {}
                    
                    event = extract_event_fields(event_data, metadata)
                    event["similarity_score"] = float(hit.score)
                    
                    events.append(event)
                except Exception as e:
                    logger.error(f"Error processing hit: {e}")
                    continue
        
        return events
    except Exception as e:
        logger.error(f"Milvus search error: {e}")
        return []

def llm_filter_events(query: str, events: List[Dict], date_context: Dict) -> List[Dict]:
    """Use LLM to filter and format recommendations"""
    if not events:
        return []
    
    try:
        events_context = []
        for i, event in enumerate(events):
            events_context.append(f"""
Event {i+1} (Similarity: {event.get('similarity_score', 0):.3f}):
Title: {event.get('title', 'N/A')}
Description: {event.get('description', '')}
Date: {event.get('event_date', 'N/A')}
Recurring Day: {event.get('recurring_day', 'None')}
Music Type: {event.get('music_type', '')}
Mood: {event.get('mood', '')}
Location: {event.get('location', '')}
Image URL: {event.get('image_url', '')}
Instagram: {event.get('instagram_link', '')}
""")
        
        prompt = f"""
# TASK: Select events for user query.

## DATE CONTEXT:
- TODAY: {date_context['today']}
- ... (rest of context)

## USER QUERY:
"{query}"

## CANDIDATE EVENTS (Already filtered by date):
{chr(10).join(events_context)}

## INSTRUCTIONS:
1. **MATCH THE CATEGORY:** 
   - If user asks for "Artsy/Art", look for: Exhibitions, Galleries, Drawing, Painting, Fairs.
   - If user asks for "Tango", ONLY return Tango.
   - If user asks for "Party", ONLY return Club/DJ/Dancing.
2. **EXCLUDE IRRELEVANT:** If user asks for "Artsy", DO NOT include Tango, Clubs, or Dinner shows unless they are explicitly described as an art exhibition.
3. **NO HALLUCINATIONS:** Only use the events listed above.
4. **RECURRING EVENTS:** Always include the 'recurring_day' field in your JSON output.
"""

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an event recommendation expert. Always include recurring_day if present in event data. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        recommendations = data.get("recommendations", data.get("events", []))
        
        if not isinstance(recommendations, list):
            return events[:5]  # Fallback to top 5 events
        
        validated_recommendations = []
        for rec in recommendations:
            cleaned_rec = {
                "title": rec.get("title") or "Untitled Event",
                "description": rec.get("description") or "",
                "event_date": rec.get("event_date") or "Date not specified",
                "recurring_day": rec.get("recurring_day"),
                "mood": rec.get("mood"),
                "music_type": rec.get("music_type"),
                "image_url": rec.get("image_url"),
                "instagram_link": rec.get("instagram_link")
            }
            validated_recommendations.append(cleaned_rec)
        
        return validated_recommendations[:6]
        
    except Exception as e:
        logger.error(f"LLM filtering error: {e}")
        return events[:6]

def build_milvus_query(user_query: str, ai_data: Dict) -> str:
    """
    Enhance user query with AI analysis for better Milvus retrieval
    """
    date_range = ai_data.get('date_range') or {}
    category = ai_data.get('category')
    target_mood = ai_data.get('target_mood')
    social_context = ai_data.get('social_context')
    
    # SAFE extraction with default empty lists
    specific_keywords = ai_data.get('specific_keywords')
    inferred_keywords = ai_data.get('inferred_keywords')
    
    # Ensure they are lists
    if specific_keywords is None:
        specific_keywords = []
    if inferred_keywords is None:
        inferred_keywords = []
    
    query_parts = [user_query]
    
    # Add date context if available
    if date_range and isinstance(date_range, dict):
        start_date = date_range.get('start')
        if start_date:
            end_date = date_range.get('end', start_date)
            if start_date == end_date:
                query_parts.append(f"on {start_date}")
            else:
                query_parts.append(f"from {start_date} to {end_date}")
    
    # Add mood context
    if target_mood and isinstance(target_mood, str):
        query_parts.append(f"{target_mood} vibe")
    
    # Add category context
    if category and isinstance(category, str):
        query_parts.append(f"{category} events")
    
    # Add social context
    if social_context and isinstance(social_context, str):
        social_context_map = {
            'date': 'romantic date night',
            'friends': 'with friends',
            'solo': 'solo',
            'family': 'family friendly',
            'business': 'business networking'
        }
        social_text = social_context_map.get(social_context, social_context)
        if social_text:
            query_parts.append(social_text)
    
    # Add keywords - SAFE CONCATENATION
    all_keywords = []
    if specific_keywords and isinstance(specific_keywords, list):
        all_keywords.extend([k for k in specific_keywords if isinstance(k, str)])
    if inferred_keywords and isinstance(inferred_keywords, list):
        all_keywords.extend([k for k in inferred_keywords if isinstance(k, str)])
    
    # Clean keywords
    all_keywords = [k.strip() for k in all_keywords if k and len(str(k).strip()) > 2]
    if all_keywords:
        unique_keywords = list(set(all_keywords))
        query_parts.append(" ".join(unique_keywords))
    
    enhanced_query = " ".join(query_parts)
    logger.info(f"🔍 Enhanced query for Milvus: {enhanced_query}")
    
    return enhanced_query
# ==============================================================================
# 🛠️ HELPER: STRICT DATE FILTERING
# ==============================================================================
def filter_events_by_date(events: List[Dict], ai_data: Dict) -> List[Dict]:
    """
    Strictly filters events based on the date range provided by AI Analysis.
    Handles specific dates (YYYY-MM-DD) and Recurring Days (Monday, etc).
    """
    date_range = ai_data.get('date_range')
    
    # If no date requested by user, return ALL events found
    if not date_range or not date_range.get('start'):
        return events

    start_str = date_range.get('start')
    end_str = date_range.get('end', start_str)
    
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return events # Fallback if date format is wrong

    # Calculate valid weekdays (e.g., if range is Dec 9 (Tuesday), valid=['Tuesday'])
    valid_weekdays = []
    curr = start_date
    while curr <= end_date:
        valid_weekdays.append(curr.strftime("%A")) 
        curr += timedelta(days=1)

    filtered_events = []
    
    logger.info(f"📅 STRICT FILTERING: Looking for dates {start_str} to {end_str} OR weekdays {valid_weekdays}")

    for event in events:
        is_match = False
        
        # 1. Check Specific Date Match (e.g., "2025-12-09")
        e_date = event.get('event_date')
        if e_date and e_date != 'Date not specified':
            try:
                # Compare strings YYYY-MM-DD
                event_dt_obj = datetime.strptime(e_date, "%Y-%m-%d").date()
                if start_date <= event_dt_obj <= end_date:
                    is_match = True
            except:
                pass 

        # 2. Check Recurring Day Match (e.g., "Tuesday")
        # Only check this if specific date didn't match
        if not is_match:
            rec_day = event.get('recurring_day')
            if rec_day and rec_day in valid_weekdays:
                is_match = True

        if is_match:
            filtered_events.append(event)

    logger.info(f"📉 Filtered down from {len(events)} to {len(filtered_events)} strict matches")
    return filtered_events
def retrieve_events_direct(user_query: str, ai_data: Dict, user_language: str = 'en') -> List[Dict]:
    """
    Direct Milvus RAG event retrieval with STRICT DATE FILTERING
    """
    try:
        # Check if Milvus is available
        if not milvus_collection:
            logger.info("⚠️ Milvus not available - skipping RAG retrieval")
            return []
        
        # Build enhanced query
        try:
            enhanced_query = build_milvus_query(user_query, ai_data)
        except Exception as e:
            logger.error(f"❌ Error building Milvus query: {e}")
            enhanced_query = user_query 
        
        logger.info(f"🔍 Direct Milvus search with query: {enhanced_query}")
        
        # Create embedding
        query_embedding = create_embedding(enhanced_query)
        if not query_embedding:
            return []
        
        # 1. RETRIEVE BROADLY (Limit increased to 100 to find hidden matches)
        raw_events = search_milvus_events(query_embedding, limit=100)
        
        if not raw_events:
            return []

        # 2. APPLY STRICT DATE FILTERING (Python Side)
        # This removes "Date Not Specified" or wrong dates when a date is asked
        date_filtered_events = filter_events_by_date(raw_events, ai_data)
        
        # If user asked for a date, but we found nothing matching that date:
        if ai_data.get('date_range') and not date_filtered_events:
            logger.info("📅 No events found for the specific requested date.")
            return [] # Return empty so code falls back to ChatGPT or Database
        
        # Use filtered list if it exists, otherwise use raw (for queries without dates)
        events_to_process = date_filtered_events if date_filtered_events else raw_events

        # 3. Use LLM to filter CATEGORIES (Artsy vs Tango)
        date_context = get_date_context()
        recommendations = llm_filter_events(user_query, events_to_process, date_context)
        
        formatted_events = []
        for event in recommendations:
            if not isinstance(event, dict): continue
            
            # Recover location if missing
            location = event.get('location', '')
            if not location:
                for raw in raw_events:
                    if raw.get('title') == event.get('title'):
                        location = raw.get('location', '')
                        break
            
            formatted_event = {
                'title': event.get('title', 'Untitled Event'),
                'description': event.get('description', ''),
                'event_date': event.get('event_date', 'Date not specified'),
                'mood': event.get('mood'),
                'music_type': event.get('music_type'),
                'location': location,
                'event_time': event.get('event_time', ''), 
                'recurring_day': event.get('recurring_day'),
                'ticket_link': event.get('ticket_link', ''),
                'instagram_link': event.get('instagram_link'),
                'image_url': event.get('image_url'),
                'category': 'event'
            }
            formatted_events.append(formatted_event)
        
        return formatted_events
        
    except Exception as e:
        logger.error(f"❌ Direct Milvus retrieval error: {e}")
        traceback.print_exc()
        return []
# ==============================================================================
# 🧠 ENHANCED AI & UTILS (UNCHANGED - KEEP YOUR EXISTING CODE)
# ==============================================================================

def analyze_user_intent(user_text):
    """
    UPDATED: Added 'is_out_of_scope' detection + reduced temperature for consistency
    """
    today_str = date.today().strftime("%Y-%m-%d")
    weekday_str = date.today().strftime("%A")
    tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    system_prompt = (
        f"Current Date: {today_str} ({weekday_str}). Tomorrow is: {tomorrow_str}. "
        "You are a multilingual AI that understands ALL languages (English, Spanish, Portuguese, French, German, Italian, Russian, Arabic, Hebrew, Hindi, Telugu, Tamil, Chinese, Japanese, Korean, and ALL others). "
        "Your job is to analyze a user's request for events or businesses in Buenos Aires and extract structured data."
        "Withou user asking anythin do not give the recommendations "
        "EXTRACT THE FOLLOWING (return as JSON):\n"
        "⚠️ CRITICAL RULE: If the user is ONLY greeting you (hi, hello, hey, what's up, how are you) "
    "WITHOUT asking for ANY specific recommendation or place, then 'is_greeting' MUST be TRUE. "
    "Examples: 'hey whats up' → is_greeting: TRUE ✅ | 'whats up, any bars?' → is_greeting: FALSE ❌\n\n"
        "1. 'is_greeting': boolean (true ONLY if message is JUST 'hi', 'hello', 'hola', 'hey', 'salut', 'ciao', 'नमस्ते', 'నమస్కారం', '你好', 'こんにちは', '안녕하세요' etc. with ABSOLUTELY NO OTHER REQUEST. If user says 'hi' AND asks for anything else, return FALSE)\n"
        "   Examples:\n"
        "   - 'hi' → is_greeting: true ✅\n"
        "   - 'hello' → is_greeting: true ✅\n"
        "   - 'hi any events on Dec 6' → is_greeting: FALSE ❌ (has request!)\n"
        "   - 'hello where can I find bars' → is_greeting: FALSE ❌ (has request!)\n"
        "   - 'hey whats up' → is_greeting: True \n-"
       " 2. 'is_gratitude': boolean\n"
        "   - TRUE if message is ONLY expressing thanks: 'thank you', 'thanks', 'gracias', 'cool thanks', 'perfect thanks'.\n"
        "3. 'is_identity_question': boolean. \n"
        "   - TRUE ONLY if user asks about THEIR OWN identity: 'Who am I?', 'Do you know me?', 'What is my name?' - Any language \n"
        "   - FALSE if user asks about YOUR identity: 'Who are you?', 'What is your name?'. (This goes to general chat) - Any language \n"
        
        "4. 'wants_to_upload': boolean. CRITICAL - Detect this intent in ANY language:\n"
        "   True if user expresses intent to:\n"
        "   - Upload/Submit/Add/Post/Share/Promote an event\n"
        "   - Recommend their own event/party/venue/business\n"
        "   - List their event or ask how to add/submit it\n"
        "   - Say 'I have an event', 'I'm organizing', 'I want to promote', 'I want to list'\n"
        "   Examples across languages:\n"
        "   - English: 'upload event', 'add my party', 'how can I submit', 'I want to recommend my event'\n"
        "   - Spanish: 'subir evento', 'agregar mi fiesta', 'cómo puedo enviar', 'quiero recomendar'\n"
        "   - Portuguese: 'enviar evento', 'adicionar minha festa', 'quero recomendar'\n"
        "   - French: 'ajouter événement', 'télécharger mon événement', 'je veux recommender'\n"
        "   - German: 'Veranstaltung hochladen', 'meine Party hinzufügen', 'ich möchte empfehlen'\n"
        "   - Italian: 'caricare evento', 'aggiungere la minha festa', 'voglio raccomandare'\n"
        "   - Russian: 'загрузить событие', 'добавить мою вечеринку', 'я хочу порекомендовать'\n"
        "   - Arabic: 'إضافة حدث', 'رفع حدثي', 'كيف أضيف', 'أريد أن أوصي'\n"
        "   - Hebrew: 'להעלות אירוע', 'להוסיף את המסיבה שלי', 'אני רוצה להמליץ'\n"
        "   - Hindi: 'इवेंट अपलोड करें', 'मेरी पार्टी जोड़ें', 'मैं सिफारिश करना चाहता हूं'\n"
        "   - Telugu: 'ఈవెంట్ అప్‌లోడ్ చేయండి', 'నా పార్టీని జోడించండి', 'నేను సిఫార్సు చేయాలనుకుంటున్నాను'\n"
        "   - Chinese: '上传活动', '添加我的派对', '如何提交', '我想推荐'\n"
        "   - Japanese: 'イベントをアップロード', 'パーティーを追加', '推薦したい'\n"
        "   - Korean: 'イベント 업로드', '내 파티 추가', '제출 방법', '추천하고 싶어요'\n"
        "   ANY similar phrase in ANY language should return true.\n"

        "5. 'is_out_of_scope': boolean. **FOLLOW THIS EXACT PROCESS:**\n"
        "   \n"
        "   **STEP 1 - CHECK FOR ENTERTAINMENT KEYWORDS (if ANY found → return FALSE immediately):**\n"
        "   Look for these words in the user's message (in ANY language):\n"
        "   - Drinking: drink, drinks, bar, pub, cocktail, beer, wine, alcohol\n"
        "   - Eating: eat, food, restaurant, cafe, coffee, dinner, lunch, brunch\n"
        "   - Nightlife: club, party, dance, DJ, nightlife, night out\n"
        "   - Events: event, concert, show, festival, happening, tonight, today\n"
        "   - Entertainment: music, live, theater, cinema, movie, museum, gallery\n"
        "   - IF user asks about: Eating, Drinking, Nightlife, Clubbing, Events, Art, Theater -> FALSE (In Scope)\n"
        "   - IF user asks about: Social Groups, Women Communities, Meetups, Expats -> FALSE (In Scope)\n"
        "   - IF user asks about: Buying items, Doctors, Real Estate, Jobs, Repairs -> TRUE (Out of Scope)\n"
        "   - Example: 'Where can I adopt a dog?' -> TRUE (Out of Scope)\n"
        "   - Example: 'Women communities' -> FALSE (In Scope)\n"
        "   \n"
        "   **IF ANY OF THESE WORDS APPEAR → IMMEDIATELY RETURN FALSE (in scope)**\n"
        "   Do not analyze grammar or context. Just check if the word exists.\n"
        "   \n"
        "   Examples:\n"
        "   - 'Where do i drink question' → contains 'drink' → FALSE ✅\n"
        "   - 'drink' → contains 'drink' → FALSE ✅\n"
        "   - 'bar question' → contains 'bar' → FALSE ✅\n"
        "   - 'eat where' → contains 'eat' → FALSE ✅\n"
        "   - 'event?' → contains 'event' → FALSE ✅\n"
        "   \n"
        "   **STEP 2 - IF NO ENTERTAINMENT KEYWORDS, CHECK IF OUT OF SCOPE:**\n"
        "   Only return TRUE if asking about:\n"
        "   - Shopping: buy, purchase, shop, store, mall, electronics\n"
        "   - Services: doctor, hospital, dentist, lawyer, veterinarian, haircut\n"
        "   - Transport: bus, taxi, uber, train, airport\n"
        "   - Utilities: bills, internet, electricity, water\n"
        "   - Real Estate: rent, apartment, house, real estate\n"
        "   - Jobs: job, employment, hire, resume\n"
        "   - Education: university, school, course, tutor\n"
        "   - General: weather, news, Wikipedia, how to cook\n"
        "   \n"
        "   **DEFAULT: When uncertain → return FALSE**\n"
        
        "6. 'date_range': {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'} or null\n"
        "   CRITICAL DATE DETECTION RULES:\n"
        "   - If user mentions ANY temporal word like 'tomorrow', 'tonight', 'today', 'this weekend', 'next week', 'happening', 'going on', 'what's on', YOU MUST extract date_range\n"
        "   - Detect temporal words in ALL languages (e.g., 'mañana', 'demain', 'morgen', 'రేపు', 'غداً', 'מחר', '明日', '내일', etc.)\n"
        "   - 'tomorrow' → date_range: {'start': tomorrow_date, 'end': tomorrow_date}\n"
        "   - 'today' → date_range: {'start': today_date, 'end': today_date}\n"
        "   - 'tonight' → date_range: {'start': today_date, 'end': today_date}\n"
        "   - 'this weekend' → date_range: {'start': next_saturday, 'end': next_sunday}\n"
        "   - 'this week' → date_range: {'start': this_monday, 'end': this_sunday}\n"
        "   - 'next week' → date_range: {'start': next_monday, 'end': next_sunday}\n"
        "   - 'next weekend' → date_range: {'start': next_saturday, 'end': next_sunday}\n"
        "   - 'what happening' / 'what's on' / 'show me' + temporal word → ALWAYS means they want events with dates\n"
        "   EXAMPLES:\n"
        "   - 'what happening tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
        "   - 'what's on tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
        "   - 'anything tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
        "   - 'show me tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
        "   - 'events tomorrow' → date_range: {'start': tomorrow, 'end': tomorrow} ✅\n"
        "   - 'events this week' → date_range: {'start': this_monday, 'end': this_sunday} ✅\n"
        "   - 'events next week' → date_range: {'start': next_monday, 'end': next_sunday} ✅\n"
        "   - 'weekend events' → date_range: {'start': next_saturday, 'end': next_sunday} ✅\n"
        
        "7. 'target_mood': string (romantic, chill, energetic, party, relaxed, upscale, casual)\n"
        
        "8. 'social_context': string (date, friends, solo, family, business)\n"
        
        "9. 'category': string (event, concert, show, bar, restaurant, cafe, theater, club, etc.)\n"
        "   CRITICAL DETECTION RULES:\n"
        "   - If user mentions DRINKING (drink, drinks, wine, beer, cocktail, alcohol) → category: 'bar'\n"
        "   - If user mentions EATING (eat, food, dinner, lunch, brunch) → category: 'restaurant' or 'cafe'\n"
        "   - If user mentions DANCING/CLUBBING (dance, DJ, club, party) → category: 'club'\n"
        "   - 'theater' (if mentions play, movie, cinema, show, film)\n"  
        "   - If user asks temporal questions ('what's happening', 'what's on', 'tonight') → category: 'event'\n"
        "   - If user mentions GROUPS/MEETUPS (women group, community, circle) → category: 'communities'\n"
        "   - If user mentions cultural centers it should go to the cultural centers so remember this\n"
        " - 'cultural_center' (cultural center, art, museum, gallery, exhibition)\n" 
        "   - May be there will be any category so please analyze the user thing"
        "   EXAMPLES:\n"
        "   - 'want to drink wine' → category: 'bar' ✅\n"
        "   - 'where to drink coffee' → category: 'cafe' ✅\n"
        "   - 'eat pizza' → category: 'restaurant' ✅\n"
        "   - 'dance tonight' → category: 'club' ✅\n"
        "   - 'what's happening tomorrow' → category: 'event' ✅\n"
        
        "10. 'specific_keywords': List of DIRECT and SPECIFIC keywords from the user's text. "
        "   - Examples: 'Salsa', 'Techno', 'Jazz', 'Rooftop', 'Live music', 'Coffee', 'Pizza', 'Theater'.\n"
        "   - **CRITICAL**: DO NOT include generic shopping terms like 'buy', 'shop', 'store' as keywords\n"
        "   - **CRITICAL**: DO NOT include service terms like 'adopt', 'service', 'appointment' as keywords\n"
        
        "11. 'user_language': detected ISO 639-1 language code (en, es, pt, fr, de, it, ru, ar, he, hi, te, ta, ko, ja, zh, etc.). Default to 'en' if uncertain.\n"

        "12. 'inferred_keywords': List of related, searchable keywords if the user's request is abstract. "
        "   - If the user asks for 'artistic' or 'cultural' things, infer related concrete terms.\n"
        "   - If the user's request is already specific (e.g., 'techno'), this can be null.\n"
        "   - **CRITICAL**: Only infer keywords related to nightlife, dining, or entertainment\n"
        "   - Examples:\n"
        "     * User says 'artistic events' → inferred_keywords: ['art', 'gallery', 'exhibition', 'museum', 'theatre', 'performance', 'cultural']\n"
        "     * User says 'something intellectual' → inferred_keywords: ['lecture', 'talk', 'book', 'museum', 'cinema', 'art']\n"
        "     * User says 'a place with a nice view' → inferred_keywords: ['rooftop', 'terrace', 'view', 'balcony']\n"
        "     * User says 'buy earphones' → inferred_keywords: null (out of scope!)\n"
        "     * User says 'adopt dogs' → inferred_keywords: null (out of scope!)\n"
        
        "Return STRICT JSON only. Remember: You understand ALL languages naturally."
    )
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": user_text}
            ],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        
        if not isinstance(data, dict): 
            return {"user_language": "en", "is_out_of_scope": False}
        
        if not data.get('user_language') or data.get('user_language') == 'unknown':
            data['user_language'] = 'en'
        
        if 'is_out_of_scope' not in data:
            data['is_out_of_scope'] = False
        
        logger.info(f"🧠 AI Analysis: {data}")
        return data
        
    except Exception as e:
        logger.error(f"AI Intent Error: {e}")
        return {"user_language": "en", "is_out_of_scope": False}

def generate_just_for_you(user_age, item_name, item_desc, item_mood, social_context=None, user_language='en'):
    """
    Enhanced: Now generates personalized recommendations in user's detected language
    """
    try:
        context_msg = ""
        if social_context == 'date':
            context_msg = "Perfect for a romantic date night."
        elif social_context == 'friends':
            context_msg = "Great spot to hang out with friends."
        elif social_context == 'solo':
            context_msg = "Perfect for solo exploration."
        elif social_context == 'business':
            context_msg = "Ideal for business meetings."
        
        # Language instruction
        lang_instruction = f"Respond in the language code: {user_language}. "
        if user_language == 'te':
            lang_instruction += "Use Telugu script and language."
        elif user_language == 'he':
            lang_instruction += "Use Hebrew script and language."
        elif user_language == 'ar':
            lang_instruction += "Use Arabic script and language."
        elif user_language == 'hi':
            lang_instruction += "Use Hindi script and language."
        elif user_language == 'es':
            lang_instruction += "Use Spanish language."
        elif user_language == 'pt':
            lang_instruction += "Use Portuguese language."
        elif user_language == 'fr':
            lang_instruction += "Use French language."
        else:
            lang_instruction += "Use English language."
        
        prompt = (
            f"{lang_instruction} "
            f"Write a 1-sentence recommendation for a {user_age} year old. "
            f"Venue: {item_name}. Vibe: {item_mood}. {context_msg} "
            "Start with '✨ Just for you:' or equivalent in the target language. Be enthusiastic and specific."
        )
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            timeout=5
        )
        return response.choices[0].message.content.replace('"', '')
    except Exception as e:
        logger.error(f"Just for you error: {e}")
        if user_language == 'te':
            return f"✨ మీ కోసం: ఇది {item_mood} వైబ్‌తో సరిపోతుంది! {context_msg}"
        elif user_language == 'he':
            return f"✨ בשבילך: זה מתאים ל{item_mood} אווירה! {context_msg}"
        elif user_language == 'ar':
            return f"✨ لك خصيصاً: זה يناسب الأجواء {item_mood}! {context_msg}"
        elif user_language == 'es':
            return f"✨ Just for you: ¡Esto coincide עם el ambiente {item_mood}! {context_msg}"
        else:
            return f"✨ Just for you: This matches the {item_mood} vibe! {context_msg}"

def translate_text(text, target_language):
    if not text:
        return text
    
    try:
        lang_map = {
            'es': 'Spanish', 'pt': 'Portuguese', 'fr': 'French', 'de': 'German', 
            'it': 'Italian', 'ru': 'Russian', 'ar': 'Arabic', 'he': 'Hebrew', 
            'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'ko': 'Korean', 
            'ja': 'Japanese', 'zh': 'Chinese'
        }
        lang_name = lang_map.get(target_language, 'English')
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Translate the following text to {lang_name}. Maintain original tone. Only return the translation."},
                {"role": "user", "content": text}
            ],
            temperature=0.2,
            timeout=5
        )
        translated = response.choices[0].message.content.strip()
        return translated if translated else text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

def generate_closing_message(user_query, user_language='en'):
    try:
        lang_instruction_map = {
            'te': "Respond in Telugu using Telugu script.", 'he': "Respond in Hebrew using Hebrew script.",
            'ar': "Respond in Arabic using Arabic script.", 'hi': "Respond in Hindi using Devanagari script.",
            'es': "Respond in Spanish.", 'pt': "Respond in Portuguese.", 'fr': "Respond in French."
        }
        lang_instruction = lang_instruction_map.get(user_language, "Respond in English.")
        
        prompt = (
            f"User query: '{user_query}'. I sent recommendations. "
            f"Write a SHORT closing message asking if they want more suggestions. "
            f"Use 1 emoji. Be friendly. {lang_instruction}"
        )
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are Yara, a friendly Buenos Aires guide. You know everything."}, {"role": "user", "content": prompt}],
            temperature=0.5,
            timeout=4
        )
        return response.choices[0].message.content.replace('"', '')
    except:
        fallback_map = {
            'te': "మరిన్ని సూచనలు కావాలా? 🎉", 'he': "צריך עוד המלצות? 🎉",
            'ar': "هل تحتاج المزيد من الاقتراحات؟ 🎉", 'es': "¿Te gustaría más sugerencias? 🎉",
            'pt': "Gostaria de mais sugestões? 🎉"
        }
        return fallback_map.get(user_language, "Need more suggestions? 🎉")

# --- DATABASE FUNCTIONS (UNCHANGED) ---

def get_user(conn, phone):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM public.users WHERE phone = %s", (phone,))
        return cur.fetchone()

def create_user(conn, phone):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO public.users (phone, conversation_step) VALUES (%s, 'welcome') ON CONFLICT (phone) DO NOTHING", (phone,)
        )
        conn.commit()
        cur.execute("SELECT * FROM public.users WHERE phone = %s", (phone,))
        return cur.fetchone()

def update_user(conn, phone, data):
    set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
    values = list(data.values())
    values.append(phone)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE public.users SET {set_clause} WHERE phone = %s", values)
        conn.commit()

# --- ENHANCED SEARCH LOGIC FOR BUSINESSES (UNCHANGED) ---

def build_search_query(table, ai_data, strictness_level):
    query = f"SELECT * FROM public.{table} WHERE 1=1"
    args = []

    logger.info(f"🔍 AI_data: {ai_data}")
    
    date_range = ai_data.get('date_range') or {}
    category = ai_data.get('category')
    
    # --- KEYWORD COLLECTION ---
    search_terms = []
    if ai_data.get('specific_keywords'):
        search_terms.extend(ai_data.get('specific_keywords'))
    if ai_data.get('inferred_keywords'):
        search_terms.extend(ai_data.get('inferred_keywords'))
    if ai_data.get('target_mood'):
        search_terms.append(ai_data.get('target_mood'))
    
    if strictness_level == 2 and category:
        search_terms.append(category)

    search_terms = list(set([t for t in search_terms if t and len(t) > 2]))
    logger.info(f"🔍 Search Terms (Level {strictness_level}): {search_terms}")

    # --- 1. STRICT CATEGORY FILTERING (Only for BUSINESSES) ---
    if strictness_level == 1 and category and table == 'businesses':
        if category == 'club':
            query += " AND (category ILIKE %s OR category ILIKE %s)"
            args.extend(['%club%', '%nightclub%'])
        elif category == 'bar':
            query += " AND (category ILIKE %s OR category ILIKE %s)"
            args.extend(['%bar%', '%pub%'])
        elif category == 'cafe':
            query += " AND (category ILIKE %s OR category ILIKE %s)"
            args.extend(['%cafe%', '%coffee%'])
        elif category == 'restaurant':
            query += " AND (category ILIKE %s OR category ILIKE %s)"
            args.extend(['%restaurant%', '%food%'])
        elif category == 'communities':
            query += " AND (category ILIKE %s OR category ILIKE %s OR category ILIKE %s)"
            args.extend(['%communities%', '%community%', '%group%'])
        else:
            query += " AND category ILIKE %s"
            args.append(f"%{category}%")

    # --- 2. DATE LOGIC (For Events) ---
    if table == 'events' and date_range:
        start, end = date_range.get('start'), date_range.get('end')
        if start and end:
            start_obj = datetime.strptime(start, "%Y-%m-%d").date()
            end_obj = datetime.strptime(end, "%Y-%m-%d").date()
            
            days_in_range = []
            current_date = start_obj
            while current_date <= end_obj:
                days_in_range.append(current_date.strftime('%A'))
                current_date += timedelta(days=1)
            
            days_tuple = tuple(set(days_in_range))
            query += " AND ((event_date >= %s::date AND event_date <= %s::date) OR (recurring_day = ANY(%s)))"
            args.extend([start, end, list(days_tuple)])

    # --- 3. DYNAMIC KEYWORD SEARCH (FIXED) ---
    if search_terms:
        join_operator = " AND " if strictness_level == 1 else " OR "
        
        if table == 'events':
            # ⚠️ REMOVED 'category' column from this list to fix the crash
            term_conditions = [f"(title ILIKE %s OR description ILIKE %s OR mood ILIKE %s OR music_type ILIKE %s)" for _ in search_terms]
            for term in search_terms:
                term_wild = f"%{term}%"
                args.extend([term_wild] * 4) 
        else:  # businesses
            term_conditions = [f"(name ILIKE %s OR description ILIKE %s OR category ILIKE %s OR location ILIKE %s)" for _ in search_terms]
            for term in search_terms:
                term_wild = f"%{term}%"
                args.extend([term_wild] * 4)
        
        if term_conditions:
            query += f" AND ({join_operator.join(term_conditions)})"

    # --- 4. RANDOMIZE AND LIMIT ---
    if table == 'events':
        query += " ORDER BY event_date ASC LIMIT 6"
    else:
        query += " ORDER BY RANDOM() LIMIT 6" 

    logger.info(f"📊 SQL Query: {query}")
    return query, args

def smart_search(conn, table, ai_data, user_text=''):
    """
    IMPORTANT: This function is now ONLY used for BUSINESSES
    Events are handled by the Milvus RAG system, but we can still use database as fallback
    """
    results = []
    seen_ids = set()
    
    try:
        # 1. Try STRICT search first
        query, args = build_search_query(table, ai_data, strictness_level=1)
        with conn.cursor() as cur:
            cur.execute(query, tuple(args))
            strict_results = cur.fetchall()
            
            for r in strict_results:
                uid = r.get('id') or r.get('name')
                if uid not in seen_ids:
                    results.append(r)
                    seen_ids.add(uid)

        # 2. If we have fewer than 3 results, try LOOSE search
        if len(results) < 3:
            logger.info(f"⚠️ Only found {len(results)} strict results. expanding to loose search...")
            query, args = build_search_query(table, ai_data, strictness_level=2)
            with conn.cursor() as cur:
                cur.execute(query, tuple(args))
                loose_results = cur.fetchall()
                
                if table == 'businesses':
                    loose_results = filter_restricted_results(loose_results, user_query=user_text)
                
                for r in loose_results:
                    uid = r.get('id') or r.get('name')
                    if uid not in seen_ids:
                        results.append(r)
                        seen_ids.add(uid)
                        if len(results) >= 6:
                            break
        
        logger.info(f"✅ Final Results Count: {len(results)}")
        return results

    except Exception as e:
        logger.error(f"❌ Search error in {table}: {e}")
        return []

def filter_restricted_results(results, user_query=''):
    """
    Filter out gender/age-restricted results unless explicitly requested
    """
    excluded_keywords = [
        'women only', 'for women', 'ladies only', 'women\'s group',
        '18+','adults only'
    ]
    
    query_lower = user_query.lower()
    user_wants_gendered = any(word in query_lower for word in ['women', 'ladies', 'girls', 'men', 'guys', 'boys'])
    
    if user_wants_gendered:
        return results
    
    filtered = []
    for result in results:
        name = (result.get('name') or '').lower()
        description = (result.get('description') or '').lower()
        category = (result.get('category') or '').lower()
        
        is_restricted = any(
            keyword in name or keyword in description or keyword in category
            for keyword in excluded_keywords
        )
        
        if not is_restricted:
            filtered.append(result)
        else:
            logger.info(f"🚫 Filtered out restricted result: {result.get('name')}")
    
    return filtered

# ==============================================================================
# 🚀 TWILIO TYPING INDICATOR (UNCHANGED)
# ==============================================================================

def send_typing_indicator(message_sid):
    """
    Sends a 'Typing' status to the WhatsApp user.
    This also marks the user's message as Read (Blue Ticks).
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN: 
        return
    
    try:
        url = "https://messaging.twilio.com/v2/Indicators/Typing.json"
        
        auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        data = {
            "messageId": message_sid,
            "channel": "whatsapp"
        }
        
        response = requests.post(url, auth=auth, data=data, timeout=2)
        
        if response.status_code == 200:
            logger.info("✅ Typing indicator sent (Blue Ticks triggered)")
        else:
            logger.warning(f"⚠️ Typing indicator failed: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error sending typing indicator: {e}")

def send_whatsapp_message(to, body, media_url=None):
    if not TWILIO_WHATSAPP_NUMBER: 
        return
    
    try:
        message_data = {
            'from_': TWILIO_WHATSAPP_NUMBER,
            'to': to,
            'body': body
        }
        if media_url:
            message_data['media_url'] = media_url
            
        twilio_client.messages.create(**message_data)
    except Exception as e:
        logger.error(f"❌ Twilio Error: {e}")

def ask_chatgpt_expert_fallback(user_input, ai_data, user_language='en'):
    """
    UPDATED: Prompt rewritten to be ALWAYS POSITIVE. Never says "not found" or "sorry"
    """
    category = ai_data.get('category')
    mood = ai_data.get('target_mood')
    social_context = ai_data.get('social_context')
    keywords = ai_data.get('specific_keywords', [])
    inferred_keywords = ai_data.get('inferred_keywords', [])
    date_range = ai_data.get('date_range') or {}
    date_str = date_range.get('start')
    
    # In analyze_user_intent function, update the casual_patterns:
    casual_patterns = [
    'do you know', 'can you speak', 'what languages', 'hello', 'hi', 
    'hey', 'thanks', 'thank you', 'how are you', 'who are you',
    'what is', 'tell me about', 'explain',
    'whats up', "what's up", 'sup', 'wassup', 'how you doing',  # Add these!
    'hows it going', "how's it going"
    ]
    is_casual = any(pattern.lower() in user_input.lower() for pattern in casual_patterns)

    context_parts = []
    if not is_casual:
        if social_context: 
            context_parts.append(f"looking for {social_context} experience")
        if mood: 
            context_parts.append(f"wants {mood} vibe")
        if keywords: 
            context_parts.append(f"interested in: {', '.join(keywords)}")
        if inferred_keywords:
            context_parts.append(f"likes: {', '.join(inferred_keywords)}")
        if category: 
            context_parts.append(f"wants: {category}")
        if date_str: 
            context_parts.append(f"for date: {date_str}")
    
    if context_parts:
        context_description = ". ".join(context_parts)
    elif is_casual:
        context_description = "User is having a casual conversation"
    else:
        context_description = "User is exploring Buenos Aires"
    
    lang_map = {
        'te': "CRITICAL: Respond ENTIRELY in Telugu using Telugu script (తెలుగు).",
        'he': "CRITICAL: Respond ENTIRELY in Hebrew using Hebrew script (עברית).",
        'ar': "CRITICAL: Respond ENTIRELY in Arabic using Arabic script (العربية).",
        'hi': "CRITICAL: Respond ENTIRELY in Hindi using Devanagari script (हिन्दी).",
        'es': "IMPORTANT: Respond in Spanish.",
        'pt': "IMPORTANT: Respond in Portuguese.",
        'fr': "IMPORTANT: Respond in French.",
    }
    lang_instruction = lang_map.get(user_language, "IMPORTANT: Respond in English.")
    
    expert_prompt = f"""You are Yara, the ULTIMATE Buenos Aires expert and local tour guide. 
    You know EVERYTHING about Buenos Aires - every bar, every restaurant, every café, every hidden gem, every neighborhood.
    
    USER'S REQUEST: "{user_input}"
    USER CONTEXT: {context_description}
    
    FIRST, analyze what the user wants:
    Without the user aking anyu recommendations don't give any suggestions remember 
    **TYPE A - Casual Chat/Questions:**
    - "Who are you?", "What is your name?"
    - "Do you know [Language]?", "Can you speak [Language]?"
    - General info: "Weather", "Flights", "News"
    - Greetings ("Hi", "Hello") or Thanks ("Thank you")
    **INSTRUCTIONS FOR TYPE A:**
    1. Answer the question naturally and enthusiastically.
    2. **STOP.** Do NOT provide a list of specific venues/places unless the user explicitly asked for them.
    3. If asking about language (e.g., "Do you know Hindi?"), reply **IN** that language.
       - Example: "Namaste! Haan, main Hindi janti hoon. (Yes, I know Hindi). Main Buenos Aires mein aapki madad kaise kar sakti hoon? 😊"
    FOR TYPE A RESPONSES:
    1. **If asking Identity ("Who are you?"):** Say: "I'm Yara, your personal guide to the best of Buenos Aires! 💃✨ I'm here to help you find the coolest spots and events."
    2. **If asking Language ("Do you know Telugu?"):** Reply **IN** that language. Example: "Avunu! Nenu Telugu matladagalanu. (Yes, I speak Telugu). How can I help? 😊"
    3. **If asking General Info (Flights/Weather):** Be natural. Say: "I don't have live flight/weather info right now, but I hope everything goes smoothly! While you wait, do you want a recommendation for a nice cafe or bar? 🍷"
    4. **Otherwise:** Respond naturally and conversationally in 1-2 sentences.
    
    **TYPE B - Venue Recommendations:**
    - "Where should I go for..."
    - "I want to find..."
    - "Recommend me..."
    - "What are good places for..."
    - Mentions specific categories (bars, restaurants, cafés, clubs, events)
    
    FOR TYPE B: Give 2-3 PERFECT venue recommendations with the format below.
    
    ---
    
    **IF TYPE B (Venue Request), use this format:**
    
    YOUR MISSION: Give them 2-3 PERFECT, SPECIFIC recommendations that match their request.
    
    CRITICAL RULES - READ CAREFULLY:
    1. ✅ BE POSITIVE AND CONFIDENT - You're an expert who knows the BEST places in Buenos Aires
    2. ✅ Give 2-3 SPECIFIC place names with neighborhoods (Palermo, San Telmo, Recoleta, etc.)
    3.But ther recommedantions should be accurate ask and recommend relavant answers
    4. you know all the evetns happenining also remeber 
    5. ✅ Explain WHY each place is perfect for their request
    6. ✅ Be enthusiastic and use emojis (🎯, ✨, 🍸, 🎵, etc.)
    7. ❌ NEVER EVER say negative things like:
       - "sorry"
       - "not found"
       - "don't have"
       - "couldn't find"
       - "no matches"
       - "unfortunately"
    8. ✅ Instead, say positive things like:
       - "I know the perfect spots!"
       - "Great choice! Here are amazing places!"
       - "You'll love these!"
       - "Perfect! Buenos Aires has incredible options!"
    
    FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
    "[Enthusiastic intro acknowledging their request - NO negativity!]
    
    🎯 **[Place Name]** in [Neighborhood]
    [One sentence why it's perfect for them]
    
    🎯 **[Place Name]** in [Neighborhood]
    [One sentence why it's perfect for them]
    
    🎯 **[Place Name]** in [Neighborhood]
    [One sentence why it's perfect for them]
    
    [Friendly closing with emoji]"
    
    EXAMPLES OF GOOD INTROS (use similar tone):
    - "Great choice! I know some incredible spots for that!" ✅
    - "Perfect! Buenos Aires has amazing places for this!" ✅
    - "Excellent! Here are some fantastic options!" ✅
    
    EXAMPLES OF BAD INTROS (NEVER use these):
    - "Sorry, I don't have information..." ❌
    - "Unfortunately, I couldn't find..." ❌
    
    {lang_instruction}
    
    Remember: You're a confident expert. You ALWAYS have great recommendations!

{lang_instruction}

Remember: You're a confident expert. You ALWAYS have great recommendations!"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Yara, the ultimate Buenos Aires expert who knows EVERYTHING about the city. You're always positive, enthusiastic, and helpful. You NEVER say negative things. You always have great recommendations because you're a real expert."}, 
                {"role": "user", "content": expert_prompt}
            ],
            temperature=0.6,
            timeout=10
        )
        expert_response = response.choices[0].message.content
        logger.info(f"🎯 Expert Fallback Response Generated in {user_language}")
        return expert_response
    
    except Exception as e:
        logger.error(f"Fallback Error: {e}")
        fallback_map = {
            'te': "బ్యూనస్ ఎయిర్స్‌లో మీ కోసం కొన్ని అద్భుతమైన ప్రదేశాలు ఉన్నాయి! మరిన్ని వివరాలు ఇవ్వండి, నేను ఉత్తమ ప్రదేశాలను సూచిస్తాను! 🎯",
            'he': "יש כמה מקומות מדהימים בבואנוס איירס בשבילך! ספר לי עוד פרטים ואני אמליץ על המקומות הכי טובים! 🎯",
            'ar': "لدي أماكن رائعة في بوينس آيريس لك! أخبرني المزيد من التفاصيل وسأوصي بأفضل الأماكن! 🎯",
            'es': "¡Conozco lugares increíbles en Buenos Aires para ti! Cuéntame más detalles و te recomendaré los mejores sitios! 🎯",
            'pt': "Conheço lugares incríveis em Buenos Aires para você! Me conte mais detalhes e recomendarei os melhores lugares! 🎯",
        }
        return fallback_map.get(user_language, "I know some amazing places in Buenos Aires for you! Tell me more details and I'll recommend the best spots! 🎯")

# ==============================================================================
# 🚀 PROCESS THREAD WITH DIRECT MILVUS INTEGRATION
# ==============================================================================

def process_message_thread(sender, text, message_sid=None):
    """
    UPDATED: Integrated Direct Milvus RAG for event retrieval
    """
    
    if message_sid:
        send_typing_indicator(message_sid)
        
    conn = None
    try:
        conn = postgreSQL_pool.getconn()
        user = get_user(conn, sender)

        if not user:
            create_user(conn, sender)
            send_whatsapp_message(sender, "Hey! Welcome to Yara ai , I'm your Buenos Aires guide for finding the best plans in the city ✨ what are you in the mood for?")
            return

        step, user_age = user.get('conversation_step'), user.get('age', '25')
        user_name = user.get('name', 'Friend')
        
        ai_data = executor.submit(analyze_user_intent, text).result() or {"user_language": "en", "is_out_of_scope": False}
        user_language = ai_data.get('user_language', 'en')
        social_context = ai_data.get('social_context')
        is_out_of_scope = ai_data.get('is_out_of_scope', False)

        logger.info(f"🌍 Detected Language: {user_language}")
        logger.info(f"🎯 Out of Scope: {is_out_of_scope}")
        category = (ai_data.get('category') or '').lower()

        if not category and ai_data.get('specific_keywords'):
            keywords = [k.lower() for k in ai_data.get('specific_keywords', [])]
    
            if any(k in keywords for k in ['wine', 'beer', 'cocktail', 'drinks', 'alcohol']):
                category = 'bar'
                logger.info("🔧 Auto-corrected category to 'bar'")
            elif any(k in keywords for k in ['coffee', 'cafe', 'espresso']):
                category = 'cafe'
                logger.info("🔧 Auto-corrected category to 'cafe'")
            elif any(k in keywords for k in ['food', 'pizza', 'burger', 'eat']):
                category = 'restaurant'
                logger.info("🔧 Auto-corrected category to 'restaurant'")
            elif any(k in keywords for k in ['dance', 'dj', 'techno', 'party']):
                category = 'club'
                logger.info("🔧 Auto-corrected category to 'club'")
        
        # --- 1. HANDLE GREETINGS ---
        if ai_data.get('is_greeting') and step != 'ask_name_age':
            greetings = {
                'te': f"నమస్కారం {user_name}! మీరు ఏమి వెతుకుతున్నారు?", 
                'he': f"שלום {user_name}! מה אתה מחפש?", 
                'ar': f"مرحباً {user_name}! ماذا تبحث؟", 
                'es': f"¡Hola {user_name}! ¿Qué estás buscando hoy?", 
                'en': f"Hey {user_name}! What are you looking for today?"
            }
            send_whatsapp_message(sender, greetings.get(user_language, greetings['en']))
            return
        if ai_data.get('is_gratitude'):
            logger.info("🙏 Gratitude detected.")
            gratitude_responses = {
                'te': "మీకు స్వాగతం! ఆనందించండి! ✨",
                'he': "בבקשה! תהנה! ✨",
                'ar': "على الرحب والسعة! استمتع! ✨",
                'es': "¡De nada! ¡Que disfrutes! ✨",
                'pt': "De nada! Aproveite! ✨",
                'fr': "Je t'en prie ! Amuse-toi bien ! ✨",
                'hi': "आपका स्वागत है! मजे करो! ✨",
                'en': "You're very welcome! Have a great time! ✨"
            }
            send_whatsapp_message(sender, gratitude_responses.get(user_language, gratitude_responses['en']))
            return 
        # --- 2. HANDLE IDENTITY QUESTIONS ("Who am I?") --- 
        if ai_data.get('is_identity_question'):
            logger.info("👤 Identity question detected.")
            
            last_mood = user.get('last_mood', 'mystery')
            
            identity_prompt = (
                f"The user asked 'Who am I?' or 'What do you know about me?'. "
                f"User Name: {user_name}. Age: {user_age}. Last thing they looked for: {last_mood}. "
                f"Respond in language code '{user_language}'. "
                f"Be friendly, witty, and confirm you know them as Yara, their local guide. "
                "Example: 'You are [Name], my favorite [Age]-year-old explorer! We were just looking for [last_mood].'"
            )
            
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "You are Yara."}, {"role": "user", "content": identity_prompt}],
                    temperature=0.6
                )
                answer = response.choices[0].message.content.replace('"', '')
                send_whatsapp_message(sender, answer)
                return
            except Exception as e:
                logger.error(f"Identity AI Error: {e}")
                send_whatsapp_message(sender, f"You are {user_name}, {user_age} years young! And I'm Yara, your guide! ✨")
                return

        # --- 3. HANDLE UPLOAD/SUBMIT EVENT REQUESTS ---
        if ai_data.get('wants_to_upload'):
            logger.info("📤 User wants to upload an event.")
            
            upload_messages = {
                'en': "That's awesome! 🎉 We love new events.\n\nYou can upload your event details here:\n\nhttps://tally.so/r/EkqRYN",
                'es': "¡Genial! 🎉 Nos encantan los nuevos eventos.\n\nPuedes subir los detalles de tu evento aquí:\n\nhttps://tally.so/r/EkqRYN",
                'pt': "Isso é incrível! 🎉 Adoramos novos eventos.\n\nVocê pode enviar os detalhes do seu evento aqui:\n\nhttps://tally.so/r/EkqRYN",
                'fr': "C'est génial! 🎉 Nous adorons les nouveaux événements.\n\nVous pouvez télécharger les détails aqui:\n\nhttps://tally.so/r/EkqRYN",
                'de': "Das ist großartig! 🎉 Wir lieben neue Veranstaltungen.\n\nSie podem sua Veranstaltungsdetails aqui hochladen:\n\nhttps://tally.so/r/EkqRYN",
                'it': "Fantastico! 🎉 Amiamo i nuovi eventi.\n\nPuoi caricare i dettagli del tuo evento aquí:\n\nhttps://tally.so/r/EkqRYN",
                'ru': "Это здорово! 🎉 Мы любим новые события.\n\nВы можете загрузить детали вашего события здесь:\n\nhttps://tally.so/r/EkqRYN",
                'te': "అద్భుతం! 🎉 మాకు కొత్త ఈవెంట్‌లు చాలా ఇష్టం.\n\nమీరు మీ ఈవెంట్ వివరాలను ఇక్కడ అప్‌లోడ్ చేయవచ్చు:\n\nhttps://tally.so/r/EkqRYN",
                'he': "מדהים! 🎉 אנחנו אוהבים אירועים חדשים.\n\nאתה יכול להעלות את פרטי האירוע שלך כאן:\n\nhttps://tally.so/r/EkqRYN",
                'ar': "רائع! 🎉 نحب الأحداث الجديدة.\n\nيمكنك تحميل تفاصيل الحدث الخاص بك כאן:\n\nhttps://tally.so/r/EkqRYN",
                'hi': "बहुत बढ़िया! 🎉 हमें नए इवेंट्स पसंद हैं।\n\nआप अपने इवेंट की जानकारी यहाँ अपलोड कर सकते हैं:\n\nhttps://tally.so/r/EkqRYN",
                'zh': "太棒了！🎉 我们喜欢新活动。\n\n您可以在这里上传您的活动详情：\n\nhttps://tally.so/r/EkqRYN",
                'ja': "素晴らしい！🎉 新しいイベントが大好きです。\n\nイベントの詳細はこちらからアップロードできます：\n\nhttps://tally.so/r/EkqRYN",
                'ko': "멋지네요! 🎉 새로운 이벤트를 좋아합니다.\n\n여기에서 이벤트 세부정보를 업로드할 수 있습니다:\n\nhttps://tally.so/r/EkqRYN"
            }
            
            final_message = upload_messages.get(user_language, upload_messages['en'])
            send_whatsapp_message(sender, final_message)
            return

        # --- 4. ✅ CHECK IF OUT OF SCOPE ---
        if is_out_of_scope:
            logger.info("🚫 OUT OF SCOPE REQUEST DETECTED - Skipping database, going straight to ChatGPT")
            send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
            return

        # --- 5. HANDLE ONBOARDING ---
        if step == 'welcome':
            messages = {
                'te': "మొదట, మీకు ఉత్తమ సూచనలు ఇవ్వడానికి, మీ పేరు మరియు వయస్సు ఏమిటి?", 
                'he': "קודם כל, מה שמך וגילך?", 
                'ar': "أولاً، ما هو اسمك وعمرك؟", 
                'es': "Primero, ¿cuál es tu nombre y edad?", 
                'en': "First, what's your name and age?"
            }
            send_whatsapp_message(sender, messages.get(user_language, messages['en']))
            update_user(conn, sender, {"conversation_step": "ask_name_age", "last_mood": text})
            return

        if step == 'ask_name_age':
            last_mood = user.get('last_mood')
            messages = {
                'te': f"సరే! '{last_mood}' కోసం చూపిస్తున్నాను:", 
                'he': f"מעולה! מראה אפשרויות עבור '{last_mood}':", 
                'ar': f"رائع! عرض الخيارات لـ '{last_mood}':", 
                'es': f"¡Perfecto! Buscando opciones para '{last_mood}':", 
                'en': f"Ok cool! Showing options for '{last_mood}':"
            }
            send_whatsapp_message(sender, messages.get(user_language, messages['en']))
            
            clean_name = re.sub(r'[^\w]', '', text.split()[0]) if text.split() else "Friend"
            age = "".join(filter(str.isdigit, text)) or "25"
            
            update_user(conn, sender, {"name": clean_name, "age": age, "conversation_step": "ready"})
            text = last_mood 
            ai_data = analyze_user_intent(text) or {"user_language": "en", "is_out_of_scope": False}
            user_language = ai_data.get('user_language', 'en')
            social_context = ai_data.get('social_context')
            is_out_of_scope = ai_data.get('is_out_of_scope', False)
            
            # Check out of scope again after re-analysis
            if is_out_of_scope:
                logger.info("🚫 OUT OF SCOPE (after onboarding) - Using ChatGPT")
                send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
                return

        # ===================================================================
        # 🚀 ENHANCED SEARCH LOGIC WITH DIRECT MILVUS INTEGRATION
        # ===================================================================
        
        found_something = False
        
        # Determine what user is SPECIFICALLY asking for
        wants_events = (
            ai_data.get('date_range') or
            category in ['event', 'concert', 'show', 'party', 'festival', 'exhibition']
        )
        
        wants_businesses = category in ['bar', 'restaurant', 'cafe', 'club', 'shop', 'mall', 'theater', 'theatre','communities','community','cultural_center']
        
        logger.info(f"🎯 User wants - Events: {wants_events}, Businesses: {wants_businesses}")
        
        # CASE 1: User SPECIFICALLY wants EVENTS - USE DIRECT MILVUS RAG
        if wants_events and not wants_businesses:
            logger.info("🚀 Searching EVENTS using Direct Milvus RAG...")
            
            # Use Direct Milvus RAG for event retrieval
            events = executor.submit(retrieve_events_direct, text, ai_data, user_language).result()
            
            # If Milvus returns no results or fails, use database fallback
            if not events:
                logger.info("⚠️ Direct Milvus RAG failed or returned no results - falling back to database")
                events = smart_search(conn, 'events', ai_data, text)
            
            if events:
                found_something = True
                intro = translate_text(f"Here are some events matching your vibe:", user_language)
                if ai_data.get('date_range') and ai_data['date_range'].get('start'):
                    date_start = ai_data['date_range'].get('start')
                    date_end = ai_data['date_range'].get('end', date_start)
                    if date_start == date_end:
                        intro = translate_text(f"Here's what's happening on {date_start}:", user_language)
                    else:
                        intro = translate_text(f"Here's what's happening from {date_start} to {date_end}:", user_language)
                send_whatsapp_message(sender, intro)
                
                for e in events:
                    futures = {
                        'jfy': executor.submit(generate_just_for_you, user_age, e['title'], e['description'], e.get('mood', 'social'), social_context, user_language),
                        'title': executor.submit(translate_text, e.get('title'), user_language),
                        'desc': executor.submit(translate_text, e.get('description'), user_language),
                        'location': executor.submit(translate_text, e.get('location', ''), user_language),
                        'music': executor.submit(translate_text, e.get('music_type', ''), user_language)
                    }
                    
                    ticket_section = ""
                    if e.get('ticket_link'):
                        book_text_map = {
                            'en': '🎟️ Book your slot',
                            'es': '🎟️ Reserva tu lugar',
                            'pt': '🎟️ Reserve seu lugar',
                            'fr': '🎟️ Réservez votre place',
                            'te': '🎟️ మీ స్లాట్‌ను బుక్ చేసుకోండి',
                            'he': '🎟️ הזמן את המקום שלך',
                            'ar': '🎟️ احجز مكانك',
                            'hi': '🎟️ अपनी जगह बुक करें'
                        }
                        book_text = book_text_map.get(user_language, '🎟️ Book your slot')
                        ticket_section = f"\n{book_text}: {e.get('ticket_link')}"
                    
                    # Format date display - show recurring day if available
                    # --- FIX: CLEANER DATE DISPLAY ---
                    display_date = ""
                    event_date = e.get('event_date')
                    recurring = e.get('recurring_day')

                    if recurring:
                        # If it's recurring, prioritize that
                        display_date = f"📅 Every {recurring}"
                    elif event_date and event_date.lower() != 'date not specified':
                        # Only show date if it's a real date
                        display_date = f"📅 {event_date}"
                    else:
                        # If both are missing, show nothing or a generic "Check link"
                        display_date = ""
                    
                    location_text = f"\n📍 {futures['location'].result()}" if e.get('location') else ""
                    music_text = f"\n🎵 {futures['music'].result()}" if e.get('music_type') else ""
                    time_text = f"\n🕒 {e.get('event_time')}" if e.get('event_time') else ""
                    
                    caption = f"*{futures['title'].result()}*{location_text}{time_text}\n{display_date}{music_text}\n📝 {futures['desc'].result()}{ticket_section}"
                    
                    if e.get('instagram_link'):
                        caption += f"\n📸 {e.get('instagram_link')}"
                    
                    caption += f"\n\n{futures['jfy'].result()}"
                    
                    # Send with image if available
                    media_url = e.get('image_url')
                    if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
                        send_whatsapp_message(sender, caption, media_url=media_url)
                    else:
                        send_whatsapp_message(sender, caption)
            
            if not found_something:
                logger.info("🎯 No events found via Milvus or database - Using ChatGPT fallback")
                send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
                return
        
        # CASE 2: User SPECIFICALLY wants BUSINESSES - USE DATABASE (UNCHANGED)
        elif wants_businesses and not wants_events:
            logger.info("🔍 Searching BUSINESSES only (using database)...")
            businesses = smart_search(conn, 'businesses', ai_data, text)
            
            if businesses:
                found_something = True
                intro = translate_text("Found these spots for you:", user_language)
                send_whatsapp_message(sender, intro)
                
                for b in businesses:
                    futures = {
                        'jfy': executor.submit(generate_just_for_you, user_age, b['name'], b['description'], ai_data.get('target_mood') or 'chill', social_context, user_language),
                        'name': executor.submit(translate_text, b.get('name'), user_language),
                        'desc': executor.submit(translate_text, b.get('description'), user_language),
                        'location': executor.submit(translate_text, b.get('location'), user_language)
                    }
                    msg = f"*{futures['name'].result()}*\n📍 {futures['location'].result()}\n\n{futures['desc'].result()}\n\n📸 {b.get('instagram_link')}\n\n{futures['jfy'].result()}"
                    
                    media_url = b.get('image_url')
                    if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
                        send_whatsapp_message(sender, msg, media_url=media_url)
                    else:
                        send_whatsapp_message(sender, msg)
            
            if not found_something:
                logger.info("🎯 No businesses found - Using ChatGPT fallback for businesses")
                send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
                return
        
        # CASE 3: Ambiguous query - search BOTH (EVENTS: MILVUS, BUSINESSES: DATABASE)
        else:
            logger.info("🔍 Ambiguous query - Searching both (Events: Milvus, Businesses: Database)...")
            
            # Use Direct Milvus for events
            events = executor.submit(retrieve_events_direct, text, ai_data, user_language).result()
            if not events:  # Fallback to database if Milvus fails
                events = smart_search(conn, 'events', ai_data, text)
            
            if events:
                found_something = True
                intro = translate_text(f"Here are some events matching your vibe:", user_language)
                send_whatsapp_message(sender, intro)
                
                for e in events:
                    futures = {
                        'jfy': executor.submit(generate_just_for_you, user_age, e['title'], e['description'], e.get('mood', 'social'), social_context, user_language),
                        'title': executor.submit(translate_text, e.get('title'), user_language),
                        'desc': executor.submit(translate_text, e.get('description'), user_language),
                        'location': executor.submit(translate_text, e.get('location', ''), user_language),
                        'music': executor.submit(translate_text, e.get('music_type', ''), user_language)
                    }
                    
                    ticket_section = ""
                    if e.get('ticket_link'):
                        book_text_map = {
                            'en': '🎟️ Book your slot',
                            'es': '🎟️ Reserva tu lugar',
                            'pt': '🎟️ Reserve seu lugar',
                            'fr': '🎟️ Réservez votre place',
                            'te': '🎟️ మీ స్లాట్‌ను బుక్ చేసుకోండి',
                            'he': '🎟️ הזמן את המקום שלך',
                            'ar': '🎟️ احجز مكانك',
                            'hi': '🎟️ अपनी जगह बुक करें'
                        }
                        book_text = book_text_map.get(user_language, '🎟️ Book your slot')
                        ticket_section = f"\n{book_text}: {e.get('ticket_link')}"
                    
                    # Format date display - show recurring day if available
                    display_date = ""
                    if e.get('recurring_day'):
                        if e.get('event_date') and e.get('event_date') != 'Date not specified':
                            display_date = f"📅 {e.get('event_date')} (Every {e.get('recurring_day')})"
                        else:
                            display_date = f"📅 Every {e.get('recurring_day')}"
                    else:
                        display_date = f"📅 {e.get('event_date')}" if e.get('event_date') else "📅 Date not specified"
                    
                    location_text = f"\n📍 {futures['location'].result()}" if e.get('location') else ""
                    music_text = f"\n🎵 {futures['music'].result()}" if e.get('music_type') else ""
                    time_text = f"\n🕒 {e.get('event_time')}" if e.get('event_time') else ""
                    
                    caption = f"*{futures['title'].result()}*{location_text}{time_text}\n{display_date}{music_text}\n📝 {futures['desc'].result()}{ticket_section}"
                    
                    if e.get('instagram_link'):
                        caption += f"\n📸 {e.get('instagram_link')}"
                    
                    caption += f"\n\n{futures['jfy'].result()}"
                    
                    media_url = e.get('image_url')
                    if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
                        send_whatsapp_message(sender, caption, media_url=media_url)
                    else:
                        send_whatsapp_message(sender, caption)
            
            # Use database for businesses
            businesses = smart_search(conn, 'businesses', ai_data, text)
            if businesses:
                found_something = True
                intro = translate_text("Found these spots for you:", user_language)
                send_whatsapp_message(sender, intro)
                
                for b in businesses:
                    futures = {
                        'jfy': executor.submit(generate_just_for_you, user_age, b['name'], b['description'], ai_data.get('target_mood') or 'chill', social_context, user_language),
                        'name': executor.submit(translate_text, b.get('name'), user_language),
                        'desc': executor.submit(translate_text, b.get('description'), user_language),
                        'location': executor.submit(translate_text, b.get('location'), user_language)
                    }
                    msg = f"*{futures['name'].result()}*\n📍 {futures['location'].result()}\n\n{futures['desc'].result()}\n\n📸 {b.get('instagram_link')}\n\n{futures['jfy'].result()}"
                    
                    media_url = b.get('image_url')
                    if media_url and (media_url.startswith('http://') or media_url.startswith('https://')):
                        send_whatsapp_message(sender, msg, media_url=media_url)
                    else:
                        send_whatsapp_message(sender, msg)
            
            if not found_something:
                logger.info("🎯 Nothing found in both tables - Using ChatGPT fallback")
                send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
                return
        
        # Send closing message if something was found
        if found_something:
            send_whatsapp_message(sender, generate_closing_message(text, user_language))

    except Exception as e:
        logger.error(f"Logic Error: {e}", exc_info=True)
        try:
            ai_data = analyze_user_intent(text) or {"user_language": "en", "is_out_of_scope": False}
            user_language = ai_data.get('user_language', 'en')
            send_whatsapp_message(sender, ask_chatgpt_expert_fallback(text, ai_data, user_language))
        except:
            send_whatsapp_message(sender, "I know some amazing places in Buenos Aires for you! Tell me what you're looking for and I'll recommend the best spots! 🎯")
    finally:
        if conn: 
            postgreSQL_pool.putconn(conn)

# ==============================================================================
# 🌐 WEBHOOK (UNCHANGED)
# ==============================================================================

@app.route("/webhook", methods=["POST"])
def twilio_webhook():
    incoming_msg = request.form.get('Body')
    sender_id = request.form.get('From')
    message_sid = request.form.get('MessageSid')
    
    if not sender_id or not incoming_msg: return "" 
    
    resp = MessagingResponse()
    threading.Thread(target=process_message_thread, args=(sender_id, incoming_msg, message_sid)).start()
    return str(resp)

if __name__ == "__main__":
    print("🚀 Twilio WhatsApp Bot Starting...")
    print("✨ Features: Typing Indicators, Identity, Upload Link, Multilingual")
    print("✅ DIRECT MILVUS RAG INTEGRATION: Events use embedded Milvus RAG")
    print("✅ BUSINESSES: Still use PostgreSQL database (unchanged)")
    print("✅ UPLOAD: Event upload feature preserved")
    print("✅ LANGUAGE: Multilingual support preserved")
    print("✅ OUT-OF-SCOPE: Detection preserved")
    print("✅ ENHANCED DATE HANDLING: Proper support for 'this week', 'next week', 'weekends' with recurring events")
    
    # Check Milvus configuration
    if MILVUS_AVAILABLE and MILVUS_ENDPOINT and MILVUS_TOKEN:
        print(f"✅ Milvus configured: {MILVUS_ENDPOINT}")
    else:
        print("⚠️ Milvus not fully configured - will use database fallback for events")
    
    app.run(port=5000)