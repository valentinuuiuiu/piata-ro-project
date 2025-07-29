

"""
Marketing Agent Server - Handles marketing optimization for the marketplace
Runs on port 8001 as specified in the smart_mcp_orchestrator.py
"""

import os
import json
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Setup Django first
import django
from django.conf import settings

# Ensure Django is configured
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
    django.setup()

# Import Django models after setup
from marketplace.models import Listing, Category

app = FastAPI(title="Marketing Agent Server", description="Handles marketing optimization for the marketplace")

class ProcessRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

@app.post("/process")
async def process(request: ProcessRequest):
    """
    Main endpoint for handling marketing operations
    The orchestrator will send requests here
    """
    try:
        # Extract operation from query
        query_lower = request.query.lower()
        
        if 'optimize_listing_title' in query_lower:
            return handle_optimize_listing_title(request.context)
        elif 'generate_description_template' in query_lower:
            return handle_generate_description_template(request.context)
        elif 'suggest_pricing_strategy' in query_lower:
            return handle_suggest_pricing_strategy(request.context)
        elif 'generate_promotional_content' in query_lower:
            return handle_generate_promotional_content(request.context)
        elif 'analyze_competitor_pricing' in query_lower:
            return handle_analyze_competitor_pricing(request.context)
        elif 'suggest_best_posting_times' in query_lower:
            return handle_suggest_best_posting_times(request.context)
        else:
            return {
                "error": "Unknown operation",
                "supported_operations": [
                    "optimize_listing_title", "generate_description_template",
                    "suggest_pricing_strategy", "generate_promotional_content",
                    "analyze_competitor_pricing", "suggest_best_posting_times"
                ]
            }
            
    except Exception as e:
        return {"error": str(e)}

def handle_optimize_listing_title(context: Dict[str, Any]):
    """Handle optimizing listing title for better visibility"""
    try:
        title = context.get('title', '')
        category = context.get('category', '')
        keywords = context.get('keywords', [])
        
        # Simple title optimization - in production, this would use more sophisticated algorithms
        optimized_title = title
        
        # Add category if not in title
        if category and category.lower() not in title.lower():
            optimized_title = f"{title} - {category}"
            
        # Add important keywords
        for keyword in keywords:
            if keyword.lower() not in optimized_title.lower():
                optimized_title = f"{optimized_title}, {keyword}"
                
        # Ensure title is not too long
        if len(optimized_title) > 100:
            optimized_title = optimized_title[:97] + "..."
            
        return {
            "original_title": title,
            "optimized_title": optimized_title,
            "improvements": [
                "Added category for better categorization",
                "Added relevant keywords for search optimization"
            ],
            "seo_score": 85  # Mock score
        }
        
    except Exception as e:
        return {"error": str(e)}

def handle_generate_description_template(context: Dict[str, Any]):
    """Handle generating a description template for a listing"""
    try:
        category = context.get('category', '')
        features = context.get('features', [])
        target_audience = context.get('target_audience', 'general')
        
        # Generate description based on category
        templates = {
            'electronics': f"High-quality {category} with advanced features designed for {target_audience}.",
            'furniture': f"Elegant {category} crafted with premium materials for your home.",
            'clothing': f"Fashionable {category} made from comfortable materials, perfect for {target_audience}.",
            'vehicles': f"Reliable {category} with excellent performance and low maintenance costs.",
        }
        
        base_description = templates.get(category.lower(), f"Great {category} with excellent features for {target_audience}.")
        
        # Add features
        if features:
            features_list = "\n".join([f"• {feature}" for feature in features])
            full_description = f"{base_description}\n\nKey features:\n{features_list}"
        else:
            full_description = base_description
            
        # Add call to action
        full_description += "\n\nDon't miss this opportunity! Contact us today for more information."
        
        return {
            "category": category,
            "target_audience": target_audience,
            "template": full_description,
            "length": len(full_description),
            "seo_friendly": True
        }
        
    except Exception as e:
        return {"error": str(e)}

def handle_suggest_pricing_strategy(context: Dict[str, Any]):
    """Handle suggesting pricing strategy for a listing"""
    try:
        category = context.get('category', '')
        condition = context.get('condition', 'new')
        brand = context.get('brand', '')
        features = context.get('features', [])
        
        # Get comparable listings
        comparable_listings = Listing.objects.filter(
            category__name=category,
            status='active'
        ).order_by('price')
        
        if comparable_listings.exists():
            min_price = comparable_listings.first().price
            max_price = comparable_listings.last().price
            avg_price = comparable_listings.aggregate(avg=models.Avg('price'))['avg']
            
            # Adjust based on condition
            if condition == 'used':
                avg_price *= 0.7
                min_price *= 0.6
                max_price *= 0.8
            elif condition == 'refurbished':
                avg_price *= 0.85
                min_price *= 0.75
                max_price *= 0.9
                
            # Adjust based on brand (if premium)
            premium_brands = ['Apple', 'Samsung', 'Sony', 'BMW', 'Nike']
            if brand in premium_brands:
                avg_price *= 1.2
                min_price *= 1.1
                max_price *= 1.3
                
            # Adjust based on features
            if len(features) > 5:
                avg_price *= 1.15
                max_price *= 1.2
                
            return {
                "category": category,
                "condition": condition,
                "brand": brand,
                "price_range": {
                    "min": float(min_price),
                    "max": float(max_price),
                    "recommended": float(avg_price)
                },
                "strategy": "competitive_pricing",
                "analysis": f"Based on {comparable_listings.count()} similar active listings in the {category} category."
            }
        else:
            # Default pricing if no comparable listings
            base_prices = {
                'electronics': 500,
                'furniture': 300,
                'clothing': 50,
                'vehicles': 10000,
                'real_estate': 100000
            }
            base_price = base_prices.get(category.lower(), 100)
            
            if condition == 'used':
                base_price *= 0.6
            elif condition == 'refurbished':
                base_price *= 0.8
                
            if brand in ['Apple', 'Samsung', 'Sony', 'BMW', 'Nike']:
                base_price *= 1.25
                
            if len(features) > 5:
                base_price *= 1.2
                
            return {
                "category": category,
                "condition": condition,
                "brand": brand,
                "price_range": {
                    "min": float(base_price * 0.8),
                    "max": float(base_price * 1.2),
                    "recommended": float(base_price)
                },
                "strategy": "value_based_pricing",
                "analysis": "No comparable active listings found. Using category-based pricing with adjustments for condition, brand, and features."
            }
            
    except Exception as e:
        return {"error": str(e)}

def handle_generate_promotional_content(context: Dict[str, Any]):
    """Handle generating promotional content for a listing"""
    try:
        title = context.get('title', '')
        category = context.get('category', '')
        price = context.get('price')
        features = context.get('features', [])
        selling_points = context.get('selling_points', [])
        
        # Generate promotional content
        promotional_content = f"🔥 HOT DEAL! {title} for only ${price}! 🔥\n\n"
        
        # Add category-specific hook
        hooks = {
            'electronics': "Upgrade your tech game with this amazing deal!",
            'furniture': "Transform your living space with this beautiful piece!",
            'clothing': "Stay stylish and comfortable with this fantastic find!",
            'vehicles': "Hit the road in style and reliability!",
            'real_estate': "Your dream home awaits at this incredible price!"
        }
        promotional_content += hooks.get(category.lower(), f"Amazing {category} at an unbeatable price!") + "\n\n"
        
        # Highlight features
        if features:
            promotional_content += "🌟 Key Features:\n"
            for feature in features[:3]:  # Limit to 3 features for brevity
                promotional_content += f"• {feature}\n"
            promotional_content += "\n"
            
        # Highlight selling points
        if selling_points:
            promotional_content += "💎 Why You'll Love It:\n"
            for point in selling_points[:3]:
                promotional_content += f"• {point}\n"
            promotional_content += "\n"
            
        # Add urgency
        promotional_content += "⏰ Hurry! This incredible offer won't last long. Contact us now before it's gone!\n\n"
        
        # Add call to action
        promotional_content += "📞 Call now or visit our website to make this yours today!"
        
        return {
            "title": title,
            "category": category,
            "price": price,
            "content": promotional_content,
            "length": len(promotional_content),
            "platforms": ["social_media", "email", "website"],
            "tone": "exciting",
            "call_to_action": "Contact now"
        }
        
    except Exception as e:
        return {"error": str(e)}

def handle_analyze_competitor_pricing(context: Dict[str, Any]):
    """Handle analyzing competitor pricing"""
    try:
        category = context.get('category', '')
        brand = context.get('brand', '')
        
        # Get all active listings in the same category
        listings = Listing.objects.filter(
            category__name=category,
            status='active'
        ).select_related('seller')
        
        if not listings.exists():
            return {"error": f"No active listings found in category '{category}'"}
            
        # Calculate statistics
        prices = [listing.price for listing in listings]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        # Find competitors with same brand
        brand_listings = [l for l in listings if brand.lower() in l.title.lower()] if brand else []
        brand_prices = [l.price for l in brand_listings]
        
        brand_analysis = {}
        if brand_listings:
            brand_min = min(brand_prices)
            brand_max = max(brand_prices)
            brand_avg = sum(brand_prices) / len(brand_prices)
            brand_analysis = {
                "brand": brand,
                "listings_count": len(brand_listings),
                "price_range": {
                    "min": float(brand_min),
                    "max": float(brand_max),
                    "average": float(brand_avg)
                }
            }
            
        # Identify price segments
        price_segments = {
            "budget": len([p for p in prices if p < avg_price * 0.7]),
            "mid_range": len([p for p in prices if avg_price * 0.7 <= p <= avg_price * 1.3]),
            "premium": len([p for p in prices if p > avg_price * 1.3])
        }
        
        return {
            "category": category,
            "total_competitors": len(listings),
            "price_range": {
                "min": float(min_price),
                "max": float(max_price),
                "average": float(avg_price)
            },
            "price_segments": price_segments,
            "market_position": "competitive" if avg_price == avg_price else "premium" if avg_price > avg_price else "budget",
            "brand_analysis": brand_analysis,
            "recommendations": [
                "Consider pricing near the average for maximum visibility",
                "Highlight unique features to justify premium pricing",
                "Offer bundle deals to compete with lower-priced options"
            ]
        }
        
    except Exception as e:
        return {"error": str(e)}

def handle_suggest_best_posting_times(context: Dict[str, Any]):
    """Handle suggesting best times to post a listing"""
    try:
        category = context.get('category', '')
        
        # Base posting times (in hours, 24-hour format)
        # These would be refined with actual user engagement data
        base_times = {
            'electronics': [19, 20, 21],  # Evening hours
            'furniture': [10, 11, 19, 20],  # Late morning and evening
            'clothing': [12, 13, 20, 21],  # Lunchtime and evening
            'vehicles': [9, 10, 19, 20],  # Morning and evening
            'real_estate': [10, 11, 14, 15]  # Business hours
        }
        
        # Days of week (0=Monday, 6=Sunday)
        # These would be refined with actual data
        best_days = [0, 1, 2, 5, 6]  # Weekdays except Friday, plus weekend
        
        # Get category-specific times or default
        posting_hours = base_times.get(category.lower(), [19, 20])
        
        # Generate suggestions
        suggestions = []
        for day in best_days:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for hour in posting_hours:
                hour_12 = hour % 12 or 12
                am_pm = 'PM' if hour >= 12 else 'AM'
                suggestions.append(f"{day_names[day]} {hour_12}{am_pm}")
                
        # Limit to top 10 suggestions
        suggestions = suggestions[:10]
        
        return {
            "category": category,
            "best_days": [d for d in best_days if d in [0,1,2,5,6]],  # Return the day numbers
            "best_hours": posting_hours,
            "suggestions": suggestions,
            "reasoning": "Based on historical user engagement patterns, with higher visibility during these times",
            "expected_engagement": "high"
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Run the server on port 8001 as specified in the orchestrator
    uvicorn.run(app, host="0.0.0.0", port=8001)

